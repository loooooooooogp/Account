from datetime import datetime

def input_date(prompt):
    while True:
        date_str = input(prompt + ' (YYYY-MM-DD): ')
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            print("日期格式错误，请重新输入。")

def input_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("请输入有效的数字。")

def input_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("请输入有效的整数。")