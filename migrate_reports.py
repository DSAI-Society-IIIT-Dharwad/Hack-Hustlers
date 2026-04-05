import sqlite3, os

db_path = os.path.join('instance', 'telemedicine.db')
if not os.path.exists(db_path):
    db_path = 'telemedicine.db'

conn = sqlite3.connect(db_path)
try:
    conn.execute("ALTER TABLE reports ADD COLUMN native_report TEXT DEFAULT ''")
    print('Added native_report column')
except Exception as e:
    print(f'native_report already exists or error: {e}')

try:
    conn.execute("ALTER TABLE reports ADD COLUMN native_language TEXT DEFAULT 'en'")
    print('Added native_language column')
except Exception as e:
    print(f'native_language already exists or error: {e}')

conn.commit()
conn.close()
print('Migration complete')
