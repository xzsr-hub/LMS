-- 删除现有数据库并重新创建
-- DROP DATABASE IF EXISTS library_management; -- 注释掉此行，防止删除现有数据库
CREATE DATABASE IF NOT EXISTS library_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library_management;

-- 1. 图书ISBN类别信息表
CREATE TABLE IF NOT EXISTS book_categories (
    isbn VARCHAR(20) PRIMARY KEY COMMENT 'ISBN书号',
    category VARCHAR(100) NOT NULL COMMENT '图书类别',
    title VARCHAR(255) NOT NULL COMMENT '书名',
    author VARCHAR(255) NOT NULL COMMENT '作者',
    publisher VARCHAR(255) COMMENT '出版社',
    publish_date DATE COMMENT '出版日期',
    price DECIMAL(10,2) COMMENT '价格',
    total_copies INT NOT NULL DEFAULT 1 COMMENT '馆藏数量',
    available_copies INT NOT NULL DEFAULT 1 COMMENT '可借数量',
    description TEXT COMMENT '图书简介',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_available_copies CHECK (available_copies <= total_copies),
    CONSTRAINT chk_total_copies CHECK (total_copies >= 0),
    CONSTRAINT chk_price CHECK (price >= 0)
);

-- 2. 图书信息表（具体到每一本书）
CREATE TABLE IF NOT EXISTS books (
    book_number VARCHAR(20) PRIMARY KEY COMMENT '图书书号（唯一）',
    isbn VARCHAR(20) NOT NULL COMMENT 'ISBN书号',
    is_available ENUM('可借', '不可借') NOT NULL DEFAULT '可借' COMMENT '是否可借',
    status ENUM('正常', '损坏', '遗失') NOT NULL DEFAULT '正常' COMMENT '图书状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (isbn) REFERENCES book_categories(isbn) ON DELETE CASCADE
);

-- 3. 读者信息表
CREATE TABLE IF NOT EXISTS readers (
    library_card_no VARCHAR(20) PRIMARY KEY COMMENT '借书证号',
    name VARCHAR(100) NOT NULL COMMENT '姓名',
    gender ENUM('男', '女') NOT NULL DEFAULT '男' COMMENT '性别',
    birth_date DATE COMMENT '出生年月',
    id_card VARCHAR(18) UNIQUE COMMENT '身份证号',
    title VARCHAR(50) COMMENT '职称',
    max_borrow_count INT NOT NULL DEFAULT 5 COMMENT '可借数量',
    current_borrow_count INT NOT NULL DEFAULT 0 COMMENT '已借数量',
    department VARCHAR(100) COMMENT '工作部门',
    address VARCHAR(255) COMMENT '家庭住址',
    phone VARCHAR(20) COMMENT '联系电话',
    registration_date DATE DEFAULT (CURRENT_DATE()) COMMENT '注册日期',
    status ENUM('正常', '冻结', '注销') NOT NULL DEFAULT '正常' COMMENT '读者状态',
    password_hash VARCHAR(255) NULL COMMENT '读者密码哈希值',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_current_borrow CHECK (current_borrow_count <= max_borrow_count),
    CONSTRAINT chk_id_card_length CHECK (LENGTH(id_card) IN (15, 18)),
    CONSTRAINT chk_max_borrow CHECK (max_borrow_count > 0)
);

-- 4. 借阅信息表
CREATE TABLE IF NOT EXISTS borrowings (
    borrowing_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '借阅记录ID',
    library_card_no VARCHAR(20) NOT NULL COMMENT '借书证号',
    book_number VARCHAR(20) NOT NULL COMMENT '借阅书号',
    borrow_date DATE DEFAULT (CURRENT_DATE()) COMMENT '借出日期',
    due_date DATE NOT NULL COMMENT '应还日期',
    return_date DATE NULL COMMENT '归还日期（NULL表示未归还）',
    fine_amount DECIMAL(10,2) DEFAULT 0 COMMENT '罚金',
    status ENUM('借阅中', '已归还', '逾期', '遗失') NOT NULL DEFAULT '借阅中' COMMENT '借阅状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (library_card_no) REFERENCES readers(library_card_no) ON DELETE CASCADE,
    FOREIGN KEY (book_number) REFERENCES books(book_number) ON DELETE CASCADE,
    
    -- 约束
    CONSTRAINT chk_dates CHECK (due_date >= borrow_date),
    CONSTRAINT chk_return_date CHECK (return_date IS NULL OR return_date >= borrow_date)
);

