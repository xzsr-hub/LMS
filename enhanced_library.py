from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from enhanced_database import get_connection
import enhanced_config as config
import bcrypt # 导入 bcrypt 库

# ====================== 用户认证与密码管理 ======================

def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希密码是否匹配"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_admin_user(username: str, password: str, full_name: str = "", email: str = ""):
    """创建管理员用户（如果尚不存在）"""
    hashed_pwd = hash_password(password)
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO users (username, password_hash, role, full_name, email)
                    VALUES (%s, %s, 'admin', %s, %s)
                """, (username, hashed_pwd, full_name, email))
                conn.commit()
                print(f"管理员用户 '{username}' 创建成功。")
                return True
            except Exception as e:
                # 通常是由于用户名或邮箱已存在 (UNIQUE constraint)
                print(f"创建管理员用户 '{username}' 失败: {e}")
                conn.rollback()
                return False

def set_reader_password(library_card_no: str, password: str):
    """为读者设置或更新密码"""
    hashed_pwd = hash_password(password)
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    UPDATE readers SET password_hash = %s WHERE library_card_no = %s
                """, (hashed_pwd, library_card_no))
                if cur.rowcount == 0:
                    print(f"读者证号 '{library_card_no}' 不存在，密码设置失败。")
                    return False
                conn.commit()
                print(f"读者 '{library_card_no}' 密码设置成功。")
                return True
            except Exception as e:
                print(f"为读者 '{library_card_no}' 设置密码失败: {e}")
                conn.rollback()
                return False

def authenticate_admin(username: str, password: str) -> Optional[Dict]:
    """验证管理员身份"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, password_hash, role, full_name, email, is_active 
                FROM users WHERE username = %s AND role = 'admin'
            """, (username,))
            admin_data = cur.fetchone()
            if admin_data and admin_data['is_active'] and verify_password(password, admin_data['password_hash']):
                # 返回包含角色的字典
                return {
                    'user_id': admin_data['user_id'],
                    'username': admin_data['username'],
                    'role': 'admin',
                    'full_name': admin_data.get('full_name', admin_data['username']),
                    'email': admin_data.get('email')
                }
            return None

def authenticate_reader(library_card_no: str, password: str) -> Optional[Dict]:
    """验证读者身份"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT library_card_no, name, password_hash, status 
                FROM readers WHERE library_card_no = %s
            """, (library_card_no,))
            reader_data = cur.fetchone()
            if reader_data and reader_data['status'] == '正常' and reader_data['password_hash'] and \
               verify_password(password, reader_data['password_hash']):
                return {
                    'library_card_no': reader_data['library_card_no'],
                    'name': reader_data['name'],
                    'role': 'reader' 
                }
            return None

def authenticate_user(username_or_card_no: str, password: str) -> Optional[Dict]:
    """
    统一用户认证函数。
    根据输入首先尝试作为管理员认证，如果失败，则尝试作为读者认证。
    """
    # 尝试管理员认证
    admin_info = authenticate_admin(username_or_card_no, password)
    if admin_info:
        return admin_info

    # 尝试读者认证
    reader_info = authenticate_reader(username_or_card_no, password)
    if reader_info:
        return reader_info
            
    return None # 用户名/借书证号不存在或密码错误

def register_reader(library_card_no: str, name: str, password: str, gender: str = '男', 
                    birth_date: str = None, id_card: str = None, title: str = None,
                    department: str = None, address: str = None, phone: str = None) -> tuple[bool, str]:
    """注册新读者"""
    hashed_pwd = hash_password(password)
    
    max_borrow_count = config.MAX_BORROW_BOOKS

    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # 检查借书证号是否已存在
                cur.execute("SELECT library_card_no FROM readers WHERE library_card_no = %s", (library_card_no,))
                if cur.fetchone():
                    return False, "借书证号已存在。"
                
                if id_card:
                    cur.execute("SELECT id_card FROM readers WHERE id_card = %s", (id_card,))
                    if cur.fetchone():
                        return False, "身份证号已存在。"

                cur.execute("""
                    INSERT INTO readers 
                    (library_card_no, name, password_hash, gender, birth_date, id_card, title,
                     max_borrow_count, current_borrow_count, department, address, phone, status, registration_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, %s, '正常', CURDATE())
                """, (library_card_no, name, hashed_pwd, gender, birth_date, id_card, title,
                      max_borrow_count, department, address, phone))
                conn.commit()
                return True, f"读者 '{name}' ({library_card_no}) 注册成功！"
            except Exception as e:
                conn.rollback()
                # 更具体的错误判断
                if "Duplicate entry" in str(e) and "for key 'library_card_no'" in str(e):
                     return False, "借书证号已存在。"
                if "Duplicate entry" in str(e) and "for key 'id_card'" in str(e):
                     return False, "身份证号已存在。"
                return False, f"注册失败：{str(e)}"

