from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
from urllib.parse import urlencode
import yaml
import math
import os
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "dashboard"
CONFIG = ROOT / "config.yaml"

app = Flask(__name__)


def update_search_url(original, keyword):
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

    default = "https://www.facebook.com/marketplace/brisbane/search"
    parsed = urlparse(original or default)

    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.facebook.com"
        or not parsed.path.startswith("/marketplace/")
    ):
        parsed = urlparse(default)

    params = dict(parse_qsl(parsed.query))
    params["query"] = keyword
    params["sortBy"] = "creation_time_descend"

    return urlunparse(parsed._replace(query=urlencode(params)))

@app.route("/")
def home():
    return send_from_directory(DASHBOARD, "index.html")


@app.route("/manage")
def manage():
    return send_from_directory(DASHBOARD, "manage.html")

@app.get("/api/monitors")
def get_monitors():
    data = yaml.safe_load(CONFIG.read_text())
    return jsonify(data.get("watches", []))

@app.post("/api/monitors")
def save_monitors():
    payload = request.get_json(silent=True)

    if not isinstance(payload, list):
        return jsonify(error="Expected a list"), 400

    if len(payload) > 30:
        return jsonify(error="Too many monitors"), 400

    watches = []

    for item in payload:
        if not isinstance(item, dict):
            return jsonify(error="Invalid monitor"), 400

        name = str(item.get("name", "")).strip()
        keyword = str(item.get("keyword", "")).strip()

        try:
            price = float(item.get("max_price", 0))
        except (TypeError, ValueError):
            return jsonify(error="Invalid price"), 400

        if not name or not keyword or len(name) > 100 or len(keyword) > 150:
            return jsonify(error="Invalid name or keyword"), 400

        if not 0 <= price <= 100000:
            return jsonify(error="Price out of range"), 400


        location_mode = item.get("location_mode", "current")
        radius_km = item.get("radius_km", 20)
        latitude = item.get("latitude")
        longitude = item.get("longitude")

        try:
            radius_km = float(radius_km)
            if radius_km not in (5, 10, 20, 40, 100):
                raise ValueError()

            if latitude is not None and longitude is not None:
                latitude = float(latitude)
                longitude = float(longitude)
                if not (math.isfinite(latitude) and math.isfinite(longitude)
                        and -90 <= latitude <= 90
                        and -180 <= longitude <= 180):
                    raise ValueError()
            elif latitude is not None or longitude is not None:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify(error="Invalid location or radius"), 400


        # Preserve existing monitor settings where possible
        existing = next(
            (
                w for w in
                yaml.safe_load(CONFIG.read_text()).get("watches", [])
                if w.get("name") == name
            ),
            {}
        )

        watches.append({
            "name": name,
            "enabled": item.get("enabled", True) is True,
            "marketplace_url":
                update_search_url(existing.get("marketplace_url"), keyword),
            "max_price": price,
            "notify_on_free": True,
            "currency": "AUD",
            "keywords_include": existing.get("keywords_include", []),
            "keywords_exclude": existing.get("keywords_exclude", []),
            "location_mode": location_mode,
            "radius_km": radius_km,
            "latitude": latitude,
            "longitude": longitude
        })

    config = yaml.safe_load(CONFIG.read_text())
    config["watches"] = watches

    fd, temporary = tempfile.mkstemp(
        prefix=".config-", suffix=".yaml", dir=ROOT
    )

    try:
        with os.fdopen(fd, "w") as file:
            yaml.safe_dump(config, file, sort_keys=False, allow_unicode=True)
        os.replace(temporary, CONFIG)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    return jsonify(success=True, count=len(watches))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
