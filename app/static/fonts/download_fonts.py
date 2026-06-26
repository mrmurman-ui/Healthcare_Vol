"""
Run this ONCE on your machine to download Noto Sans Thai fonts.
py -3.12 scripts/download_fonts.py
"""
import urllib.request, os, sys

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "app", "static", "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

# Google Fonts API URLs for Noto Sans Thai woff2
FONT_URLS = {
    "NotoSansThai-300.woff2":  "https://fonts.gstatic.com/s/notosansthai/v25/iJWqBXeUZi_OHPqn4wq6kgXtAZytyF0E2_iFZA.woff2",
    "NotoSansThai-400.woff2":  "https://fonts.gstatic.com/s/notosansthai/v25/iJWnBXeUZi_OHPqn4wq6hQ2_hbJ1xyN9wd43SofpEg.woff2",
    "NotoSansThai-500.woff2":  "https://fonts.gstatic.com/s/notosansthai/v25/iJWqBXeUZi_OHPqn4wq6kgXtAZytyF0E2_iFZA.woff2",
    "NotoSansThai-600.woff2":  "https://fonts.gstatic.com/s/notosansthai/v25/iJWqBXeUZi_OHPqn4wq6kgXtAZytybcq2_iFZA.woff2",
    "NotoSansThai-700.woff2":  "https://fonts.gstatic.com/s/notosansthai/v25/iJWqBXeUZi_OHPqn4wq6kgXtAZytyKIq2_iFZA.woff2",
    "NotoSansThai-800.woff2":  "https://fonts.gstatic.com/s/notosansthai/v25/iJWqBXeUZi_OHPqn4wq6kgXtAZytyL4q2_iFZA.woff2",
}

headers = {"User-Agent": "Mozilla/5.0"}
success = 0
for filename, url in FONT_URLS.items():
    dest = os.path.join(FONTS_DIR, filename)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"  ✅ Already exists: {filename}")
        success += 1
        continue
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r, open(dest, "wb") as f:
            data = r.read()
            f.write(data)
        print(f"  ✅ Downloaded: {filename} ({len(data):,} bytes)")
        success += 1
    except Exception as e:
        print(f"  ❌ Failed: {filename} — {e}")

print(f"\n{success}/{len(FONT_URLS)} fonts ready in: {FONTS_DIR}")
if success == len(FONT_URLS):
    print("✅ All fonts downloaded! Restart the app.")
else:
    print("⚠️  Some fonts missing. The app will use Google CDN as fallback.")