# ====================== 图书类别管理 ======================

def add_book_category(isbn: str, category: str, title: str, author: str, 
                     publisher: str = None, publish_date: str = None, 
                     price: float = None, total_copies: int = 1, description: str = None):
    """添加新的图书类别信息"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO book_categories 
                (isbn, category, title, author, publisher, publish_date, price, 
                 total_copies, available_copies, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (isbn, category, title, author, publisher, publish_date, 
                  price, total_copies, total_copies, description))
            conn.commit()
            print(f"成功添加图书类别：{title}")

def search_books(title: str = None, author: str = None, isbn: str = None, category: str = None):
    """图书查询功能，支持模糊查询。包含实际副本数和可借阅数。"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT 
                    bc.isbn, bc.category, bc.title, bc.author, bc.publisher, 
                    bc.publish_date, bc.price, bc.total_copies, bc.description,
                    COALESCE(SUM(CASE WHEN b.book_number IS NOT NULL THEN 1 ELSE 0 END), 0) as actual_total_copies, 
                    COALESCE(SUM(CASE WHEN b.is_available = '可借' THEN 1 ELSE 0 END), 0) as actual_available_copies
                FROM book_categories bc
                LEFT JOIN books b ON bc.isbn = b.isbn
                WHERE 1=1
            """
            params = []
            
            if title:
                sql += " AND bc.title LIKE %s"
                params.append(f"%{title}%")
            if author:
                sql += " AND bc.author LIKE %s"
                params.append(f"%{author}%")
            if isbn:
                sql += " AND bc.isbn = %s" # ISBN通常是精确匹配
                params.append(isbn)
            if category:
                sql += " AND bc.category LIKE %s"
                params.append(f"%{category}%")
            
            sql += " GROUP BY bc.isbn, bc.category, bc.title, bc.author, bc.publisher, bc.publish_date, bc.price, bc.total_copies, bc.description ORDER BY bc.title"
            
            cur.execute(sql, params)
            # 将查询结果转换为字典列表，并确保 available_copies 是整数
            results = []
            for row in cur.fetchall():
                row_dict = dict(row)
                # 更新 book_categories 表中的 available_copies 字段，使其与实际可借数量一致
                # 注意：这应该由触发器或后端逻辑在借还书时自动处理，此处仅为查询时修正显示
                # 更好的做法是 schema 中的 available_copies 字段始终准确
                row_dict['available_copies'] = row_dict.get('actual_available_copies', 0)
                results.append(row_dict)
            return results

# ====================== 具体图书管理 ======================

def add_book_copy(isbn: str, book_number: str):
    """为已有的ISBN添加新的图书副本"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 检查ISBN是否存在
            cur.execute("SELECT isbn FROM book_categories WHERE isbn = %s", (isbn,))
            if not cur.fetchone():
                raise ValueError("该ISBN不存在，请先添加图书类别信息")
            
            # 添加具体图书
            cur.execute("""
                INSERT INTO books (book_number, isbn, is_available, status)
                VALUES (%s, %s, '可借', '正常')
            """, (book_number, isbn))
            
            # 更新类别表的总数和可借数
            cur.execute("""
                UPDATE book_categories 
                SET total_copies = total_copies + 1, 
                    available_copies = available_copies + 1
                WHERE isbn = %s
            """, (isbn,))
            
            conn.commit()
            print(f"成功添加图书副本：{book_number}")

def update_book_status(book_number: str, status: str):
    """更新图书状态（正常、损坏、遗失）"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE books SET status = %s WHERE book_number = %s
            """, (status, book_number))
            conn.commit()
            print(f"图书 {book_number} 状态已更新为：{status}")

# ====================== 读者管理 ======================

