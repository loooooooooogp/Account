import sys
from database import init_db
from auth import register_user, login_user
from transaction_manager import add_transaction, get_transactions, edit_transaction, delete_transaction
from account_manager import add_account, get_accounts, delete_account
from mystatistics import get_category_stats, get_monthly_stats, get_account_stats, get_summary
from utils import input_date, input_float, input_int

def main():
    init_db()
    current_user = None
    
    while True:
        if current_user is None:
            print("\n=== 个人账簿管理系统 ===")
            print("1. 注册")
            print("2. 登录")
            print("3. 退出")
            choice = input("请选择操作: ")
            
            if choice == '1':
                username = input("用户名: ")
                password = input("密码: ")
                if register_user(username, password):
                    print("注册成功！")
                else:
                    print("用户名已存在。")
            elif choice == '2':
                username = input("用户名: ")
                password = input("密码: ")
                user = login_user(username, password)
                if user:
                    current_user = user
                    print(f"登录成功，欢迎 {username}！")
                else:
                    print("用户名或密码错误。")
            elif choice == '3':
                print("再见！")
                sys.exit(0)
            else:
                print("无效选择。")
        else:
            print("\n=== 主菜单 ===")
            print("1. 添加交易记录")
            print("2. 查看交易记录")
            print("3. 管理账户")
            print("4. 查看统计")
            print("5. 退出登录")
            choice = input("请选择操作: ")
            
            if choice == '1':
                # 添加交易记录
                print("\n--- 添加交易记录 ---")
                accounts = get_accounts(current_user[0])
                if not accounts:
                    print("请先添加账户！")
                    continue
                print("可用账户：")
                for acc in accounts:
                    print(f"{acc[0]}. {acc[1]} (类型: {acc[2]}, 余额: {acc[3]})")
                account_id = input_int("请选择账户ID: ")
                t_type = input("类型 (income/expense): ")
                if t_type not in ('income', 'expense'):
                    print("类型输入错误！")
                    continue
                # 分类选择
                from database import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM categories WHERE (user_id = ? OR user_id IS NULL) AND type = ?", (current_user[0], t_type))
                categories = cursor.fetchall()
                conn.close()
                if not categories:
                    print("请先添加分类！")
                    continue
                print("可用分类：")
                for cat in categories:
                    print(f"{cat[0]}. {cat[1]}")
                category_id = input_int("请选择分类ID: ")
                amount = input_float("金额: ")
                date = input_date("日期")
                description = input("备注(可选): ")
                add_transaction(current_user[0], account_id, t_type, amount, category_id, date, description)
                print("交易记录添加成功！")
            elif choice == '2':
                # 查看交易记录
                print("\n--- 查看交易记录 ---")
                filters = {}
                print("1. 全部  2. 按类型  3. 按分类  4. 按时间段")
                f_choice = input("请选择过滤方式(回车为全部): ")
                if f_choice == '2':
                    t_type = input("类型 (income/expense): ")
                    if t_type in ('income', 'expense'):
                        filters['type'] = t_type
                elif f_choice == '3':
                    from database import get_db_connection
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, name FROM categories WHERE (user_id = ? OR user_id IS NULL)", (current_user[0],))
                    categories = cursor.fetchall()
                    conn.close()
                    print("可用分类：")
                    for cat in categories:
                        print(f"{cat[0]}. {cat[1]}")
                    category_id = input_int("请选择分类ID: ")
                    filters['category_id'] = category_id
                elif f_choice == '4':
                    filters['start_date'] = input("开始日期 (YYYY-MM-DD): ")
                    filters['end_date'] = input("结束日期 (YYYY-MM-DD): ")
                    records = get_transactions(current_user[0], filters)
                if not records:
                    print("无交易记录。"); continue
                print("ID | 类型 | 金额 | 分类 | 账户 | 日期 | 备注")
                for r in records:
                    print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]}")
                # 可选：编辑/删除
                print("1. 编辑 2. 删除 3. 返回")
                op = input("请选择操作: ")
                if op == '1':
                    tid = input_int("输入要编辑的交易ID: ")
                    field = input("要修改的字段(account_id/type/amount/category_id/date/description): ")
                    value = input("新值: ")
                    if field in ('amount',):
                        value = float(value)
                    elif field in ('account_id', 'category_id'):
                        value = int(value)
                    elif field == 'date':
                        from utils import input_date
                        value = input_date("新日期")
                    updates = {field: value}
                    if edit_transaction(tid, current_user[0], updates):
                        print("修改成功！")
                    else:
                        print("修改失败！")
                elif op == '2':
                    tid = input_int("输入要删除的交易ID: ")
                    if delete_transaction(tid, current_user[0]):
                        print("删除成功！")
                    else:
                        print("删除失败！")
                else:
                    continue
            elif choice == '3':
                # 管理账户
                print("\n--- 账户管理 ---")
                print("1. 添加账户 2. 查看账户 3. 删除账户 4. 返回")
                acc_choice = input("请选择: ")
                if acc_choice == '1':
                    name = input("账户名称: ")
                    acc_type = input("账户类型(如现金/银行卡): ")
                    balance = input_float("初始余额: ")
                    add_account(current_user[0], name, acc_type, balance)
                    print("账户添加成功！")
                elif acc_choice == '2':
                    accounts = get_accounts(current_user[0])
                    print("ID | 名称 | 类型 | 余额")
                    for acc in accounts:
                        print(f"{acc[0]} | {acc[1]} | {acc[2]} | {acc[3]}")
                elif acc_choice == '3':
                    accounts = get_accounts(current_user[0])
                    print("ID | 名称 | 类型 | 余额")
                    for acc in accounts:
                        print(f"{acc[0]} | {acc[1]} | {acc[2]} | {acc[3]}")
                    del_id = input_int("输入要删除的账户ID: ")
                    if delete_account(del_id, current_user[0]):
                        print("删除成功！")
                    else:
                        print("账户下有交易记录，无法删除！")
                else:
                    continue
            elif choice == '4':
                # 查看统计
                print("\n--- 统计功能 ---")
                print("1. 按分类统计")
                print("2. 按月份统计")
                print("3. 按账户统计")
                print("4. 财务汇总")
                stat_choice = input("请选择统计类型: ")
                if stat_choice == '1':
                    start_date = input("开始日期 (YYYY-MM-DD): ")
                    end_date = input("结束日期 (YYYY-MM-DD): ")
                    result = get_category_stats(current_user[0], start_date, end_date)
                    print("按分类统计结果:")
                    for row in result:
                        print(row)
                elif stat_choice == '2':
                    year = input("年份 (如2024): ")
                    result = get_monthly_stats(current_user[0], int(year))
                    print("按月份统计结果:")
                    for row in result:
                        print(row)
                elif stat_choice == '3':
                    start_date = input("开始日期 (YYYY-MM-DD): ")
                    end_date = input("结束日期 (YYYY-MM-DD): ")
                    result = get_account_stats(current_user[0], start_date, end_date)
                    print("按账户统计结果:")
                    for row in result:
                        print(row)
                elif stat_choice == '4':
                    start_date = input("开始日期 (YYYY-MM-DD): ")
                    end_date = input("结束日期 (YYYY-MM-DD): ")
                    summary = get_summary(current_user[0], start_date, end_date)
                    print("财务汇总:")
                    for k, v in summary.items():
                        print(f"{k}: {v}")
                else:
                    print("无效选择。")
            elif choice == '5':
                current_user = None
                print("已退出登录。")
            else:
                print("无效选择。")

if __name__ == '__main__':
    main()