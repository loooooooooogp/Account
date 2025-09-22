import sqlite3
from database import get_db_connection
from typing import List, Dict, Tuple, Optional, Union

# 类型别名，提高代码可读性
StatResult = List[Dict[str, Union[str, float, int]]]
SummaryResult = Dict[str, float]


class StatisticsManager:
    """财务统计管理器，封装各类统计方法"""
    
    def __init__(self, user_id: int):
        """初始化统计管理器，绑定用户ID"""
        self.user_id = user_id
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """上下文管理器：自动获取数据库连接"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：自动关闭数据库连接"""
        if self.conn:
            self.conn.close()
        # 传播异常（如果有）
        return False

    def _get_formatted_results(self, cursor: sqlite3.Cursor) -> StatResult:
        """
        将查询结果转换为带列名的字典列表
        :param cursor: 数据库游标对象
        :return: 格式化后的结果列表
        """
        columns = [desc[0] for desc in cursor.description]
        return [
            {col: (round(val, 2) if isinstance(val, float) else val) 
             for col, val in zip(columns, row)} 
            for row in cursor.fetchall()
        ]

    def get_by_category(self, start_date: str, end_date: str) -> StatResult:
        """
        按分类统计收支
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :return: 按分类统计的结果
        """
        try:
            query = '''
            SELECT 
                c.name as category, 
                t.type as transaction_type, 
                SUM(t.amount) as total_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE 
                t.user_id = ? 
                AND t.date BETWEEN ? AND ?
            GROUP BY category, transaction_type
            ORDER BY total_amount DESC
            '''
            self.cursor.execute(query, (self.user_id, start_date, end_date))
            return self._get_formatted_results(self.cursor)
            
        except sqlite3.Error as e:
            raise ValueError(f"按分类统计失败: {str(e)}")

    def get_by_month(self, target_year: int) -> StatResult:
        """
        按月份统计指定年份的收支
        :param target_year: 目标年份 (如2024)
        :return: 按月份统计的结果
        """
        try:
            query = '''
            SELECT 
                strftime('%m', t.date) as month,
                strftime('%m-%Y', t.date) as month_year,  # 更友好的月份格式
                t.type as transaction_type,
                SUM(t.amount) as total_amount
            FROM transactions t
            WHERE 
                t.user_id = ? 
                AND strftime('%Y', t.date) = ?
            GROUP BY month, transaction_type
            ORDER BY month
            '''
            self.cursor.execute(query, (self.user_id, str(target_year)))
            return self._get_formatted_results(self.cursor)
            
        except sqlite3.Error as e:
            raise ValueError(f"按月份统计失败: {str(e)}")

    def get_by_account(self, start_date: str, end_date: str) -> StatResult:
        """
        按账户统计收支
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :return: 按账户统计的结果
        """
        try:
            query = '''
            SELECT 
                a.name as account,
                t.type as transaction_type,
                SUM(t.amount) as total_amount
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            WHERE 
                t.user_id = ? 
                AND t.date BETWEEN ? AND ?
            GROUP BY account, transaction_type
            ORDER BY total_amount DESC
            '''
            self.cursor.execute(query, (self.user_id, start_date, end_date))
            return self._get_formatted_results(self.cursor)
            
        except sqlite3.Error as e:
            raise ValueError(f"按账户统计失败: {str(e)}")

    def get_financial_summary(self, start_date: str, end_date: str) -> SummaryResult:
        """
        获取指定日期范围内的财务汇总
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :return: 包含总收入、总支出和结余的字典
        """
        try:
            # 总收入
            self.cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE user_id = ? AND type = 'income' AND date BETWEEN ? AND ?
            ''', (self.user_id, start_date, end_date))
            total_income = round(self.cursor.fetchone()[0], 2)
            
            # 总支出
            self.cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND date BETWEEN ? AND ?
            ''', (self.user_id, start_date, end_date))
            total_expense = round(self.cursor.fetchone()[0], 2)
            
            return {
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": round(total_income - total_expense, 2),
                "saving_rate": round(
                    (total_income - total_expense) / total_income * 100 
                    if total_income > 0 else 0, 
                    1
                )  # 新增储蓄率计算
            }
            
        except sqlite3.Error as e:
            raise ValueError(f"财务汇总统计失败: {str(e)}")


# 便捷函数：外部调用接口
def get_category_stats(user_id: int, start_date: str, end_date: str) -> StatResult:
    """按分类统计的便捷接口"""
    with StatisticsManager(user_id) as manager:
        return manager.get_by_category(start_date, end_date)


def get_monthly_stats(user_id: int, year: int) -> StatResult:
    """按月份统计的便捷接口"""
    with StatisticsManager(user_id) as manager:
        return manager.get_by_month(year)


def get_account_stats(user_id: int, start_date: str, end_date: str) -> StatResult:
    """按账户统计的便捷接口"""
    with StatisticsManager(user_id) as manager:
        return manager.get_by_account(start_date, end_date)


def get_summary(user_id: int, start_date: str, end_date: str) -> SummaryResult:
    """获取财务汇总的便捷接口"""
    with StatisticsManager(user_id) as manager:
        return manager.get_financial_summary(start_date, end_date)
