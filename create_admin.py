# create_admin.py
import sys
import os

# 确保脚本可以找到 enhanced_library 和 enhanced_config
# 如果 create_admin.py 与 enhanced_library.py 在同一目录，则通常不需要以下路径修改
# 但为了确保，尤其是在不同执行环境下，可以添加项目根目录到 sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from enhanced_library import create_admin_user
    import enhanced_config # 确保数据库配置能被加载
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 create_admin.py 文件位于项目根目录，并且虚拟环境已激活（如果使用的话）。")
    sys.exit(1)

def setup_admin():
    """
    设置管理员账户。
    您可以在这里修改默认的用户名、密码、全名和邮箱。
    """
    admin_username = "admin0"
    admin_password = "123456" # 请务必修改为强密码！
    admin_full_name = "系统管理员"
    admin_email = "admin@example.com" # 可选

    print(f"正在尝试创建管理员账户: {admin_username}...")
    
    # 在调用 create_admin_user 之前，确保数据库已初始化 (如果需要)
    # 通常 enhanced_library 或 enhanced_database 中有 init_db() 函数
    try:
        from enhanced_database import init_db
        print("正在初始化数据库连接（如果尚未初始化）...")
        init_db() # 确保表结构存在
        print("数据库连接和表结构已确认。")
    except ImportError:
        print("警告: enhanced_database.init_db 未找到，假设数据库已正确设置。")
    except Exception as db_e:
        print(f"数据库初始化时发生错误: {db_e}")
        print("请先确保数据库服务正在运行且配置正确。")
        return

    success = create_admin_user(
        username=admin_username,
        password=admin_password,
        full_name=admin_full_name,
        email=admin_email
    )

    if success:
        print(f"管理员账户 '{admin_username}' 创建成功或已存在且信息一致。")
        print("请使用此账户登录系统。")
    else:
        print(f"管理员账户 '{admin_username}' 创建失败。请查看之前的错误信息。")
        print("可能的原因是用户名已存在但密码不同，或者数据库连接问题。")

if __name__ == "__main__":
    setup_admin()