def add_reader(library_card_no: str, name: str, gender: str = '男', 
               birth_date: str = None, id_card: str = None, title: str = None,
               max_borrow_count: int = None, department: str = None,
               address: str = None, phone: str = None, password: Optional[str] = None):
    """
    添加新读者 (通常由管理员操作)。
    如果提供了 password，则会为读者设置密码。
    返回: tuple[bool, str] (操作是否成功, 消息)
    """
    if max_borrow_count is None:
        max_borrow_count = config.MAX_BORROW_BOOKS
        
    password_hash_val = None
    if password:
        password_hash_val = hash_password(password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT library_card_no FROM readers WHERE library_card_no = %s", (library_card_no,))
                if cur.fetchone():
                    return False, "借书证号已存在。"
                
                if id_card: # 只有在提供了id_card时才检查唯一性
                    cur.execute("SELECT id_card FROM readers WHERE id_card = %s", (id_card,))
                    if cur.fetchone():
                        return False, "身份证号已存在。"
                
                cur.execute("""
                    INSERT INTO readers 
                    (library_card_no, name, gender, birth_date, id_card, title,
                     max_borrow_count, current_borrow_count, department, address, phone, 
                     password_hash, status, registration_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, %s, %s, '正常', CURDATE())
                """, (library_card_no, name, gender, birth_date, id_card, title,
                      max_borrow_count, department, address, phone, password_hash_val))
                conn.commit()
                return True, f"读者 '{name}' ({library_card_no}) 添加成功！"
            except Exception as e:
                conn.rollback()
                if "Duplicate entry" in str(e) and "for key 'readers.library_card_no'" in str(e): # 更精确的错误捕获
                     return False, "借书证号已存在。"
                if id_card and "Duplicate entry" in str(e) and "for key 'readers.id_card'" in str(e): # 更精确的错误捕获
                     return False, "身份证号已存在。"
                return False, f"添加读者失败：{str(e)}"

def search_readers(card_no: str = None, name: str = None, department: str = None):
    """读者信息查询"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.callproc('GetReaderInfo', (card_no, name, department))
            results = cur.fetchall()
            
            # 转换英文字段为中文显示
            for reader in results:
                # 假设数据库中存储的是 '男' 或 '女'
                # if reader['gender'] == 'male':
                #     reader['gender'] = '男'
                # elif reader['gender'] == 'female':
                #     reader['gender'] = '女'
                    
                # 假设数据库中存储的是 '正常', '冻结', '注销'
                # if reader['status'] == 'active':
                #     reader['status'] = '正常'
                # elif reader['status'] == 'frozen':
                #     reader['status'] = '冻结'
                # elif reader['status'] == 'cancelled':
                #     reader['status'] = '注销'
                pass # 添加 pass 语句以解决 IndentationError
            
            return results

def update_reader_info(library_card_no: str, **kwargs):
    """更新读者信息"""
    if not kwargs:
        return False, "没有提供任何更新信息。" # 返回元组
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            set_clause_parts = []
            values = []
            for key, value in kwargs.items():
                # 如果更新的是密码，需要哈希处理
                if key == 'password':
                    if value: # 只有当密码非空时才更新
                        set_clause_parts.append("password_hash = %s")
                        values.append(hash_password(str(value)))
                    # 如果密码为空字符串，则不更新密码字段
                elif key == 'gender' and value not in ['男', '女']:
                     return False, "性别信息无效，必须是 '男' 或 '女'."
                else:
                    set_clause_parts.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clause_parts: # 如果没有有效的字段更新（比如只提供了空密码）
                return False, "没有有效的更新信息。"

            set_clause = ", ".join(set_clause_parts)
            values.append(library_card_no)
            
            try:
                cur.execute(f"""
                    UPDATE readers SET {set_clause} WHERE library_card_no = %s
                """, tuple(values)) # values 需要是元组
                if cur.rowcount == 0:
                    return False, "未找到该读者，或信息未发生变化。"
                conn.commit()
                return True, f"读者 {library_card_no} 信息已更新。"
            except Exception as e:
                conn.rollback()
                return False, f"更新读者信息失败: {e}"

# ====================== 借阅管理 ======================

def borrow_book(library_card_no: str, book_number: str, days: int = None) -> tuple[bool, str]:
    """借书处理。返回 (操作是否成功, 消息)"""
    if days is None:
        days = config.DEFAULT_BORROW_DAYS
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_borrow_count, max_borrow_count, status FROM readers WHERE library_card_no = %s", (library_card_no,))
            reader = cur.fetchone()
            
            if not reader:
                return False, "读者不存在。"
            if reader['status'] != '正常': # Schema 使用 '正常'
                return False, "读者状态异常，无法借书。"
            if reader['current_borrow_count'] >= reader['max_borrow_count']:
                return False, "已达到借书数量限制。"
            
            cur.execute("SELECT is_available, status FROM books WHERE book_number = %s", (book_number,))
            book = cur.fetchone()
            
            if not book:
                return False, "图书不存在。"
            if book['is_available'] != '可借': # Schema 使用 '可借'
                return False, f"图书 '{book_number}' 当前不可借 (状态: {book['is_available']}, 物理状态: {book['status']})。"
            if book['status'] != '正常': # Schema 使用 '正常'
                 return False, f"图书 '{book_number}' 状态异常 ({book['status']})，无法借出。"

            due_date = date.today() + timedelta(days=days)
            try:
                cur.execute("""
                    INSERT INTO borrowings (library_card_no, book_number, due_date, status)
                    VALUES (%s, %s, %s, '借阅中') 
                """, (library_card_no, book_number, due_date))
                # 触发器会自动处理 books 和 readers 表的更新
                conn.commit()
                return True, f"借书成功！书号: {book_number}, 应还日期: {due_date.strftime('%Y-%m-%d')}。"
            except Exception as e:
                conn.rollback()
                return False, f"借书失败: {e}"

def return_book(borrowing_id: int) -> tuple[bool, str]:
    """还书处理。返回 (操作是否成功, 消息)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT library_card_no, book_number, due_date, status
                FROM borrowings 
                WHERE borrowing_id = %s
            """, (borrowing_id,))
            borrowing = cur.fetchone()
            
            if not borrowing:
                return False, "借阅记录不存在。"
            if borrowing['status'] == '已归还': # Schema 使用 '已归还'
                return False, "该书已归还。"
            
            fine_amount = 0
            today = date.today()
            # 确保 due_date 是 date 类型
            due_date_obj = borrowing['due_date']
            if isinstance(due_date_obj, str):
                due_date_obj = date.fromisoformat(due_date_obj)

            if due_date_obj < today:
                overdue_days = (today - due_date_obj).days
                fine_amount = overdue_days * config.FINE_PER_DAY
            
            try:
                cur.execute("""
                    UPDATE borrowings 
                    SET return_date = %s, fine_amount = %s, status = '已归还' 
                    WHERE borrowing_id = %s
                """, (today, fine_amount, borrowing_id))
                # 触发器会自动处理 books 和 readers 表的更新
                conn.commit()
                message = f"还书成功！书号: {borrowing['book_number']}."
                if fine_amount > 0:
                    message += f" 产生逾期罚金: {fine_amount:.2f}元。"
                return True, message
            except Exception as e:
                conn.rollback()
                return False, f"还书失败: {e}"

# ====================== 查询统计功能 ======================

def get_overdue_books():
    """查询逾期未归还图书"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM overdue_books")
            return cur.fetchall()

