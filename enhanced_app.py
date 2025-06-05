import sys
from tabulate import tabulate  # type: ignore
from datetime import date, datetime

import enhanced_database as db
import enhanced_library as lib

MAIN_MENU = """
======== 图书管理系统 (增强版) ========
1.  图书管理
2.  读者管理
3.  借阅管理
4.  查询统计
5.  系统管理
0.  退出系统
====================================
"""

BOOK_MENU = """
-------- 图书管理 --------
1. 添加图书类别
2. 添加图书副本
3. 查询图书信息
4. 更新图书状态
5. 返回主菜单
------------------------
"""

READER_MENU = """
-------- 读者管理 --------
1. 添加读者
2. 查询读者信息
3. 更新读者信息
4. 返回主菜单
------------------------
"""

BORROW_MENU = """
-------- 借阅管理 --------
1. 借书
2. 还书
3. 当前借阅记录
4. 返回主菜单
------------------------
"""

QUERY_MENU = """
-------- 查询统计 --------
1. 逾期图书查询
2. 读者借阅历史
3. 借阅统计
4. 按图书查询借阅者
5. 返回主菜单
------------------------
"""

def prompt_string(message: str, required: bool = True) -> str:
    while True:
        value = input(message).strip()
        if value or not required:
            return value if value else None
        print("此项为必填项，请重新输入！")

def prompt_int(message: str, required: bool = True) -> int:
    while True:
        try:
            value = input(message).strip()
            if not value and not required:
                return None
            return int(value)
        except ValueError:
            print("请输入有效的整数！")

def prompt_float(message: str, required: bool = True) -> float:
    while True:
        try:
            value = input(message).strip()
            if not value and not required:
                return None
            return float(value)
        except ValueError:
            print("请输入有效的数字！")

def prompt_date(message: str, required: bool = True) -> str:
    while True:
        try:
            value = input(message + " (格式: YYYY-MM-DD): ").strip()
            if not value and not required:
                return None
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            print("请输入有效的日期格式 (YYYY-MM-DD)！")

# ==================== 图书管理功能 ====================

def add_book_category():
    print("\n=== 添加图书类别 ===")
    isbn = prompt_string("ISBN书号: ")
    category = prompt_string("图书类别: ")
    title = prompt_string("书名: ")
    author = prompt_string("作者: ")
    publisher = prompt_string("出版社 (可选): ", False)
    publish_date = prompt_date("出版日期", False)
    price = prompt_float("价格 (可选): ", False)
    total_copies = prompt_int("馆藏数量: ")
    description = prompt_string("图书简介 (可选): ", False)
    
    try:
        lib.add_book_category(isbn, category, title, author, publisher, 
                             publish_date, price, total_copies, description)
    except Exception as e:
        print(f"添加失败：{e}")

def add_book_copy():
    print("\n=== 添加图书副本 ===")
    isbn = prompt_string("ISBN书号: ")
    book_number = prompt_string("图书书号: ")
    
    try:
        lib.add_book_copy(isbn, book_number)
    except Exception as e:
        print(f"添加失败：{e}")

def search_books():
    print("\n=== 图书查询 ===")
    title = prompt_string("书名 (支持模糊查询，可选): ", False)
    author = prompt_string("作者 (支持模糊查询，可选): ", False)
    isbn = prompt_string("ISBN (精确查询，可选): ", False)
    category = prompt_string("类别 (支持模糊查询，可选): ", False)
    
    results = lib.search_books(title, author, isbn, category)
    if results:
        print(f"\n找到 {len(results)} 条记录：")
        print(tabulate(results, headers="keys", tablefmt="psql"))
    else:
        print("未找到符合条件的图书。")

def update_book_status():
    print("\n=== 更新图书状态 ===")
    book_number = prompt_string("图书书号: ")
    print("状态选项：1-正常, 2-损坏, 3-遗失")
    status_choice = prompt_int("选择状态 (1-3): ")
    
    status_map = {1: '正常', 2: '损坏', 3: '遗失'}
    if status_choice in status_map:
        try:
            lib.update_book_status(book_number, status_map[status_choice])
        except Exception as e:
            print(f"更新失败：{e}")
    else:
        print("无效的状态选择！")

