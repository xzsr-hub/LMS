# 图书管理系统功能实现文档

## 功能概述

本次实现完成了图书管理系统中三个核心函数的增强，包括读者身份验证和图书/读者搜索功能。所有函数都包含了完整的错误处理和日志记录机制。

## 实现的函数

### 1. `authenticate_reader(library_card_no: str, password: str) -> Optional[Dict]`

**功能**: 验证读者身份

**参数**:
- `library_card_no`: 读者借书证号
- `password`: 读者密码

**返回值**: 
- 成功: 包含读者信息的字典 `{'library_card_no': str, 'name': str, 'role': 'reader'}`
- 失败: `None`

**功能特点**:
- 完整的输入验证（检查空值和None）
- 安全的bcrypt密码验证
- 读者状态检查（只允许"正常"状态的读者登录）
- 详细的日志记录（成功/失败原因）
- 优雅的错误处理

### 2. `search_books(title=None, author=None, isbn=None, category=None) -> List[Dict]`

**功能**: 搜索图书信息，支持多条件组合查询

**参数**:
- `title`: 书名（支持模糊查询）
- `author`: 作者（支持模糊查询）
- `isbn`: ISBN号（精确匹配）
- `category`: 图书类别（支持模糊查询）

**返回值**: 图书信息列表，每个元素包含完整的图书信息

**功能特点**:
- 支持单条件或多条件组合搜索
- 模糊查询支持（title, author, category）
- 显示实际库存和可借数量
- 详细的搜索参数日志
- 优雅的错误处理，失败时返回空列表

### 3. `search_readers(card_no=None, name=None, department=None) -> List[Dict]`

**功能**: 搜索读者信息，支持多条件组合查询

**参数**:
- `card_no`: 借书证号（精确匹配）
- `name`: 姓名（支持模糊查询）
- `department`: 部门（支持模糊查询）

**返回值**: 读者信息列表，每个元素包含完整的读者信息

**功能特点**:
- 支持存储过程和直接SQL两种查询方式
- 智能降级：存储过程失败时自动切换到直接SQL查询
- 支持单条件或多条件组合搜索
- 详细的搜索参数日志
- 优雅的错误处理，失败时返回空列表

## 日志和错误处理机制

### 日志配置
- 日志级别: INFO
- 输出位置: 控制台 + `/tmp/lms.log` 文件
- 日志格式: 时间戳 - 模块名 - 级别 - 消息

### 错误处理策略
1. **输入验证**: 检查必需参数的有效性
2. **数据库连接**: 使用上下文管理器确保连接正确关闭
3. **异常捕获**: 捕获所有数据库异常并记录详细错误信息
4. **优雅降级**: 函数失败时返回合理的默认值（None或空列表）
5. **详细日志**: 记录操作参数、执行结果和错误原因

## 安全特性

1. **密码安全**: 使用bcrypt进行密码哈希和验证
2. **SQL注入防护**: 使用参数化查询
3. **输入验证**: 严格验证所有输入参数
4. **状态检查**: 只允许状态正常的读者进行认证

## 使用示例

```python
import enhanced_library as lib

# 读者身份验证
user_info = lib.authenticate_reader("R001", "password123")
if user_info:
    print(f"登录成功: {user_info['name']}")
else:
    print("登录失败")

# 搜索图书
books = lib.search_books(title="Python", author="张三")
print(f"找到 {len(books)} 本图书")

# 搜索读者
readers = lib.search_readers(name="李", department="计算机")
print(f"找到 {len(readers)} 位读者")
```

## 测试验证

所有函数都经过了测试验证，包括:
- 正常功能测试
- 异常输入测试
- 数据库连接失败测试
- 日志记录验证

测试结果显示所有函数都能正确处理各种情况，并且在数据库不可用时也能优雅地处理错误。