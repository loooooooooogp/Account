# database.py
import sqlite3
import os

DB_PATH = 'data/finance.db'

# 在 database.py 中修改 init_db 函数
def init_db():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # 检查数据库是否已经初始化
    db_exists = os.path.exists(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_account_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_user_id INTEGER NOT NULL,  -- 账户所有者
        linked_user_id INTEGER NOT NULL,  -- 被关联的用户
        account_id INTEGER NOT NULL,      -- 被关联的账户
        permission_level TEXT DEFAULT 'read',  -- read: 只读, write: 可写
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_user_id) REFERENCES users (id),
        FOREIGN KEY (linked_user_id) REFERENCES users (id),
        FOREIGN KEY (account_id) REFERENCES accounts (id),
        UNIQUE(linked_user_id, account_id)  -- 防止重复关联
    )
    ''')
    # 只有在新数据库时才插入预置分类
    if not db_exists:
        print("初始化新数据库，插入预置分类...")
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
        print(f"插入了 {len(preset_categories)} 个预置分类")
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)