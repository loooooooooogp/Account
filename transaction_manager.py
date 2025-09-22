from database import get_db_connection
from datetime import datetime

def add_transaction(user_id, account_id, type, amount, category_id, date, description=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 首先更新账户余额
    if type == 'income':
        cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))
    else:
        cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))
    
    # 插入交易记录
    cursor.execute('''
    INSERT INTO transactions (user_id, account_id, type, amount, category_id, date, description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, account_id, type, amount, category_id, date, description))
    
    conn.commit()
    conn.close()

def get_transactions(user_id, filters=None):
    # filters 可以是一个字典，包含类型、分类、时间范围等
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
    SELECT t.id, t.type, t.amount, c.name as category, a.name as account, t.date, t.description
    FROM transactions t
    JOIN categories c ON t.category_id = c.id
    JOIN accounts a ON t.account_id = a.id
    WHERE t.user_id = ?
    '''
    params = [user_id]
    
    if filters:
        if 'type' in filters:
            query += ' AND t.type = ?'
            params.append(filters['type'])
        if 'category_id' in filters:
            query += ' AND t.category_id = ?'
            params.append(filters['category_id'])
        if 'start_date' in filters:
            query += ' AND t.date >= ?'
            params.append(filters['start_date'])
        if 'end_date' in filters:
            query += ' AND t.date <= ?'
            params.append(filters['end_date'])
    
    query += ' ORDER BY t.date DESC'
    cursor.execute(query, params)
    transactions = cursor.fetchall()
    conn.close()
    return transactions

def edit_transaction(transaction_id, user_id, updates):
    # updates 是一个字典，包含要更新的字段
    conn = get_db_connection()
    cursor = conn.cursor()
    # 先获取原交易记录
    cursor.execute('SELECT account_id, type, amount FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
    old_trans = cursor.fetchone()
    if not old_trans:
        conn.close()
        return False
    
    old_account_id, old_type, old_amount = old_trans
    
    # 首先恢复原账户余额
    if old_type == 'income':
        cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (old_amount, old_account_id))
    else:
        cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (old_amount, old_account_id))
    
    # 更新交易记录
    set_clause = []
    params = []
    for key, value in updates.items():
        set_clause.append(f"{key} = ?")
        params.append(value)
    params.append(transaction_id)
    params.append(user_id)
    
    cursor.execute(f'UPDATE transactions SET {", ".join(set_clause)} WHERE id = ? AND user_id = ?', params)
    
    # 更新新账户余额
    new_account_id = updates.get('account_id', old_account_id)
    new_type = updates.get('type', old_type)
    new_amount = updates.get('amount', old_amount)
    
    if new_type == 'income':
        cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (new_amount, new_account_id))
    else:
        cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (new_amount, new_account_id))
    
    conn.commit()
    conn.close()
    return True

def delete_transaction(transaction_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 先获取交易记录以更新账户余额
    cursor.execute('SELECT account_id, type, amount FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
    trans = cursor.fetchone()
    if not trans:
        conn.close()
        return False
    
    account_id, type, amount = trans
    if type == 'income':
        cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))
    else:
        cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))
    
    cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
    conn.commit()
    conn.close()
    return True