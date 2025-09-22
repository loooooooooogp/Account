from database import get_db_connection

def add_account(user_id, name, type, initial_balance=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO accounts (user_id, name, type, balance) VALUES (?, ?, ?, ?)', 
                   (user_id, name, type, initial_balance))
    conn.commit()
    conn.close()

def get_accounts(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, type, balance FROM accounts WHERE user_id = ?', (user_id,))
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def update_account(account_id, user_id, updates):
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = []
    params = []
    for key, value in updates.items():
        set_clause.append(f"{key} = ?")
        params.append(value)
    params.append(account_id)
    params.append(user_id)
    cursor.execute(f'UPDATE accounts SET {", ".join(set_clause)} WHERE id = ? AND user_id = ?', params)
    conn.commit()
    conn.close()

def delete_account(account_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 检查该账户下是否有交易记录
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE account_id = ? AND user_id = ?', (account_id, user_id))
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return False  # 有交易记录，不能删除
    cursor.execute('DELETE FROM accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    conn.commit()
    conn.close()
    return True