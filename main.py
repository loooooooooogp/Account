import sys
import getpass
import platform
from database import init_db, get_db_connection
from auth import register_user, login_user
from transaction_manager import add_transaction, get_transactions, edit_transaction, delete_transaction
from account_manager import add_account, get_accounts, delete_account, update_account
from mystatistics import get_category_stats, get_monthly_stats, get_account_stats, get_summary
from utils import input_date, input_float, input_int

# 新增密码输入函数，显示星号
def input_password(prompt="密码: "):
    """显示星号的密码输入函数"""
    if platform.system() == "Windows":
        # Windows 平台
        import msvcrt
        print(prompt, end='', flush=True)
        password = []
        while True:
            ch = msvcrt.getch()
            if ch in [b'\r', b'\n']:  # 回车键
                print('')
                break
            elif ch == b'\x08':  # 退格键
                if password:
                    password.pop()
                    print('\b \b', end='', flush=True)
            else:
                password.append(ch.decode('utf-8'))
                print('*', end='', flush=True)
        return ''.join(password)
    else:
        # Linux/Mac 平台
        import termios
        import tty
        print(prompt, end='', flush=True)
        password = []
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ['\r', '\n']:  # 回车键
                    print('')
                    break
                elif ch == '\x7f':  # 退格键
                    if password:
                        password.pop()
                        print('\b \b', end='', flush=True)
                else:
                    password.append(ch)
                    print('*', end='', flush=True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ''.join(password)
    

# 在 main.py 中修改 get_user_categories 函数
def get_user_categories(user_id, transaction_type=None):
    """返回用户可见的分类 (id, name, type)，去除重复"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    if transaction_type:
        # 使用 DISTINCT 确保不返回重复记录
        cur.execute("""
            SELECT DISTINCT id, name, type, user_id 
            FROM categories 
            WHERE (user_id = ? OR user_id IS NULL) AND type = ?
            ORDER BY user_id DESC, id ASC
        """, (user_id, transaction_type))
    else:
        cur.execute("""
            SELECT DISTINCT id, name, type, user_id 
            FROM categories 
            WHERE (user_id = ? OR user_id IS NULL)
            ORDER BY user_id DESC, id ASC
        """, (user_id,))
    
    rows = cur.fetchall()
    conn.close()

    # 使用字典来确保名称唯一性
    seen_names = set()
    unique_categories = []
    
    for cid, name, ctype, cuid in rows:
        if name not in seen_names:
            seen_names.add(name)
            unique_categories.append((cid, name, ctype))
    
    return unique_categories
def validate_account_access(user_id, account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    ok = cur.fetchone() is not None
    conn.close()
    return ok


def validate_category_access(user_id, category_id, transaction_type=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if transaction_type:
        cur.execute('SELECT id FROM categories WHERE id = ? AND (user_id = ? OR user_id IS NULL) AND type = ?', (category_id, user_id, transaction_type))
    else:
        cur.execute('SELECT id FROM categories WHERE id = ? AND (user_id = ? OR user_id IS NULL)', (category_id, user_id))
    ok = cur.fetchone() is not None
    conn.close()
    return ok


def add_transaction_flow(current_user):
    user_id = current_user[0]
    accounts = get_accounts(user_id)
    if not accounts:
        print("暂无账户，请先添加账户！")
        return
    
    print("可用账户：")
    for a in accounts:
        print(f"{a[0]}. {a[1]} (余额: {a[3]:.2f})")

    while True:
        aid = input_int("请选择账户ID: ")
        if validate_account_access(user_id, aid):
            break
        print("无效账户ID")

    while True:
        t = input("类型 (income/expense): ").lower()
        if t in ('income', 'expense'):
            break
        print("类型错误")

    cats = get_user_categories(user_id, t)
    if not cats:
        print("没有可用分类")
        return
    
    print("可用分类：")
    for c in cats:
        print(f"{c[0]}. {c[1]}")

    while True:
        cid = input_int("请选择分类ID: ")
        if validate_category_access(user_id, cid, t):
            break
        print("无效分类ID")

    amt = input_float("金额: ")
    if amt <= 0:
        print("金额必须大于0")
        return
    
    dt = input_date("日期 (YYYY-MM-DD)")  # 确保提示信息正确
    
    desc = input("备注(可选): ").strip() or None
    
    # 修复日期格式字符串
    ok = add_transaction(user_id, aid, t, amt, cid, dt.strftime('%Y-%m-%d'), desc)
    print("添加成功" if ok else "添加失败")


def view_transactions_flow(current_user):
    user_id = current_user[0]
    filters = {}
    print("1. 全部 2. 按类型 3. 按分类 4. 按时间 5. 组合")
    ch = input("请选择: ").strip()
    if ch == '2':
        while True:
            t = input("类型 (income/expense): ").lower()
            if t in ('income', 'expense'):
                filters['type'] = t
                break
            print("类型错误")
    elif ch == '3':
        cats = get_user_categories(user_id)
        for c in cats:
            print(f"{c[0]}. {c[1]} ({c[2]})")
        cid = input_int("分类ID: ")
        if validate_category_access(user_id, cid):
            filters['category_id'] = cid
    elif ch == '4':
        filters['start_date'] = input("开始日期: ")
        filters['end_date'] = input("结束日期: ")
    elif ch == '5':
        if input("按类型过滤? (y/n): ").lower() == 'y':
            while True:
                t = input("类型 (income/expense): ").lower()
                if t in ('income', 'expense'):
                    filters['type'] = t
                    break
        if input("按分类过滤? (y/n): ").lower() == 'y':
            cats = get_user_categories(user_id)
            for c in cats:
                print(f"{c[0]}. {c[1]} ({c[2]})")
            cid = input_int("分类ID: ")
            if validate_category_access(user_id, cid):
                filters['category_id'] = cid
        if input("按时间过滤? (y/n): ").lower() == 'y':
            filters['start_date'] = input("开始日期: ")
            filters['end_date'] = input("结束日期: ")

    records = get_transactions(user_id, filters)
    if not records:
        print("没有记录")
        return
    if filters.get('start_date') and filters.get('end_date'):
        summ = get_summary(user_id, filters['start_date'], filters['end_date'])
        print(f"统计: 收入 {summ['total_income']:.2f} 支出 {summ['total_expense']:.2f} 结余 {summ['balance']:.2f}")

    print(f"找到 {len(records)} 条记录")
    for r in records:
        tid, t, amt, cat, acc, date, desc = r
        print(f"{tid} | {t} | {amt:.2f} | {cat} | {acc} | {date} | {desc}")

    while True:
        op = input("1 编辑 2 删除 3 返回: ").strip()
        if op == '1':
            edit_transaction_flow(current_user, records)
            break
        elif op == '2':
            delete_transaction_flow(current_user, records)
            break
        elif op == '3':
            break


def edit_transaction_flow(current_user, records):
    tid = input_int("输入交易ID: ")
    rec = next((r for r in records if r[0] == tid), None)
    if not rec:
        print("无效ID")
        return
    updates = {}
    print("选择字段修改: 1账户 2类型 3金额 4分类 5日期 6备注 7保存")
    while True:
        c = input("选择: ").strip()
        if c == '1':
            for a in get_accounts(current_user[0]):
                print(f"{a[0]}. {a[1]}")
            updates['account_id'] = input_int("新的账户ID: ")
        elif c == '2':
            nt = input("新的类型: ").lower()
            updates['type'] = nt
        elif c == '3':
            updates['amount'] = input_float("新的金额: ")
        elif c == '4':
            tt = updates.get('type', rec[1])
            for cat in get_user_categories(current_user[0], tt):
                print(f"{cat[0]}. {cat[1]}")
            updates['category_id'] = input_int("新的分类ID: ")
        elif c == '5':
            nd = input_date("新的日期")
            updates['date'] = nd.strftime('%Y-%m-%d')
        elif c == '6':
            updates['description'] = input("新的备注: ").strip() or None
        elif c == '7':
            break
        else:
            print("无效选择")
    if updates:
        ok = edit_transaction(tid, current_user[0], updates)
        print("修改成功" if ok else "修改失败")


def delete_transaction_flow(current_user, records):
    tid = input_int("输入交易ID: ")
    rec = next((r for r in records if r[0] == tid), None)
    if not rec:
        print("无效ID")
        return
    if input("确认删除? (y/n): ").lower() == 'y':
        ok = delete_transaction(tid, current_user[0])
        print("删除成功" if ok else "删除失败")

# 在 main.py 的已登录用户菜单部分添加
def account_sharing_flow(current_user):
    """账户关联管理流程"""
    user_id = current_user[0]
    
    while True:
        print("\n=== 账户共享管理 ===")
        print("1. 共享我的账户给其他用户")
        print("2. 查看我共享的账户")
        print("3. 查看我被共享的账户")
        print("4. 取消共享")
        print("5. 返回主菜单")
        
        choice = input("请选择: ").strip()
        
        if choice == '1':
            share_account_flow(current_user)
        elif choice == '2':
            view_shared_accounts_flow(current_user)
        elif choice == '3':
            view_linked_accounts_flow(current_user)
        elif choice == '4':
            unshare_account_flow(current_user)
        elif choice == '5':
            break
        else:
            print("无效选择")

def share_account_flow(current_user):
    """共享账户流程"""
    user_id = current_user[0]
    
    # 获取用户自己的账户
    from account_manager import get_accounts
    accounts = get_accounts(user_id, include_linked=False)
    
    if not accounts:
        print("您还没有账户，请先添加账户")
        return
    
    print("您的账户:")
    for acc in accounts:
        print(f"{acc[0]}. {acc[1]} ({acc[2]}) - 余额: {acc[3]:.2f}")
    
    account_id = input_int("选择要共享的账户ID: ")
    
    # 验证账户所有权
    from account_sharing import validate_linked_account_access
    if not validate_linked_account_access(user_id, account_id):
        print("账户不存在或无权操作")
        return
    
    linked_username = input("输入要共享给的用户名: ").strip()
    if not linked_username:
        print("用户名不能为空")
        return
    
    print("权限级别:")
    print("1. 只读 (只能查看)")
    print("2. 读写 (可以查看和添加交易)")
    perm_choice = input("选择权限级别: ").strip()
    
    permission_level = 'read'
    if perm_choice == '2':
        permission_level = 'write'
    
    from account_sharing import link_user_account
    success, message = link_user_account(user_id, linked_username, account_id, permission_level)
    print(message)

def view_shared_accounts_flow(current_user):
    """查看我共享的账户"""
    user_id = current_user[0]
    
    from account_sharing import get_shared_accounts
    shared_accounts = get_shared_accounts(user_id)
    
    if not shared_accounts:
        print("您还没有共享任何账户")
        return
    
    print("\n您共享的账户:")
    print("-" * 60)
    for link in shared_accounts:
        link_id, account_id, name, acc_type, linked_user, permission, created_at = link
        perm_text = "读写" if permission == 'write' else "只读"
        print(f"关联ID: {link_id} | 账户: {name} ({acc_type}) | 共享给: {linked_user} | 权限: {perm_text}")

def view_linked_accounts_flow(current_user):
    """查看我被共享的账户"""
    user_id = current_user[0]
    
    from account_sharing import get_linked_accounts
    linked_accounts = get_linked_accounts(user_id)
    
    if not linked_accounts:
        print("您还没有被共享任何账户")
        return
    
    print("\n您被共享的账户:")
    print("-" * 60)
    for link in linked_accounts:
        link_id, account_id, name, acc_type, balance, owner, permission, created_at = link
        perm_text = "读写" if permission == 'write' else "只读"
        print(f"关联ID: {link_id} | 账户: {name} ({acc_type}) | 所有者: {owner} | 余额: {balance:.2f} | 权限: {perm_text}")

def unshare_account_flow(current_user):
    """取消共享流程"""
    user_id = current_user[0]
    
    from account_sharing import get_shared_accounts
    shared_accounts = get_shared_accounts(user_id)
    
    if not shared_accounts:
        print("您还没有共享任何账户")
        return
    
    print("您共享的账户:")
    for link in shared_accounts:
        link_id, account_id, name, acc_type, linked_user, permission, created_at = link
        print(f"关联ID: {link_id} | 账户: {name} | 共享给: {linked_user}")
    
    link_id = input_int("输入要取消的关联ID: ")
    
    from account_sharing import unlink_user_account
    success, message = unlink_user_account(user_id, link_id)
    print(message)


def main():
    init_db()
    current_user = None
    while True:
        if current_user is None:
            print("\n=== 个人账簿管理系统 ===")
            print("1 注册 2 登录 3 退出")
            c = input("请选择: ").strip()
            if c == '1':
                u = input("用户名: ")
                p = input_password("密码: ")
                if register_user(u, p):
                    print("注册成功")
                else:
                    print("用户名已存在")
            elif c == '2':
                u = input("用户名: ")
                p = input_password("密码: ")
                user = login_user(u, p)
                if user:
                    current_user = user
                    print(f"登录成功，欢迎 {current_user[1]}")
                else:
                    print("登录失败")
            elif c == '3':
                print("退出")
                sys.exit(0)
            else:
                print("无效选择")
        else:
            print("\n=== 主菜单 ===")
            print("1 添加交易 2 查看交易 3 管理账户 4 查看统计 5 账户关联 6退出登录")
            c = input("请选择: ").strip()
            if c == '1':
                add_transaction_flow(current_user)
            elif c == '2':
                view_transactions_flow(current_user)
            elif c == '3':
                print("\n--- 账户管理 ---")
                print("1 添加 2 查看 3 删除 4 更新 5 返回")
                ac = input("请选择: ").strip()
                if ac == '1':
                    name = input("名称: ")
                    at = input("类型: ")
                    bal = input_float("初始余额: ")
                    add_account(current_user[0], name, at, bal)
                elif ac == '2':
                    for a in get_accounts(current_user[0]):
                        print(f"{a[0]} | {a[1]} | {a[2]} | {a[3]}")
                elif ac == '3':
                    did = input_int("删除ID: ")
                    if delete_account(did, current_user[0]):
                        print("删除成功")
                    else:
                        print("删除失败")
                elif ac == '4':
                    for a in get_accounts(current_user[0]):
                        print(f"{a[0]} | {a[1]} | {a[2]} | {a[3]}")
                    uid = input_int("更新ID: ")
                    new_name = input("新名(回车跳过): ").strip()
                    new_type = input("新类型(回车跳过): ").strip()
                    new_bal = None
                    bi = input("新余额(回车跳过): ").strip()
                    if bi:
                        try:
                            new_bal = float(bi)
                        except ValueError:
                            print("余额格式错误")
                    up = {}
                    if new_name:
                        up['name'] = new_name
                    if new_type:
                        up['type'] = new_type
                    if new_bal is not None:
                        up['balance'] = new_bal
                    if up:
                        update_account(uid, current_user[0], up)
                else:
                    pass
            elif c == '4':
                print("\n--- 统计 ---")
                print("1 分类 2 月份 3 账户 4 汇总")
                sc = input("请选择: ").strip()
                if sc == '1':
                    s = input("开始: ")
                    e = input("结束: ")
                    for r in get_category_stats(current_user[0], s, e):
                        print(r)
                elif sc == '2':
                    y = int(input("年份: "))
                    for r in get_monthly_stats(current_user[0], y):
                        print(r)
                elif sc == '3':
                    s = input("开始: ")
                    e = input("结束: ")
                    for r in get_account_stats(current_user[0], s, e):
                        print(r)
                elif sc == '4':
                    s = input("开始: ")
                    e = input("结束: ")
                    for k, v in get_summary(current_user[0], s, e).items():
                        print(f"{k}: {v}")
            elif c == '5':
                account_sharing_flow(current_user)
            elif c == '6':
                current_user = None
            else:
                print("无效选择")

if __name__ == '__main__':
    main()