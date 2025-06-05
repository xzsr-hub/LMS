import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QStackedWidget, QWidget, QVBoxLayout, 
    QLabel, QMessageBox, QTabWidget, QFormLayout, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QGridLayout, QDateEdit, QTextEdit, 
    QHeaderView, QAbstractItemView, QSpacerItem, QSizePolicy, QHBoxLayout,
    QComboBox, QFrame, QGroupBox, QSplitter, QToolBar, QSpinBox, QCheckBox,
    QProgressBar, QScrollArea, QCalendarWidget, QFileDialog, QProgressDialog, QGraphicsDropShadowEffect,
    QDialog, QDialogButtonBox, QStyledItemDelegate
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap, QBrush, QColor, QMovie, QLinearGradient
from PyQt5.QtCore import Qt, QDate, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QSize
from typing import Optional, Dict, Any

import enhanced_database as db
import enhanced_library as lib
import os
import shutil
import datetime
import json

# ====================== 数据备份线程 ======================
class BackupThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    backup_completed = pyqtSignal(bool, str)

    def __init__(self, backup_path):
        super().__init__()
        self.backup_path = backup_path

    def run(self):
        try:
            self.status_updated.emit("正在准备备份...")
            self.progress_updated.emit(10)
            
            # 创建备份目录
            os.makedirs(self.backup_path, exist_ok=True)
            
            self.status_updated.emit("正在导出数据库...")
            self.progress_updated.emit(30)
            
            # 导出数据库结构和数据
            from enhanced_database import get_connection
            
            backup_data = {
                'backup_time': datetime.datetime.now().isoformat(),
                'tables': {}
            }
            
            self.status_updated.emit("正在备份图书类别...")
            self.progress_updated.emit(50)
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 备份各表数据
                    tables = ['book_categories', 'books', 'readers', 'borrowings']
                    for i, table in enumerate(tables):
                        self.status_updated.emit(f"正在备份 {table} 表...")
                        cur.execute(f"SELECT * FROM {table}")
                        backup_data['tables'][table] = cur.fetchall()
                        self.progress_updated.emit(50 + (i + 1) * 10)
            
            # 保存备份文件
            backup_file = os.path.join(self.backup_path, f"library_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            self.status_updated.emit("正在写入备份文件...")
            self.progress_updated.emit(90)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.status_updated.emit("备份完成！")
            self.progress_updated.emit(100)
            
            self.backup_completed.emit(True, f"备份成功！\n文件保存至：{backup_file}")
            
        except Exception as e:
            self.backup_completed.emit(False, f"备份失败：{str(e)}")

# ========================== 主窗口 ==========================
class MainWindow(QMainWindow):
    def __init__(self, user_info: Dict[str, Any]): # 接受 user_info
        super().__init__()
        self.user_info = user_info # 保存用户信息
        self.setWindowTitle(f"智慧图书管理系统 v2.0 - {self.user_info.get('full_name') or self.user_info.get('name') or self.user_info.get('username', '用户')}") 
        self.setGeometry(50, 50, 1600, 1000) 
        self.setWindowIcon(QIcon.fromTheme("applications-education"))

        # 主题设置
        self.dark_theme = False
        
        font = QFont("Microsoft YaHei UI", 9) 
        QApplication.setFont(font)
        
        # 设置窗口背景渐变
        self.setAutoFillBackground(True)
        self.background_brush = QBrush(QColor("#f5f7fa"))
        self.update_background_gradient()
        
        self.apply_enhanced_stylesheet()

        self.init_ui() # init_ui 中会创建所有 widgets
        self.check_db_connection()
        
        # 初始化动画
        self.setup_animations()

        # 根据用户角色调整UI
        self.adjust_ui_for_role()

    def update_background_gradient(self):
        """更新主窗口背景渐变"""
        palette = self.palette()
        if not self.dark_theme:
            # 多色水平渐变效果
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0.0, QColor("#6a11cb"))
            gradient.setColorAt(0.25, QColor("#2575fc"))
            gradient.setColorAt(0.5, QColor("#ff8008"))
            gradient.setColorAt(0.75, QColor("#FFC837"))
            gradient.setColorAt(1.0, QColor("#36d1dc"))
        else:
            # 深色模式保留原双色垂直渐变
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor("#181818"))
            gradient.setColorAt(1, QColor("#0f0f0f"))
        
        self.background_brush = QBrush(gradient)
        palette.setBrush(QPalette.Window, self.background_brush)
        self.setPalette(palette)
    
    def resizeEvent(self, event):
        """窗口大小改变时更新背景"""
        super().resizeEvent(event)
        self.update_background_gradient()

    def setup_animations(self):
        """设置UI动画效果"""
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.update_animations)
        self.fade_timer.start(50)

    def update_animations(self):
        """更新动画效果"""
        pass  # 可以在这里添加自定义动画逻辑

    def apply_enhanced_stylesheet(self):
        """全面升级的UI样式表，打造精致、现代、专业的视觉体验"""
        is_dark = self.dark_theme
        theme_colors = {
            # Primary Palette (Blue Tones)
            'primary': '#007bff' if not is_dark else '#008cff',  # Brighter blue for dark
            'primary_light': '#58a6ff' if not is_dark else '#5eadff',
            'primary_dark': '#0056b3' if not is_dark else '#0066cc',
            'primary_variant': '#e7f3ff' if not is_dark else 'rgba(0, 123, 255, 0.1)', # Subtle background for primary elements

            # Accent Palette (e.g., for highlights, secondary actions)
            'accent': '#6f42c1' if not is_dark else '#8a63d2', # Purple accent
            'accent_light': '#9a73e8' if not is_dark else '#ab87f0',

            # Backgrounds & Surfaces
            'background_base': '#f8f9fa' if not is_dark else '#121212', # Main window background
            'background_paper': '#ffffff' if not is_dark else '#1e1e1e', # Cards, dialogs, menus
            'background_elevated': '#ffffff' if not is_dark else '#2a2a2a', # Slightly elevated surfaces

            # Text Colors
            'text_primary': '#212529' if not is_dark else '#e0e0e0', # Main text
            'text_secondary': '#6c757d' if not is_dark else '#a0a0a0', # Subdued text
            'text_disabled': '#adb5bd' if not is_dark else '#666666',
            'text_on_primary': '#ffffff', # Text on primary-colored backgrounds
            'text_on_accent': '#ffffff',

            # Borders & Dividers
            'border_main': '#dee2e6' if not is_dark else '#3a3a3a', # Main borders for components
            'border_divider': '#e9ecef' if not is_dark else '#2c2c2c', # Lighter dividers
            # 'border_focus': theme_colors['primary'] if not is_dark else theme_colors['primary_light'], # Moved

            # Semantic Colors
            'success': '#28a745' if not is_dark else '#34c759',
            'success_light': '#d4edda' if not is_dark else 'rgba(52, 199, 89, 0.15)',
            'warning': '#ffc107' if not is_dark else '#ffcc00',
            'warning_light': '#fff3cd' if not is_dark else 'rgba(255, 204, 0, 0.15)',
            'danger': '#dc3545' if not is_dark else '#ff3b30',
            'danger_light': '#f8d7da' if not is_dark else 'rgba(255, 59, 48, 0.15)',
            'info': '#17a2b8' if not is_dark else '#00a9e0',
            'info_light': '#d1ecf1' if not is_dark else 'rgba(0, 169, 224, 0.15)',
            
            # Specific component colors (initial definitions)
            # 'scrollbar_handle': theme_colors['primary'] if not is_dark else theme_colors['primary_light'], # Moved
        }

        # Define keys that depend on other keys in theme_colors after the initial dict creation
        theme_colors['border_focus'] = theme_colors['primary'] if not is_dark else theme_colors['primary_light']
        theme_colors['scrollbar_handle'] = theme_colors['primary'] if not is_dark else theme_colors['primary_light']
        theme_colors['tooltip_bg'] = theme_colors['background_paper'] if not is_dark else '#333333'
        theme_colors['tooltip_text'] = theme_colors['text_primary'] if not is_dark else '#f0f0f0'


        # Helper to convert hex to rgba for subtle backgrounds
        def hex_to_rgba(hex_color, alpha):
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"rgba({r}, {g}, {b}, {alpha})"

        style = f"""
            /* ====== Global Styles ====== */
            QWidget {{
                font-family: "Segoe UI", "Microsoft YaHei UI", "Helvetica Neue", Arial, sans-serif;
                color: {theme_colors['text_primary']};
                font-size: 10pt; /* Slightly larger base font */
            }}

            QMainWindow {{
                background: {'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6a11cb, stop:0.25 #2575fc, stop:0.5 #ff8008, stop:0.75 #FFC837, stop:1 #36d1dc)' if not is_dark else 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #181818, stop:1 #0f0f0f)'};
            }}

            /* ====== MenuBar & Menu ====== */
            QMenuBar {{
                background-color: {theme_colors['background_paper']};
                border-bottom: 1px solid {theme_colors['border_divider']};
                padding: 8px 10px; /* Increased padding */
                font-weight: 500;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 8px 15px; /* Consistent padding */
                border-radius: 6px;
                margin: 2px 4px;
            }}
            QMenuBar::item:selected {{ /* Hover */
                background-color: {hex_to_rgba(theme_colors['primary'], 0.1)};
                color: {theme_colors['primary']};
            }}
            QMenuBar::item:pressed {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.2)};
            }}
            QMenu {{
                background-color: {theme_colors['background_paper']};
                border: 1px solid {theme_colors['border_main']};
                border-radius: 8px;
                padding: 8px; /* Overall padding for the menu popup */
                font-size: 9.5pt;
            }}
            QMenu::item {{
                padding: 10px 20px; /* Generous padding for items */
                border-radius: 5px;
                margin: 2px 0; /* Vertical margin */
            }}
            QMenu::item:selected {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.15)};
                color: {theme_colors['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme_colors['border_divider']};
                margin: 6px 5px; /* More space around separator */
            }}
            QMenu::indicator {{ /* Checkmark/radio button indicator */
                width: 18px;
                height: 18px;
                padding-left: 5px;
            }}

            /* ====== ToolBar ====== */
            QToolBar {{
                background-color: {theme_colors['background_paper']};
                border-bottom: 1px solid {theme_colors['border_divider']};
                padding: 8px;
                spacing: 8px; /* Spacing between items */
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                color: {theme_colors['text_secondary']};
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: 500;
                min-width: auto; /* Allow more natural sizing */
            }}
            QToolBar QToolButton:hover {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.1)};
                color: {theme_colors['primary']};
            }}
            QToolBar QToolButton:pressed {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.2)};
            }}
            QToolBar QToolButton:checked {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.15)};
                color: {theme_colors['primary']};
                font-weight: 600;
            }}
            QToolBar::separator {{
                width: 1px;
                background-color: {theme_colors['border_divider']};
                margin: 5px 8px;
            }}

            /* ====== Buttons ====== */
            QPushButton {{
                background-color: {theme_colors['primary']};
                color: {theme_colors['text_on_primary']};
                border: 1px solid {theme_colors['primary']};
                padding: 10px 22px; /* Balanced padding */
                border-radius: 8px; /* Softer radius */
                font-weight: 500;
                font-size: 10pt;
                min-height: 30px; /* Ensure comfortable click area */
            }}
            QPushButton:hover {{
                background-color: {theme_colors['primary_light']};
                border-color: {theme_colors['primary_light']};
            }}
            QPushButton:pressed {{
                background-color: {theme_colors['primary_dark']};
                border-color: {theme_colors['primary_dark']};
            }}
            QPushButton:disabled {{
                background-color: {theme_colors['text_disabled'] if is_dark else '#e9ecef'};
                color: {theme_colors['text_disabled'] if not is_dark else '#888888'};
                border-color: {theme_colors['text_disabled'] if is_dark else '#ced4da'};
            }}

            QPushButton.success {{ background-color: {theme_colors['success']}; border-color: {theme_colors['success']}; color: {theme_colors['text_on_primary']}; }}
            QPushButton.success:hover {{ background-color: {hex_to_rgba(theme_colors['success'], 0.85)}; }}
            QPushButton.warning {{ background-color: {theme_colors['warning']}; border-color: {theme_colors['warning']}; color: #212529; }} /* Darker text for yellow */
            QPushButton.warning:hover {{ background-color: {hex_to_rgba(theme_colors['warning'], 0.85)}; }}
            QPushButton.danger {{ background-color: {theme_colors['danger']}; border-color: {theme_colors['danger']}; color: {theme_colors['text_on_primary']}; }}
            QPushButton.danger:hover {{ background-color: {hex_to_rgba(theme_colors['danger'], 0.85)}; }}
            QPushButton.info {{ background-color: {theme_colors['info']}; border-color: {theme_colors['info']}; color: {theme_colors['text_on_primary']}; }}
            QPushButton.info:hover {{ background-color: {hex_to_rgba(theme_colors['info'], 0.85)}; }}

            /* Secondary/Outline Button Style */
            QPushButton.secondary {{
                background-color: {theme_colors['background_paper']};
                color: {theme_colors['primary']};
                border: 1px solid {theme_colors['primary']};
            }}
            QPushButton.secondary:hover {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.05)};
                border-color: {theme_colors['primary_light']};
            }}
            QPushButton.secondary:pressed {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.1)};
            }}
            
            /* Link-like Button */
            QPushButton.link {{
                background-color: transparent;
                color: {theme_colors['primary']};
                border: none;
                text-decoration: underline;
                padding: 4px 8px;
            }}
            QPushButton.link:hover {{
                color: {theme_colors['primary_dark']};
            }}


            /* ====== Input Fields (QLineEdit, QTextEdit, QSpinBox, QDateEdit, QComboBox) ====== */
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDateEdit, QComboBox {{
                background-color: {theme_colors['background_paper']};
                border: 1px solid {theme_colors['border_main']};
                border-radius: 8px;
                padding: 10px 12px; /* Comfortable padding */
                color: {theme_colors['text_primary']};
                selection-background-color: {hex_to_rgba(theme_colors['primary'], 0.3)};
                selection-color: {theme_colors['text_primary']};
                font-size: 9.5pt;
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
                border-color: {theme_colors['border_focus']}; /* Use the correctly defined border_focus */
                /* box-shadow: 0 0 0 2px {hex_to_rgba(theme_colors['primary'], 0.2)}; Removed for QSS compatibility */
            }}
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QSpinBox:disabled, QDateEdit:disabled, QComboBox:disabled {{
                background-color: {hex_to_rgba(theme_colors['text_disabled'], 0.1 if not is_dark else 0.2)};
                color: {theme_colors['text_disabled']};
                border-color: {hex_to_rgba(theme_colors['border_main'], 0.5)};
            }}
            QTextEdit, QPlainTextEdit {{
                min-height: 60px; /* Minimum height for text areas */
            }}
            QDateEdit::up-button, QDateEdit::down-button, QSpinBox::up-button, QSpinBox::down-button {{
                subcontrol-origin: border;
                width: 20px;
                border-radius: 6px;
                background-color: transparent; /* Buttons are part of the field */
            }}
            QDateEdit::up-arrow, QSpinBox::up-arrow {{ image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='{theme_colors['text_secondary'].replace('#', '%23')}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 15l-6-6-6 6'/%3E%3C/svg%3E"); }}
            QDateEdit::down-arrow, QSpinBox::down-arrow {{ image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='{theme_colors['text_secondary'].replace('#', '%23')}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); }}
            QDateEdit::up-button:hover, QSpinBox::up-button:hover, QDateEdit::down-button:hover, QSpinBox::down-button:hover {{
                 background-color: {hex_to_rgba(theme_colors['text_secondary'], 0.1)};
            }}

            /* ====== QComboBox ====== */
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px; /* Wider dropdown button */
                border-left-width: 1px;
                border-left-color: {theme_colors['border_divider']};
                border-left-style: solid;
                border-top-right-radius: 7px; /* Match parent */
                border-bottom-right-radius: 7px;
            }}
            QComboBox::down-arrow {{
                image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='{theme_colors['text_secondary'].replace('#', '%23')}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
                padding-right: 5px; /* Center arrow */
            }}
            QComboBox::down-arrow:on {{ /* When dropdown is open */
                /* image: url(... up arrow ...); if needed */
            }}
            QComboBox QAbstractItemView {{ /* Dropdown list style */
                background-color: {theme_colors['background_paper']};
                border: 1px solid {theme_colors['border_main']};
                border-radius: 8px; /* Consistent radius */
                selection-background-color: {hex_to_rgba(theme_colors['primary'], 0.15)};
                selection-color: {theme_colors['primary']};
                padding: 5px;
                font-size: 9.5pt;
            }}

            /* ====== QTableWidget ====== */
            QTableWidget {{
                background-color: {theme_colors['background_paper']};
                border: 1px solid {theme_colors['border_main']};
                border-radius: 10px;
                gridline-color: {theme_colors['border_divider']};
                selection-background-color: {hex_to_rgba(theme_colors['primary'], 0.2)};
                selection-color: {theme_colors['text_primary']};
                font-size: 9.5pt;
                alternate-background-color: {hex_to_rgba(theme_colors['background_base'], 0.5 if not is_dark else 0.2)};
            }}
            QHeaderView::section {{
                background-color: {theme_colors['background_base']}; /* Lighter header */
                padding: 12px 10px; /* Adjusted padding */
                border: none;
                border-bottom: 1px solid {theme_colors['border_main']};
                border-right: 1px solid {theme_colors['border_divider']};
                font-weight: 600; /* Bolder header text */
                color: {theme_colors['text_secondary']};
                font-size: 9.5pt;
            }}
            QHeaderView::section:horizontal {{
                border-top: 1px solid {theme_colors['border_main']}; /* Add top border for horizontal header */
            }}
             QHeaderView::section:vertical {{
                border-left: 1px solid {theme_colors['border_main']};
            }}
            QTableWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {theme_colors['border_divider']};
            }}
            QTableWidget::item:selected {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.25)};
                color: {theme_colors['primary'] if not is_dark else theme_colors['text_on_primary']};
            }}

            /* ====== QTabWidget ====== */
            QTabWidget::pane {{
                border: 1px solid {theme_colors['border_main']};
                border-top: none; /* Pane border joins with tab bar bottom */
                border-radius: 0 0 10px 10px; /* Rounded bottom corners */
                background-color: {theme_colors['background_paper']};
                padding: 15px; /* Padding inside tab content */
            }}
            QTabBar::tab {{
                background-color: {theme_colors['background_base']};
                border: 1px solid {theme_colors['border_divider']};
                border-bottom: none; /* Remove bottom border for non-selected */
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px 25px; /* Generous tab padding */
                margin-right: 3px; /* Space between tabs */
                color: {theme_colors['text_secondary']};
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {theme_colors['background_paper']}; /* Selected tab matches pane */
                color: {theme_colors['primary']};
                border-color: {theme_colors['border_main']};
                border-bottom: 2px solid {theme_colors['primary']}; /* Highlight selected */
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.05)};
                color: {theme_colors['primary']};
            }}
            QTabBar::tab:last {{ margin-right: 0; }}

            /* ====== QGroupBox ====== */
            QGroupBox {{
                background-color: {theme_colors['background_elevated']};
                border: 1px solid {theme_colors['border_main']};
                border-radius: 10px;
                margin-top: 25px; /* Space for title */
                padding: 20px 15px 15px 15px; /* Top padding to not overlap title */
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                top: -12px; /* Pull title up onto the border */
                padding: 3px 12px;
                background-color: {theme_colors['background_elevated']};
                border: 1px solid {theme_colors['border_main']};
                border-radius: 6px;
                color: {theme_colors['primary']};
                font-weight: 600;
                font-size: 10pt;
            }}

            /* ====== QFrame (used as card/panel) ====== */
            QFrame#welcome_panel, QFrame.card_panel {{ /* Assuming you set objectName */
                background-color: {theme_colors['background_paper']};
                border: 1px solid {theme_colors['border_divider']};
                border-radius: 12px;
                /* Add box-shadow if supported, or use border for depth */
            }}

            /* ====== QStatusBar ====== */
            QStatusBar {{
                background-color: {theme_colors['background_paper']};
                border-top: 1px solid {theme_colors['border_divider']};
                padding: 8px 12px;
                color: {theme_colors['text_secondary']};
                font-weight: 500;
            }}
            QStatusBar::item {{
                border: none; /* Remove default item borders */
            }}

            /* ====== QProgressBar ====== */
            QProgressBar {{
                border: 1px solid {theme_colors['border_main']};
                border-radius: 10px; /* Consistent radius */
                background-color: {hex_to_rgba(theme_colors['text_disabled'], 0.1 if not is_dark else 0.2)};
                height: 20px; /* Taller progress bar */
                text-align: center;
                color: {theme_colors['text_on_primary'] if not is_dark else theme_colors['text_primary']};
                font-weight: 500;
            }}
            QProgressBar::chunk {{
                background-color: {theme_colors['primary']};
                border-radius: 9px; /* Slightly smaller to fit inside */
                margin: 1px;
            }}

            /* ====== QScrollBar ====== */
            QScrollBar:vertical {{
                border: none;
                background-color: {theme_colors['background_base']};
                width: 14px; /* Slightly wider */
                margin: 1px 0 1px 0; /* Small margin from edge */
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {hex_to_rgba(theme_colors['scrollbar_handle'], 0.7)};
                min-height: 30px;
                border-radius: 6px;
                border: 1px solid {hex_to_rgba(theme_colors['scrollbar_handle'], 0.5)}; /* Subtle border */
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme_colors['scrollbar_handle']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px; /* Hide default arrows */
                background: transparent;
            }}
            QScrollBar:horizontal {{
                border: none;
                background-color: {theme_colors['background_base']};
                height: 14px;
                margin: 0 1px 0 1px;
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {hex_to_rgba(theme_colors['scrollbar_handle'], 0.7)};
                min-width: 30px;
                border-radius: 6px;
                border: 1px solid {hex_to_rgba(theme_colors['scrollbar_handle'], 0.5)};
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme_colors['scrollbar_handle']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: transparent;
            }}
            
            /* ====== Tooltip ====== */
            QToolTip {{
                background-color: {theme_colors['tooltip_bg']};
                color: {theme_colors['tooltip_text']};
                border: 1px solid {theme_colors['border_main']};
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 9pt;
                opacity: 230; /* Slight transparency */
            }}

            /* ====== Welcome Page Specifics - assuming panel_frame has objectName 'welcome_panel' ====== */
            QFrame#welcome_panel {{
                 padding: 40px; /* More padding for welcome panel */
            }}
            QLabel#welcome_title {{ /* e.g. title_label.setObjectName("welcome_title") */
                color: {theme_colors['primary']};
                font-size: 28pt; /* Larger title */
                font-weight: 300; /* Lighter font weight for modern feel */
                padding-bottom: 10px;
                border-bottom: 1px solid {hex_to_rgba(theme_colors['primary'], 0.3)};
            }}
             QLabel#welcome_subtitle {{ /* e.g. subtitle_label.setObjectName("welcome_subtitle") */
                color: {theme_colors['text_secondary']};
                font-size: 12pt;
                font-weight: 400;
                letter-spacing: 1px; /* Subtle letter spacing */
            }}
            QPushButton#quick_action {{ /* Applied to welcome page buttons */
                background-color: {hex_to_rgba(theme_colors['primary'], 0.08)};
                color: {theme_colors['primary']};
                border: 1px solid {hex_to_rgba(theme_colors['primary'], 0.2)};
                font-size: 11pt;
                padding: 15px 20px;
                min-height: 100px; /* Taller quick action buttons */
            }}
            QPushButton#quick_action:hover {{
                background-color: {hex_to_rgba(theme_colors['primary'], 0.15)};
                border-color: {theme_colors['primary']};
            }}
        """

        # QSS does not support complex box-shadows or transitions well.
        # The filtering for 'transform' and 'box-shadow' remains.
        filtered_lines = []
        for line in style.splitlines():
            stripped = line.strip()
            # Keep 'transition' and 'box-shadow' if they are in comments
            if (stripped.startswith(('transition:', 'transform:', 'box-shadow:')) and 
                not stripped.startswith('/*') and not stripped.endswith('*/')):
                continue
            filtered_lines.append(line)
        self.setStyleSheet('\n'.join(filtered_lines))

    def init_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 创建工具栏
        self.create_toolbar()

        # 更优雅的欢迎页面
        welcome_widget = self.create_welcome_widget()
        self.stacked_widget.addWidget(welcome_widget)

        # 创建菜单栏
        self.create_menu_bar()

        self.statusBar().showMessage("系统就绪")

        # 初始化所有管理界面
        self.book_management_widget = BookManagementWidget(self, self.user_info)
        self.reader_management_widget = ReaderManagementWidget(self, self.user_info)
        self.borrow_management_widget = BorrowManagementWidget(self, self.user_info)
        self.query_statistics_widget = QueryStatisticsWidget(self, self.user_info)
        
        self.stacked_widget.addWidget(self.book_management_widget)
        self.stacked_widget.addWidget(self.reader_management_widget)
        self.stacked_widget.addWidget(self.borrow_management_widget)
        self.stacked_widget.addWidget(self.query_statistics_widget)

        # 默认显示欢迎页面或基于角色的特定页面
        self.stacked_widget.setCurrentIndex(0) # 欢迎页面是第一个添加的

    def create_toolbar(self):
        """创建增强版工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # 快速导航按钮组
        nav_group = QWidget()
        nav_layout = QHBoxLayout(nav_group)
        nav_layout.setSpacing(5)
        
        # 主要功能按钮
        book_action = QAction("📚 图书管理", self)
        book_action.setToolTip("管理图书类别和副本信息")
        book_action.triggered.connect(self.show_book_management_view)
        toolbar.addAction(book_action)

        reader_action = QAction("👥 读者管理", self)
        reader_action.setToolTip("管理读者信息和权限")
        reader_action.triggered.connect(self.show_reader_management_view)
        toolbar.addAction(reader_action)

        borrow_action = QAction("📖 借阅管理", self)
        borrow_action.setToolTip("处理借书和还书业务")
        borrow_action.triggered.connect(self.show_borrow_management_view)
        toolbar.addAction(borrow_action)

        query_action = QAction("📊 查询统计", self)
        query_action.setToolTip("数据分析和统计报表")
        query_action.triggered.connect(self.show_query_statistics_view)
        toolbar.addAction(query_action)

        toolbar.addSeparator()

        # 数据操作按钮组
        refresh_action = QAction("🔄 刷新数据", self)
        refresh_action.setToolTip("刷新所有模块的数据")
        refresh_action.triggered.connect(self.refresh_all_data)
        toolbar.addAction(refresh_action)

        backup_action = QAction("💾 数据备份", self)
        backup_action.setToolTip("备份数据库到本地")
        backup_action.triggered.connect(self.backup_database)
        toolbar.addAction(backup_action)
        
        # 新增功能按钮
        import_action = QAction("📥 数据导入", self)
        import_action.setToolTip("从文件导入数据")
        import_action.triggered.connect(self.import_data)
        toolbar.addAction(import_action)
        
        export_action = QAction("📤 数据导出", self)
        export_action.setToolTip("导出数据到Excel文件")
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # 系统设置按钮组
        theme_action = QAction("🌓 切换主题", self)
        theme_action.setToolTip("在浅色和深色主题之间切换")
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)
        
        settings_action = QAction("⚙️ 系统设置", self)
        settings_action.setToolTip("系统配置和偏好设置")
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        help_action = QAction("❓ 帮助", self)
        help_action.setToolTip("查看使用帮助和文档")
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)

        # 将动作存储起来，方便后续根据角色控制显隐
        self.toolbar_actions = {
            "book_management": book_action,
            "reader_management": reader_action,
            "borrow_management": borrow_action,
            "query_statistics": query_action,
            "refresh_data": refresh_action,
            "backup_database": backup_action,
            "import_data": import_action,
            "export_data": export_action,
            "toggle_theme": theme_action,
            "system_settings": settings_action,
            "help": help_action
        }
        # 也可以将分隔符也管理起来，如果需要动态添加/移除
        # self.toolbar_separators = toolbar.findChildren(QAction, options=Qt.FindDirectChildrenOnly)
        # print([sep for sep in self.toolbar_separators if sep.isSeparator()])

    def create_welcome_widget(self):
        """创建欢迎页面，并为关键元素设置objectName以应用特定样式"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(50, 20, 50, 20)  # 优化页面边距
        welcome_layout.setAlignment(Qt.AlignCenter)
        welcome_layout.setSpacing(30)
        
        # 主标题
        title_label = QLabel("智慧图书管理系统")
        title_label.setObjectName("welcome_title") # <--- 添加 objectName
        title_label.setFont(QFont("Microsoft YaHei UI", 32, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        # 样式将由全局QSS的 #welcome_title 选择器控制
        
        # 副标题
        subtitle_label = QLabel("高效 • 智能 • 专业")
        subtitle_label.setObjectName("welcome_subtitle") # <--- 添加 objectName
        subtitle_label.setFont(QFont("Microsoft YaHei UI", 16))
        subtitle_label.setAlignment(Qt.AlignCenter)
        # 样式将由全局QSS的 #welcome_subtitle 选择器控制
        
        # 快速操作面板
        quick_panel = self.create_quick_action_panel()
        quick_panel.setObjectName("welcome_panel") # <--- 为面板框架添加 objectName
        # 为欢迎面板添加阴影效果
        shadow_wp = QGraphicsDropShadowEffect()
        shadow_wp.setBlurRadius(25)
        shadow_wp.setOffset(0, 8)
        shadow_wp.setColor(QColor(0, 0, 0, 80))
        quick_panel.setGraphicsEffect(shadow_wp)
        
        welcome_layout.addWidget(title_label)
        welcome_layout.addWidget(subtitle_label)
        welcome_layout.addWidget(quick_panel)
        
        return welcome_widget

    def create_quick_action_panel(self):
        """创建快速操作面板，按钮已设置objectName为quick_action"""
        panel_frame = QFrame()
        panel_frame.setObjectName("welcome_panel_inner") # 如果需要独立于外部框架样式，可以设置不同名称
        # 为快速操作面板添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 60))
        panel_frame.setGraphicsEffect(shadow)
        
        panel_layout = QGridLayout(panel_frame)
        panel_layout.setSpacing(25)
        
        actions = [
            ("📚\n图书管理", "管理图书类别和副本", self.show_book_management_view),
            ("👥\n读者管理", "管理读者信息", self.show_reader_management_view),
            ("📖\n借阅管理", "处理借书还书", self.show_borrow_management_view),
            ("📊\n查询统计", "数据分析和报表", self.show_query_statistics_view)
        ]
        
        for i, (title, desc, action) in enumerate(actions):
            btn = QPushButton(title)
            btn.setObjectName("quick_action") # 已有，用于应用 #quick_action 样式
            btn.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
            btn.setMinimumSize(200, 120) # 考虑通过QSS设置 min-height
            btn.setToolTip(desc)
            btn.clicked.connect(action)
            panel_layout.addWidget(btn, i // 2, i % 2)
        
        return panel_frame

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("&文件")
        
        new_action = QAction("新建项目", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 帮助菜单
        help_menu = menubar.addMenu("&帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        self.menu_actions = {
            "file_new": new_action,
            "file_exit": exit_action,
            "help_about": about_action
        }
        # 如果需要，可以更细致地管理整个菜单对象 file_menu, help_menu

    def check_db_connection(self):
        try:
            db.init_db()
            self.statusBar().showMessage("数据库连接成功 ✓")
            QTimer.singleShot(3000, lambda: self.statusBar().showMessage("系统就绪"))
        except Exception as e:
            QMessageBox.critical(self, "数据库连接错误", f"无法连接到数据库:\n{e}\n\n请检查配置并确保MySQL服务正在运行。")
            self.statusBar().showMessage("数据库连接失败 ✗")

    def show_about_dialog(self):
        QMessageBox.about(self, "关于智慧图书管理系统",
                            "智慧图书管理系统 GUI 版\n版本 2.0\n\n基于 PyQt5 和 MySQL 开发\n提供完整的图书管理方案\n\n© 数据库期中项目")

    # 视图切换方法
    def show_book_management_view(self):
        self.stacked_widget.setCurrentWidget(self.book_management_widget)
        self.statusBar().showMessage("图书管理模块")

    def show_reader_management_view(self):
        self.stacked_widget.setCurrentWidget(self.reader_management_widget)
        self.statusBar().showMessage("读者管理模块")

    def show_borrow_management_view(self):
        self.stacked_widget.setCurrentWidget(self.borrow_management_widget)
        self.statusBar().showMessage("借阅管理模块")

    def show_query_statistics_view(self):
        self.stacked_widget.setCurrentWidget(self.query_statistics_widget)
        self.statusBar().showMessage("查询统计模块")

    # 工具栏操作
    def refresh_all_data(self):
        """完善的数据刷新功能"""
        try:
            # 创建进度对话框
            progress = QProgressDialog("正在刷新数据...", "取消", 0, 100, self)
            progress.setWindowTitle("数据刷新")
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoReset(False)
            progress.setAutoClose(False)
            progress.show()
            
            # 刷新步骤
            steps = [
                ("正在刷新图书管理数据...", 25),
                ("正在刷新读者管理数据...", 50), 
                ("正在刷新借阅管理数据...", 75),
                ("正在刷新查询统计数据...", 100)
            ]
            
            for i, (message, value) in enumerate(steps):
                if progress.wasCanceled():
                    break
                    
                progress.setLabelText(message)
                progress.setValue(value)
                QApplication.processEvents()
                
                # 根据当前模块刷新对应数据
                if i == 0:
                    self.book_management_widget.refresh_data()
                elif i == 1:
                    self.reader_management_widget.refresh_data()
                elif i == 2:
                    self.borrow_management_widget.refresh_data()
                elif i == 3:
                    self.query_statistics_widget.refresh_data()
                
                # 模拟处理时间
                QTimer.singleShot(200, lambda: None)
                QApplication.processEvents()
            
            if not progress.wasCanceled():
                progress.setValue(100)
                progress.setLabelText("数据刷新完成！")
                QTimer.singleShot(1000, progress.close)
                
                # 显示成功消息
                self.show_status_message("✅ 所有数据刷新完成", 5000, "success")
                
                # 添加刷新动画效果
                self.animate_refresh_success()
            else:
                progress.close()
                self.show_status_message("❌ 数据刷新已取消", 3000, "warning")
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(self, "刷新失败", f"刷新数据失败：\n{e}")
            self.show_status_message("❌ 数据刷新失败", 3000, "danger")

    def animate_refresh_success(self):
        """刷新成功动画效果"""
        # 简单的状态栏颜色变化动画
        original_style = self.statusBar().styleSheet()
        success_style = """
            QStatusBar {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4caf50, stop: 1 #66bb6a);
                color: white;
                font-weight: bold;
            }
        """
        
        self.statusBar().setStyleSheet(success_style)
        QTimer.singleShot(2000, lambda: self.statusBar().setStyleSheet(original_style))

    def backup_database(self):
        """完善的数据库备份功能"""
        try:
            # 选择备份目录
            backup_dir = QFileDialog.getExistingDirectory(
                self, 
                "选择备份保存目录", 
                os.path.expanduser("~/Desktop"),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            
            if not backup_dir:
                return
            
            # 创建时间戳文件夹
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"library_backup_{timestamp}")
            
            # 启动备份线程
            self.backup_thread = BackupThread(backup_path)
            
            # 创建进度对话框
            self.backup_progress = QProgressDialog("准备备份...", "取消", 0, 100, self)
            self.backup_progress.setWindowTitle("数据库备份")
            self.backup_progress.setWindowModality(Qt.WindowModal)
            self.backup_progress.setAutoReset(False)
            self.backup_progress.setAutoClose(False)
            
            # 连接信号
            self.backup_thread.progress_updated.connect(self.backup_progress.setValue)
            self.backup_thread.status_updated.connect(self.backup_progress.setLabelText)
            self.backup_thread.backup_completed.connect(self.on_backup_completed)
            self.backup_progress.canceled.connect(self.backup_thread.terminate)
            
            # 开始备份
            self.backup_thread.start()
            self.backup_progress.show()
            
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"启动备份失败：\n{e}")

    def on_backup_completed(self, success, message):
        """备份完成回调"""
        self.backup_progress.close()
        
        if success:
            QMessageBox.information(self, "备份成功", message)
            self.show_status_message("💾 数据备份完成", 5000, "success")
        else:
            QMessageBox.critical(self, "备份失败", message)
            self.show_status_message("❌ 数据备份失败", 3000, "danger")

    def show_status_message(self, message, timeout=3000, msg_type="info"):
        """增强的状态栏消息显示"""
        # 根据消息类型设置不同颜色
        color_map = {
            "success": "#4caf50",
            "warning": "#ff9800", 
            "danger": "#f44336",
            "info": "#2196f3"
        }
        
        color = color_map.get(msg_type, "#2196f3")
        
        # 设置临时样式
        temp_style = f"""
            QStatusBar {{
                background: {color};
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px;
            }}
        """
        
        original_style = self.statusBar().styleSheet()
        self.statusBar().setStyleSheet(temp_style)
        self.statusBar().showMessage(message, timeout)
        
        # 恢复原始样式
        QTimer.singleShot(timeout, lambda: self.statusBar().setStyleSheet(original_style))

    def toggle_theme(self):
        """切换主题"""
        self.dark_theme = not self.dark_theme
        self.apply_enhanced_stylesheet()
        self.update_background_gradient()
        self.show_status_message(f"已切换到{'深色' if self.dark_theme else '浅色'}主题", 2000)

    def import_data(self):
        """数据导入功能"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择要导入的数据文件",
                os.path.expanduser("~/Desktop"),
                "JSON文件 (*.json);;Excel文件 (*.xlsx);;CSV文件 (*.csv)"
            )
            
            if not file_path:
                return
            
            # 显示导入确认对话框
            reply = QMessageBox.question(
                self, 
                "确认导入", 
                f"确定要从以下文件导入数据吗？\n\n{file_path}\n\n注意：导入操作可能会覆盖现有数据！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 这里可以实现具体的导入逻辑
                QMessageBox.information(self, "导入功能", "数据导入功能将在后续版本中实现")
                self.show_status_message("📥 数据导入准备就绪", 3000, "info")
            
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"数据导入失败：\n{e}")

    def export_data(self):
        """数据导出功能"""
        try:
            # 选择导出格式
            format_dialog = QMessageBox()
            format_dialog.setWindowTitle("选择导出格式")
            format_dialog.setText("请选择要导出的数据格式：")
            
            excel_btn = format_dialog.addButton("📊 Excel格式", QMessageBox.ActionRole)
            csv_btn = format_dialog.addButton("📄 CSV格式", QMessageBox.ActionRole)
            json_btn = format_dialog.addButton("💾 JSON格式", QMessageBox.ActionRole)
            cancel_btn = format_dialog.addButton("取消", QMessageBox.RejectRole)
            
            format_dialog.exec_()
            clicked_btn = format_dialog.clickedButton()
            
            if clicked_btn == cancel_btn:
                return
            
            # 根据选择的格式确定文件扩展名
            if clicked_btn == excel_btn:
                file_filter = "Excel文件 (*.xlsx)"
                default_ext = ".xlsx"
            elif clicked_btn == csv_btn:
                file_filter = "CSV文件 (*.csv)"
                default_ext = ".csv"
            else:  # JSON
                file_filter = "JSON文件 (*.json)"
                default_ext = ".json"
            
            # 选择保存位置
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"library_export_{timestamp}{default_ext}"
            
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存导出文件",
                os.path.join(os.path.expanduser("~/Desktop"), default_filename),
                file_filter
            )
            
            if save_path:
                # 这里可以实现具体的导出逻辑
                QMessageBox.information(self, "导出功能", f"数据将导出到：\n{save_path}\n\n导出功能将在后续版本中实现")
                self.show_status_message("📤 数据导出准备就绪", 3000, "info")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"数据导出失败：\n{e}")

    def show_settings(self):
        """显示系统设置对话框"""
        settings_dialog = SystemSettingsDialog(self)
        settings_dialog.exec_()

    def show_help(self):
        """显示帮助信息"""
        help_text = """
        📖 智慧图书管理系统 v2.0 使用帮助
        
        🔧 主要功能：
        • 📚 图书管理：管理图书类别和副本
        • 👥 读者管理：管理读者信息和权限
        • 📖 借阅管理：处理借书还书业务
        • 📊 查询统计：数据分析和报表
        
        🛠️ 工具栏功能：
        • 🔄 刷新数据：重新加载所有数据
        • 💾 数据备份：备份数据库到本地
        • 📥📤 导入导出：数据的导入导出
        • 🌓 主题切换：切换界面主题
        
        💡 使用技巧：
        • 双击表格行可以快速编辑
        • 使用Ctrl+快捷键快速操作
        • 状态栏显示操作结果反馈
        
        📞 技术支持：
        如有问题请联系系统管理员
        """
        
        help_dialog = QMessageBox()
        help_dialog.setWindowTitle("使用帮助")
        help_dialog.setText(help_text)
        help_dialog.setIcon(QMessageBox.Information)
        help_dialog.exec_()

    def adjust_ui_for_role(self):
        """根据用户角色调整UI元素的可见性和功能"""
        role = self.user_info.get('role')

        if role == 'admin':
            # 管理员拥有所有权限，默认所有UI元素都可见
            self.statusBar().showMessage("管理员已登录。欢迎！", 5000)
            # 可以选择显式设置所有动作可见，以防默认状态不一致
            for action_key in self.toolbar_actions:
                self.toolbar_actions[action_key].setVisible(True)
            # (如果管理了分隔符，也设置其可见性)
            # 管理员可以访问所有主界面

            # 确保传递user_info到所有子模块
            self.book_management_widget.user_info = self.user_info
            self.reader_management_widget.user_info = self.user_info
            self.borrow_management_widget.user_info = self.user_info
            self.query_statistics_widget.user_info = self.user_info
            
            # 确保所有子模块调用其adjust_ui_for_role方法
            self.book_management_widget.adjust_ui_for_role()
            self.reader_management_widget.adjust_ui_for_role()
            self.borrow_management_widget.adjust_ui_for_role()
            self.query_statistics_widget.adjust_ui_for_role()

        elif role == 'reader':
            self.statusBar().showMessage(f"读者 '{self.user_info.get('name', '用户')}' 已登录。欢迎！", 5000)
            
            # 隐藏/禁用管理员专属工具栏按钮
            admin_toolbar_actions = [
                "reader_management",
                "backup_database", "import_data", "export_data", "system_settings"
            ]
            reader_visible_toolbar_actions = [
                "book_management", # 读者应能搜索图书，但不能编辑
                "borrow_management", # 读者可以看到自己的借阅记录和还书状态
                "query_statistics", # 读者应能查看自己的借阅统计或热门图书
                "refresh_data", # 有限刷新，例如只刷新自己的数据
                "toggle_theme", 
                "help"
            ]

            for action_key, action_obj in self.toolbar_actions.items():
                if action_key in reader_visible_toolbar_actions:
                    action_obj.setVisible(True)
                else:
                    action_obj.setVisible(False)
            
            # 调整菜单栏
            # 例如，文件菜单中可能只保留"退出"
            if self.menu_actions.get("file_new"): # 检查是否存在
                 self.menu_actions["file_new"].setVisible(False)

            # 传递user_info到所有子模块
            self.book_management_widget.user_info = self.user_info
            self.reader_management_widget.user_info = self.user_info
            self.borrow_management_widget.user_info = self.user_info
            self.query_statistics_widget.user_info = self.user_info
            
            # 确保所有子模块调用其adjust_ui_for_role方法
            self.book_management_widget.adjust_ui_for_role()
            self.reader_management_widget.adjust_ui_for_role()
            self.borrow_management_widget.adjust_ui_for_role()
            self.query_statistics_widget.adjust_ui_for_role()

            # 调整欢迎页上的快速操作按钮
            self.adjust_welcome_actions_for_reader()
            self.stacked_widget.setCurrentIndex(0) # 欢迎页面

        else: # 未知角色或无角色信息
            QMessageBox.warning(self, "角色错误", "无法识别用户角色，将以受限模式运行。")
            # 默认隐藏所有可能敏感的操作
            for action_key in self.toolbar_actions:
                if action_key not in ["toggle_theme", "help"]:
                    self.toolbar_actions[action_key].setVisible(False)
            self.stacked_widget.setCurrentIndex(0) # 欢迎页

    def adjust_welcome_actions_for_reader(self):
        """调整欢迎页面上的快速操作按钮以适应读者角色"""
        # 假设 self.create_welcome_widget() 中创建的按钮可以通过 objectName 或直接引用找到
        # 示例：隐藏或修改管理员相关的快速操作
        # panel_frame = self.stacked_widget.widget(0).findChild(QFrame, "welcome_panel_inner")
        quick_panel_frame = None
        welcome_widget = self.stacked_widget.widget(0) # 假设欢迎页总是第一个
        if welcome_widget:
            # 查找 create_quick_action_panel 返回的 QFrame
            # 这个查找方式比较脆弱，如果布局改变会失效
            # 更好的方式是在创建时保存对这些按钮的引用
            panels = welcome_widget.findChildren(QFrame)
            for panel in panels:
                if panel.objectName() == "welcome_panel_inner": # 检查是否是之前设定的名称
                    quick_panel_frame = panel
                    break
                # 如果 welcome_panel_inner 不存在，尝试直接找 quick_action 按钮的父级
                # (这取决于 create_quick_action_panel 的具体实现)
                if not quick_panel_frame and panel.findChild(QPushButton, "quick_action"):
                    quick_panel_frame = panel # 可能就是这个 panel
                    # break # 如果有多个panel包含quick_action，这里需要更精确

        if quick_panel_frame:
            buttons = quick_panel_frame.findChildren(QPushButton)
            for btn in buttons:
                if btn.objectName() == "quick_action":
                    text = btn.text()
                    if "读者管理" in text: # 对读者隐藏
                        btn.setVisible(False)
                    elif "借阅管理" in text: 
                        btn.setText("📖\n我的借阅")
                        btn.setToolTip("查看我的借阅记录和还书")
                        # 保留原有连接，因为借阅管理已经根据角色进行了调整
                    elif "图书管理" in text: # 重定向到读者图书搜索
                        btn.setText("📚\n搜索图书")
                        btn.setToolTip("搜索和浏览图书")
                        # 保留原有连接，因为图书管理已经根据角色进行了调整
                    elif "查询统计" in text: # 重定向到读者统计
                        btn.setText("📊\n借阅统计")
                        btn.setToolTip("查看我的借阅统计和热门图书")
                        # 保留原有连接，因为查询统计已经根据角色进行了调整
        else:
            print("警告: 未找到欢迎页面的快速操作面板 (welcome_panel_inner 或包含quick_action按钮的面板)")

    def show_book_detail_for_reader(self, item):
        """为读者显示图书详情"""
        selected_row_index = item.row()
        cat_data = self.category_table.item(selected_row_index, 0).data(Qt.UserRole)
        if not cat_data:
            return

        # 创建详情对话框
        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle("图书详情")
        detail_layout = QVBoxLayout(detail_dialog)
        
        # 创建表单布局放置详细信息
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)

        # 添加图书信息
        form_layout.addRow("<b>ISBN:</b>", QLabel(cat_data.get('isbn', 'N/A')))
        form_layout.addRow("<b>类别:</b>", QLabel(cat_data.get('category', 'N/A')))
        form_layout.addRow("<b>书名:</b>", QLabel(cat_data.get('title', 'N/A')))
        form_layout.addRow("<b>作者:</b>", QLabel(cat_data.get('author', 'N/A')))
        form_layout.addRow("<b>出版社:</b>", QLabel(cat_data.get('publisher', 'N/A')))
        form_layout.addRow("<b>出版日期:</b>", QLabel(str(cat_data.get('publish_date', 'N/A'))))
        form_layout.addRow("<b>价格:</b>", QLabel(f"{cat_data.get('price', 'N/A')} 元"))
        
        # 馆藏信息
        total_copies = cat_data.get('total_copies', 0) or cat_data.get('actual_total_copies', 0)
        available_copies = cat_data.get('available_copies', 0) or cat_data.get('actual_available_copies', 0)
        
        form_layout.addRow("<b>馆藏数量:</b>", QLabel(str(total_copies)))
        
        # 可借状态，添加颜色指示
        available_label = QLabel(str(available_copies))
        if available_copies > 0:
            available_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            available_label.setStyleSheet("color: red;")
        form_layout.addRow("<b>可借数量:</b>", available_label)
        
        detail_layout.addLayout(form_layout)
        
        # 添加图书简介
        if cat_data.get('description'):
            description_group = QGroupBox("图书简介")
            desc_layout = QVBoxLayout(description_group)
            description_text = QLabel(cat_data.get('description', ''))
            description_text.setWordWrap(True)
            desc_layout.addWidget(description_text)
            detail_layout.addWidget(description_group)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        if available_copies > 0:
            btn_borrow = QPushButton("📚 借阅此书")
            btn_borrow.setStyleSheet("background-color: #4caf50; color: white;")
            btn_borrow.clicked.connect(lambda: self.borrow_book(cat_data))
            button_layout.addWidget(btn_borrow)
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(detail_dialog.accept)
        button_layout.addWidget(btn_close)
        
        detail_layout.addLayout(button_layout)
        
        # 设置对话框尺寸
        detail_dialog.setMinimumWidth(400)
        detail_dialog.exec_()

    def handle_show_registration(self):
        """显示读者注册对话框"""
        # 暂时关闭登录对话框，以便注册对话框显示在前面
        # self.hide() # 隐藏当前登录对话框不是最佳做法，可能导致流程混乱
        
        reg_dialog = RegistrationDialog(self)
        if reg_dialog.exec_() == QDialog.Accepted:
            # 注册成功后，可以引导用户返回登录，或者自动登录 (取决于产品设计)
            # 此处简单提示，并保持登录对话框打开
            QMessageBox.information(self, "注册成功", "读者注册成功！请使用您的借书证号和密码登录。")
            # self.username_input.setText(reg_dialog.get_registered_card_no()) # 可选：自动填充刚注册的卡号
            # self.password_input.clear()
            # self.password_input.setFocus()
        # self.show() # 如果之前隐藏了，则重新显示登录对话框

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        return self.user_info

# ====================== 系统设置对话框 ======================
class SystemSettingsDialog(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.setText("系统设置功能")
        self.setInformativeText("系统设置功能将在后续版本中实现\n包括：数据库配置、界面设置、用户偏好等")
        self.setIcon(QMessageBox.Information)

# ====================== 登录对话框 ======================
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统登录")
        self.setModal(True)
        self.user_info: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # 移除角色选择
        # self.role_combo = QComboBox()
        # self.role_combo.addItems(["管理员", "读者"])
        # form_layout.addRow("登录角色:", self.role_combo)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("管理员用户名 或 读者借书证号")
        form_layout.addRow("账号:", self.username_input) # 标签改为"账号"

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入密码")
        form_layout.addRow("密码:", self.password_input)

        layout.addLayout(form_layout)

        # 按钮
        self.buttons = QDialogButtonBox()
        self.login_button = self.buttons.addButton("登录", QDialogButtonBox.AcceptRole)
        self.register_button = self.buttons.addButton("注册新读者", QDialogButtonBox.ActionRole) # 新增注册按钮
        self.cancel_button = self.buttons.addButton(QDialogButtonBox.Cancel)
        
        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.handle_show_registration) # 连接注册按钮的信号
        self.cancel_button.clicked.connect(self.reject)
        
        layout.addWidget(self.buttons)

        self.setMinimumWidth(380) # 调整宽度

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "登录失败", "账号和密码不能为空！")
            return

        # 使用统一认证函数
        authenticated_user_info = lib.authenticate_user(username, password)

        if authenticated_user_info:
            self.user_info = authenticated_user_info
            role_display = "管理员" if self.user_info.get('role') == 'admin' else "读者"
            user_identifier = self.user_info.get('full_name') or self.user_info.get('name') or self.user_info.get('username')
            QMessageBox.information(self, "登录成功", f"{role_display} '{user_identifier}' 登录成功！")
            self.accept()
        else:
            QMessageBox.warning(self, "登录失败", "账号或密码错误，或账户状态异常。")

    def handle_show_registration(self):
        """显示读者注册对话框"""
        # 暂时关闭登录对话框，以便注册对话框显示在前面
        # self.hide() # 隐藏当前登录对话框不是最佳做法，可能导致流程混乱
        
        reg_dialog = RegistrationDialog(self)
        if reg_dialog.exec_() == QDialog.Accepted:
            # 注册成功后，可以引导用户返回登录，或者自动登录 (取决于产品设计)
            # 此处简单提示，并保持登录对话框打开
            QMessageBox.information(self, "注册成功", "读者注册成功！请使用您的借书证号和密码登录。")
            # self.username_input.setText(reg_dialog.get_registered_card_no()) # 可选：自动填充刚注册的卡号
            # self.password_input.clear()
            # self.password_input.setFocus()
        # self.show() # 如果之前隐藏了，则重新显示登录对话框

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        return self.user_info

# ====================== 读者注册对话框 ======================
class RegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("读者注册")
        self.setModal(True)
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.library_card_no_input = QLineEdit()
        self.library_card_no_input.setPlaceholderText("例如：R003 (建议字母R开头+数字)")
        self.form_layout.addRow("借书证号*:", self.library_card_no_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("您的真实姓名")
        self.form_layout.addRow("姓名*:", self.name_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("至少6位字符")
        self.form_layout.addRow("密码*:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("再次输入密码")
        self.form_layout.addRow("确认密码*:", self.confirm_password_input)
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])
        self.form_layout.addRow("性别:", self.gender_combo)

        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate().addYears(-20)) # 默认20年前
        self.birth_date_input.setDisplayFormat("yyyy-MM-dd")
        self.form_layout.addRow("出生日期:", self.birth_date_input)
        
        self.id_card_input = QLineEdit()
        self.id_card_input.setPlaceholderText("可选，15或18位身份证号")
        self.form_layout.addRow("身份证号:", self.id_card_input)

        self.department_input = QLineEdit()
        self.department_input.setPlaceholderText("可选，如：计算机学院")
        self.form_layout.addRow("部门/学院:", self.department_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("可选，您的联系电话")
        self.form_layout.addRow("联系电话:", self.phone_input)
        
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("可选，您的联系地址")
        self.address_input.setFixedHeight(60)
        self.form_layout.addRow("联系地址:", self.address_input)

        self.layout.addLayout(self.form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("注册")
        self.buttons.accepted.connect(self.handle_registration)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        
        self.setMinimumWidth(450)
        self._registered_card_no: Optional[str] = None

    def handle_registration(self):
        library_card_no = self.library_card_no_input.text().strip()
        name = self.name_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        gender = self.gender_combo.currentText()
        birth_date_str = self.birth_date_input.date().toString("yyyy-MM-dd")
        id_card = self.id_card_input.text().strip() or None
        department = self.department_input.text().strip() or None
        phone = self.phone_input.text().strip() or None
        address = self.address_input.toPlainText().strip() or None

        # 基本校验
        if not all([library_card_no, name, password, confirm_password]):
            QMessageBox.warning(self, "注册失败", "带星号（*）的字段不能为空！")
            return
        if password != confirm_password:
            QMessageBox.warning(self, "注册失败", "两次输入的密码不一致！")
            self.password_input.clear()
            self.confirm_password_input.clear()
            self.password_input.setFocus()
            return
        if len(password) < 6: # 简单密码长度校验
            QMessageBox.warning(self, "注册失败", "密码长度至少为6位！")
            return
        if id_card and not (len(id_card) == 15 or len(id_card) == 18):
            QMessageBox.warning(self, "注册失败", "身份证号格式不正确（应为15或18位）。")
            return

        success, message = lib.register_reader(
            library_card_no=library_card_no,
            name=name,
            password=password,
            gender=gender,
            birth_date=birth_date_str if self.birth_date_input.date() != QDate.currentDate().addYears(-20) else None, # 只有修改过才传递
            id_card=id_card,
            department=department,
            phone=phone,
            address=address
            # title 字段暂未在注册表单中提供，可以根据需要添加
        )

        if success:
            self._registered_card_no = library_card_no # 保存注册成功的卡号
            QMessageBox.information(self, "注册成功", message)
            self.accept()
        else:
            QMessageBox.critical(self, "注册失败", message)
            # 根据错误类型，可以考虑清除特定字段或设置焦点
            if "借书证号已存在" in message:
                self.library_card_no_input.selectAll()
                self.library_card_no_input.setFocus()
            elif "身份证号已存在" in message:
                self.id_card_input.selectAll()
                self.id_card_input.setFocus()


    def get_registered_card_no(self) -> Optional[str]:
        return self._registered_card_no

# ====================== 导入附加模块 ======================
# 确保 ReaderManagementWidget, BorrowManagementWidget, QueryStatisticsWidget 的导入路径正确
# 如果它们在同一目录下，可以直接导入
try:
    from additional_widgets import ReaderManagementWidget, BorrowManagementWidget, QueryStatisticsWidget
except ImportError:
    # 处理可能的ImportError，例如如果文件不在PYTHONPATH或当前目录
    QMessageBox.critical(None, "模块导入错误", 
                         "无法加载附加模块 (additional_widgets.py)。\n"
                         "请确保该文件与主程序在同一目录或已正确安装。")
    sys.exit(1)

# ====================== 图书管理模块 ======================
class BookManagementWidget(QWidget):
    def __init__(self, parent=None, user_info=None):
        super().__init__(parent)
        self.parent_window = parent
        self.user_info = user_info
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # 模块标题
        title_label = QLabel("📚 图书管理")
        title_label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #1976d2; margin-bottom: 15px;")
        self.layout.addWidget(title_label)

        self.tabs = QTabWidget()
        self.tab_category = QWidget()
        self.tab_copy = QWidget()

        self.tabs.addTab(self.tab_category, "📖 图书类别管理")
        self.tabs.addTab(self.tab_copy, "📋 图书副本管理")

        self.init_category_tab()
        self.init_copy_tab()

        self.layout.addWidget(self.tabs)
        
    def adjust_ui_for_role(self):
        """根据用户角色调整UI界面"""
        is_admin = self.user_info and self.user_info.get('role') == 'admin'
        is_reader = self.user_info and self.user_info.get('role') == 'reader'

        # 更新Tab标签文字
        self.tabs.setTabText(0, "📖 图书类别管理" if is_admin else "🔍 图书查询")
        self.tabs.setTabText(1, "📋 图书副本管理" if is_admin else "📚 图书副本状态")

        # 类别管理标签页
        self.btn_add_category.setVisible(is_admin)
        self.btn_clear_cat_form.setVisible(is_admin)
        self.btn_load_cat_to_form.setVisible(is_admin)
        
        # 表单区域（读者只需要搜索功能）
        form_fields = [
            self.cat_isbn, self.cat_category, self.cat_title, self.cat_author,
            self.cat_publisher, self.cat_publish_date, self.cat_price,
            self.cat_total_copies, self.cat_description
        ]
        
        # 读者只能使用表单进行搜索，不能添加/编辑
        if is_reader:
            self.btn_search_category.setText("🔍 搜索图书")
            # 禁用不必要的表单字段，但保留搜索相关字段
            for field in form_fields:
                if field in [self.cat_isbn, self.cat_title, self.cat_author, self.cat_category]:
                    field.setReadOnly(False)  # 允许输入搜索条件
                else:
                    field.setReadOnly(True)   # 其他字段设为只读
        else:
            self.btn_search_category.setText("🔍 搜索类别")
            # 管理员可以使用所有字段
            for field in form_fields:
                field.setReadOnly(False)
        
        # 副本管理标签页
        self.btn_add_copy.setVisible(is_admin)
        self.btn_update_copy_status.setVisible(is_admin)
        
        # 表格交互
        table_mode = QAbstractItemView.NoEditTriggers  # 默认不可编辑
        self.category_table.setEditTriggers(table_mode)
        self.copy_table.setEditTriggers(table_mode)
        
        # 双击表格行的行为
        try:
            # 尝试断开所有已连接的信号
            self.category_table.itemDoubleClicked.disconnect()
        except TypeError:
            # 如果没有连接的信号，disconnect()会引发异常
            pass
            
        # 根据角色连接不同的处理函数
        if is_admin:
            self.category_table.itemDoubleClicked.connect(self.load_category_to_form)
        else:
            self.category_table.itemDoubleClicked.connect(self.show_book_detail_for_reader)

    def refresh_data(self):
        """刷新数据"""
        self.load_all_categories()
        self.refresh_copies()
        self.load_isbn_options()

    def init_category_tab(self):
        main_layout = QVBoxLayout(self.tab_category)
        main_layout.setSpacing(20)

        # 使用分割器来分离表单和表格
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：表单区域
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.StyledPanel)
        form_layout = QVBoxLayout(form_frame)
        
        # 表单分组
        form_group = QGroupBox("图书信息录入")
        form_group_layout = QGridLayout(form_group)
        form_group_layout.setSpacing(12)

        # 左列
        form_group_layout.addWidget(QLabel("ISBN:"), 0, 0)
        self.cat_isbn = QLineEdit()
        self.cat_isbn.setPlaceholderText("例如：978-7-111-64345-3")
        form_group_layout.addWidget(self.cat_isbn, 0, 1)

        form_group_layout.addWidget(QLabel("图书类别:"), 1, 0)
        self.cat_category = QLineEdit()
        self.cat_category.setPlaceholderText("例如：计算机、文学、科学")
        form_group_layout.addWidget(self.cat_category, 1, 1)

        form_group_layout.addWidget(QLabel("书名:"), 2, 0)
        self.cat_title = QLineEdit()
        self.cat_title.setPlaceholderText("请输入完整书名")
        form_group_layout.addWidget(self.cat_title, 2, 1)

        form_group_layout.addWidget(QLabel("作者:"), 3, 0)
        self.cat_author = QLineEdit()
        self.cat_author.setPlaceholderText("主要作者姓名")
        form_group_layout.addWidget(self.cat_author, 3, 1)

        # 右列
        form_group_layout.addWidget(QLabel("出版社:"), 0, 2)
        self.cat_publisher = QLineEdit()
        self.cat_publisher.setPlaceholderText("出版社名称")
        form_group_layout.addWidget(self.cat_publisher, 0, 3)

        form_group_layout.addWidget(QLabel("出版日期:"), 1, 2)
        self.cat_publish_date = QDateEdit()
        self.cat_publish_date.setDate(QDate.currentDate())
        self.cat_publish_date.setCalendarPopup(True)
        form_group_layout.addWidget(self.cat_publish_date, 1, 3)

        form_group_layout.addWidget(QLabel("价格:"), 2, 2)
        self.cat_price = QLineEdit()
        self.cat_price.setPlaceholderText("例如：89.00")
        form_group_layout.addWidget(self.cat_price, 2, 3)

        form_group_layout.addWidget(QLabel("馆藏数量:"), 3, 2)
        self.cat_total_copies = QLineEdit()
        self.cat_total_copies.setPlaceholderText("数字")
        form_group_layout.addWidget(self.cat_total_copies, 3, 3)

        # 描述跨列
        form_group_layout.addWidget(QLabel("图书简介:"), 4, 0)
        self.cat_description = QTextEdit()
        self.cat_description.setFixedHeight(80)
        self.cat_description.setPlaceholderText("请输入图书简介...")
        form_group_layout.addWidget(self.cat_description, 4, 1, 1, 3)

        form_layout.addWidget(form_group)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.btn_add_category = QPushButton("➕ 添加类别")
        self.btn_search_category = QPushButton("🔍 搜索类别")
        self.btn_clear_cat_form = QPushButton("🗑️ 清空表单")
        self.btn_load_cat_to_form = QPushButton("📝 编辑选中")
        
        button_layout.addWidget(self.btn_add_category)
        button_layout.addWidget(self.btn_search_category)
        button_layout.addWidget(self.btn_clear_cat_form)
        button_layout.addWidget(self.btn_load_cat_to_form)
        button_layout.addStretch()
        
        form_layout.addLayout(button_layout)
        splitter.addWidget(form_frame)

        # 下半部分：表格区域
        table_frame = QFrame()
        table_frame.setFrameStyle(QFrame.StyledPanel)
        table_layout = QVBoxLayout(table_frame)
        
        table_label = QLabel("📊 图书类别列表")
        table_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        table_label.setStyleSheet("color: #495057; margin-bottom: 10px;")
        table_layout.addWidget(table_label)

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(9)
        self.category_table.setHorizontalHeaderLabels([
            "ISBN", "类别", "书名", "作者", "出版社", "出版日期", "价格", "馆藏", "可借"
        ])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.category_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.category_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setSortingEnabled(True)
        
        table_layout.addWidget(self.category_table)
        splitter.addWidget(table_frame)

        # 设置分割器比例
        splitter.setSizes([300, 400])
        main_layout.addWidget(splitter)

        # 连接信号
        self.btn_add_category.clicked.connect(self.add_category)
        self.btn_search_category.clicked.connect(self.search_categories)
        self.btn_clear_cat_form.clicked.connect(self.clear_category_form)
        self.btn_load_cat_to_form.clicked.connect(self.load_category_to_form)
        self.category_table.itemDoubleClicked.connect(self.load_category_to_form)

        self.load_all_categories()

    def init_copy_tab(self):
        main_layout = QVBoxLayout(self.tab_copy)
        main_layout.setSpacing(20)

        # 使用分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：副本管理表单
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.StyledPanel)
        form_layout = QVBoxLayout(form_frame)
        
        copy_group = QGroupBox("图书副本管理")
        copy_group_layout = QGridLayout(copy_group)
        copy_group_layout.setSpacing(12)

        # ISBN选择
        copy_group_layout.addWidget(QLabel("选择ISBN:"), 0, 0)
        self.copy_isbn_combo = QComboBox()
        self.copy_isbn_combo.setEditable(True)
        self.copy_isbn_combo.currentTextChanged.connect(self.on_isbn_selected)
        copy_group_layout.addWidget(self.copy_isbn_combo, 0, 1)

        # 显示选中ISBN的信息
        self.copy_book_info = QLabel("请选择一个ISBN查看图书信息")
        self.copy_book_info.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        copy_group_layout.addWidget(self.copy_book_info, 0, 2, 1, 2)

        # 图书书号
        copy_group_layout.addWidget(QLabel("图书书号:"), 1, 0)
        self.copy_book_number = QLineEdit()
        self.copy_book_number.setPlaceholderText("例如：BK001")
        copy_group_layout.addWidget(self.copy_book_number, 1, 1)

        # 状态选择
        copy_group_layout.addWidget(QLabel("图书状态:"), 1, 2)
        self.copy_status = QComboBox()
        self.copy_status.addItems(["normal", "damaged", "lost"])
        copy_group_layout.addWidget(self.copy_status, 1, 3)

        form_layout.addWidget(copy_group)

        # 操作按钮
        copy_button_layout = QHBoxLayout()
        self.btn_add_copy = QPushButton("➕ 添加副本")
        self.btn_refresh_copies = QPushButton("🔄 刷新列表")
        self.btn_update_copy_status = QPushButton("✏️ 更新状态")
        self.btn_search_by_isbn = QPushButton("🔍 按ISBN搜索")
        
        copy_button_layout.addWidget(self.btn_add_copy)
        copy_button_layout.addWidget(self.btn_refresh_copies)
        copy_button_layout.addWidget(self.btn_update_copy_status)
        copy_button_layout.addWidget(self.btn_search_by_isbn)
        copy_button_layout.addStretch()
        
        form_layout.addLayout(copy_button_layout)
        splitter.addWidget(form_frame)

        # 下半部分：副本表格
        table_frame = QFrame()
        table_frame.setFrameStyle(QFrame.StyledPanel)
        table_layout = QVBoxLayout(table_frame)
        
        copy_table_label = QLabel("📋 图书副本列表")
        copy_table_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        copy_table_label.setStyleSheet("color: #495057; margin-bottom: 10px;")
        table_layout.addWidget(copy_table_label)

        self.copy_table = QTableWidget()
        self.copy_table.setColumnCount(6)
        self.copy_table.setHorizontalHeaderLabels([
            "图书书号", "ISBN", "书名", "是否可借", "状态", "创建时间"
        ])
        self.copy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.copy_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.copy_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.copy_table.setAlternatingRowColors(True)
        self.copy_table.setSortingEnabled(True)
        
        table_layout.addWidget(self.copy_table)
        splitter.addWidget(table_frame)

        splitter.setSizes([200, 400])
        main_layout.addWidget(splitter)

        # 连接信号
        self.btn_add_copy.clicked.connect(self.add_copy)
        self.btn_refresh_copies.clicked.connect(self.refresh_copies)
        self.btn_update_copy_status.clicked.connect(self.update_copy_status)
        self.btn_search_by_isbn.clicked.connect(self.search_copies_by_isbn)
        self.copy_table.itemClicked.connect(self.load_copy_to_form)

        self.load_isbn_options()
        self.refresh_copies()

    # ==================== 图书类别管理方法 ====================
    def add_category(self):
        isbn = self.cat_isbn.text().strip()
        category = self.cat_category.text().strip()
        title = self.cat_title.text().strip()
        author = self.cat_author.text().strip()
        publisher = self.cat_publisher.text().strip() or None
        publish_date_str = self.cat_publish_date.date().toString("yyyy-MM-dd")
        price_str = self.cat_price.text().strip()
        total_copies_str = self.cat_total_copies.text().strip()
        description = self.cat_description.toPlainText().strip() or None

        if not all([isbn, category, title, author, total_copies_str]):
            QMessageBox.warning(self, "输入错误", "ISBN、类别、书名、作者和馆藏数量是必填项！")
            return
        
        try:
            price = float(price_str) if price_str else None
            total_copies = int(total_copies_str)
            if total_copies < 0 or (price is not None and price < 0):
                raise ValueError("数量和价格不能为负")
        except ValueError as ve:
            QMessageBox.warning(self, "输入错误", f"价格或馆藏数量格式不正确: {ve}")
            return

        try:
            lib.add_book_category(isbn, category, title, author, publisher, 
                                 publish_date_str, price, total_copies, description)
            QMessageBox.information(self, "操作成功", f"图书类别 '{title}' 添加成功！")
            self.clear_category_form()
            self.load_all_categories()
            self.load_isbn_options()  # 刷新副本管理的ISBN选项
            if self.parent_window: 
                self.parent_window.statusBar().showMessage(f"✓ 类别 '{title}' 已添加", 3000)
        except Exception as e:
            QMessageBox.critical(self, "操作失败", f"添加图书类别失败：\n{e}")

    def search_categories(self):
        isbn = self.cat_isbn.text().strip() or None
        category = self.cat_category.text().strip() or None
        title = self.cat_title.text().strip() or None
        author = self.cat_author.text().strip() or None
        
        try:
            results = lib.search_books(title=title, author=author, isbn=isbn, category=category)
            self.populate_category_table(results)
            if self.parent_window: 
                self.parent_window.statusBar().showMessage(f"🔍 搜索完成，找到 {len(results)} 条记录", 3000)
        except Exception as e:
            QMessageBox.critical(self, "查询失败", f"搜索图书类别失败：\n{e}")

    def load_all_categories(self):
        try:
            results = lib.search_books()
            self.populate_category_table(results)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载图书类别失败：\n{e}")

    def populate_category_table(self, categories):
        self.category_table.setRowCount(0)
        for row_num, cat_data in enumerate(categories):
            self.category_table.insertRow(row_num)
            items = [
                cat_data.get('isbn', ''),
                cat_data.get('category', ''),
                cat_data.get('title', ''),
                cat_data.get('author', ''),
                cat_data.get('publisher', ''),
                str(cat_data.get('publish_date', '')),
                str(cat_data.get('price', '')),
                str(cat_data.get('total_copies', '')),
                str(cat_data.get('available_copies', ''))
            ]
            
            for col, item_text in enumerate(items):
                item = QTableWidgetItem(item_text)
                self.category_table.setItem(row_num, col, item)
            
            self.category_table.item(row_num, 0).setData(Qt.UserRole, cat_data)

    def clear_category_form(self):
        self.cat_isbn.clear()
        self.cat_category.clear()
        self.cat_title.clear()
        self.cat_author.clear()
        self.cat_publisher.clear()
        self.cat_publish_date.setDate(QDate.currentDate())
        self.cat_price.clear()
        self.cat_total_copies.clear()
        self.cat_description.clear()
        self.cat_isbn.setFocus()

    def load_category_to_form(self):
        selected_rows = self.category_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先在表格中选择要编辑的图书类别。")
            return
        
        selected_row_index = selected_rows[0].row()
        cat_data = self.category_table.item(selected_row_index, 0).data(Qt.UserRole)
        if not cat_data: 
            return

        self.cat_isbn.setText(cat_data.get('isbn', ''))
        self.cat_category.setText(cat_data.get('category', ''))
        self.cat_title.setText(cat_data.get('title', ''))
        self.cat_author.setText(cat_data.get('author', ''))
        self.cat_publisher.setText(cat_data.get('publisher', ''))
        
        publish_date_obj = cat_data.get('publish_date')
        if isinstance(publish_date_obj, str):
            self.cat_publish_date.setDate(QDate.fromString(publish_date_obj, "yyyy-MM-dd"))
        elif hasattr(publish_date_obj, 'year'):
            self.cat_publish_date.setDate(QDate(publish_date_obj.year, publish_date_obj.month, publish_date_obj.day))
        else:
            self.cat_publish_date.setDate(QDate.currentDate())
            
        self.cat_price.setText(str(cat_data.get('price', '')))
        self.cat_total_copies.setText(str(cat_data.get('total_copies', '')))
        self.cat_description.setPlainText(cat_data.get('description', ''))

    # ==================== 图书副本管理方法 ====================
    def load_isbn_options(self):
        """加载所有可用的ISBN到下拉框"""
        try:
            categories = lib.search_books()
            self.copy_isbn_combo.clear()
            self.copy_isbn_combo.addItem("", "")  # 空选项
            
            for cat in categories:
                isbn = cat.get('isbn', '')
                title = cat.get('title', '')
                display_text = f"{isbn} - {title}"
                self.copy_isbn_combo.addItem(display_text, isbn)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载ISBN选项失败：\n{e}")

    def on_isbn_selected(self):
        """当选择ISBN时显示图书信息"""
        current_data = self.copy_isbn_combo.currentData()
        if current_data:
            try:
                results = lib.search_books(isbn=current_data)
                if results:
                    book_info = results[0]
                    info_text = f"📖 {book_info.get('title', '')} | 👤 {book_info.get('author', '')} | 📚 库存: {book_info.get('available_copies', 0)}/{book_info.get('total_copies', 0)}"
                    self.copy_book_info.setText(info_text)
                    self.copy_book_info.setStyleSheet("color: #1976d2; font-weight: 500; padding: 10px;")
                else:
                    self.copy_book_info.setText("未找到该ISBN的图书信息")
                    self.copy_book_info.setStyleSheet("color: #f44336; padding: 10px;")
            except Exception as e:
                self.copy_book_info.setText(f"获取图书信息失败: {e}")
                self.copy_book_info.setStyleSheet("color: #f44336; padding: 10px;")
        else:
            self.copy_book_info.setText("请选择一个ISBN查看图书信息")
            self.copy_book_info.setStyleSheet("color: #666; font-style: italic; padding: 10px;")

    def add_copy(self):
        """添加图书副本"""
        isbn = self.copy_isbn_combo.currentData()
        book_number = self.copy_book_number.text().strip()
        
        if not isbn:
            QMessageBox.warning(self, "输入错误", "请选择一个ISBN！")
            return
            
        if not book_number:
            QMessageBox.warning(self, "输入错误", "请输入图书书号！")
            return

        try:
            lib.add_book_copy(isbn, book_number)
            QMessageBox.information(self, "操作成功", f"图书副本 '{book_number}' 添加成功！")
            self.copy_book_number.clear()
            self.refresh_copies()
            self.load_all_categories()  # 刷新类别表格的可借数量
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"✓ 副本 '{book_number}' 已添加", 3000)
        except Exception as e:
            QMessageBox.critical(self, "操作失败", f"添加图书副本失败：\n{e}")

    def refresh_copies(self):
        """刷新副本列表"""
        try:
            # 获取所有图书副本（这里需要修改 enhanced_library.py 来提供这个功能）
            # 暂时通过数据库直接查询
            from enhanced_database import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT b.book_number, b.isbn, bc.title, b.is_available, b.status, b.created_at
                        FROM books b
                        LEFT JOIN book_categories bc ON b.isbn = bc.isbn
                        ORDER BY b.book_number
                    """)
                    results = cur.fetchall()
                    
            self.populate_copy_table(results)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"刷新副本列表失败：\n{e}")

    def populate_copy_table(self, copies):
        """填充副本表格"""
        self.copy_table.setRowCount(0)
        for row_num, copy_data in enumerate(copies):
            self.copy_table.insertRow(row_num)
            
            # 状态转换
            is_available = copy_data.get('is_available', '')
            if is_available == 'available':
                is_available_text = '✅ 可借'
            else:
                is_available_text = '❌ 不可借'
                
            status = copy_data.get('status', '')
            if status == 'normal':
                status_text = '🟢 正常'
            elif status == 'damaged':
                status_text = '🟡 损坏'
            elif status == 'lost':
                status_text = '🔴 遗失'
            else:
                status_text = status
            
            items = [
                copy_data.get('book_number', ''),
                copy_data.get('isbn', ''),
                copy_data.get('title', ''),
                is_available_text,
                status_text,
                str(copy_data.get('created_at', ''))
            ]
            
            for col, item_text in enumerate(items):
                item = QTableWidgetItem(item_text)
                self.copy_table.setItem(row_num, col, item)
            
            self.copy_table.item(row_num, 0).setData(Qt.UserRole, copy_data)

    def load_copy_to_form(self):
        """将选中的副本信息加载到表单"""
        selected_rows = self.copy_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        selected_row_index = selected_rows[0].row()
        copy_data = self.copy_table.item(selected_row_index, 0).data(Qt.UserRole)
        if not copy_data:
            return

        # 设置ISBN
        isbn = copy_data.get('isbn', '')
        for i in range(self.copy_isbn_combo.count()):
            if self.copy_isbn_combo.itemData(i) == isbn:
                self.copy_isbn_combo.setCurrentIndex(i)
                break
                
        self.copy_book_number.setText(copy_data.get('book_number', ''))
        
        # 设置状态
        status = copy_data.get('status', 'normal')
        status_index = self.copy_status.findText(status)
        if status_index >= 0:
            self.copy_status.setCurrentIndex(status_index)

    def update_copy_status(self):
        """更新选中副本的状态"""
        selected_rows = self.copy_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要更新的图书副本。")
            return
        
        selected_row_index = selected_rows[0].row()
        copy_data = self.copy_table.item(selected_row_index, 0).data(Qt.UserRole)
        if not copy_data:
            return
            
        book_number = copy_data.get('book_number', '')
        new_status = self.copy_status.currentText()
        
        try:
            lib.update_book_status(book_number, new_status)
            QMessageBox.information(self, "操作成功", f"图书 '{book_number}' 状态已更新为 '{new_status}'")
            self.refresh_copies()
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"✓ '{book_number}' 状态已更新", 3000)
        except Exception as e:
            QMessageBox.critical(self, "操作失败", f"更新图书状态失败：\n{e}")

    def search_copies_by_isbn(self):
        """按ISBN搜索副本"""
        isbn = self.copy_isbn_combo.currentData()
        if not isbn:
            QMessageBox.warning(self, "搜索条件", "请先选择一个ISBN！")
            return
            
        try:
            from enhanced_database import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT b.book_number, b.isbn, bc.title, b.is_available, b.status, b.created_at
                        FROM books b
                        LEFT JOIN book_categories bc ON b.isbn = bc.isbn
                        WHERE b.isbn = %s
                        ORDER BY b.book_number
                    """, (isbn,))
                    results = cur.fetchall()
                    
            self.populate_copy_table(results)
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"🔍 找到 {len(results)} 个副本", 3000)
        except Exception as e:
            QMessageBox.critical(self, "搜索失败", f"按ISBN搜索副本失败：\n{e}")

    def borrow_book(self, book_info):
        """处理借书操作"""
        # 这里应该实现借书逻辑
        QMessageBox.information(self, "借书操作", f"您已成功借阅图书 '{book_info.get('title', '')}'")

    def return_book(self, book_info):
        """处理归还操作"""
        # 这里应该实现归还逻辑
        QMessageBox.information(self, "归还操作", f"您已成功归还图书 '{book_info.get('title', '')}'")

# ========================== 程序入口 ==========================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 首先显示登录对话框
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        user_info = login_dialog.get_user_info()
        if user_info:
            main_win = MainWindow(user_info) # 传递用户信息
            main_win.show()
            sys.exit(app.exec_())
        else:
            sys.exit() # 如果没有用户信息则退出
    else:
        sys.exit() # 用户取消登录则退出