from flask import Flask, render_template, request, redirect, send_file, abort
import sqlite3
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# =========================
# Paths (ABSOLUTE) - 중요!
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "demo.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULT_DIR = os.path.join(BASE_DIR, "inspection_result")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# =========================
# DB Helpers
# =========================
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    - demo.db 없으면 생성됨(연결 시 자동 생성)
    - users / inspections 테이블 없으면 생성
    - users 비어있으면 더미 데이터 주입
    """
    conn = get_db()
    cur = conn.cursor()

    # users: 자산 마스터
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        asset_no TEXT NOT NULL UNIQUE,
        sticker_no TEXT
    )
    """)

    # inspections: 자산별 최신 점검 1건만 유지(덮어쓰기)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_no TEXT NOT NULL UNIQUE,

        sticker_no TEXT,
        item1 INTEGER,
        item2 INTEGER,
        item3 INTEGER,
        item4 INTEGER,
        item5 INTEGER,

        comment TEXT,
        photo_path TEXT,

        inspect_date TEXT,
        inspector TEXT,
        status TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(asset_no) REFERENCES users(asset_no)
    )
    """)

    # 더미 데이터 (asset_no는 UNIQUE)
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO users (name, department, asset_no, sticker_no)
            VALUES (?,?,?,?)
        """, [
            ("김서현", "사이버대응팀", "PC-001", "ST-1001"),
            ("김범준", "사이버대응팀", "PC-002", "ST-1002"),
            ("주혜진", "사이버대응팀", "PC-003", "ST-1003"),
            ("전남재", "사이버대응팀", "PC-004", "ST-1004"),
        ])

    conn.commit()

    # 디버그 로그: 실제 DB 파일 경로/데이터 확인
    cur.execute("SELECT COUNT(*) FROM users")
    print("✅ DB PATH:", DB_FILE)
    print("✅ USERS COUNT:", cur.fetchone()[0])

    conn.close()

# =========================
# Routes
# =========================
@app.route("/")
def index():
    """
    - 자산 전체 목록 + 검색(성명/부서/자산번호)
    - 상단 통계(전체/완료)
    - 자산번호 클릭 -> 상세(/detail/<asset_no>)
    - 하단 엑셀 다운로드 버튼(/export)
    """
    q = request.args.get("q", "").strip()

    conn = get_db()
    cur = conn.cursor()

    # 목록 (검색 포함) + 점검 상태 join
    users = cur.execute("""
        SELECT
            u.name, u.department, u.asset_no, u.sticker_no AS master_sticker,
            i.status,
            i.inspect_date, i.inspector
        FROM users u
        LEFT JOIN inspections i
          ON u.asset_no = i.asset_no
        WHERE u.name LIKE ?
           OR u.department LIKE ?
           OR u.asset_no LIKE ?
        ORDER BY u.asset_no
    """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()

    # 통계는 전체 users 기준 + submitted 기준
    total = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    done = cur.execute("SELECT COUNT(*) FROM inspections WHERE status='submitted'").fetchone()[0]

    conn.close()
    return render_template("index.html", users=users, total=total, done=done, q=q)


@app.route("/detail/<asset_no>", methods=["GET", "POST"])
def detail(asset_no):
    """
    - 자산 상세 점검 입력 페이지
    - 저장 시 inspections에 asset_no 기준으로 insert/replace (자산당 최신 1건)
    - 사진 첨부 + 코멘트 + 스티커번호 + 5개 항목 + 점검일/점검자
    """
    conn = get_db()
    cur = conn.cursor()

    user = cur.execute("SELECT * FROM users WHERE asset_no=?", (asset_no,)).fetchone()
    if not user:
        conn.close()
        abort(404, description="Unknown asset_no")

    inspection = cur.execute("SELECT * FROM inspections WHERE asset_no=?", (asset_no,)).fetchone()

    if request.method == "POST":
        form = request.form

        # 사진 저장
        photo = request.files.get("photo")
        photo_path = inspection["photo_path"] if inspection else None

        if photo and photo.filename:
            safe_name = photo.filename.replace("/", "_").replace("\\", "_")
            filename = f"{asset_no}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(photo_path)

        # inspections: asset_no UNIQUE라서 replace로 덮어쓰기
        cur.execute("""
            INSERT OR REPLACE INTO inspections (
                asset_no,
                sticker_no,
                item1, item2, item3, item4, item5,
                comment, photo_path,
                inspect_date, inspector, status
            )
            VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, (
            asset_no,
            form.get("sticker_no") or user["sticker_no"],
            int(form.get("item1", 1)),
            int(form.get("item2", 1)),
            int(form.get("item3", 1)),
            int(form.get("item4", 1)),
            int(form.get("item5", 1)),
            form.get("comment", ""),
            photo_path,
            form.get("inspect_date", ""),
            form.get("inspector", ""),
            "submitted"
        ))

        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template("detail.html", user=user, inspection=inspection)


@app.route("/export")
def export():
    """
    - inspection_result/ 폴더에 저장
    - 파일명: 정보보호의날_<점검날짜>_<점검자>.xlsx
      - 점검날짜: 오늘 날짜(YYYYMMDD) (데모 기준)
      - 점검자: inspections에 존재하는 첫 값 없으면 '점검자'
    """
    conn = get_db()

    df = pd.read_sql("""
        SELECT
            u.name AS 성명,
            u.department AS 부서,
            u.asset_no AS 자산번호,
            u.sticker_no AS 마스터스티커번호,
            i.sticker_no AS 확인스티커번호,
            i.item1 AS 항목1,
            i.item2 AS 항목2,
            i.item3 AS 항목3,
            i.item4 AS 항목4,
            i.item5 AS 항목5,
            i.inspect_date AS 점검일,
            i.inspector AS 점검자,
            i.comment AS 코멘트,
            i.status AS 상태
        FROM users u
        LEFT JOIN inspections i
          ON u.asset_no = i.asset_no
        ORDER BY u.asset_no
    """, conn)

    conn.close()

    today = datetime.now().strftime("%Y%m%d")
    inspector = (
        df["점검자"].dropna().iloc[0]
        if not df["점검자"].dropna().empty
        else "점검자"
    )

    filename = f"정보보호의날_{today}_{inspector}.xlsx"
    file_path = os.path.join(RESULT_DIR, filename)

    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)


# =========================
# Main
# =========================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
