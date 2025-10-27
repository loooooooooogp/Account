import sqlite3
import re
from datetime import datetime, date
from database import get_db_connection
from typing import List, Dict, Tuple, Optional, Union
import textwrap
import os

# 类型别名，提高代码可读性
StatResult = List[Dict[str, Union[str, float, int]]]
SummaryResult = Dict[str, float]


class StatisticsVisualizer:
    """统计结果可视化类"""
    
    @staticmethod
    def print_category_stats(results: StatResult, title: str = "分类统计"):
        """打印分类统计结果"""
        if not results:
            print("📊 暂无分类统计数据")
            return
            
        print(f"\n{'='*50}")
        print(f"📊 {title}")
        print(f"{'='*50}")
        
        # 按收入和支出分组
        income_data = [r for r in results if r['transaction_type'] == 'income']
        expense_data = [r for r in results if r['transaction_type'] == 'expense']
        
        if income_data:
            print(f"\n💰 收入分类:")
            print("-" * 30)
            total_income = sum(item['total_amount'] for item in income_data)
            for item in income_data:
                percentage = (item['total_amount'] / total_income) * 100
                bar = "█" * int(percentage / 5)  # 每个█代表5%
                print(f"  {item['category']:<15} {item['total_amount']:>8.2f} {percentage:>5.1f}% {bar}")
        
        if expense_data:
            print(f"\n💸 支出分类:")
            print("-" * 30)
            total_expense = sum(item['total_amount'] for item in expense_data)
            for item in expense_data:
                percentage = (item['total_amount'] / total_expense) * 100
                bar = "█" * int(percentage / 5)
                print(f"  {item['category']:<15} {item['total_amount']:>8.2f} {percentage:>5.1f}% {bar}")

    @staticmethod
    def print_monthly_stats(results: StatResult, year: int):
        """打印月度统计结果"""
        if not results:
            print(f"📊 {year}年暂无月度统计数据")
            return
            
        print(f"\n{'='*60}")
        print(f"📅 {year}年月度统计")
        print(f"{'='*60}")
        
        # 按月份组织数据
        monthly_data = {}
        for item in results:
            month = item['month']
            if month not in monthly_data:
                monthly_data[month] = {'income': 0, 'expense': 0}
            
            if item['transaction_type'] == 'income':
                monthly_data[month]['income'] = item['total_amount']
            else:
                monthly_data[month]['expense'] = item['total_amount']
        
        # 打印月度表格
        print(f"\n{'月份':<8} {'收入':<10} {'支出':<10} {'结余':<10} {'储蓄率':<10}")
        print("-" * 50)
        
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            balance = data['income'] - data['expense']
            saving_rate = (balance / data['income'] * 100) if data['income'] > 0 else 0
            
            # 添加表情符号
            balance_emoji = "📈" if balance >= 0 else "📉"
            saving_emoji = "💰" if saving_rate >= 20 else "💸" if saving_rate >= 10 else "⚠️"
            
            print(f"{month}月     {data['income']:>8.2f} {data['expense']:>8.2f} "
                  f"{balance_emoji}{balance:>8.2f} {saving_emoji}{saving_rate:>8.1f}%")

    @staticmethod
    def print_account_stats(results: StatResult, title: str = "账户统计"):
        """打印账户统计结果"""
        if not results:
            print("📊 暂无账户统计数据")
            return
            
        print(f"\n{'='*50}")
        print(f"🏦 {title}")
        print(f"{'='*50}")
        
        # 按账户和类型分组
        account_data = {}
        for item in results:
            account = item['account']
            if account not in account_data:
                account_data[account] = {'income': 0, 'expense': 0}
            
            if item['transaction_type'] == 'income':
                account_data[account]['income'] += item['total_amount']
            else:
                account_data[account]['expense'] += item['total_amount']
        
        for account, data in account_data.items():
            balance = data['income'] - data['expense']
            print(f"\n📁 {account}:")
            print(f"  💰 收入: {data['income']:>10.2f}")
            print(f"  💸 支出: {data['expense']:>10.2f}")
            print(f"  ⚖️  结余: {balance:>10.2f} {'✅' if balance >= 0 else '❌'}")

    @staticmethod
    def print_summary(summary: SummaryResult):
        """打印财务汇总结果"""
        print(f"\n{'='*60}")
        print(f"📈 财务汇总 ({summary.get('period', '')})")
        print(f"{'='*60}")
        
        # 主要财务指标
        income = summary['total_income']
        expense = summary['total_expense']
        balance = summary['balance']
        saving_rate = summary['saving_rate']
        
        print(f"\n📊 主要指标:")
        print(f"  💰 总收入: {income:>12.2f}")
        print(f"  💸 总支出: {expense:>12.2f}")
        print(f"  ⚖️  净结余: {balance:>12.2f} {'✅' if balance >= 0 else '❌'}")
        print(f"  📈 储蓄率: {saving_rate:>11.1f}%")
        
        # 财务健康评估
        advice = summary.get('financial_advice', '')
        print(f"\n💡 财务建议: {advice}")
        
        # 可视化进度条
        if income > 0:
            expense_ratio = (expense / income) * 100
            saving_ratio = saving_rate
            
            print(f"\n📊 收支比例:")
            print(f"  🟢 储蓄: {'█' * int(saving_ratio / 2):<50} {saving_ratio:.1f}%")
            print(f"  🔴 支出: {'█' * int(expense_ratio / 2):<50} {expense_ratio:.1f}%")


