# auth.py
import hashlib
import sqlite3
from database import get_db_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        print(f"调试: 用户 {username} 注册成功，用户ID: {cursor.lastrowid}")  # 添加调试信息
        return True
    except sqlite3.IntegrityError:
        print(f"调试: 用户名 {username} 已存在")  # 添加调试信息
        return False
    except Exception as e:
        print(f"调试: 注册时发生错误: {str(e)}")  # 添加调试信息
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', (username, hashed_password))
    user = cursor.fetchone()
    print(f"调试: 登录查询结果 - 用户: {user}")  # 添加调试信息
    conn.close()
    return user