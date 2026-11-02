"""One-request, logged-out Marketplace accessibility diagnostic.

No login, cookies, proxy, CAPTCHA handling, pagination, or scraping of private data.
This is an access feasibility check, not a working listings monitor.
"""
import asyncio
import json
from urllib.parse import urlencode
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

SEARCH_URL = "https://www.facebook.com/marketplace/brisbane/search/?" + urlencode(
    {"query": "ergonomic office chair", "maxPrice": 100}
)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="en-AU", timezone_id="Australia/Brisbane")
        page = await context.new_page()
        try:
            response = await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2500)
            final_url = page.url
            title = await page.title()
            item_links = await page.locator('a[href*="/marketplace/item/"]').count()
            login_detected = any(x in final_url.lower() for x in ("/login", "/checkpoint"))
            print(json.dumps({
                "http_status": response.status if response else None,
                "final_url": final_url.split("?")[0],
                "page_title": title[:120],
                "listing_link_count": item_links,
                "login_or_checkpoint_redirect": login_detected,
                "note": "Links may be absent despite public listings; a count alone does not establish reliable access."
            }, ensure_ascii=False, indent=2))
            if login_detected:
                print("RESULT: LOGIN_REQUIRED_OR_CHECKPOINT — stop; do not bypass.")
            elif item_links:
                print("RESULT: PUBLIC_LISTING_LINKS_VISIBLE — inspect data quality in a later test.")
            else:
                print("RESULT: NO_LISTING_LINKS — access not demonstrated.")
        except PlaywrightTimeout:
            print("RESULT: TIMEOUT — page did not load within 30 seconds.")
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
