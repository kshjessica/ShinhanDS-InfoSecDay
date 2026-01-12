from flask import Flask, render_template, request, redirect, jsonify, send_file
import sqlite3
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
DB_FILE = "demo.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# 초기 DB 생성
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        department TEXT,
        asset_no TEXT,
        sticker_no TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspect_date TEXT,
        inspector TEXT,
        name TEXT,
        department TEXT,
        asset_no TEXT,
        sticker_no TEXT,
        item1 INTEGER,
        item2 INTEGER,
        item3 INTEGER,
        item4 INTEGER,
        item5 INTEGER,
        comment TEXT,
        photo_path TEXT,
        status TEXT
    )
    """)

    # 데모용 사용자 데이터
    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cur.executemany("""
        INSERT INTO users (name, department, asset_no, sticker_no)
        VALUES (?,?,?,?)
        """, [
            ("김서현", "정보보호본부", "PC-001", "ST-1001"),
            ("이민수", "개발팀", "PC-002", "ST-1002"),
            ("박지은", "기획팀", "PC-003", "ST-1003")
        ])

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    cur = conn.cursor()

    users = cur.execute("SELECT name FROM users").fetchall()

    if request.method == "POST":
        data = request.form
        photo = request.files.get("photo")

        photo_path = None
        if photo and photo.filename:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}"
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(photo_path)

        cur.execute("""
        INSERT INTO inspections (
            inspect_date, inspector, name, department,
            asset_no, sticker_no,
            item1, item2, item3, item4, item5,
            comment, photo_path, status
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["inspect_date"],
            data["inspector"],
            data["name"],
            data["department"],
            data["asset_no"],
            data["sticker_no"],
            data["item1"],
            data["item2"],
            data["item3"],
            data["item4"],
            data["item5"],
            data.get("comment"),
            photo_path,
            data["status"]
        ))

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    conn.close()
    return render_template("index.html", users=users)


@app.route("/get_user")
def get_user():
    name = request.args.get("name")
    conn = get_db()
    cur = conn.cursor()

    user = cur.execute(
        "SELECT department, asset_no, sticker_no FROM users WHERE name=?",
        (name,)
    ).fetchone()

    conn.close()

    if user:
        return jsonify(dict(user))
    return jsonify({})


@app.route("/dashboard")
def dashboard():
    conn = get_db()
    df = pd.read_sql(
        "SELECT * FROM inspections WHERE status='submitted'", conn
    )
    conn.close()

    total = len(df)
    if total == 0:
        compliance = 0
        weak_count = 0
    else:
        compliance = round(
            (df[["item1","item2","item3","item4","item5"]] == 1)
            .sum().sum() / (total * 5) * 100, 1
        )
        weak_count = (df[["item1","item2","item3","item4","item5"]] == 0).sum().sum()

    return render_template(
        "dashboard.html",
        total=total,
        compliance=compliance,
        weak_count=weak_count
    )


@app.route("/export")
def export():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM inspections", conn)
    conn.close()

    file_name = "inspection_result.xlsx"
    df.to_excel(file_name, index=False)
    return send_file(file_name, as_attachment=True)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
