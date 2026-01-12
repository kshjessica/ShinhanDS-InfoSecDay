import sqlite3

conn = sqlite3.connect("demo.db")

with open("schema.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())

conn.close()
print("demo.db 초기화 완료")
