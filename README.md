# 📌 정보보호의 날 점검 웹 (Demo)

사내 정보보호의 날에 수행하는 **PC·자산 보안 점검을 수기에서 웹 기반으로 전환**하기 위한
**간단한 데모용 웹 애플리케이션**입니다.

Python(Flask)을 사용해 빠르게 구축했으며,
점검 입력 → 자동 채움 → 통계 가시화 → 엑셀 출력까지의 **전체 흐름 시연**을 목적으로 합니다.

---

## 1. 주요 기능

### ✅ 점검 입력

* 점검일, 점검자 입력
* 성명 선택 시 **부서 / 자산번호 / 스티커번호 자동 채움**
* 5개 점검 항목 체크

  1. 본체용(하드디스크) 보안스티커
  2. 스마트키퍼/케이블락
  3. 클린데스크
  4. 퇴근 시 PC OFF
  5. 패스워드 메모
* 사진 첨부
* 코멘트 입력
* **임시저장 / 제출** 구분

### 📊 대시보드

* 전체 점검률 가시화
* 제출 건수 확인

### 📁 결과 관리

* 점검 결과 **엑셀(.xlsx) 다운로드**

---

## 2. 기술 스택

* Backend: **Python 3 + Flask**
* DB: **SQLite**
* Frontend: HTML + Bootstrap(간단 UI)
* Data Export: **pandas, openpyxl**
* 파일 업로드: 로컬 디렉터리 저장

---

## 3. 프로젝트 구조

```
.
├─ app.py              # Flask 메인 앱
├─ demo.db             # SQLite DB
├─ templates/
│  ├─ index.html       # 점검 입력 화면
│  └─ dashboard.html   # 통계 대시보드
├─ uploads/            # 사진 첨부 파일 저장
├─ inspection_result.xlsx  # 엑셀 출력 파일
└─ README.md
```

---

## 4. DB 구조

### 1️⃣ 사용자(자산) 마스터

```sql
users (
  id INTEGER PK,
  name TEXT,
  department TEXT,
  asset_no TEXT,
  sticker_no TEXT
)
```

### 2️⃣ 점검 결과

```sql
inspections (
  id INTEGER PK,
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
  status TEXT   -- temp / submitted
)
```

---

## 5. 실행 방법

### 1️⃣ 환경 준비

```bash
pip install flask pandas openpyxl
```

### 2️⃣ DB 초기화

```bash
python
>>> import sqlite3
>>> conn = sqlite3.connect("demo.db")
>>> conn.executescript(open("schema.sql").read())
>>> conn.close()
```

*(또는 app.py 실행 후 수동 생성 가능)*

### 3️⃣ 서버 실행

```bash
python app.py
```

### 4️⃣ 접속

```
http://127.0.0.1:5000
```

---

## 6. 사용 흐름 (데모 시연 기준)

1. 점검자 웹 접속
2. 성명 선택 → 자산 정보 자동 입력
3. 현장 점검 후 체크 + 사진 첨부
4. 임시저장 또는 제출
5. 대시보드에서 점검률 확인
6. 엑셀로 결과 다운로드

---

## 7. 데모 한계 및 향후 확장 방향

### 🔹 현재 (데모)

* 로컬 계정/DB
* 수동 사용자 등록
* 단일 점검 회차

### 🔹 확장 가능

* 사내 SSO 연동
* 자산관리 시스템 연계
* QR/바코드 스캔
* 부서/회차별 통계
* 미흡 항목 조치 워크플로우
* 모바일 앱(WebView) 연동

---

## 8. 활용 목적

* 정보보호의 날 **디지털 전환 PoC**
* 사내앱 개발 전 **요구사항 정렬 및 공감대 형성**
* C-Level / 유관부서 **시연용 데모**