-- 新增：用户表 (主要用于管理员)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    role ENUM('admin', 'reader') NOT NULL COMMENT '用户角色', -- 'reader'角色可用于未来扩展
    full_name VARCHAR(100) COMMENT '全名',
    email VARCHAR(100) UNIQUE COMMENT '电子邮箱',
    is_active BOOLEAN DEFAULT TRUE COMMENT '账户是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) COMMENT '用户信息表，包含管理员和可能的其他类型用户';

-- 可选：为管理员表插入一个初始管理员账户 (密码为 admin123, 请在实际使用中修改并妥善保管)
-- 注意：密码哈希值应由后端生成，此处仅为示例。
-- INSERT INTO users (username, password_hash, role, full_name, email) 
-- VALUES ('admin', '$2b$12$abcdefghijklmnopqrstuv.abcdefghijklmnopqrstuv.abcdefghijkl', 'admin', '系统管理员', 'admin@example.com'); 
-- (实际哈希值需要后端生成)

-- 创建索引
-- 注意：索引可能已经存在，如果存在会报错，但不影响程序运行
-- 可以忽略这些错误
CREATE INDEX idx_book_title ON book_categories(title);
CREATE INDEX idx_book_author ON book_categories(author);
CREATE INDEX idx_book_category ON book_categories(category);
CREATE INDEX idx_book_number ON books(book_number);
CREATE INDEX idx_reader_name ON readers(name);
CREATE INDEX idx_borrowing_dates ON borrowings(borrow_date, due_date);

-- 视图：到期未归还图书信息
DROP VIEW IF EXISTS overdue_books;
CREATE VIEW overdue_books AS
SELECT 
    b.borrowing_id,
    b.book_number,
    bc.title AS book_title,
    r.name AS reader_name,
    r.library_card_no,
    b.borrow_date,
    b.due_date,
    DATEDIFF(CURRENT_DATE, b.due_date) AS overdue_days
FROM borrowings b
JOIN books bk ON b.book_number = bk.book_number
JOIN book_categories bc ON bk.isbn = bc.isbn
JOIN readers r ON b.library_card_no = r.library_card_no
WHERE b.return_date IS NULL 
AND b.due_date < CURRENT_DATE;

-- 存储过程：根据图书编号查询未归还读者
DELIMITER //
DROP PROCEDURE IF EXISTS GetUnreturnedReadersByBook //
CREATE PROCEDURE GetUnreturnedReadersByBook(IN book_num VARCHAR(20))
BEGIN
    SELECT r.name, r.library_card_no, b.borrow_date, b.due_date
    FROM borrowings b
    JOIN readers r ON b.library_card_no = r.library_card_no
    WHERE b.book_number = book_num 
    AND b.return_date IS NULL;
END //
DELIMITER ;

-- 存储过程：读者资料查询
DELIMITER //
DROP PROCEDURE IF EXISTS GetReaderInfo //
CREATE PROCEDURE GetReaderInfo(
    IN card_no VARCHAR(20),
    IN reader_name VARCHAR(100),
    IN dept VARCHAR(100)
)
BEGIN
    SELECT r.*,
           GROUP_CONCAT(
               CONCAT(bc.title, ' (', b.book_number, ')')
               SEPARATOR ', '
           ) AS unreturned_books
    FROM readers r
    LEFT JOIN borrowings br ON r.library_card_no = br.library_card_no 
                            AND br.return_date IS NULL
    LEFT JOIN books b ON br.book_number = b.book_number
    LEFT JOIN book_categories bc ON b.isbn = bc.isbn
    WHERE (card_no IS NULL OR r.library_card_no = card_no)
    AND (reader_name IS NULL OR r.name LIKE CONCAT('%', reader_name, '%'))
    AND (dept IS NULL OR r.department LIKE CONCAT('%', dept, '%'))
    GROUP BY r.library_card_no;
END //
DELIMITER ;

