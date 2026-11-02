"""Infrastructure-only smoke test. Does not access Facebook or send notifications."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("about:blank")
        print("PASS: Chromium launched on GitHub Actions")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