class StatisticsManager:
    """财务统计管理器，封装各类统计方法"""
    
    def __init__(self, user_id: int):
        """初始化统计管理器，绑定用户ID"""
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("用户ID必须是正整数")
        self.user_id = user_id
        self.conn = None
        self.cursor = None
        self.visualizer = StatisticsVisualizer()

    def __enter__(self):
        """上下文管理器：自动获取数据库连接"""
        try:
            self.conn = get_db_connection()
            self.cursor = self.conn.cursor()
            return self
        except Exception as e:
            raise ConnectionError(f"数据库连接失败: {str(e)}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：自动关闭数据库连接"""
        if self.conn:
            self.conn.close()
        # 传播异常（如果有）
        return False

    def _validate_date_format(self, date_str: str) -> bool:
        """验证日期格式是否为 YYYY-MM-DD"""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _validate_date_range(self, start_date: str, end_date: str) -> None:
        """验证日期范围是否有效"""
        if not self._validate_date_format(start_date):
            raise ValueError(f"开始日期格式无效: {start_date}，请使用 YYYY-MM-DD 格式")
        if not self._validate_date_format(end_date):
            raise ValueError(f"结束日期格式无效: {end_date}，请使用 YYYY-MM-DD 格式")
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_dt > end_dt:
            raise ValueError("开始日期不能晚于结束日期")
        
        # 放宽限制：允许未来日期，但给出提示
        today = datetime.now().date()
        if end_dt.date() > today:
            print(f"⚠️  注意：结束日期 {end_date} 在未来，将只统计到今天的记录")

    def _validate_year(self, year: int) -> None:
        """验证年份是否有效"""
        current_year = datetime.now().year
        if not (1900 <= year <= current_year + 5):  # 允许未来5年
            raise ValueError(f"年份必须在 1900 到 {current_year + 5} 之间")

    def _get_formatted_results(self, cursor: sqlite3.Cursor) -> StatResult:
        """
        将查询结果转换为带列名的字典列表
        :param cursor: 数据库游标对象
        :return: 格式化后的结果列表
        """
        try:
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                formatted_row = {}
                for col, val in zip(columns, row):
                    if isinstance(val, float):
                        formatted_row[col] = round(val, 2)
                    elif val is None:
                        formatted_row[col] = 0  # 将None转换为0
                    else:
                        formatted_row[col] = val
                results.append(formatted_row)
            return results
        except Exception as e:
            raise ValueError(f"结果格式化失败: {str(e)}")

    def _check_user_exists(self) -> bool:
        """检查用户是否存在"""
        try:
            self.cursor.execute("SELECT id FROM users WHERE id = ?", (self.user_id,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error:
            # 如果users表不存在，假设用户有效（向后兼容）
            return True

    def get_by_category(self, start_date: str, end_date: str, display: bool = True) -> StatResult:
        """
        按分类统计收支
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param display: 是否显示可视化结果
        :return: 按分类统计的结果
        """
        try:
            # 输入验证
            self._validate_date_range(start_date, end_date)
            
            if not self._check_user_exists():
                raise ValueError(f"用户ID {self.user_id} 不存在")

            # 自动调整结束日期为今天（如果结束日期在未来）
            today = datetime.now().strftime('%Y-%m-%d')
            actual_end_date = min(end_date, today)
            
            if end_date > today:
                print(f"📅 已将结束日期从 {end_date} 调整为 {actual_end_date}")

            query = '''
            SELECT 
                c.name as category, 
                t.type as transaction_type, 
                COALESCE(SUM(t.amount), 0) as total_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE 
                t.user_id = ? 
                AND t.date BETWEEN ? AND ?
            GROUP BY category, transaction_type
            HAVING total_amount > 0  -- 只显示有交易的分类
            ORDER BY total_amount DESC
            '''
            self.cursor.execute(query, (self.user_id, start_date, actual_end_date))
            results = self._get_formatted_results(self.cursor)
            
            if display:
                if not results:
                    print(f"📊 提示: 在 {start_date} 到 {actual_end_date} 期间没有找到交易记录")
                else:
                    self.visualizer.print_category_stats(results, f"分类统计 ({start_date} 至 {actual_end_date})")
            
            return results
            
        except sqlite3.Error as e:
            raise ValueError(f"按分类统计失败: {str(e)}")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"按分类统计时发生未知错误: {str(e)}")

    def get_by_month(self, target_year: int, display: bool = True) -> StatResult:
        """
        按月份统计指定年份的收支
        :param target_year: 目标年份 (如2024)
        :param display: 是否显示可视化结果
        :return: 按月份统计的结果
        """
        try:
            # 输入验证
            self._validate_year(target_year)
            
            if not self._check_user_exists():
                raise ValueError(f"用户ID {self.user_id} 不存在")

            query = '''
            SELECT 
                strftime('%m', t.date) as month,
                strftime('%Y-%m', t.date) as month_year,  -- 更友好的月份格式
                t.type as transaction_type,
                COALESCE(SUM(t.amount), 0) as total_amount
            FROM transactions t
            WHERE 
                t.user_id = ? 
                AND strftime('%Y', t.date) = ?
            GROUP BY month, transaction_type
            ORDER BY month, transaction_type
            '''
            self.cursor.execute(query, (self.user_id, str(target_year)))
            results = self._get_formatted_results(self.cursor)
            
            if display:
                if not results:
                    print(f"📊 提示: {target_year} 年没有找到交易记录")
                else:
                    self.visualizer.print_monthly_stats(results, target_year)
            
            return results
            
        except sqlite3.Error as e:
            raise ValueError(f"按月份统计失败: {str(e)}")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"按月份统计时发生未知错误: {str(e)}")

    def get_by_account(self, start_date: str, end_date: str, display: bool = True) -> StatResult:
        """
        按账户统计收支
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param display: 是否显示可视化结果
        :return: 按账户统计的结果
        """
        try:
            # 输入验证
            self._validate_date_range(start_date, end_date)
            
            if not self._check_user_exists():
                raise ValueError(f"用户ID {self.user_id} 不存在")

            # 自动调整结束日期为今天（如果结束日期在未来）
            today = datetime.now().strftime('%Y-%m-%d')
            actual_end_date = min(end_date, today)
            
            if end_date > today:
                print(f"📅 已将结束日期从 {end_date} 调整为 {actual_end_date}")

            query = '''
            SELECT 
                a.name as account,
                t.type as transaction_type,
                COALESCE(SUM(t.amount), 0) as total_amount
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            WHERE 
                t.user_id = ? 
                AND t.date BETWEEN ? AND ?
            GROUP BY account, transaction_type
            HAVING total_amount > 0  -- 只显示有交易的账户
            ORDER BY total_amount DESC
            '''
            self.cursor.execute(query, (self.user_id, start_date, actual_end_date))
            results = self._get_formatted_results(self.cursor)
            
            if display:
                if not results:
                    print(f"📊 提示: 在 {start_date} 到 {actual_end_date} 期间没有找到账户交易记录")
                else:
                    self.visualizer.print_account_stats(results, f"账户统计 ({start_date} 至 {actual_end_date})")
            
            return results
            
        except sqlite3.Error as e:
            raise ValueError(f"按账户统计失败: {str(e)}")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"按账户统计时发生未知错误: {str(e)}")

    def get_financial_summary(self, start_date: str, end_date: str, display: bool = True) -> SummaryResult:
        """
        获取指定日期范围内的财务汇总
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param display: 是否显示可视化结果
        :return: 包含总收入、总支出和结余的字典
        """
        try:
            # 输入验证
            self._validate_date_range(start_date, end_date)
            
            if not self._check_user_exists():
                raise ValueError(f"用户ID {self.user_id} 不存在")

            # 自动调整结束日期为今天（如果结束日期在未来）
            today = datetime.now().strftime('%Y-%m-%d')
            actual_end_date = min(end_date, today)
            
            if end_date > today:
                print(f"📅 已将结束日期从 {end_date} 调整为 {actual_end_date}")

            # 总收入
            self.cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE user_id = ? AND type = 'income' AND date BETWEEN ? AND ?
            ''', (self.user_id, start_date, actual_end_date))
            total_income = round(self.cursor.fetchone()[0], 2)
            
            # 总支出
            self.cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND date BETWEEN ? AND ?
            ''', (self.user_id, start_date, actual_end_date))
            total_expense = round(self.cursor.fetchone()[0], 2)
            
            # 计算储蓄率（避免除零错误）
            saving_rate = 0.0
            if total_income > 0:
                saving_rate = round((total_income - total_expense) / total_income * 100, 1)
            
            result = {
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": round(total_income - total_expense, 2),
                "saving_rate": saving_rate,
                "period": f"{start_date} 至 {actual_end_date}",
                "user_id": self.user_id
            }
            
            # 添加财务健康提示
            if saving_rate > 20:
                result["financial_advice"] = "🎉 储蓄率良好，继续保持！"
            elif saving_rate < 0:
                result["financial_advice"] = "🚨 警告：支出超过收入，请注意控制开支"
            elif saving_rate < 10:
                result["financial_advice"] = "💡 储蓄率偏低，建议增加收入或减少支出"
            else:
                result["financial_advice"] = "✅ 储蓄率正常"
            
            if display:
                self.visualizer.print_summary(result)
            
            return result
            
        except sqlite3.Error as e:
            raise ValueError(f"财务汇总统计失败: {str(e)}")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"财务汇总统计时发生未知错误: {str(e)}")


