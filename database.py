import sqlite3
import os

DB_PATH = 'data/finance.db'

def init_db():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建账户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        balance REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建分类表（预置一些常用分类）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,  
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        UNIQUE(user_id, name, type)
    )
    ''')
    
    # 创建交易记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        account_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category_id INTEGER NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (account_id) REFERENCES accounts (id),
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    # 插入预置分类
    preset_categories = [
        (None, '工资', 'income'),
        (None, '奖金', 'income'),
        (None, '餐饮', 'expense'),
        (None, '交通', 'expense'),
        (None, '购物', 'expense'),
        (None, '医疗', 'expense'),
        (None, '教育', 'expense'),
        (None, '娱乐', 'expense'),
        (None, '其他', 'expense')
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO categories (user_id, name, type) VALUES (?, ?, ?)', preset_categories)
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)