def get_current_borrowings():
    """查询当前所有借阅记录"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT b.borrowing_id, b.library_card_no, r.name as reader_name,
                       b.book_number, bc.title as book_title, bc.author,
                       b.borrow_date, b.due_date, b.status, -- 直接使用 borrowings.status
                       CASE 
                           WHEN b.return_date IS NULL AND b.due_date < CURRENT_DATE THEN DATEDIFF(CURRENT_DATE, b.due_date)
                           ELSE 0 
                       END as overdue_days 
                FROM borrowings b
                JOIN readers r ON b.library_card_no = r.library_card_no
                JOIN books bk ON b.book_number = bk.book_number
                JOIN book_categories bc ON bk.isbn = bc.isbn
                WHERE b.return_date IS NULL
                ORDER BY b.due_date
            """)
            return cur.fetchall()

def get_unreturned_readers_by_book(book_number: str):
    """根据图书编号查询未归还读者"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.callproc('GetUnreturnedReadersByBook', (book_number,))
            return cur.fetchall()

def get_borrowing_statistics(start_date: str, end_date: str):
    """统计指定时间段的借阅次数"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.callproc('GetBorrowingStats', (start_date, end_date))
            return cur.fetchall()

def get_reader_borrowing_history(library_card_no: str, start_date: str = None, end_date: str = None, book_number_filter: str = None):
    """查询读者借阅历史"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT b.borrowing_id, bc.category, bc.title, bc.author, b.book_number,
                       b.borrow_date, b.due_date, b.return_date, b.fine_amount, b.status
                FROM borrowings b
                JOIN books bk ON b.book_number = bk.book_number
                JOIN book_categories bc ON bk.isbn = bc.isbn
                WHERE b.library_card_no = %s
            """
            params = [library_card_no]
            
            if start_date:
                sql += " AND b.borrow_date >= %s"
                params.append(start_date)
            if end_date:
                sql += " AND b.borrow_date <= %s"
                params.append(end_date)
            if book_number_filter:
                sql += " AND b.book_number = %s"
                params.append(book_number_filter)
                
            sql += " ORDER BY b.borrow_date DESC"
            
            cur.execute(sql, params)
            return cur.fetchall()

