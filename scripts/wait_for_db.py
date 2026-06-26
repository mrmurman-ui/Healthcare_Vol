import os
import time
import psycopg2

url = os.environ["DATABASE_URL_SYNC"]

for i in range(30):
    try:
        psycopg2.connect(url)
        print("DB ready")
        break
    except Exception:
        print(f"Retry {i+1}/30...")
        time.sleep(2)