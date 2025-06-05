#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication

# 导入应用程序组件
from gui_app import LoginDialog, MainWindow

def main():
    # 初始化 QApplication
    app = QApplication(sys.argv)
    
    # 使用测试用户直接登录
    user_info = {
        'username': 'admin0', 
        'role': 'admin',
        'full_name': 'Admin Test'
    }
    
    # 直接创建主窗口，跳过登录对话框
    main_window = MainWindow(user_info)
    main_window.show()
    
    # 显示窗口
    print("正在启动图书管理系统 - 测试模式")
    print("已自动以管理员身份登录")
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 