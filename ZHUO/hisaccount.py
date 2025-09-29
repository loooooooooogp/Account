import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class AccountManager:
    def __init__(self, data_file="accounts.json"):
        self.data_file = data_file
        self.accounts = self.load_data()
        
        # 预置分类
        self.preset_categories = {
            "收入": ["工资", "奖金", "投资回报", "兼职收入", "其他收入"],
            "支出": ["餐饮", "交通", "购物", "住房", "娱乐", "医疗", "教育", "其他支出"]
        }
        
        # 预置账户
        self.preset_accounts = ["现金", "支付宝", "微信钱包", "银行卡", "云闪付"]

    def load_data(self) -> List[Dict]:
        """加载账目数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []

    def save_data(self):
        """保存账目数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, ensure_ascii=False, indent=2)

    def add_transaction(self, transaction_type: str, amount: float, category: str, 
                       account: str, date_time: Optional[str] = None) -> bool:
        """
        记录收支
        
        Args:
            transaction_type: 类型（收入/支出）
            amount: 金额（支持小数点后两位）
            category: 分类
            account: 账户
            date_time: 日期时间（可选，默认当前时间）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 验证输入
            if transaction_type not in ["收入", "支出"]:
                print("错误：类型必须是'收入'或'支出'")
                return False
                
            if not isinstance(amount, (int, float)) or amount <= 0:
                print("错误：金额必须是正数")
                return False
                
            amount = round(float(amount), 2)  # 确保小数点后两位
            
            # 处理日期时间
            if date_time:
                try:
                    dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print("错误：日期时间格式应为'YYYY-MM-DD HH:MM:SS'")
                    return False
            else:
                dt = datetime.now()
                date_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建交易记录
            transaction = {
                "id": len(self.accounts) + 1,
                "type": transaction_type,
                "amount": amount,
                "category": category,
                "account": account,
                "datetime": date_time
            }
            
            self.accounts.append(transaction)
            self.save_data()
            print("交易记录添加成功！")
            return True
            
        except Exception as e:
            print(f"添加交易记录时出错：{e}")
            return False

    def view_transactions(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        查看账目列表，支持筛选
        
        Args:
            filters: 筛选条件字典，可包含以下键：
                     - type: 类型（收入/支出）
                     - category: 分类
                     - account: 账户
                     - min_amount: 最小金额
                     - max_amount: 最大金额
                     - start_date: 开始日期
                     - end_date: 结束日期
                     
        Returns:
            List[Dict]: 符合条件的交易记录列表
        """
        filtered_transactions = self.accounts.copy()
        
        if filters:
            # 按类型筛选
            if "type" in filters and filters["type"]:
                filtered_transactions = [t for t in filtered_transactions 
                                        if t["type"] == filters["type"]]
            
            # 按分类筛选
            if "category" in filters and filters["category"]:
                filtered_transactions = [t for t in filtered_transactions 
                                        if t["category"] == filters["category"]]
            
            # 按账户筛选
            if "account" in filters and filters["account"]:
                filtered_transactions = [t for t in filtered_transactions 
                                        if t["account"] == filters["account"]]
            
            # 按金额范围筛选
            if "min_amount" in filters and filters["min_amount"] is not None:
                filtered_transactions = [t for t in filtered_transactions 
                                        if t["amount"] >= filters["min_amount"]]
            
            if "max_amount" in filters and filters["max_amount"] is not None:
                filtered_transactions = [t for t in filtered_transactions 
                                        if t["amount"] <= filters["max_amount"]]
            
            # 按时间范围筛选
            if "start_date" in filters and filters["start_date"]:
                try:
                    start_dt = datetime.strptime(filters["start_date"], "%Y-%m-%d")
                    filtered_transactions = [t for t in filtered_transactions 
                                            if datetime.strptime(t["datetime"], "%Y-%m-%d %H:%M:%S") >= start_dt]
                except ValueError:
                    print("警告：开始日期格式无效，已忽略该筛选条件")
            
            if "end_date" in filters and filters["end_date"]:
                try:
                    end_dt = datetime.strptime(filters["end_date"], "%Y-%m-%d")
                    # 结束日期设置为当天的最后一秒
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                    filtered_transactions = [t for t in filtered_transactions 
                                            if datetime.strptime(t["datetime"], "%Y-%m-%d %H:%M:%S") <= end_dt]
                except ValueError:
                    print("警告：结束日期格式无效，已忽略该筛选条件")
        
        # 按时间倒序排列
        filtered_transactions.sort(key=lambda x: x["datetime"], reverse=True)
        
        return filtered_transactions

    def edit_transaction(self, transaction_id: int, **kwargs) -> bool:
        """
        编辑账目
        
        Args:
            transaction_id: 要编辑的交易记录ID
            **kwargs: 要更新的字段和值
            
        Returns:
            bool: 操作是否成功
        """
        for transaction in self.accounts:
            if transaction["id"] == transaction_id:
                # 验证和更新字段
                if "type" in kwargs:
                    if kwargs["type"] not in ["收入", "支出"]:
                        print("错误：类型必须是'收入'或'支出'")
                        return False
                    transaction["type"] = kwargs["type"]
                
                if "amount" in kwargs:
                    try:
                        amount = round(float(kwargs["amount"]), 2)
                        if amount <= 0:
                            print("错误：金额必须是正数")
                            return False
                        transaction["amount"] = amount
                    except ValueError:
                        print("错误：金额必须是数字")
                        return False
                
                if "category" in kwargs:
                    transaction["category"] = kwargs["category"]
                
                if "account" in kwargs:
                    transaction["account"] = kwargs["account"]
                
                if "datetime" in kwargs:
                    try:
                        datetime.strptime(kwargs["datetime"], "%Y-%m-%d %H:%M:%S")
                        transaction["datetime"] = kwargs["datetime"]
                    except ValueError:
                        print("错误：日期时间格式应为'YYYY-MM-DD HH:MM:SS'")
                        return False
                
                self.save_data()
                print("交易记录更新成功！")
                return True
        
        print(f"错误：未找到ID为{transaction_id}的交易记录")
        return False

    def delete_transaction(self, transaction_id: int, confirm: bool = False) -> bool:
        """
        删除账目
        
        Args:
            transaction_id: 要删除的交易记录ID
            confirm: 是否已确认删除（避免重复确认）
            
        Returns:
            bool: 操作是否成功
        """
        if not confirm:
            print(f"警告：您即将删除ID为{transaction_id}的交易记录")
            confirmation = input("确认删除？(y/n): ")
            if confirmation.lower() != 'y':
                print("删除操作已取消")
                return False
        
        for i, transaction in enumerate(self.accounts):
            if transaction["id"] == transaction_id:
                del self.accounts[i]
                self.save_data()
                print("交易记录已删除！")
                return True
        
        print(f"错误：未找到ID为{transaction_id}的交易记录")
        return False

    def get_categories(self) -> Dict[str, List[str]]:
        """获取所有分类（预置和自定义的）"""
        # 从现有交易记录中提取自定义分类
        custom_categories = {"收入": [], "支出": []}
        for transaction in self.accounts:
            cat_type = "收入" if transaction["type"] == "收入" else "支出"
            if (transaction["category"] not in self.preset_categories[cat_type] and 
                transaction["category"] not in custom_categories[cat_type]):
                custom_categories[cat_type].append(transaction["category"])
        
        return {
            "收入": self.preset_categories["收入"] + custom_categories["收入"],
            "支出": self.preset_categories["支出"] + custom_categories["支出"]
        }

    def get_accounts(self) -> List[str]:
        """获取所有账户（预置和自定义的）"""
        # 从现有交易记录中提取自定义账户
        custom_accounts = []
        for transaction in self.accounts:
            if (transaction["account"] not in self.preset_accounts and 
                transaction["account"] not in custom_accounts):
                custom_accounts.append(transaction["account"])
        
        return self.preset_accounts + custom_accounts

    def input_transaction(self):
        """交互式输入交易记录"""
        print("\n=== 添加新交易记录 ===")
        
        # 选择交易类型
        print("请选择交易类型:")
        print("1. 收入")
        print("2. 支出")
        type_choice = input("请输入选择 (1/2): ").strip()
        if type_choice == "1":
            transaction_type = "收入"
        elif type_choice == "2":
            transaction_type = "支出"
        else:
            print("无效选择，默认为支出")
            transaction_type = "支出"
        
        # 输入金额
        while True:
            try:
                amount = float(input("请输入金额: ").strip())
                if amount <= 0:
                    print("金额必须大于0，请重新输入")
                    continue
                break
            except ValueError:
                print("金额必须是数字，请重新输入")
        
        # 选择分类
        categories = self.get_categories()[transaction_type]
        print(f"\n请选择{transaction_type}分类:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        print(f"{len(categories) + 1}. 自定义分类")
        
        try:
            cat_choice = int(input("请输入选择: ").strip())
            if 1 <= cat_choice <= len(categories):
                category = categories[cat_choice - 1]
            elif cat_choice == len(categories) + 1:
                category = input("请输入自定义分类名称: ").strip()
            else:
                print("无效选择，使用默认分类")
                category = categories[0]
        except ValueError:
            print("无效输入，使用默认分类")
            category = categories[0]
        
        # 选择账户
        accounts = self.get_accounts()
        print(f"\n请选择账户:")
        for i, acc in enumerate(accounts, 1):
            print(f"{i}. {acc}")
        print(f"{len(accounts) + 1}. 自定义账户")
        
        try:
            acc_choice = int(input("请输入选择: ").strip())
            if 1 <= acc_choice <= len(accounts):
                account = accounts[acc_choice - 1]
            elif acc_choice == len(accounts) + 1:
                account = input("请输入自定义账户名称: ").strip()
            else:
                print("无效选择，使用默认账户")
                account = accounts[0]
        except ValueError:
            print("无效输入，使用默认账户")
            account = accounts[0]
        
        # 输入日期时间
        use_current = input("是否使用当前时间？(y/n): ").strip().lower()
        if use_current == 'y' or use_current == '':
            date_time = None
        else:
            date_time = input("请输入日期时间 (格式: YYYY-MM-DD HH:MM:SS): ").strip()
        
        # 添加交易记录
        self.add_transaction(transaction_type, amount, category, account, date_time)

    def display_transactions(self, transactions: List[Dict]):
        """显示交易记录列表"""
        if not transactions:
            print("没有找到符合条件的交易记录")
            return
        
        print("\n=== 交易记录列表 ===")
        print(f"{'ID':<4} {'日期时间':<20} {'类型':<6} {'金额':<10} {'分类':<10} {'账户':<10}")
        print("-" * 65)
        
        total_income = 0
        total_expense = 0
        
        for t in transactions:
            print(f"{t['id']:<4} {t['datetime']:<20} {t['type']:<6} {t['amount']:<10.2f} {t['category']:<10} {t['account']:<10}")
            
            if t['type'] == '收入':
                total_income += t['amount']
            else:
                total_expense += t['amount']
        
        print("-" * 65)
        print(f"总收入: {total_income:.2f}元")
        print(f"总支出: {total_expense:.2f}元")
        print(f"余额: {(total_income - total_expense):.2f}元")

    def view_transactions_menu(self):
        """查看交易记录菜单"""
        print("\n=== 查看交易记录 ===")
        print("1. 查看所有记录")
        print("2. 按条件筛选")
        choice = input("请输入选择: ").strip()
        
        filters = {}
        if choice == "2":
            print("\n请输入筛选条件（直接回车跳过该条件）:")
            
            type_choice = input("类型 (1.收入 / 2.支出): ").strip()
            if type_choice == "1":
                filters["type"] = "收入"
            elif type_choice == "2":
                filters["type"] = "支出"
            
            if "type" in filters:
                categories = self.get_categories()[filters["type"]]
                print("可用分类: " + ", ".join(categories))
                category = input("分类: ").strip()
                if category and category in categories:
                    filters["category"] = category
            
            accounts = self.get_accounts()
            print("可用账户: " + ", ".join(accounts))
            account = input("账户: ").strip()
            if account and account in accounts:
                filters["account"] = account
            
            try:
                min_amount = input("最小金额: ").strip()
                if min_amount:
                    filters["min_amount"] = float(min_amount)
            except ValueError:
                print("最小金额无效，已忽略")
            
            try:
                max_amount = input("最大金额: ").strip()
                if max_amount:
                    filters["max_amount"] = float(max_amount)
            except ValueError:
                print("最大金额无效，已忽略")
            
            start_date = input("开始日期 (YYYY-MM-DD): ").strip()
            if start_date:
                filters["start_date"] = start_date
            
            end_date = input("结束日期 (YYYY-MM-DD): ").strip()
            if end_date:
                filters["end_date"] = end_date
        
        transactions = self.view_transactions(filters)
        self.display_transactions(transactions)

    def edit_transaction_menu(self):
        """编辑交易记录菜单"""
        self.display_transactions(self.accounts)
        
        try:
            transaction_id = int(input("\n请输入要编辑的交易记录ID: ").strip())
        except ValueError:
            print("无效的ID")
            return
        
        # 查找交易记录
        transaction = None
        for t in self.accounts:
            if t["id"] == transaction_id:
                transaction = t
                break
        
        if not transaction:
            print(f"未找到ID为{transaction_id}的交易记录")
            return
        
        print(f"\n编辑交易记录 {transaction_id}:")
        print(f"1. 类型: {transaction['type']}")
        print(f"2. 金额: {transaction['amount']}")
        print(f"3. 分类: {transaction['category']}")
        print(f"4. 账户: {transaction['account']}")
        print(f"5. 日期时间: {transaction['datetime']}")
        
        field = input("请选择要修改的字段 (1-5): ").strip()
        
        if field == "1":
            new_value = input("请输入新类型 (收入/支出): ").strip()
            if new_value not in ["收入", "支出"]:
                print("类型必须是'收入'或'支出'")
                return
            self.edit_transaction(transaction_id, type=new_value)
        
        elif field == "2":
            try:
                new_value = float(input("请输入新金额: ").strip())
                if new_value <= 0:
                    print("金额必须大于0")
                    return
                self.edit_transaction(transaction_id, amount=new_value)
            except ValueError:
                print("金额必须是数字")
        
        elif field == "3":
            categories = self.get_categories()[transaction["type"]]
            print("可用分类: " + ", ".join(categories))
            new_value = input("请输入新分类: ").strip()
            self.edit_transaction(transaction_id, category=new_value)
        
        elif field == "4":
            accounts = self.get_accounts()
            print("可用账户: " + ", ".join(accounts))
            new_value = input("请输入新账户: ").strip()
            self.edit_transaction(transaction_id, account=new_value)
        
        elif field == "5":
            new_value = input("请输入新日期时间 (YYYY-MM-DD HH:MM:SS): ").strip()
            try:
                datetime.strptime(new_value, "%Y-%m-%d %H:%M:%S")
                self.edit_transaction(transaction_id, datetime=new_value)
            except ValueError:
                print("日期时间格式无效")
        
        else:
            print("无效选择")

    def delete_transaction_menu(self):
        """删除交易记录菜单"""
        self.display_transactions(self.accounts)
        
        try:
            transaction_id = int(input("\n请输入要删除的交易记录ID: ").strip())
        except ValueError:
            print("无效的ID")
            return
        
        self.delete_transaction(transaction_id)

    def main_menu(self):
        """主菜单"""
        while True:
            print("\n=== 账目管理系统 ===")
            print("1. 添加交易记录")
            print("2. 查看交易记录")
            print("3. 编辑交易记录")
            print("4. 删除交易记录")
            print("5. 退出")
            
            choice = input("请输入选择 (1-5): ").strip()
            
            if choice == "1":
                self.input_transaction()
            elif choice == "2":
                self.view_transactions_menu()
            elif choice == "3":
                self.edit_transaction_menu()
            elif choice == "4":
                self.delete_transaction_menu()
            elif choice == "5":
                print("感谢使用账目管理系统！")
                break
            else:
                print("无效选择，请重新输入")

# 运行程序
if __name__ == "__main__":
    manager = AccountManager()
    manager.main_menu()