def get_reader_statistics_summary(reader_id: Optional[str] = None) -> Dict[str, Any]:
    """获取读者借阅统计摘要"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 基础参数
            params = []
            where_clause = ""
            
            if reader_id:
                where_clause = "WHERE bo.library_card_no = %s"
                params.append(reader_id)
                    
            # 当前借阅数
            where_return_null = "WHERE bo.return_date IS NULL" if not where_clause else f"{where_clause} AND bo.return_date IS NULL"
            cur.execute(f"""
                SELECT COUNT(*) AS current_borrowings
                FROM borrowings bo
                {where_return_null}
            """, params)
            current_borrowings = cur.fetchone()['current_borrowings']
            
            # 历史借阅总数
            cur.execute(f"""
                SELECT COUNT(*) AS total_borrowings
                FROM borrowings bo
                {where_clause}
            """, params)
            total_borrowings = cur.fetchone()['total_borrowings']
            
            # 最近一次借阅
            cur.execute(f"""
                SELECT bo.borrow_date, bc.title
                FROM borrowings bo 
                JOIN books b ON bo.book_number = b.book_number
                JOIN book_categories bc ON b.isbn = bc.isbn
                {where_clause}
                ORDER BY bo.borrow_date DESC
                LIMIT 1
            """, params)
            latest_borrow = cur.fetchone()
            
            # 逾期图书数
            where_overdue = "WHERE bo.return_date IS NULL AND bo.due_date < CURDATE()" if not where_clause else f"{where_clause} AND bo.return_date IS NULL AND bo.due_date < CURDATE()"
            cur.execute(f"""
                SELECT COUNT(*) AS overdue_books
                FROM borrowings bo
                {where_overdue}
            """, params)
            overdue_books = cur.fetchone()['overdue_books']
            
            # 添加读者总数统计
            cur.execute("""
                SELECT COUNT(*) AS total_readers
                FROM readers
            """)
            total_readers = cur.fetchone()['total_readers']
            
            # 添加学生读者数量统计
            cur.execute("""
                SELECT COUNT(*) AS student_readers
                FROM readers
                WHERE title LIKE '%学生%'
            """)
            student_readers = cur.fetchone()['student_readers']
            
            # 添加教师读者数量统计
            cur.execute("""
                SELECT COUNT(*) AS teacher_readers
                FROM readers
                WHERE title LIKE '%教师%' OR title LIKE '%老师%' OR title LIKE '%讲师%' OR title LIKE '%教授%'
            """)
            teacher_readers = cur.fetchone()['teacher_readers']
            
            # 添加活跃读者数量统计（过去30天内有借阅记录的读者）
            cur.execute("""
                SELECT COUNT(DISTINCT library_card_no) AS active_readers
                FROM borrowings
                WHERE borrow_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            """)
            active_readers = cur.fetchone()['active_readers']
            
            # 添加本月新增读者数量统计
            cur.execute("""
                SELECT COUNT(*) AS new_this_month
                FROM readers
                WHERE registration_date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
            """)
            new_this_month = cur.fetchone()['new_this_month']
                
            return {
                'current_borrowings': current_borrowings,
                'total_borrowings': total_borrowings,
                'latest_borrow_date': latest_borrow['borrow_date'] if latest_borrow else None,
                'latest_borrow_title': latest_borrow['title'] if latest_borrow else None,
                'overdue_books': overdue_books,
                'total_readers': total_readers,
                'student_readers': student_readers,
                'teacher_readers': teacher_readers,
                'active_readers': active_readers,
                'new_this_month': new_this_month
            }

def get_all_borrowing_history(start_date: str = None, end_date: str = None):
    """获取所有借阅历史记录"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT 
                    bo.borrowing_id, 
                    bo.library_card_no, 
                    r.name AS reader_name,
                    bo.book_number, 
                    bc.title AS book_title,
                    bc.author,
                    bo.borrow_date, 
                    bo.due_date,
                    bo.return_date,
                    CASE
                        WHEN bo.return_date IS NULL AND bo.due_date < CURDATE() THEN '逾期未还'
                        WHEN bo.return_date IS NULL THEN '借阅中'
                        WHEN bo.return_date > bo.due_date THEN '已还(逾期)'
                        ELSE '已还'
                    END AS status
                FROM borrowings bo
                JOIN readers r ON bo.library_card_no = r.library_card_no
                JOIN books b ON bo.book_number = b.book_number
                JOIN book_categories bc ON b.isbn = bc.isbn
                WHERE 1=1
            """
            
            params = []
            
            if start_date:
                sql += " AND bo.borrow_date >= %s"
                params.append(start_date)
            
            if end_date:
                sql += " AND bo.borrow_date <= %s"
                params.append(end_date)
                
            sql += " ORDER BY bo.borrow_date DESC"
            
            cur.execute(sql, params)
            return cur.fetchall()

def get_reader_borrowing_ranks():
    """获取读者借阅排行榜"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    r.library_card_no,
                    r.name,
                    COUNT(bo.borrowing_id) AS borrow_count
                FROM readers r
                LEFT JOIN borrowings bo ON r.library_card_no = bo.library_card_no
                GROUP BY r.library_card_no, r.name
                ORDER BY borrow_count DESC
                LIMIT 10
            """)
            return cur.fetchall()

def get_book_borrowing_ranks():
    """获取图书借阅排行榜"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    bc.isbn,
                    bc.title,
                    COUNT(bo.borrowing_id) AS borrow_count
                FROM book_categories bc
                JOIN books b ON bc.isbn = b.isbn
                LEFT JOIN borrowings bo ON b.book_number = bo.book_number
                GROUP BY bc.isbn, bc.title
                ORDER BY borrow_count DESC
                LIMIT 10
            """)
            return cur.fetchall()

def get_reader_current_borrow_count(library_card_no: str) -> int:
    """获取读者当前借阅数量"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS current_count
                FROM borrowings
                WHERE library_card_no = %s AND return_date IS NULL
            """, (library_card_no,))
            result = cur.fetchone()
            return result['current_count'] if result else 0

def get_reader_total_borrow_history_count(library_card_no: str) -> int:
    """获取读者历史借阅总数"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total_count
                FROM borrowings
                WHERE library_card_no = %s
            """, (library_card_no,))
            result = cur.fetchone()
            return result['total_count'] if result else 0

def get_book_borrowing_history(book_number: str):
    """根据图书编号查询借阅历史"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    b.borrowing_id, 
                    b.library_card_no, 
                    r.name AS reader_name,
                    b.book_number, 
                    bc.title AS book_title,
                    bc.author,
                    b.borrow_date, 
                    b.due_date,
                    b.return_date,
                    CASE
                        WHEN b.return_date IS NULL AND b.due_date < CURDATE() THEN '逾期未还'
                        WHEN b.return_date IS NULL THEN '借阅中'
                        WHEN b.return_date > b.due_date THEN '已还(逾期)'
                        ELSE '已还'
                    END AS status
                FROM borrowings b
                JOIN readers r ON b.library_card_no = r.library_card_no
                JOIN books bk ON b.book_number = bk.book_number
                JOIN book_categories bc ON bk.isbn = bc.isbn
                WHERE b.book_number = %s
                ORDER BY b.borrow_date DESC
            """, (book_number,))
            return cur.fetchall() 