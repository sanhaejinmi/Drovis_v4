import sqlite3
import bcrypt
from core.db import get_user_connection

# 회원가입
def register_user(username, password, email):
    conn = get_user_connection()     # DB 연결
    cur = conn.cursor()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        cur.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, hashed_pw, email),
        )
        conn.commit()
        return True, "회원가입 성공"
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 아이디 또는 이메일"
    finally:
        conn.close()

# 로그인 검증
def verify_user(username, password):
    conn = get_user_connection()     # DB 연결
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    # 입력된 비밀번호화 해시 비교
    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        return True
    return False