# ==================== 读者管理功能 ====================

def add_reader():
    print("\n=== 添加读者 ===")
    library_card_no = prompt_string("借书证号: ")
    name = prompt_string("姓名: ")
    print("性别选项：1-男, 2-女")
    gender_choice = prompt_int("选择性别 (1-2): ")
    gender = '男' if gender_choice == 1 else '女'
    
    birth_date = prompt_date("出生年月", False)
    id_card = prompt_string("身份证号 (可选): ", False)
    title = prompt_string("职称 (可选): ", False)
    max_borrow_count = prompt_int("可借数量 (可选): ", False)
    department = prompt_string("工作部门 (可选): ", False)
    address = prompt_string("家庭住址 (可选): ", False)
    phone = prompt_string("联系电话 (可选): ", False)
    
    try:
        lib.add_reader(library_card_no, name, gender, birth_date, id_card, 
                      title, max_borrow_count, department, address, phone)
    except Exception as e:
        print(f"添加失败：{e}")

def search_readers():
    print("\n=== 读者查询 ===")
    card_no = prompt_string("借书证号 (可选): ", False)
    name = prompt_string("姓名 (支持模糊查询，可选): ", False)
    department = prompt_string("部门 (支持模糊查询，可选): ", False)
    
    results = lib.search_readers(card_no, name, department)
    if results:
        print(f"\n找到 {len(results)} 条记录：")
        for reader in results:
            print(f"\n借书证号: {reader['library_card_no']}")
            print(f"姓名: {reader['name']}")
            print(f"性别: {reader['gender']}")
            print(f"部门: {reader['department'] or '未填写'}")
            print(f"可借/已借: {reader['max_borrow_count']}/{reader['current_borrow_count']}")
            print(f"状态: {reader['status']}")
            if reader['unreturned_books']:
                print(f"未归还图书: {reader['unreturned_books']}")
            print("-" * 50)
    else:
        print("未找到符合条件的读者。")

def update_reader():
    print("\n=== 更新读者信息 ===")
    library_card_no = prompt_string("借书证号: ")
    
    print("可更新的字段：")
    print("1. 姓名  2. 电话  3. 地址  4. 部门  5. 可借数量")
    
    updates = {}
    if input("是否更新姓名？(y/n): ").lower() == 'y':
        updates['name'] = prompt_string("新姓名: ")
    if input("是否更新电话？(y/n): ").lower() == 'y':
        updates['phone'] = prompt_string("新电话: ", False)
    if input("是否更新地址？(y/n): ").lower() == 'y':
        updates['address'] = prompt_string("新地址: ", False)
    if input("是否更新部门？(y/n): ").lower() == 'y':
        updates['department'] = prompt_string("新部门: ", False)
    if input("是否更新可借数量？(y/n): ").lower() == 'y':
        updates['max_borrow_count'] = prompt_int("新可借数量: ")
    
    if updates:
        try:
            lib.update_reader_info(library_card_no, **updates)
        except Exception as e:
            print(f"更新失败：{e}")
    else:
        print("没有要更新的信息。")

# ==================== 借阅管理功能 ====================

def borrow_book():
    print("\n=== 借书 ===")
    library_card_no = prompt_string("借书证号: ")
    book_number = prompt_string("图书书号: ")
    days = prompt_int("借阅天数 (默认30天，可选): ", False)
    
    success = lib.borrow_book(library_card_no, book_number, days)
    if not success:
        print("借书失败，请检查输入信息。")

def return_book():
    print("\n=== 还书 ===")
    borrowing_id = prompt_int("借阅记录ID: ")
    
    success = lib.return_book(borrowing_id)
    if not success:
        print("还书失败，请检查借阅记录ID。")

def view_current_borrowings():
    print("\n=== 当前借阅记录 ===")
    results = lib.get_current_borrowings()
    if results:
        print(tabulate(results, headers="keys", tablefmt="psql"))
    else:
        print("当前没有借阅记录。")

