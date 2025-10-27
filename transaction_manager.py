from database import get_db_connection
from datetime import datetime

# 添加账户共享相关的导入
from account_sharing import validate_linked_account_access

def add_transaction(user_id, account_id, type, amount, category_id, date, description=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 修改：检查账户是否属于当前用户或当前用户有写权限的关联账户
    if not validate_linked_account_access(user_id, account_id, require_write=True):
        conn.close()
        print("错误：账户不存在或您没有写权限。")
        return False

    # 检查分类是否属于当前用户或系统预置
    cursor.execute('SELECT id FROM categories WHERE id = ? AND (user_id = ? OR user_id IS NULL)', (category_id, user_id))
    if not cursor.fetchone():
        conn.close()
        print("错误：分类不存在或不可用。")
        return False

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
    return True

def get_transactions(user_id, filters=None):
    # filters 可以是一个字典，包含类型、分类、时间范围等
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 修改查询：包括用户自己的交易和关联账户的交易
    query = '''
    SELECT t.id, t.type, t.amount, c.name as category, a.name as account, t.date, t.description
    FROM transactions t
    JOIN categories c ON t.category_id = c.id
    JOIN accounts a ON t.account_id = a.id
    WHERE (t.user_id = ? OR t.account_id IN (
        SELECT account_id FROM user_account_links WHERE linked_user_id = ?
    ))
    '''
    params = [user_id, user_id]
    
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
    
    # 修改：先获取原交易记录，检查用户是否有权限编辑
    cursor.execute('''
        SELECT t.account_id, t.type, t.amount, t.user_id 
        FROM transactions t
        WHERE t.id = ? AND (t.user_id = ? OR t.account_id IN (
            SELECT account_id FROM user_account_links 
            WHERE linked_user_id = ? AND permission_level = 'write'
        ))
    ''', (transaction_id, user_id, user_id))
    
    old_trans = cursor.fetchone()
    if not old_trans:
        conn.close()
        print("错误：交易记录不存在或您没有编辑权限。")
        return False
    
    old_account_id, old_type, old_amount, transaction_owner = old_trans
    
    # 检查新账户的权限（如果更新了账户）
    new_account_id = updates.get('account_id', old_account_id)
    if new_account_id != old_account_id:
        if not validate_linked_account_access(user_id, new_account_id, require_write=True):
            conn.close()
            print("错误：您没有对新账户的写权限。")
            return False
    
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
    
    # 修改：更新条件，只更新用户有权限的交易
    cursor.execute(f'''
        UPDATE transactions 
        SET {", ".join(set_clause)} 
        WHERE id = ? AND (user_id = ? OR account_id IN (
            SELECT account_id FROM user_account_links 
            WHERE linked_user_id = ? AND permission_level = 'write'
        ))
    ''', params + [user_id, user_id])
    
    # 更新新账户余额
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
    
    # 修改：先获取交易记录，检查用户是否有权限删除
    cursor.execute('''
        SELECT account_id, type, amount 
        FROM transactions 
        WHERE id = ? AND (user_id = ? OR account_id IN (
            SELECT account_id FROM user_account_links 
            WHERE linked_user_id = ? AND permission_level = 'write'
        ))
    ''', (transaction_id, user_id, user_id))
    
    trans = cursor.fetchone()
    if not trans:
        conn.close()
        print("错误：交易记录不存在或您没有删除权限。")
        return False
    
    account_id, type, amount = trans
    
    # 恢复账户余额
    if type == 'income':
        cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))
    else:
        cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))
    
    # 删除交易记录
    cursor.execute('''
        DELETE FROM transactions 
        WHERE id = ? AND (user_id = ? OR account_id IN (
            SELECT account_id FROM user_account_links 
            WHERE linked_user_id = ? AND permission_level = 'write'
        ))
    ''', (transaction_id, user_id, user_id))
    
    conn.commit()
    conn.close()
    return True

# 新增函数：获取用户有权限访问的所有账户的交易
def get_all_accessible_transactions(user_id, filters=None):
    """
    获取用户有权限访问的所有账户的交易记录
    包括用户自己的账户和关联账户
    """
    if filters is None:
        filters = {}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建查询：包括用户自己的交易和所有关联账户的交易
    query = '''
    SELECT t.id, t.type, t.amount, c.name as category, a.name as account, 
           t.date, t.description, u.username as transaction_owner,
           CASE 
               WHEN t.user_id = ? THEN 'own'
               ELSE 'linked'
           END as ownership
    FROM transactions t
    JOIN categories c ON t.category_id = c.id
    JOIN accounts a ON t.account_id = a.id
    JOIN users u ON t.user_id = u.id
    WHERE (t.user_id = ? OR t.account_id IN (
        SELECT account_id FROM user_account_links WHERE linked_user_id = ?
    ))
    '''
    params = [user_id, user_id, user_id]
    
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
        if 'account_id' in filters:
            query += ' AND t.account_id = ?'
            params.append(filters['account_id'])
    
    query += ' ORDER BY t.date DESC, t.id DESC'
    cursor.execute(query, params)
    transactions = cursor.fetchall()
    conn.close()
    
    return transactions