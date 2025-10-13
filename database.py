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
    create table if not exists users (
        id integer primary key autoincrement,
        username text unique not null,
        password text not null,
        created_at timestamp default current_timestamp
    )
    ''')
    
    # 创建账户表
    cursor.execute('''
    create table if not exists accounts (
        id integer primary key autoincrement,
        user_id integer not null,
        name text not null,
        type text not null,
        balance real default 0,
        created_at timestamp default current_timestamp,
        foreign key (user_id) references users (id)
    )
    ''')
    
    # 创建分类表（预置一些常用分类）
    cursor.execute('''
    create table if not exists categories (
        id integer primary key autoincrement,
        user_id integer,  
        name text not null,
        type text not null,
        unique(user_id, name, type)
    )
    ''')
    
    # 创建交易记录表
    cursor.execute('''
    create table if not exists transactions (
        id integer primary key autoincrement,
        user_id integer not null,
        account_id integer not null,
        type text not null,
        amount real not null,
        category_id integer not null,
        date timestamp default current_timestamp,
        description text,
        created_at timestamp default current_timestamp,
        foreign key (user_id) references users (id),
        foreign key (account_id) references accounts (id),
        foreign key (category_id) references categories (id)
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
    
    cursor.executemany('insert or ignore into categories (user_id, name, type) values (?, ?, ?)', preset_categories)
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)