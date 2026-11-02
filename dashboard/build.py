import json
import html
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import yaml

from marketwatcher.models import AppConfig
from marketwatcher.marketplace import MarketplaceBrowser
from marketwatcher.parser import parse_listings, matches_watch

config = AppConfig.model_validate(
    yaml.safe_load(Path("config.yaml").read_text())
)

results = []
browser = MarketplaceBrowser(config.scanner)

try:
    browser.start()
    for watch in config.watches:
        if not watch.enabled:
            continue

        page = browser.open_url(watch.marketplace_url)
        try:
            listings = parse_listings(
                page, watch, config.scanner.max_listings_per_watch
            )
            for listing in listings:
                if not matches_watch(listing, watch):
                    continue

                anchor = page.query_selector(
                    f'a[href*="/marketplace/item/{listing.listing_id}/"]'
                )
                img = anchor.query_selector("img") if anchor else None
                image_url = img.get_attribute("src") if img else None

                results.append({
                    "id": listing.stable_id,
                    "name": listing.title,
                    "price": listing.price_text,
                    "location": listing.location_text,
                    "image": image_url,
                    "url": f"https://www.facebook.com/marketplace/item/{listing.listing_id}/"
                        if listing.listing_id else listing.url,
                    "watch": watch.name
                })
        finally:
            page.close()
finally:
    browser.close()

folder = Path("dashboard")
(folder / "listings.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2)
)

cards = []
for item in results:
    image = html.escape(item["image"] or "", quote=True)
    url = html.escape(item["url"], quote=True)
    name = html.escape(item["name"])
    price = html.escape(item["price"] or "Price unavailable")
    location = html.escape(item["location"] or "")

    category = html.escape(item["watch"], quote=True)
    cards.append(f"""
    <a class="card" data-category="{category}" href="{url}" target="_blank" rel="noopener noreferrer">
      <img src="{image}" alt="" loading="lazy">
      <div class="details">
        <strong>{price}</strong>
        <div>{name}</div>
        <small>{location}</small>
      </div>
    </a>
    """)

document = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Marketplace Dashboard</title>
<style>
body {font-family:system-ui,sans-serif; margin:0; background:#f5f6f8; color:#20242a}
header {padding:24px; background:white; border-bottom:1px solid #ddd}
h1 {font-size:24px; margin:0 0 8px}
p {color:#666; margin:0}
main {max-width:1100px; margin:24px auto; padding:0 16px}
.grid {display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:16px}
.card {background:white; border-radius:14px; overflow:hidden; color:inherit;
text-decoration:none; box-shadow:0 2px 8px #0001}
.card img {width:100%; aspect-ratio:1; object-fit:cover; background:#eee}
.details {padding:12px; line-height:1.5}
strong {font-size:19px}
small {color:#777}

nav {display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px}
nav button {border:1px solid #ddd; border-radius:20px; padding:10px 16px;
background:white; cursor:pointer; font-size:14px}
nav button.active {background:#20242a; color:white}
</style>
</head>
<body>
<header><h1>Marketplace Dashboard</h1>
<p>Latest scan · __COUNT__ listings · __TIME__</p></header>
<main>
<nav id="filters"></nav>
<div class="grid">__CARDS__</div>
</main>

<script>
const cards = [...document.querySelectorAll(".card")];
const categories = [...new Set(cards.map(c => c.dataset.category))];
const filters = document.getElementById("filters");

function showCategory(category) {
  cards.forEach(card => {
    card.style.display =
      category === "All Items" || card.dataset.category === category
      ? "" : "none";
  });
  filters.querySelectorAll("button").forEach(button => {
    button.classList.toggle("active", button.dataset.category === category);
  });
}

for (const category of categories) {
  const button = document.createElement("button");
  const count = category === "All Items"
    ? cards.length
    : cards.filter(c => c.dataset.category === category).length;
  button.textContent = `${category} (${count})`;
  button.dataset.category = category;
  button.onclick = () => showCategory(category);
  filters.appendChild(button);
}
if (categories.length) showCategory(categories[0]);
</script>
</body></html>
"""

document = (document
    .replace("__COUNT__", str(len(results)))
    .replace("__TIME__", datetime.now().strftime("%Y-%m-%d %H:%M"))
    .replace("__CARDS__", "\n".join(cards))
)

(folder / "index.html").write_text(document)
print(f"Dashboard created: {len(results)} listings")
