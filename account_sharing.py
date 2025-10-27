# account_sharing.py
from database import get_db_connection

def link_user_account(owner_user_id, linked_username, account_id, permission_level='read'):
    """
    将账户关联给其他用户
    owner_user_id: 账户所有者的用户ID
    linked_username: 要关联的用户名
    account_id: 要关联的账户ID
    permission_level: 权限级别 ('read' 或 'write')
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 验证账户是否存在且属于当前用户
        cursor.execute('SELECT id FROM accounts WHERE id = ? AND user_id = ?', 
                      (account_id, owner_user_id))
        account = cursor.fetchone()
        if not account:
            return False, "账户不存在或无权操作"
        
        # 2. 查找要关联的用户
        cursor.execute('SELECT id FROM users WHERE username = ?', (linked_username,))
        linked_user = cursor.fetchone()
        if not linked_user:
            return False, "用户不存在"
        
        linked_user_id = linked_user[0]
        
        # 3. 不能关联给自己
        if linked_user_id == owner_user_id:
            return False, "不能将账户关联给自己"
        
        # 4. 检查是否已经关联
        cursor.execute('''SELECT id FROM user_account_links 
                         WHERE linked_user_id = ? AND account_id = ?''', 
                      (linked_user_id, account_id))
        if cursor.fetchone():
            return False, "该账户已经关联给此用户"
        
        # 5. 创建关联
        cursor.execute('''INSERT INTO user_account_links 
                         (owner_user_id, linked_user_id, account_id, permission_level) 
                         VALUES (?, ?, ?, ?)''', 
                      (owner_user_id, linked_user_id, account_id, permission_level))
        
        conn.commit()
        return True, "账户关联成功"
        
    except Exception as e:
        conn.rollback()
        return False, f"关联失败: {str(e)}"
    finally:
        conn.close()

def unlink_user_account(owner_user_id, link_id):
    """
    解除账户关联
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 验证关联记录是否存在且属于当前用户
        cursor.execute('''SELECT id FROM user_account_links 
                         WHERE id = ? AND owner_user_id = ?''', 
                      (link_id, owner_user_id))
        if not cursor.fetchone():
            return False, "关联记录不存在或无权操作"
        
        cursor.execute('DELETE FROM user_account_links WHERE id = ?', (link_id,))
        conn.commit()
        return True, "解除关联成功"
        
    except Exception as e:
        conn.rollback()
        return False, f"解除关联失败: {str(e)}"
    finally:
        conn.close()

def get_linked_accounts(user_id):
    """
    获取用户被关联的账户（其他用户共享给该用户的账户）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ual.id, ual.account_id, a.name, a.type, a.balance, 
               u.username as owner_username, ual.permission_level, ual.created_at
        FROM user_account_links ual
        JOIN accounts a ON ual.account_id = a.id
        JOIN users u ON ual.owner_user_id = u.id
        WHERE ual.linked_user_id = ?
        ORDER BY ual.created_at DESC
    ''', (user_id,))
    
    linked_accounts = cursor.fetchall()
    conn.close()
    
    return linked_accounts

def get_shared_accounts(user_id):
    """
    获取用户共享给其他用户的账户
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ual.id, ual.account_id, a.name, a.type, 
               u.username as linked_username, ual.permission_level, ual.created_at
        FROM user_account_links ual
        JOIN accounts a ON ual.account_id = a.id
        JOIN users u ON ual.linked_user_id = u.id
        WHERE ual.owner_user_id = ?
        ORDER BY ual.created_at DESC
    ''', (user_id,))
    
    shared_accounts = cursor.fetchall()
    conn.close()
    
    return shared_accounts

def validate_linked_account_access(user_id, account_id, require_write=False):
    """
    验证用户是否有权访问关联账户
    require_write: 是否需要写权限
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否是账户所有者
    cursor.execute('SELECT id FROM accounts WHERE id = ? AND user_id = ?', 
                  (account_id, user_id))
    if cursor.fetchone():
        conn.close()
        return True  # 是账户所有者，拥有全部权限
    
    # 检查是否有关联权限
    if require_write:
        cursor.execute('''SELECT id FROM user_account_links 
                         WHERE linked_user_id = ? AND account_id = ? AND permission_level = 'write' ''', 
                      (user_id, account_id))
    else:
        cursor.execute('''SELECT id FROM user_account_links 
                         WHERE linked_user_id = ? AND account_id = ?''', 
                      (user_id, account_id))
    
    has_access = cursor.fetchone() is not None
    conn.close()
    return has_access