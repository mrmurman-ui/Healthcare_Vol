"""
Download Noto Sans Thai — standalone, no PYTHONPATH needed.
Run from ANYWHERE: py -3.12 scripts\download_fonts.py
"""
import urllib.request, os, re, sys

# Save fonts next to THIS script's parent folder → app/static/fonts/
THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT    = os.path.dirname(THIS_DIR)
FONTS_DIR  = os.path.join(PROJECT, "app", "static", "fonts")

os.makedirs(FONTS_DIR, exist_ok=True)
print(f"Saving fonts to: {FONTS_DIR}\n")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/css,*/*;q=0.1",
}

CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Noto+Sans+Thai:wght@300;400;500;600;700;800"
    "&display=swap"
)

# 1. Fetch CSS
print("Fetching font list from Google Fonts...")
try:
    req = urllib.request.Request(CSS_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        css = r.read().decode("utf-8")
    print(f"  Got CSS ({len(css)} chars)\n")
except Exception as e:
    print(f"  ERROR: {e}")
    print("\nCheck your internet connection and try again.")
    sys.exit(1)

# 2. Parse all weight+url pairs
pairs = re.findall(
    r"font-weight:\s*(\d+).*?url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)",
    css, re.DOTALL
)

# Deduplicate (keep first per weight)
seen = {}
for weight, url in pairs:
    if weight not in seen:
        seen[weight] = url

if not seen:
    print("Could not parse URLs. CSS snippet:")
    print(css[:800])
    sys.exit(1)

print(f"Found {len(seen)} font weights: {sorted(seen.keys())}\n")

# 3. Download each
ok = 0
for weight in sorted(seen.keys()):
    url  = seen[weight]
    name = f"NotoSansThai-{weight}.woff2"
    dest = os.path.join(FONTS_DIR, name)

    if os.path.exists(dest) and os.path.getsize(dest) > 500:
        print(f"  ✅ Already exists: {name}")
        ok += 1
        continue

    try:
        req2 = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req2, timeout=20) as r2:
            data = r2.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"  ✅ {name}  ({len(data):,} bytes)")
        ok += 1
    except Exception as e:
        print(f"  ❌ {name}  FAILED: {e}")

print(f"\n{'='*55}")
print(f"{ok}/{len(seen)} fonts downloaded to:\n  {FONTS_DIR}")
if ok >= 4:
    print("\n✅ SUCCESS — restart the app and fonts will load.")
else:
    print("\n⚠️  Some fonts missing. Re-run the script.")
