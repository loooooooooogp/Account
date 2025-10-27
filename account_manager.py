# account_manager.py
from database import get_db_connection

def add_account(user_id, name, type, initial_balance=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO accounts (user_id, name, type, balance) VALUES (?, ?, ?, ?)', 
                       (user_id, name, type, initial_balance))
        conn.commit()
        print(f"调试: 账户添加成功 - 用户ID: {user_id}, 账户名: {name}")  # 添加调试信息
        return True
    except Exception as e:
        print(f"调试: 添加账户时出错: {str(e)}")  # 添加调试信息
        return False
    finally:
        conn.close()

def get_accounts(user_id, include_linked=True):
    """
    获取用户账户，包括关联的账户
    include_linked: 是否包含关联的账户
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    accounts = []
    
    # 获取用户自己的账户
    cursor.execute('SELECT id, name, type, balance FROM accounts WHERE user_id = ?', (user_id,))
    user_accounts = cursor.fetchall()
    for acc in user_accounts:
        accounts.append(acc)  # 格式: (id, name, type, balance)
    
    # 获取关联的账户（如果需要）
    if include_linked:
        try:
            from account_sharing import get_linked_accounts
            linked_accounts = get_linked_accounts(user_id)
            for link in linked_accounts:
                link_id, account_id, name, acc_type, balance, owner, permission, created_at = link
                # 在账户名称后添加所有者信息
                display_name = f"{name} ({owner})"
                accounts.append((account_id, display_name, acc_type, balance))
        except ImportError:
            print("警告: account_sharing 模块未找到，只返回自有账户")
        except Exception as e:
            print(f"获取关联账户时出错: {e}")
    
    conn.close()
    return accounts

def update_account(account_id, user_id, updates):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证账户所有权
    cursor.execute('SELECT id FROM accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    if not cursor.fetchone():
        conn.close()
        print("错误: 账户不存在或无权操作")
        return False
    
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
    return True

def delete_account(account_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证账户所有权
    cursor.execute('SELECT id FROM accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    if not cursor.fetchone():
        conn.close()
        print("错误: 账户不存在或无权操作")
        return False
    
    # 检查该账户下是否有交易记录
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE account_id = ?', (account_id,))
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        print("错误: 该账户下有交易记录，无法删除")
        return False
    
    # 删除该账户的所有关联记录
    try:
        cursor.execute('DELETE FROM user_account_links WHERE account_id = ? AND owner_user_id = ?', 
                      (account_id, user_id))
    except Exception as e:
        print(f"警告: 删除账户关联记录时出错: {e}")
    
    cursor.execute('DELETE FROM accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    conn.commit()
    conn.close()
    return True

def get_own_accounts(user_id):
    """
    只获取用户自己的账户，不包括关联账户
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, type, balance FROM accounts WHERE user_id = ?', (user_id,))
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def validate_account_ownership(user_id, account_id):
    """
    验证用户是否拥有该账户的所有权
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    result = cursor.fetchone() is not None
    conn.close()
    return result