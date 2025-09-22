import sys
from database import init_db
from auth import register_user, login_user
from transaction_manager import add_transaction, get_transactions, edit_transaction, delete_transaction
from account_manager import add_account, get_accounts, delete_account
from statistics import get_category_stats, get_monthly_stats, get_account_stats, get_summary
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
                pass  # 这里需要实现
            elif choice == '2':
                # 查看交易记录
                pass
            elif choice == '3':
                # 管理账户
                pass
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
                    result = get_category_stats(current_user['id'], start_date, end_date)
                    print("按分类统计结果:")
                    for row in result:
                        print(row)
                elif stat_choice == '2':
                    year = input("年份 (如2024): ")
                    result = get_monthly_stats(current_user['id'], int(year))
                    print("按月份统计结果:")
                    for row in result:
                        print(row)
                elif stat_choice == '3':
                    start_date = input("开始日期 (YYYY-MM-DD): ")
                    end_date = input("结束日期 (YYYY-MM-DD): ")
                    result = get_account_stats(current_user['id'], start_date, end_date)
                    print("按账户统计结果:")
                    for row in result:
                        print(row)
                elif stat_choice == '4':
                    start_date = input("开始日期 (YYYY-MM-DD): ")
                    end_date = input("结束日期 (YYYY-MM-DD): ")
                    summary = get_summary(current_user['id'], start_date, end_date)
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