# 便捷函数：外部调用接口
def get_category_stats(user_id: int, start_date: str, end_date: str, display: bool = True) -> StatResult:
    """按分类统计的便捷接口"""
    print(f"📊 正在获取用户 {user_id} 的分类统计...")
    with StatisticsManager(user_id) as manager:
        return manager.get_by_category(start_date, end_date, display)


def get_monthly_stats(user_id: int, year: int, display: bool = True) -> StatResult:
    """按月份统计的便捷接口"""
    print(f"📊 正在获取用户 {user_id} 的 {year} 年月度统计...")
    with StatisticsManager(user_id) as manager:
        return manager.get_by_month(year, display)


def get_account_stats(user_id: int, start_date: str, end_date: str, display: bool = True) -> StatResult:
    """按账户统计的便捷接口"""
    print(f"📊 正在获取用户 {user_id} 的账户统计...")
    with StatisticsManager(user_id) as manager:
        return manager.get_by_account(start_date, end_date, display)


def get_summary(user_id: int, start_date: str, end_date: str, display: bool = True) -> SummaryResult:
    """获取财务汇总的便捷接口"""
    print(f"📊 正在获取用户 {user_id} 的财务汇总...")
    with StatisticsManager(user_id) as manager:
        return manager.get_financial_summary(start_date, end_date, display)


# 使用示例和文档
def print_usage_examples():
    """打印使用示例"""
    examples = """
📖 使用示例:

1. 按分类统计 (自动显示):
   stats = get_category_stats(1, "2024-01-01", "2024-12-31")

2. 按月统计 (不显示):
   stats = get_monthly_stats(1, 2024, display=False)

3. 按账户统计:
   stats = get_account_stats(1, "2024-01-01", "2024-12-31")

4. 财务汇总:
   summary = get_summary(1, "2024-01-01", "2024-12-31")
   
5. 只看可视化 (不返回数据):
   get_category_stats(1, "2024-01-01", "2024-12-31")

注意:
- 日期格式必须为 YYYY-MM-DD
- 用户ID必须是正整数
- 开始日期不能晚于结束日期
- 如果输入未来日期，系统会自动调整为今天

🎨 可视化特性:
- 📊 进度条图表
- 💰 财务健康评估
- 📈 趋势指示器
- 🎯 实用建议
"""
    print(examples)


if __name__ == "__main__":
    print_usage_examples()