-- 存储过程：统计图书借阅次数
DELIMITER //
DROP PROCEDURE IF EXISTS GetBorrowingStats //
CREATE PROCEDURE GetBorrowingStats(
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    SELECT 
        bc.category,
        COUNT(*) as borrow_count
    FROM borrowings b
    JOIN books bk ON b.book_number = bk.book_number
    JOIN book_categories bc ON bk.isbn = bc.isbn
    WHERE b.borrow_date BETWEEN start_date AND end_date
    GROUP BY bc.category
    ORDER BY borrow_count DESC;
END //
DELIMITER ;

-- 触发器：借书时更新相关表
DELIMITER //
DROP TRIGGER IF EXISTS tr_after_borrow_insert //
CREATE TRIGGER tr_after_borrow_insert
AFTER INSERT ON borrowings
FOR EACH ROW
BEGIN
    -- 更新图书状态为不可借
    UPDATE books 
    SET is_available = '不可借' 
    WHERE book_number = NEW.book_number;
    
    -- 更新ISBN类别表的可借数量
    UPDATE book_categories bc
    JOIN books b ON bc.isbn = b.isbn
    SET bc.available_copies = bc.available_copies - 1
    WHERE b.book_number = NEW.book_number;
    
    -- 更新读者已借数量
    UPDATE readers 
    SET current_borrow_count = current_borrow_count + 1
    WHERE library_card_no = NEW.library_card_no;
END //
DELIMITER ;

-- 触发器：还书时更新相关表
DELIMITER //
DROP TRIGGER IF EXISTS tr_after_return_update //
CREATE TRIGGER tr_after_return_update
AFTER UPDATE ON borrowings
FOR EACH ROW
BEGIN
    -- 如果是还书操作（return_date从NULL变为有值）
    IF OLD.return_date IS NULL AND NEW.return_date IS NOT NULL THEN
        -- 更新图书状态为可借
        UPDATE books 
        SET is_available = '可借' 
        WHERE book_number = NEW.book_number;
        
        -- 更新ISBN类别表的可借数量
        UPDATE book_categories bc
        JOIN books b ON bc.isbn = b.isbn
        SET bc.available_copies = bc.available_copies + 1
        WHERE b.book_number = NEW.book_number;
        
        -- 更新读者已借数量
        UPDATE readers 
        SET current_borrow_count = current_borrow_count - 1
        WHERE library_card_no = NEW.library_card_no;
    END IF;
END //
DELIMITER ;

-- 触发器：删除读者前检查是否有未归还图书
DELIMITER //
DROP TRIGGER IF EXISTS tr_before_reader_delete //
CREATE TRIGGER tr_before_reader_delete
BEFORE DELETE ON readers
FOR EACH ROW
BEGIN
    DECLARE borrow_count INT DEFAULT 0;
    
    SELECT COUNT(*) INTO borrow_count
    FROM borrowings
    WHERE library_card_no = OLD.library_card_no
    AND return_date IS NULL;
    
    IF borrow_count > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = '该读者有未归还图书，不能删除';
    END IF;
END //
DELIMITER ;

-- 插入示例数据
INSERT IGNORE INTO book_categories (isbn, category, title, author, publisher, publish_date, price, total_copies, available_copies, description) VALUES 
('9787111421900', '计算机', 'Java核心技术', '凯·霍斯特曼', '机械工业出版社', '2020-01-01', 89.90, 5, 5, 'Java编程经典教材'),
('9787121315633', '计算机', 'Python编程从入门到实践', '埃里克·马瑟斯', '人民邮电出版社', '2019-03-01', 69.90, 3, 3, 'Python入门首选'),
('9787508688923', '文学', '百年孤独', '加西亚·马尔克斯', '中信出版社', '2017-08-01', 45.00, 2, 2, '魔幻现实主义代表作');

INSERT IGNORE INTO books (book_number, isbn, is_available, status) VALUES 
('BK001', '9787111421900', '可借', '正常'),
('BK002', '9787111421900', '可借', '正常'),
('BK003', '9787121315633', '可借', '正常'),
('BK004', '9787508688923', '可借', '正常');

INSERT IGNORE INTO readers (library_card_no, name, gender, birth_date, id_card, title, max_borrow_count, current_borrow_count, department, address, phone, registration_date, status) VALUES 
('R001', '张三', '男', '1990-01-01', '110101199001011234', '程序员', 5, 0, '技术部', '北京市朝阳区', '13800138000', CURRENT_DATE(), '正常'),
('R002', '李四', '女', '1985-05-15', '110101198505155678', '经理', 10, 0, '管理部', '北京市海淀区', '13900139000', CURRENT_DATE(), '正常'); 