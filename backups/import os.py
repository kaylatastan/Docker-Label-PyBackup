import os
import time
import datetime
import pymysql
import csv

DB_HOST = os.environ.get('DB_HOST', 'mysql')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'rootpassword')
DB_NAME = os.environ.get('DB_NAME', 'sampledb')
BACKUP_DIR = '/app/backups'

def wait_for_db():
    for _ in range(20):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor
            )
            conn.close()
            return
        except Exception as e:
            print("Waiting for DB...", e)
            time.sleep(3)
    raise Exception("Database not available.")

def backup_products():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    if not rows:
        print("No data found in products table.")
        return
    columns = rows[0].keys()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{BACKUP_DIR}/products_backup_{timestamp}.csv"
    with open(backup_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    cursor.close()
    conn.close()
    print(f"Backup completed: {backup_file}")

if __name__ == "__main__":
    wait_for_db()
    backup_products()