# ==================== 查询统计功能 ====================

def view_overdue_books():
    print("\n=== 逾期图书查询 ===")
    results = lib.get_overdue_books()
    if results:
        print(tabulate(results, headers="keys", tablefmt="psql"))
    else:
        print("当前没有逾期图书。")

def view_reader_history():
    print("\n=== 读者借阅历史 ===")
    library_card_no = prompt_string("借书证号: ")
    start_date = prompt_date("开始日期", False)
    end_date = prompt_date("结束日期", False)
    
    results = lib.get_reader_borrowing_history(library_card_no, start_date, end_date)
    if results:
        print(tabulate(results, headers="keys", tablefmt="psql"))
    else:
        print("未找到借阅记录。")

def view_borrowing_stats():
    print("\n=== 借阅统计 ===")
    start_date = prompt_date("开始日期")
    end_date = prompt_date("结束日期")
    
    results = lib.get_borrowing_statistics(start_date, end_date)
    if results:
        print(tabulate(results, headers="keys", tablefmt="psql"))
    else:
        print("指定时间段内没有借阅记录。")

def view_unreturned_by_book():
    print("\n=== 按图书查询借阅者 ===")
    book_number = prompt_string("图书书号: ")
    
    results = lib.get_unreturned_readers_by_book(book_number)
    if results:
        print(tabulate(results, headers="keys", tablefmt="psql"))
    else:
        print("该图书当前没有借阅者。")

# ==================== 菜单处理函数 ====================

def book_management():
    while True:
        print(BOOK_MENU)
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            add_book_category()
        elif choice == '2':
            add_book_copy()
        elif choice == '3':
            search_books()
        elif choice == '4':
            update_book_status()
        elif choice == '5':
            break
        else:
            print("无效的选择！")
        
        input("\n按 Enter 继续...")

def reader_management():
    while True:
        print(READER_MENU)
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            add_reader()
        elif choice == '2':
            search_readers()
        elif choice == '3':
            update_reader()
        elif choice == '4':
            break
        else:
            print("无效的选择！")
        
        input("\n按 Enter 继续...")

def borrow_management():
    while True:
        print(BORROW_MENU)
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            borrow_book()
        elif choice == '2':
            return_book()
        elif choice == '3':
            view_current_borrowings()
        elif choice == '4':
            break
        else:
            print("无效的选择！")
        
        input("\n按 Enter 继续...")

def query_statistics():
    while True:
        print(QUERY_MENU)
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            view_overdue_books()
        elif choice == '2':
            view_reader_history()
        elif choice == '3':
            view_borrowing_stats()
        elif choice == '4':
            view_unreturned_by_book()
        elif choice == '5':
            break
        else:
            print("无效的选择！")
        
        input("\n按 Enter 继续...")

def system_management():
    print("\n=== 系统管理 ===")
    print("1. 重新初始化数据库")
    print("2. 返回主菜单")
    
    choice = input("请选择操作: ").strip()
    if choice == '1':
        confirm = input("确认要重新初始化数据库吗？这将删除所有数据！(y/N): ")
        if confirm.lower() == 'y':
            try:
                db.execute_sql_file('enhanced_schema.sql')
                print("数据库初始化完成！")
            except Exception as e:
                print(f"初始化失败：{e}")

def main():
    print("正在连接数据库...")
    try:
        db.init_db()
        print("数据库连接成功！")
    except Exception as e:
        print(f"连接数据库失败：{e}")
        print("请检查数据库配置和连接信息。")
        sys.exit(1)
    
    while True:
        print(MAIN_MENU)
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            book_management()
        elif choice == '2':
            reader_management()
        elif choice == '3':
            borrow_management()
        elif choice == '4':
            query_statistics()
        elif choice == '5':
            system_management()
        elif choice == '0':
            print("感谢使用图书管理系统！")
            break
        else:
            print("无效的选择，请重新输入！")

if __name__ == "__main__":
    main() 