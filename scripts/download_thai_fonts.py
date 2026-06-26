"""
Download Thai fonts for PDF export support.
Run once: python scripts/download_thai_fonts.py

Downloads NotoSansThai from Google Fonts CDN.
"""
import os, sys, urllib.request

FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "static", "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

FONT_URLS = [
    (
        "https://fonts.gstatic.com/s/notosansthai/v20/iJWnBXeUZi_OHPqn4wq6hQ2_hbJ1xyN9wd43SofCRg.ttf",
        "NotoSansThai-Regular.ttf",
    ),
    (
        "https://fonts.gstatic.com/s/notosansthai/v20/iJWnBXeUZi_OHPqn4wq6hQ2_hbJ1xyN9wd43SofCRg.ttf",
        "NotoSansThai-Bold.ttf",
    ),
]

print("[Thai Font Installer] Downloading Noto Sans Thai...")
success = 0
for url, fname in FONT_URLS:
    dest = os.path.join(FONTS_DIR, fname)
    if os.path.isfile(dest):
        print(f"  [SKIP] {fname} already exists")
        success += 1
        continue
    try:
        print(f"  Downloading {fname}...", end=" ", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r, open(dest, "wb") as f:
            f.write(r.read())
        size = os.path.getsize(dest)
        print(f"OK ({size:,} bytes)")
        success += 1
    except Exception as e:
        print(f"FAILED: {e}")
        print(f"  --> Manual install: copy '{fname}' to {FONTS_DIR}")

if success == len(FONT_URLS):
    print("\n[OK] Thai fonts installed. Restart the application.")
else:
    print(f"\n[WARN] {success}/{len(FONT_URLS)} fonts installed.")
    print("For manual install see: app/static/fonts/README.md")
