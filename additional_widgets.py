# -*- coding: utf-8 -*-
"""
附加管理模块：读者管理、借阅管理、查询统计
增强版 v2.0 - 提供完整的功能和现代化UI
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QFormLayout, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QGridLayout, QDateEdit, 
    QTextEdit, QHeaderView, QAbstractItemView, QHBoxLayout, QComboBox, 
    QFrame, QGroupBox, QSplitter, QSpinBox, QCheckBox, QProgressBar, 
    QScrollArea, QCalendarWidget, QMessageBox, QProgressDialog, QFileDialog,
    QApplication, QSpacerItem, QDialog
)
from PyQt5.QtGui import QFont, QRegExpValidator, QIntValidator, QDoubleValidator, QColor
from PyQt5.QtCore import Qt, QDate, QTimer, QRegExp, QThread, pyqtSignal
from typing import Optional, Dict, Any

import enhanced_library as lib
import enhanced_database as db
import re
import datetime

# ====================== 数据刷新线程 ======================
class DataRefreshThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    data_loaded = pyqtSignal(str, list)
    refresh_completed = pyqtSignal(bool, str)

    def __init__(self, module_name):
        super().__init__()
        self.module_name = module_name

    def run(self):
        try:
            self.status_updated.emit(f"正在刷新{self.module_name}数据...")
            self.progress_updated.emit(25)
            
            data_to_load = []
            if self.module_name == "读者管理":
                self.status_updated.emit("正在加载读者信息...")
                self.progress_updated.emit(50)
                data_to_load = lib.search_readers()
                self.data_loaded.emit("readers", data_to_load)
                self.status_updated.emit("正在加载读者统计...")
                self.progress_updated.emit(75)
            elif self.module_name == "图书管理":
                self.status_updated.emit("正在加载图书类别...")
                self.progress_updated.emit(40)
                data_to_load = lib.search_books()
                self.data_loaded.emit("book_categories", data_to_load)
                self.status_updated.emit("正在加载图书副本...")
                self.progress_updated.emit(80)
            elif self.module_name == "借阅管理":
                self.status_updated.emit("正在加载借阅记录...")
                self.progress_updated.emit(50)
            elif self.module_name == "查询统计":
                self.status_updated.emit("正在生成统计数据...")
                self.progress_updated.emit(50)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("数据刷新完成！")
            self.refresh_completed.emit(True, f"{self.module_name}数据刷新成功")
            
        except Exception as e:
            self.refresh_completed.emit(False, f"{self.module_name}数据刷新失败：{str(e)}")

# ====================== 读者管理模块 ======================
class ReaderManagementWidget(QWidget):
    def __init__(self, parent=None, user_info: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.parent_window = parent
        self.user_info = user_info
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # Store original UI elements before applying role adjustments
        self._original_widgets = {}
        self._access_denied_label_ref = None # Initialize reference for deny label
        self._build_ui() # Build the full UI first
        self.adjust_ui_for_role()

    def _build_ui(self):
        # Title Frame
        title_frame = QFrame()
        title_frame.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e3f2fd, stop:1 #bbdefb); border-radius:10px; padding:15px; }")
        title_layout = QHBoxLayout(title_frame)
        title_label = QLabel("👥 读者管理系统")
        title_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        title_label.setStyleSheet("color: #1976d2; background: transparent;")
        title_layout.addWidget(title_label)
        self.stats_label = QLabel("总读者: 0 | 活跃读者: 0")
        self.stats_label.setFont(QFont("Microsoft YaHei UI", 12))
        self.stats_label.setStyleSheet("color: #666; background: transparent;")
        title_layout.addWidget(self.stats_label)
        title_layout.addStretch()
        self._original_widgets['title_frame'] = title_frame

        # Tabs
        tabs = QTabWidget()
        self.tab_reader_info = QWidget()
        self.tab_reader_stats = QWidget()
        self.tab_reader_advanced = QWidget()
        tabs.addTab(self.tab_reader_info, "👤 读者信息管理")
        tabs.addTab(self.tab_reader_stats, "📈 读者统计分析")
        tabs.addTab(self.tab_reader_advanced, "🔧 高级功能")
        self._original_widgets['tabs'] = tabs

        # Populate tabs
        self.init_reader_info_tab()
        self.init_reader_stats_tab()
        self.init_reader_advanced_tab()
        
        self.load_all_readers() # Initial data load
        self.load_reader_statistics() # Initial stats load

    def adjust_ui_for_role(self):
        is_admin = self.user_info and self.user_info.get('role') == 'admin'

        # Remove all widgets from layout first to handle reconstruction cleanly
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().hide() # Hide, don't delete if it's an original widget
            elif item.layout(): pass # Sub-layouts handled by parent hide
        
        if is_admin:
            if self._access_denied_label_ref: self._access_denied_label_ref.hide()
            self.layout.addWidget(self._original_widgets['title_frame'])
            self._original_widgets['title_frame'].show()
            self.layout.addWidget(self._original_widgets['tabs'])
            self._original_widgets['tabs'].show()
        else:
            if self._original_widgets.get('title_frame'): self._original_widgets['title_frame'].hide()
            if self._original_widgets.get('tabs'): self._original_widgets['tabs'].hide()
            if not self._access_denied_label_ref:
                self._access_denied_label_ref = QLabel()
                self._access_denied_label_ref.setAlignment(Qt.AlignCenter)
                self._access_denied_label_ref.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
                self._access_denied_label_ref.setStyleSheet("color: #dc3545; margin-top: 20px;")
                self.layout.addWidget(self._access_denied_label_ref)
                self.layout.addStretch() # Add stretcher after deny label
            
            role_text = "您没有权限访问此模块。" if (self.user_info and self.user_info.get('role') == 'reader') else "角色未知，无法访问此模块。"
            self._access_denied_label_ref.setText(role_text)
            self._access_denied_label_ref.show()

    def init_reader_info_tab(self):
        main_layout = QVBoxLayout(self.tab_reader_info)
        main_layout.setSpacing(20)
        splitter = QSplitter(Qt.Vertical)
        
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.StyledPanel)
        form_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e0e0e0;
                border-radius: 12px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        
        reader_group = QGroupBox("📝 读者信息录入")
        reader_group_layout = QGridLayout(reader_group)
        reader_group_layout.setSpacing(15)

        # Fields
        reader_group_layout.addWidget(QLabel("借书证号:"), 0, 0); self.reader_card_number = QLineEdit(); self.reader_card_number.setPlaceholderText("例如：R2024001"); self.reader_card_number.setValidator(QRegExpValidator(QRegExp(r"R\d{7}"))); reader_group_layout.addWidget(self.reader_card_number, 0, 1)
        reader_group_layout.addWidget(QLabel("读者姓名:"), 0, 2); self.reader_name = QLineEdit(); self.reader_name.setPlaceholderText("请输入真实姓名"); 
        # 移除对中文输入的限制，或使用更宽松的正则表达式
        # self.reader_name.setValidator(QRegExpValidator(QRegExp(r"[\u4e00-\u9fa5a-zA-Z\s]{1,20}"))); 
        reader_group_layout.addWidget(self.reader_name, 0, 3)
        reader_group_layout.addWidget(QLabel("性别:"), 1, 0); self.reader_gender = QComboBox(); self.reader_gender.addItems(["👨 男", "👩 女", "🧑 其他"]); reader_group_layout.addWidget(self.reader_gender, 1, 1)
        reader_group_layout.addWidget(QLabel("身份证号:"), 1, 2); self.reader_id_number = QLineEdit(); self.reader_id_number.setPlaceholderText("18位身份证号码"); self.reader_id_number.setValidator(QRegExpValidator(QRegExp(r"\d{17}[\dxX]"))); reader_group_layout.addWidget(self.reader_id_number, 1, 3)
        reader_group_layout.addWidget(QLabel("联系电话:"), 2, 0); self.reader_phone = QLineEdit(); self.reader_phone.setPlaceholderText("11位手机号码"); self.reader_phone.setValidator(QRegExpValidator(QRegExp(r"1[3-9]\d{9}"))); reader_group_layout.addWidget(self.reader_phone, 2, 1)
        reader_group_layout.addWidget(QLabel("电子邮箱:"), 2, 2); self.reader_email = QLineEdit(); self.reader_email.setPlaceholderText("email@example.com"); reader_group_layout.addWidget(self.reader_email, 2, 3)
        reader_group_layout.addWidget(QLabel("读者类型:"), 3, 0); self.reader_type = QComboBox(); self.reader_type.addItems(["🎓 学生", "👨‍🏫 教师", "👨‍💼 职工", "👤 访客"]); reader_group_layout.addWidget(self.reader_type, 3, 1)
        reader_group_layout.addWidget(QLabel("最大借阅数:"), 3, 2); self.reader_max_borrow = QSpinBox(); self.reader_max_borrow.setRange(1,20); self.reader_max_borrow.setValue(5); self.reader_max_borrow.setSuffix(" 本"); reader_group_layout.addWidget(self.reader_max_borrow, 3, 3)
        reader_group_layout.addWidget(QLabel("联系地址:"), 4, 0); self.reader_address = QTextEdit(); self.reader_address.setFixedHeight(80); self.reader_address.setPlaceholderText("详细联系地址..."); reader_group_layout.addWidget(self.reader_address, 4, 1, 1, 3)
        form_layout.addWidget(reader_group)

        # Buttons for Category Tab
        cat_button_layout = QHBoxLayout()
        self.btn_add_reader = QPushButton("➕ 添加读者"); self.btn_search_reader = QPushButton("🔍 搜索读者")
        self.btn_clear_reader_form = QPushButton("🗑️ 清空表单"); self.btn_load_cat_to_form = QPushButton("📝 编辑选中")
        cat_button_layout.addWidget(self.btn_add_reader); cat_button_layout.addWidget(self.btn_search_reader); cat_button_layout.addWidget(self.btn_clear_reader_form); cat_button_layout.addWidget(self.btn_load_cat_to_form); cat_button_layout.addStretch()
        form_layout.addLayout(cat_button_layout)
        splitter.addWidget(form_frame)

        # Table Frame for Categories
        table_frame_cat = QFrame(); table_frame_cat.setFrameStyle(QFrame.StyledPanel); table_layout_cat = QVBoxLayout(table_frame_cat)
        table_layout_cat.addWidget(QLabel("📊 读者信息列表"))
        self.reader_table = QTableWidget(); self.reader_table.setColumnCount(10); self.reader_table.setHorizontalHeaderLabels(["借书证号", "姓名", "性别", "身份证号", "电话", "邮箱", "类型", "最大借阅", "当前借阅", "注册时间"])
        self.reader_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.reader_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.reader_table.setEditTriggers(QAbstractItemView.NoEditTriggers); self.reader_table.setAlternatingRowColors(True); self.reader_table.setSortingEnabled(True)
        table_layout_cat.addWidget(self.reader_table)
        splitter.addWidget(table_frame_cat)
        splitter.setSizes([300, 450])
        main_layout.addWidget(splitter)

        # Connections for Category Tab
        self.btn_add_reader.clicked.connect(self.add_reader); self.btn_search_reader.clicked.connect(self.search_readers)
        self.btn_clear_reader_form.clicked.connect(self.clear_reader_form)
        self.btn_load_cat_to_form.clicked.connect(self.load_reader_to_form)
        self.reader_table.itemDoubleClicked.connect(self.load_reader_to_form) # For admin to edit

    def init_reader_stats_tab(self):
        layout = QVBoxLayout(self.tab_reader_stats)
        layout.setSpacing(20)
        stats_frame = QFrame(); stats_frame.setFrameStyle(QFrame.StyledPanel); stats_frame.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f8f9fa); border: 2px solid #e0e0e0; border-radius:15px; padding:20px; }")
        stats_layout = QGridLayout(stats_frame); stats_layout.setSpacing(20)
        self.create_stat_card(stats_layout, "📊 总读者数", "0", "#2196f3", 0, 0)
        self.create_stat_card(stats_layout, "🎓 学生读者", "0", "#4caf50", 0, 1)
        self.create_stat_card(stats_layout, "👨‍🏫 教师读者", "0", "#ff9800", 0, 2)
        self.create_stat_card(stats_layout, "📚 活跃读者", "0", "#9c27b0", 1, 0)
        self.create_stat_card(stats_layout, "⏰ 本月新增", "0", "#f44336", 1, 1)
        self.create_stat_card(stats_layout, "📈 借阅率", "0%", "#00bcd4", 1, 2)
        layout.addWidget(stats_frame)
        
        # Detailed stats table
        detail_frame = QGroupBox("📈 详细统计分析")
        detail_layout = QVBoxLayout(detail_frame)
        self.stats_table = QTableWidget(); self.stats_table.setColumnCount(5); self.stats_table.setHorizontalHeaderLabels(["统计类型", "数量", "占比", "变化趋势", "备注"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        detail_layout.addWidget(self.stats_table)
        layout.addWidget(detail_frame)

    def create_stat_card(self, layout, title, value, color, row, col):
        card = QFrame(); card.setFixedSize(180, 100); card.setStyleSheet(f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {color}, stop:1 {self.darken_color(color)}); border-radius:12px; border:2px solid {color}; }}")
        card_layout = QVBoxLayout(card); card_layout.setAlignment(Qt.AlignCenter)
        title_label = QLabel(title); title_label.setStyleSheet("color:white; font-weight:bold; font-size:12px;"); title_label.setAlignment(Qt.AlignCenter)
        value_label = QLabel(value); value_label.setStyleSheet("color:white; font-weight:bold; font-size:24px;"); value_label.setAlignment(Qt.AlignCenter); value_label.setObjectName(f"stat_value_{row}_{col}")
        card_layout.addWidget(title_label); card_layout.addWidget(value_label)
        layout.addWidget(card, row, col)

    def darken_color(self, color_hex):
        try:
            color_hex = color_hex.lstrip('#')
            r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, r - 30); g = max(0, g - 30); b = max(0, b - 30)
            return f"#{r:02x}{g:02x}{b:02x}"
        except: return color_hex # Fallback

    def init_reader_advanced_tab(self):
        layout = QVBoxLayout(self.tab_reader_advanced)
        batch_group = QGroupBox("🔧 批量操作")
        batch_layout = QGridLayout(batch_group)
        batch_layout.addWidget(QLabel("批量导入:"), 0, 0); self.btn_batch_import = QPushButton("📥 从Excel导入读者"); batch_layout.addWidget(self.btn_batch_import, 0, 1)
        batch_layout.addWidget(QLabel("批量导出:"), 1, 0); self.btn_batch_export = QPushButton("📤 导出所有读者"); batch_layout.addWidget(self.btn_batch_export, 1, 1)
        batch_layout.addWidget(QLabel("数据清理:"), 2, 0); self.btn_data_cleanup = QPushButton("🧹 清理无效数据"); batch_layout.addWidget(self.btn_data_cleanup, 2, 1)
        layout.addWidget(batch_group)
        self.btn_batch_import.clicked.connect(self.batch_import_readers); self.btn_batch_export.clicked.connect(self.batch_export_readers); self.btn_data_cleanup.clicked.connect(self.cleanup_reader_data)
        layout.addStretch()

    def validate_reader_input(self):
        errors = []
        if not self.reader_card_number.text().strip(): errors.append("借书证号不能为空")
        elif not re.match(r"R\d{7}", self.reader_card_number.text().strip()): errors.append("借书证号格式不正确（应为R+7位数字）")
        if not self.reader_name.text().strip(): errors.append("读者姓名不能为空")
        if not self.reader_id_number.text().strip(): errors.append("身份证号不能为空")
        elif not re.match(r"\d{17}[\dxX]", self.reader_id_number.text().strip()): errors.append("身份证号格式不正确")
        if not self.reader_phone.text().strip(): errors.append("联系电话不能为空")
        elif not re.match(r"1[3-9]\d{9}", self.reader_phone.text().strip()): errors.append("手机号格式不正确")
        email = self.reader_email.text().strip()
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email): errors.append("邮箱格式不正确")
        return errors

    def add_reader(self):
        errors = self.validate_reader_input()
        if errors: QMessageBox.warning(self, "输入验证失败", "\n".join(errors)); return
        
        library_card_no = self.reader_card_number.text().strip()
        name = self.reader_name.text().strip()
        gender = "男" if self.reader_gender.currentIndex() == 0 else "女"
        id_number = self.reader_id_number.text().strip() or None
        phone = self.reader_phone.text().strip() or None
        email = self.reader_email.text().strip() or None
        
        # 将reader_type转换为title字段
        reader_type_index = self.reader_type.currentIndex()
        title_map = {0: "学生", 1: "教师", 2: "职工", 3: "访客"}
        title = title_map.get(reader_type_index, "")
        
        max_borrow = self.reader_max_borrow.value()
        address = self.reader_address.toPlainText().strip() or None
        
        try:
            success, message = lib.add_reader(
                library_card_no=library_card_no, name=name, gender=gender,
                id_card=id_number, phone=phone, title=title,
                max_borrow_count=max_borrow, address=address
            )
            if success:
                QMessageBox.information(self, "添加成功", message)
                self.clear_reader_form()
                self.load_all_readers()
                if self.parent_window: self.parent_window.show_status_message(f"✓ 读者 '{name}' 已添加", 3000, "success")
            else: QMessageBox.warning(self, "添加失败", message)
        except Exception as e: QMessageBox.critical(self, "操作失败", f"添加读者失败：\n{e}")

    def search_readers(self):
        name = self.reader_name.text().strip() or None
        card_no = self.reader_card_number.text().strip() or None
        
        try:
            results = lib.search_readers(card_no=card_no, name=name)
            self.populate_reader_table(results)
            if self.parent_window: self.parent_window.show_status_message(f"🔍 找到 {len(results)} 位读者", 3000, "success")
        except Exception as e: QMessageBox.critical(self, "搜索失败", f"搜索读者失败：\n{e}")
    
    def update_reader(self):
        selected_rows = self.reader_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "提示", "请先选择要更新的读者。"); return
        errors = self.validate_reader_input()
        if errors: QMessageBox.warning(self, "输入验证失败", "\n".join(errors)); return
        
        selected_row_index = selected_rows[0].row()
        reader_data = self.reader_table.item(selected_row_index, 0).data(Qt.UserRole)
        if not reader_data: return
        old_card_number = reader_data.get('library_card_no')
        
        # 获取表单中的数据
        library_card_no = self.reader_card_number.text().strip()
        name = self.reader_name.text().strip()
        gender = "男" if self.reader_gender.currentIndex() == 0 else "女"
        id_number = self.reader_id_number.text().strip() or None
        phone = self.reader_phone.text().strip() or None
        email = self.reader_email.text().strip() or None
        
        # 将reader_type转换为title字段
        reader_type_index = self.reader_type.currentIndex()
        title_map = {0: "学生", 1: "教师", 2: "职工", 3: "访客"}
        title = title_map.get(reader_type_index, "")
        
        max_borrow = self.reader_max_borrow.value()
        address = self.reader_address.toPlainText().strip() or None

        try:
            success, message = lib.update_reader_info(
                old_card_number,
                library_card_no=library_card_no,
                name=name,
                gender=gender,
                id_card=id_number,
                phone=phone,
                email=email,
                title=title,
                max_borrow_count=max_borrow,
                address=address
            )
            
            if success:
                QMessageBox.information(self, "更新成功", message)
                self.clear_reader_form()
                self.load_all_readers()
                if self.parent_window: self.parent_window.show_status_message(f"✓ 读者 '{name}' 信息已更新", 3000, "success")
            else:
                QMessageBox.warning(self, "更新失败", message)
        except Exception as e:
            QMessageBox.critical(self, "操作失败", f"更新读者信息失败：\\n{e}")

    def delete_reader(self):
        selected_rows = self.reader_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "提示", "请先选择要删除的读者。"); return
        selected_row_index = selected_rows[0].row()
        reader_data = self.reader_table.item(selected_row_index, 0).data(Qt.UserRole)
        if not reader_data: return
        library_card_no = reader_data.get('library_card_no'); name = reader_data.get('name')
        try:
            conn = db.get_connection(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM borrowings WHERE library_card_no = %s AND status = 'borrowed'", (library_card_no,))
            borrowed_count = cur.fetchone()['count']; cur.close(); conn.close()
            if borrowed_count > 0: QMessageBox.warning(self, "无法删除", f"读者 '{name}' 还有 {borrowed_count} 本图书未归还！"); return
        except Exception as e: QMessageBox.critical(self, "检查失败", f"检查读者借阅状态失败：\n{e}")
        
        if QMessageBox.question(self, "确认删除", f"确定要删除读者 '{name}' 吗？此操作不可恢复！", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            try:
                success, message = lib.delete_reader_by_card_no(library_card_no)
                if success:
                    QMessageBox.information(self, "操作成功", message)
                    self.clear_reader_form(); self.load_all_readers(); self.update_quick_stats()
                    if self.parent_window: self.parent_window.show_status_message(f"✓ 读者 '{name}' 已删除", 3000, "success")
                else: QMessageBox.warning(self, "删除失败", message)
            except Exception as e: QMessageBox.critical(self, "操作失败", f"删除读者失败：\n{e}")

    def clear_reader_form(self):
        self.reader_card_number.clear(); self.reader_name.clear(); self.reader_gender.setCurrentIndex(0)
        self.reader_id_number.clear(); self.reader_phone.clear(); self.reader_email.clear()
        self.reader_type.setCurrentIndex(0); self.reader_max_borrow.setValue(5); self.reader_address.clear()
        self.reader_card_number.setFocus()

    def load_all_readers(self):
        try: self.populate_reader_table(lib.search_readers())
        except Exception as e: QMessageBox.critical(self, "加载失败", f"加载读者信息失败：\n{e}")

    def populate_reader_table(self, readers):
        self.reader_table.setRowCount(0)
        for row_num, reader_data in enumerate(readers):
            self.reader_table.insertRow(row_num)
            current_borrow = reader_data.get('current_borrow_count', 0)
            # 修改性别映射，支持中文性别值和英文性别值
            gender_display_map = {
                "male": "👨 男", "female": "👩 女", "other": "🧑 其他",
                "男": "👨 男", "女": "👩 女"  # 添加中文性别映射
            }
            # 使用title字段而不是reader_type字段
            title_display = reader_data.get('title', '')
            if title_display:
                title_display = f"🎓 {title_display}"  # 添加图标
            items = [
                reader_data.get('library_card_no', ''), reader_data.get('name', ''),
                gender_display_map.get(reader_data.get('gender', ''), ''), reader_data.get('id_number', ''),
                reader_data.get('phone', ''), reader_data.get('email', ''),
                title_display,  # 使用title字段
                str(reader_data.get('max_borrow_count', '')), str(current_borrow),
                str(reader_data.get('registration_date', ''))
            ]
            for col, text in enumerate(items): self.reader_table.setItem(row_num, col, QTableWidgetItem(text))
            self.reader_table.item(row_num, 0).setData(Qt.UserRole, reader_data)
        self.update_quick_stats()

    def load_reader_to_form(self):
        selected_rows = self.reader_table.selectionModel().selectedRows()
        if not selected_rows: return
        selected_row_index = selected_rows[0].row()
        reader_data = self.reader_table.item(selected_row_index, 0).data(Qt.UserRole)
        if not reader_data: return
        self.reader_card_number.setText(reader_data.get('library_card_no', ''))
        self.reader_name.setText(reader_data.get('name', ''))
        gender_map_rev = {"male": 0, "female": 1, "other": 2, "男": 0, "女": 1}; self.reader_gender.setCurrentIndex(gender_map_rev.get(reader_data.get('gender', ''), 0))
        self.reader_id_number.setText(reader_data.get('id_number', ''))
        self.reader_phone.setText(reader_data.get('phone', ''))
        self.reader_email.setText(reader_data.get('email', ''))
        # 设置职称/头衔
        title = reader_data.get('title', '')
        # 根据title设置reader_type下拉框
        if "学生" in title:
            self.reader_type.setCurrentIndex(0)  # 学生
        elif "教师" in title or "老师" in title or "讲师" in title or "教授" in title:
            self.reader_type.setCurrentIndex(1)  # 教师
        elif "职工" in title or "员工" in title or "工作人员" in title:
            self.reader_type.setCurrentIndex(2)  # 职工
        else:
            self.reader_type.setCurrentIndex(3)  # 访客
        self.reader_max_borrow.setValue(reader_data.get('max_borrow_count', 5))
        self.reader_address.setPlainText(reader_data.get('address', ''))

    def load_reader_statistics(self):
        try:
            stats = lib.get_reader_statistics_summary()
            if hasattr(self, 'stat_labels'):
                self.stat_labels.get('0_0', QLabel()).setText(str(stats.get('total_readers', 0)))
                self.stat_labels.get('0_1', QLabel()).setText(str(stats.get('student_readers', 0)))
                self.stat_labels.get('0_2', QLabel()).setText(str(stats.get('teacher_readers', 0)))
                self.stat_labels.get('1_0', QLabel()).setText(str(stats.get('active_readers', 0)))
                self.stat_labels.get('1_1', QLabel()).setText(str(stats.get('new_this_month', 0)))
                borrow_rate = (stats.get('active_readers',0) / stats.get('total_readers',1) * 100) if stats.get('total_readers',0) > 0 else 0
                self.stat_labels.get('1_2', QLabel()).setText(f"{borrow_rate:.1f}%")
            if hasattr(self, 'stats_label'):
                self.stats_label.setText(f"总读者: {stats.get('total_readers', 0)} | 活跃读者: {stats.get('active_readers', 0)}")
        except Exception as e: print(f"加载读者统计失败: {e}")

    def update_quick_stats(self): self.load_reader_statistics()
    def batch_import_readers(self): QMessageBox.information(self, "功能提示", "批量导入功能待实现。")
    def batch_export_readers(self): QMessageBox.information(self, "功能提示", "批量导出功能待实现。")
    def cleanup_reader_data(self): QMessageBox.information(self, "功能提示", "数据清理功能待实现。")
    def quick_search_readers(self):
        search_text = self.reader_card_number.text().strip() or self.reader_name.text().strip() or self.reader_phone.text().strip()
        if not search_text: self.load_all_readers(); return
        try:
            results = [r for r in lib.search_readers() if 
                       search_text in r.get('name', '').lower() or 
                       search_text in r.get('library_card_no', '') or
                       search_text in r.get('phone', '')]
            self.populate_reader_table(results)
            if self.parent_window: self.parent_window.show_status_message(f"🔍 搜索找到 {len(results)} 位读者", 2000, "info")
        except Exception as e: QMessageBox.critical(self, "搜索失败", f"搜索失败：\n{e}")
    def export_readers(self): self.batch_export_readers()
    def refresh_data(self):
        if self.user_info and self.user_info.get('role') == 'admin':
            self.load_all_readers()
            self.load_reader_statistics()
            if self.parent_window: self.parent_window.show_status_message("✅ 读者数据已刷新", 3000, "success")
        else: # Readers do not manage readers, so no refresh action for them here.
            pass

# ====================== 图书管理模块 ======================
class BookManagementWidget(QWidget):
    def __init__(self, parent=None, user_info: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.parent_window = parent
        self.user_info = user_info
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        self._build_ui()
        self.adjust_ui_for_role()

    def _build_ui(self):
        title_label = QLabel("📚 图书信息中心")
        title_label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold)); title_label.setStyleSheet("color: #1976d2; margin-bottom:10px;")
        self.layout.addWidget(title_label)

        self.tabs = QTabWidget()
        self.tab_category = QWidget()
        self.tab_copy = QWidget()
        self.tabs.addTab(self.tab_category, "📖 图书类别管理")
        self.tabs.addTab(self.tab_copy, "📋 图书副本管理")
        self.layout.addWidget(self.tabs)

        self.init_category_tab()
        self.init_copy_tab()
        
        self.refresh_data() # Load initial data

    def adjust_ui_for_role(self):
        is_reader = self.user_info and self.user_info.get('role') == 'reader'

        # Category Tab Adjustments
        if hasattr(self, 'form_frame_cat'): self.form_frame_cat.setVisible(not is_reader)
        if hasattr(self, 'btn_add_category'): self.btn_add_category.setVisible(not is_reader)
        if hasattr(self, 'btn_load_cat_to_form'): self.btn_load_cat_to_form.setVisible(not is_reader)
        if hasattr(self, 'btn_search_category'): self.btn_search_category.setText("🔍 搜索图书" if is_reader else "🔍 搜索类别")
        if hasattr(self, 'btn_clear_cat_form'): self.btn_clear_cat_form.setVisible(not is_reader)
        if hasattr(self, 'category_table'): self.category_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Copy Tab Adjustments
        if hasattr(self, 'copy_form_frame'): self.copy_form_frame.setVisible(not is_reader)
        if hasattr(self, 'btn_add_copy'): self.btn_add_copy.setVisible(not is_reader)
        if hasattr(self, 'btn_update_copy_status'): self.btn_update_copy_status.setVisible(not is_reader)
        if hasattr(self, 'copy_table'): self.copy_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Tab Titles
        self.tabs.setTabText(self.tabs.indexOf(self.tab_category), "🔍 搜索与浏览图书" if is_reader else "📖 图书类别管理")
        self.tabs.setTabText(self.tabs.indexOf(self.tab_copy), "📚 查看副本状态" if is_reader else "📋 图书副本管理")
        
        # For readers, ensure form fields are cleared if they were somehow populated
        if is_reader:
            if hasattr(self, 'clear_category_form'): self.clear_category_form()
            if hasattr(self, 'copy_book_number'): self.copy_book_number.clear()
            if hasattr(self, 'copy_isbn_combo'): self.copy_isbn_combo.setCurrentIndex(0) # Assuming first item is blank

    def init_category_tab(self):
        main_layout = QVBoxLayout(self.tab_category)
        main_layout.setSpacing(15)
        splitter = QSplitter(Qt.Vertical)
        
        form_frame = QFrame(); form_frame.setFrameStyle(QFrame.StyledPanel)
        form_layout_wrapper = QVBoxLayout(form_frame)
        form_group = QGroupBox("图书信息录入/编辑")
        form_group_layout = QGridLayout(form_group); form_group_layout.setSpacing(10)
        form_group_layout.addWidget(QLabel("ISBN:"), 0,0); self.cat_isbn = QLineEdit(); self.cat_isbn.setPlaceholderText("978-X-XXX-XXXXX-X"); form_group_layout.addWidget(self.cat_isbn,0,1)
        form_group_layout.addWidget(QLabel("类别:"), 1,0); self.cat_category = QLineEdit(); self.cat_category.setPlaceholderText("例如: 计算机, 文学"); form_group_layout.addWidget(self.cat_category,1,1)
        form_group_layout.addWidget(QLabel("书名:"), 2,0); self.cat_title = QLineEdit(); self.cat_title.setPlaceholderText("完整书名"); form_group_layout.addWidget(self.cat_title,2,1)
        form_group_layout.addWidget(QLabel("作者:"), 3,0); self.cat_author = QLineEdit(); self.cat_author.setPlaceholderText("主要作者"); form_group_layout.addWidget(self.cat_author,3,1)
        form_group_layout.addWidget(QLabel("出版社:"), 0,2); self.cat_publisher = QLineEdit(); self.cat_publisher.setPlaceholderText("出版社名称"); form_group_layout.addWidget(self.cat_publisher,0,3)
        form_group_layout.addWidget(QLabel("出版日期:"), 1,2); self.cat_publish_date = QDateEdit(QDate.currentDate()); self.cat_publish_date.setCalendarPopup(True); form_group_layout.addWidget(self.cat_publish_date,1,3)
        form_group_layout.addWidget(QLabel("价格:"), 2,2); self.cat_price = QLineEdit(); self.cat_price.setPlaceholderText("例如: 89.00"); self.cat_price.setValidator(QDoubleValidator(0.0, 9999.0, 2)); form_group_layout.addWidget(self.cat_price,2,3)
        form_group_layout.addWidget(QLabel("计划馆藏:"), 3,2); self.cat_total_copies = QSpinBox(); self.cat_total_copies.setRange(0,1000); self.cat_total_copies.setSuffix(" 本"); form_group_layout.addWidget(self.cat_total_copies,3,3)
        form_group_layout.addWidget(QLabel("图书简介:"), 4,0); self.cat_description = QTextEdit(); self.cat_description.setFixedHeight(70); self.cat_description.setPlaceholderText("图书简介..."); form_group_layout.addWidget(self.cat_description, 4,1,1,3)
        form_layout_wrapper.addWidget(form_group)
        
        cat_button_layout = QHBoxLayout()
        self.btn_add_category = QPushButton("➕ 添加类别")
        self.btn_search_category = QPushButton("🔍 搜索类别")
        self.btn_clear_cat_form = QPushButton("🗑️ 清空表单")
        self.btn_load_cat_to_form = QPushButton("📝 编辑选中")
        cat_button_layout.addWidget(self.btn_add_category); cat_button_layout.addWidget(self.btn_search_category); cat_button_layout.addWidget(self.btn_clear_cat_form); cat_button_layout.addWidget(self.btn_load_cat_to_form); cat_button_layout.addStretch()
        form_layout_wrapper.addLayout(cat_button_layout)
        splitter.addWidget(form_frame)

        table_frame_cat = QFrame(); table_frame_cat.setFrameStyle(QFrame.StyledPanel); table_layout_cat = QVBoxLayout(table_frame_cat)
        table_layout_cat.addWidget(QLabel("📊 图书类别列表"))
        self.category_table = QTableWidget(); self.category_table.setColumnCount(9); self.category_table.setHorizontalHeaderLabels(["ISBN", "类别", "书名", "作者", "出版社", "出版日期", "价格", "总副本", "可借副本"])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.category_table.setEditTriggers(QAbstractItemView.NoEditTriggers); self.category_table.setAlternatingRowColors(True); self.category_table.setSortingEnabled(True)
        table_layout_cat.addWidget(self.category_table)
        splitter.addWidget(table_frame_cat)
        splitter.setSizes([300, 450])
        main_layout.addWidget(splitter)

        self.btn_add_category.clicked.connect(self.add_category)
        self.btn_search_category.clicked.connect(self.search_categories)
        self.btn_clear_cat_form.clicked.connect(self.clear_category_form)
        self.btn_load_cat_to_form.clicked.connect(self.load_category_to_form)
        self.category_table.itemDoubleClicked.connect(self.load_category_to_form)

    def init_copy_tab(self):
        main_layout = QVBoxLayout(self.tab_copy)
        layout = QVBoxLayout(self.tab_copy)
        layout.addWidget(QLabel("图书副本管理"))
        self.copy_table = QTableWidget(); self.copy_table.setColumnCount(6); self.copy_table.setHorizontalHeaderLabels(["书号", "ISBN", "书名", "是否可借", "物理状态", "入库时间"])
        self.copy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.copy_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.copy_table)

    def refresh_data(self):
        self.load_all_categories_to_table()
        self.load_isbn_options_for_copy_tab()
        if self.parent_window and hasattr(self.parent_window, 'show_status_message'):
            self.parent_window.show_status_message("✅ 图书数据已刷新", 3000, "success")

    def add_category(self):
        if not (self.user_info and self.user_info.get('role') == 'admin'): QMessageBox.warning(self, "权限不足", "您没有权限执行此操作。"); return
        isbn = self.cat_isbn.text().strip(); category = self.cat_category.text().strip(); title = self.cat_title.text().strip(); author = self.cat_author.text().strip()
        publisher = self.cat_publisher.text().strip() or None; publish_date_str = self.cat_publish_date.date().toString("yyyy-MM-dd")
        price_str = self.cat_price.text().strip(); total_copies_val = self.cat_total_copies.value(); description = self.cat_description.toPlainText().strip() or None
        if not all([isbn, category, title, author]): QMessageBox.warning(self, "输入错误", "ISBN、类别、书名、作者是必填项！"); return
        try:
            price = float(price_str) if price_str else None
            success, message = lib.add_book_category(isbn, category, title, author, publisher, publish_date_str, price, total_copies_val, description)
            if success:
                QMessageBox.information(self, "操作成功", message); self.clear_category_form(); self.refresh_data()
                if self.parent_window: self.parent_window.show_status_message(f"✓ 类别 '{title}' 已添加", 3000, "success")
            else: QMessageBox.warning(self, "操作失败", message)
        except ValueError: QMessageBox.warning(self, "输入错误", "价格或馆藏数量格式不正确")
        except Exception as e: QMessageBox.critical(self, "操作失败", f"添加图书类别失败：\n{e}")

    def search_categories(self):
        isbn = self.cat_isbn.text().strip() or None; category = self.cat_category.text().strip() or None
        title = self.cat_title.text().strip() or None; author = self.cat_author.text().strip() or None
        if is_reader:
            pass
        try:
            results = lib.search_books(title=title, author=author, isbn=isbn, category=category)
            self.populate_category_table(results)
            if self.parent_window: self.parent_window.show_status_message(f"🔍 搜索完成，找到 {len(results)} 条记录", 3000)
        except Exception as e: QMessageBox.critical(self, "查询失败", f"搜索图书失败：\n{e}")

    def load_all_categories_to_table(self):
        try: self.populate_category_table(lib.search_books())
        except Exception as e: QMessageBox.critical(self, "加载失败", f"加载图书类别失败：\n{e}")

    def populate_category_table(self, categories):
        self.category_table.setRowCount(0)
        for row, cat_data in enumerate(categories):
            self.category_table.insertRow(row)
            items = [
                cat_data.get('isbn', ''), cat_data.get('category', ''), cat_data.get('title', ''),
                cat_data.get('author', ''), cat_data.get('publisher', ''),
                str(cat_data.get('publish_date', '')), f"{cat_data.get('price', 0.0):.2f}",
                str(cat_data.get('actual_total_copies', 0)),
                str(cat_data.get('actual_available_copies', 0))
            ]
            for col, text in enumerate(items): self.category_table.setItem(row, col, QTableWidgetItem(text))
            self.category_table.item(row, 0).setData(Qt.UserRole, cat_data)

    def clear_category_form(self):
        self.cat_isbn.clear(); self.cat_category.clear(); self.cat_title.clear(); self.cat_author.clear()
        self.cat_publisher.clear(); self.cat_publish_date.setDate(QDate.currentDate()); self.cat_price.clear()
        self.cat_total_copies.setValue(0); self.cat_description.clear(); self.cat_isbn.setFocus()

    def load_category_to_form(self):
        if not (self.user_info and self.user_info.get('role') == 'admin'): return
        selected = self.category_table.selectedItems()
        if not selected: QMessageBox.information(self, "提示", "请先选择要编辑的图书类别。"); return
        cat_data = self.category_table.item(selected[0].row(), 0).data(Qt.UserRole)
        if not cat_data: return
        self.cat_isbn.setText(cat_data.get('isbn', '')); self.cat_category.setText(cat_data.get('category', ''))
        self.cat_title.setText(cat_data.get('title', '')); self.cat_author.setText(cat_data.get('author', ''))
        self.cat_publisher.setText(cat_data.get('publisher', ''));
        p_date = cat_data.get('publish_date'); self.cat_publish_date.setDate(QDate.fromString(str(p_date), "yyyy-MM-dd") if p_date else QDate.currentDate())
        self.cat_price.setText(str(cat_data.get('price', ''))); self.cat_total_copies.setValue(cat_data.get('total_copies', 0))
        self.cat_description.setPlainText(cat_data.get('description', ''))

    def load_isbn_options_for_copy_tab(self):
        current_isbn_data = self.copy_isbn_combo.currentData()
        self.copy_isbn_combo.blockSignals(True)
        self.copy_isbn_combo.clear()
        self.copy_isbn_combo.addItem("- 请选择ISBN -", None)
        try:
            categories = lib.search_books()
            for cat in categories:
                self.copy_isbn_combo.addItem(f"{cat.get('isbn')} - {cat.get('title')}", cat.get('isbn'))
            
            if current_isbn_data:
                idx = self.copy_isbn_combo.findData(current_isbn_data)
                if idx != -1: self.copy_isbn_combo.setCurrentIndex(idx)
                else: self.copy_book_info_label.setText("请选择ISBN"); self.populate_copy_table([])
            else:
                 self.copy_book_info_label.setText("请选择ISBN"); self.populate_copy_table([])
        except Exception as e: QMessageBox.critical(self, "加载失败", f"加载ISBN选项失败: \n{e}")
        finally: self.copy_isbn_combo.blockSignals(False)
        if self.copy_isbn_combo.currentIndex() > 0 :
            self.on_isbn_selected_for_copy(self.copy_isbn_combo.currentText())

    def on_isbn_selected_for_copy(self, text):
        isbn = self.copy_isbn_combo.currentData()
        if isbn:
            try:
                book_details_list = lib.search_books(isbn=isbn)
                if book_details_list:
                    book = book_details_list[0]
                    self.copy_book_info_label.setText(f"<b>{book.get('title')}</b> ({book.get('author')})<br>总副本: {book.get('actual_total_copies',0)}, 可借: {book.get('actual_available_copies',0)}")
                else: self.copy_book_info_label.setText("未找到该ISBN的图书信息。")
                self.refresh_copies_for_selected_isbn()
            except Exception as e: self.copy_book_info_label.setText(f"获取信息失败: {e}")
        else:
            self.copy_book_info_label.setText("请选择ISBN")
            self.populate_copy_table([])

    def add_copy(self):
        if not (self.user_info and self.user_info.get('role') == 'admin'): QMessageBox.warning(self, "权限不足", "您没有权限执行此操作。"); return
        isbn = self.copy_isbn_combo.currentData()
        book_number = self.copy_book_number.text().strip()
        if not isbn: QMessageBox.warning(self, "选择错误", "请先选择一个ISBN！"); return
        if not book_number: QMessageBox.warning(self, "输入错误", "请输入图书书号！"); return
        try:
            success, message = lib.add_book_copy(isbn, book_number)
            if success:
                QMessageBox.information(self, "操作成功", message); self.copy_book_number.clear(); self.refresh_data()
                if self.parent_window: self.parent_window.show_status_message(f"✓ 副本 '{book_number}' 已添加", 3000, "success")
            else: QMessageBox.warning(self, "操作失败", message)
        except Exception as e: QMessageBox.critical(self, "操作失败", f"添加图书副本失败：\n{e}")

    def refresh_copies_for_selected_isbn(self):
        isbn = self.copy_isbn_combo.currentData()
        if isbn:
            try: self.populate_copy_table(lib.get_book_copies(isbn))
            except Exception as e: QMessageBox.critical(self, "加载失败", f"加载副本列表失败: {e}")
        else: self.populate_copy_table([])

    def populate_copy_table(self, copies):
        self.copy_table.setRowCount(0)
        for row, copy_data in enumerate(copies):
            self.copy_table.insertRow(row)
            is_available_text = "✅ 可借" if copy_data.get('is_available') else "❌ 不可借"
            status_map = {"normal": "🟢 正常", "damaged": "🟡 损坏", "lost": "🔴 遗失"}
            items = [
                copy_data.get('book_number', ''), copy_data.get('isbn', ''),
                copy_data.get('title', ''), is_available_text, status_map.get(copy_data.get('status', 'normal'), copy_data.get('status', 'normal')),
                str(copy_data.get('created_at', ''))
            ]
            for col, text in enumerate(items): self.copy_table.setItem(row, col, QTableWidgetItem(text))
            self.copy_table.item(row, 0).setData(Qt.UserRole, copy_data)

    def load_copy_to_form(self):
        if not (self.user_info and self.user_info.get('role') == 'admin'): return
        selected = self.copy_table.selectedItems()
        if not selected: return
        copy_data = self.copy_table.item(selected[0].row(), 0).data(Qt.UserRole)
        if not copy_data: return
        self.copy_book_number.setText(copy_data.get('book_number', ''))
        idx = self.copy_status.findText(copy_data.get('status', 'normal'))
        if idx != -1: self.copy_status.setCurrentIndex(idx)

    def update_copy_status(self):
        """更新选中副本的状态"""
        if not (self.user_info and self.user_info.get('role') == 'admin'): QMessageBox.warning(self, "权限不足", "您没有权限执行此操作。"); return
        selected = self.copy_table.selectedItems()
        if not selected: QMessageBox.information(self, "提示", "请先选择要更新状态的图书副本。"); return
        copy_data = self.copy_table.item(selected[0].row(), 0).data(Qt.UserRole)
        if not copy_data: return
        book_number = copy_data.get('book_number')
        new_status = self.copy_status.currentText()
        try:
            success, message = lib.update_book_status(book_number, new_status)
            if success:
                QMessageBox.information(self, "操作成功", message); self.refresh_data()
                if self.parent_window: self.parent_window.show_status_message(f"✓ 副本 '{book_number}' 状态更新", 3000, "success")
            else: QMessageBox.warning(self, "操作失败", message)
        except Exception as e: QMessageBox.critical(self, "操作失败", f"更新副本状态失败：\n{e}")

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
        
        if available_copies > 0 and self.user_info and self.user_info.get('role') == 'reader':
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

    def borrow_book(self, book_info):
        """处理借书操作"""
        if not self.user_info or self.user_info.get('role') != 'reader':
            QMessageBox.warning(self, "权限不足", "只有读者可以借书。")
            return
            
        reader_card_no = self.user_info.get('library_card_no')
        if not reader_card_no:
            QMessageBox.warning(self, "借阅失败", "无法获取您的借书证号。")
            return
            
        # 从book_info中获取ISBN，然后从系统获取一个可用副本
        isbn = book_info.get('isbn')
        try:
            # 获取这个ISBN的所有可用副本
            available_copies = lib.get_available_copies(isbn)
            if not available_copies:
                QMessageBox.warning(self, "借阅失败", "此图书当前没有可用副本。")
                return
                
            # 使用第一个可用副本
            book_number = available_copies[0].get('book_number')
            success, message = lib.borrow_book(reader_card_no, book_number)
            
            if success:
                QMessageBox.information(self, "借阅成功", f"您已成功借阅《{book_info.get('title')}》")
                self.refresh_data() # 刷新界面数据
            else:
                QMessageBox.warning(self, "借阅失败", message)
                
        except Exception as e:
            QMessageBox.critical(self, "借阅失败", f"借阅过程中发生错误: {e}")
            
    def refresh_data(self):
        self.load_initial_data()
        if self.parent_window and hasattr(self.parent_window, 'show_status_message'):
            self.parent_window.show_status_message("🔄 图书数据已刷新", 2000, "info")

# ====================== 借阅管理模块 ======================
class BorrowManagementWidget(QWidget):
    def __init__(self, parent=None, user_info: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.parent_window = parent
        self.user_info = user_info
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        self._original_widgets = {}
        self._access_denied_label_ref = None
        self._build_ui() # 构建完整的UI
        self.adjust_ui_for_role() # 根据角色调整UI

    def _build_ui(self):
        # 模块标题
        title_frame = QFrame()
        title_frame.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e3f2fd, stop:1 #bbdefb); border-radius:10px; padding:15px; }")
        title_layout = QHBoxLayout(title_frame)
        title_label = QLabel("📖 图书借阅与归还")
        title_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        title_label.setStyleSheet("color: #1976d2; background: transparent;")
        title_layout.addWidget(title_label)
        self.stats_label = QLabel("总借阅记录: 0 | 逾期图书: 0") # Placeholder
        self.stats_label.setFont(QFont("Microsoft YaHei UI", 12))
        self.stats_label.setStyleSheet("color: #666; background: transparent;")
        title_layout.addWidget(self.stats_label)
        title_layout.addStretch()
        self._original_widgets['title_frame'] = title_frame
        # self.layout.addWidget(title_frame) # This will be added by adjust_ui_for_role

        # 选项卡
        self.tabs = QTabWidget()
        self.tab_borrow = QWidget()
        self.tab_return = QWidget()
        self.tab_history = QWidget()
        self.tab_overdue = QWidget()

        self.tabs.addTab(self.tab_borrow, "📘 借书操作")
        self.tabs.addTab(self.tab_return, "📗 还书操作")
        self.tabs.addTab(self.tab_history, "📜 借阅历史")
        self.tabs.addTab(self.tab_overdue, "⚠️ 逾期提醒")
        self._original_widgets['tabs'] = self.tabs
        # self.layout.addWidget(self.tabs) # This will be added by adjust_ui_for_role
        
        self.init_borrow_tab()
        self.init_return_tab()
        self.init_history_tab()
        self.init_overdue_tab()

        self.refresh_data() # 初次加载数据

    def init_borrow_tab(self):
        layout = QVBoxLayout(self.tab_borrow)
        # Form for borrowing
        borrow_form_group = QGroupBox("借书信息")
        borrow_form_layout = QFormLayout(borrow_form_group)
        self.borrow_card_no_input = QLineEdit()
        self.borrow_card_no_input.setPlaceholderText("读者借书证号")
        self.borrow_book_id_input = QLineEdit()
        self.borrow_book_id_input.setPlaceholderText("图书书号")
        self.btn_process_borrow = QPushButton("✔️ 确认借阅")
        self.btn_process_borrow.clicked.connect(self.process_borrow)
        borrow_form_layout.addRow("借书证号:", self.borrow_card_no_input)
        borrow_form_layout.addRow("图书书号:", self.borrow_book_id_input)
        borrow_form_layout.addRow(self.btn_process_borrow)
        layout.addWidget(borrow_form_group)
        layout.addStretch()

    def init_return_tab(self):
        layout = QVBoxLayout(self.tab_return)
        # Form for returning
        return_form_group = QGroupBox("还书信息")
        return_form_layout = QFormLayout(return_form_group)
        self.return_book_id_input = QLineEdit()
        self.return_book_id_input.setPlaceholderText("要归还的图书书号")
        self.btn_process_return = QPushButton("✔️ 确认归还")
        self.btn_process_return.clicked.connect(self.process_return)
        return_form_layout.addRow("图书书号:", self.return_book_id_input)
        return_form_layout.addRow(self.btn_process_return)
        layout.addWidget(return_form_group)
        layout.addStretch()

    def init_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        # Filters for history
        history_filter_group = QGroupBox("查询条件")
        history_filter_layout = QFormLayout(history_filter_group)
        self.history_card_no_filter = QLineEdit()
        self.history_card_no_filter.setPlaceholderText("读者借书证号 (可选)")
        self.history_book_id_filter = QLineEdit()
        self.history_book_id_filter.setPlaceholderText("图书书号 (可选)")
        self.btn_search_history = QPushButton("🔍 查询历史")
        self.btn_search_history.clicked.connect(self.search_borrow_history)
        history_filter_layout.addRow("借书证号:", self.history_card_no_filter)
        history_filter_layout.addRow("图书书号:", self.history_book_id_filter)
        history_filter_layout.addRow(self.btn_search_history)
        layout.addWidget(history_filter_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels(["ID", "书号", "书名", "借书证号", "借阅日期", "应还日期", "归还状态/日期"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.history_table)

    def init_overdue_tab(self):
        layout = QVBoxLayout(self.tab_overdue)
        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(6)
        self.overdue_table.setHorizontalHeaderLabels(["书号", "书名", "借书证号", "读者姓名", "应还日期", "逾期天数"])
        self.overdue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.overdue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.overdue_table)

    def load_initial_data(self):
        """加载借阅管理模块的初始数据。"""
        # print("BorrowManagementWidget: load_initial_data called")
        if self.user_info and self.user_info.get('role') == 'admin':
            self.load_overdue_books()
            self.search_borrow_history() # Load all history for admin initially
        elif self.user_info and self.user_info.get('role') == 'reader':
            self.history_card_no_filter.setText(self.user_info.get('library_card_no', ''))
            self.search_borrow_history() # Load reader's history
        else:
            self.populate_history_table([]) # Clear history table if no user info
            if hasattr(self, 'overdue_table'): self.overdue_table.setRowCount(0) # Clear overdue table
        self.update_module_stats()

    def adjust_ui_for_role(self):
        is_admin = self.user_info and self.user_info.get('role') == 'admin'
        is_reader = self.user_info and self.user_info.get('role') == 'reader'
        reader_card_no = self.user_info.get('library_card_no') if is_reader else ''

        # Clear existing layout before adding conditional widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().hide() # Hide original widgets instead of deleting
        
        if not is_admin and not is_reader: # Unknown role or no user info
            if not self._access_denied_label_ref:
                self._access_denied_label_ref = QLabel("无法确定用户角色，访问受限。")
                self._access_denied_label_ref.setAlignment(Qt.AlignCenter)
                self._access_denied_label_ref.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
                self._access_denied_label_ref.setStyleSheet("color: #dc3545; margin-top: 20px;")
            self.layout.addWidget(self._access_denied_label_ref)
            self._access_denied_label_ref.show()
            self.layout.addStretch()
            return

        # Show title and tabs for known roles
        if self._original_widgets.get('title_frame'):
            self.layout.addWidget(self._original_widgets['title_frame'])
            self._original_widgets['title_frame'].show()
        if self._original_widgets.get('tabs'):
            self.layout.addWidget(self._original_widgets['tabs'])
            self._original_widgets['tabs'].show()
            
        # Borrow Tab
        if hasattr(self, 'borrow_card_no_input'):
            self.borrow_card_no_input.setText(reader_card_no if is_reader else "")
            self.borrow_card_no_input.setReadOnly(is_reader)

        # Return Tab - Admins can return any book, readers can trigger return for books (logic in lib)
        # No specific UI change here based on role for now, but functionality might differ.

        # History Tab
        if hasattr(self, 'history_card_no_filter'):
            self.history_card_no_filter.setText(reader_card_no if is_reader else "")
            self.history_card_no_filter.setReadOnly(is_reader)
        
        # Overdue Tab - typically admin only
        if hasattr(self, 'tab_overdue'):
             self.tabs.setTabVisible(self.tabs.indexOf(self.tab_overdue), is_admin)
        
        # Tab Titles (Optional: can remain generic, or be adjusted)
        if hasattr(self, 'tabs') and hasattr(self, 'tab_history'):
            self.tabs.setTabText(self.tabs.indexOf(self.tab_history), "我的借阅历史" if is_reader else "📜 借阅历史")
        
        if self._access_denied_label_ref: # Hide deny label if it was shown
            self._access_denied_label_ref.hide()

    def process_borrow(self):
        card_no = self.borrow_card_no_input.text().strip()
        book_id = self.borrow_book_id_input.text().strip()
        if not card_no or not book_id: QMessageBox.warning(self, "输入不完整", "请输入借书证号和图书书号。"); return
        
        if self.user_info.get('role') == 'reader' and card_no != self.user_info.get('library_card_no'):
            QMessageBox.warning(self, "权限错误", "您只能为自己借书。"); return

        success, message = lib.borrow_book(card_no, book_id)
        if success:
            QMessageBox.information(self, "借阅成功", message)
            self.borrow_book_id_input.clear()
            if self.user_info.get('role') == 'admin': self.borrow_card_no_input.clear() # Clear for admin for next entry
            self.refresh_data()
            if self.parent_window: self.parent_window.show_status_message(message, 3000, "success")
        else: QMessageBox.warning(self, "借阅失败", message)

    def process_return(self):
        # For GUI, borrowing_id might be more robust if selected from a list of current borrowings.
        # For now, using book_id as per original design.
        book_id_or_borrowing_id = self.return_book_id_input.text().strip() # This could be book_number or borrowing_id
        if not book_id_or_borrowing_id: QMessageBox.warning(self, "输入不完整", "请输入要归还的图书书号或借阅ID。"); return
        
        # Attempt to get borrowing_id if book_number is given and it's unique for current borrowings
        # This logic might be complex here; lib.return_book needs to be robust.
        # Let's assume lib.return_book can handle book_number or borrowing_id
        
        # Simplification: assume return_book takes book_number and finds the active borrowing.
        # Or, it could take borrowing_id if available. For now, stick to current enhanced_library
        # which likely expects a borrowing_id. Or we need a new lib function.
        # The original CLI app.py used `lib.return_book(borrowing_id)`.
        # The GUI currently has a text input for book_id.
        # This needs to be reconciled. For now, we pass what's in the input.
        # It might be better to find borrowing_id from book_id for the current user if reader,
        # or from a list if admin.
        
        # Assuming the input is borrowing_id for now, as that's what lib.return_book took in some versions.
        # If it's book_number, the lib function needs adjustment or a new one.
        # Let's assume the user inputs borrowing_id for now.
        try:
            borrow_id_to_return = int(book_id_or_borrowing_id)
        except ValueError:
             # If not an int, it might be a book_number. The library function needs to handle this.
             # For now, let's try to find an active borrowing for this book_number
             # This is a placeholder for more robust logic or a library change.
            QMessageBox.warning(self, "输入错误", "请输入有效的借阅ID (数字) 或图书书号。还书逻辑待完善。")
            return

        success, message = lib.return_book(borrow_id_to_return) # Assumes borrowing_id
        if success:
            QMessageBox.information(self, "还书成功", message)
            self.return_book_id_input.clear(); self.refresh_data()
            if self.parent_window: self.parent_window.show_status_message(message, 3000, "success")
        else: QMessageBox.warning(self, "还书失败", message)

    def search_borrow_history(self):
        card_no_filter_text = self.history_card_no_filter.text().strip()
        book_id_filter_text = self.history_book_id_filter.text().strip()

        card_no = card_no_filter_text or None
        book_id = book_id_filter_text or None
        
        if self.user_info.get('role') == 'reader':
            # Force card_no to be the logged-in reader's card_no
            my_card_no = self.user_info.get('library_card_no')
            if card_no != my_card_no:
                 self.history_card_no_filter.setText(my_card_no if my_card_no else '')
                 card_no = my_card_no
            if not card_no: # If reader has no card_no somehow, show no history
                self.populate_history_table([])
                return
        
        try:
            # Assuming lib.get_reader_borrowing_history is flexible or we call a general history function
            # Let's use get_reader_borrowing_history if card_no is present,
            # otherwise we need a general history function (or get_current_borrowings for active ones)
            if card_no:
                history = lib.get_reader_borrowing_history(library_card_no=card_no, book_number_filter=book_id) # Assuming book_number_filter param
            elif book_id and not card_no: # Search by book_id only (admin)
                history = lib.get_book_borrowing_history(book_number=book_id) # Needs this func in lib
            elif not card_no and not book_id: # Admin wants all history
                 history = lib.get_all_borrowing_history() # Needs this func in lib
            else: # Should not happen if logic above is correct
                history = []
                
            self.populate_history_table(history)
        except AttributeError as ae: # Catch if lib functions are missing
            QMessageBox.critical(self, "功能缺失", f"查询借阅历史时发生库函数错误: {ae}")
            self.populate_history_table([])
        except Exception as e:
            QMessageBox.critical(self, "查询失败", f"查询借阅历史失败: {e}")
            self.populate_history_table([])

    def populate_history_table(self, history_data):
        self.history_table.setRowCount(0)
        if not history_data: return
        for row, data in enumerate(history_data):
            self.history_table.insertRow(row)
            
            status_display = data.get('status', '未知')
            if data.get('status') == '已归还' and data.get('return_date'):
                status_display = f"已归还 ({data.get('return_date')})"
            elif data.get('status') == '借阅中' and data.get('due_date'):
                due_date = QDate.fromString(str(data.get('due_date')), "yyyy-MM-dd")
                if due_date < QDate.currentDate():
                    status_display = f"<font color='red'>逾期中 (应还: {data.get('due_date')})</font>"
                else:
                    status_display = f"借阅中 (应还: {data.get('due_date')})"
            
            items = [
                str(data.get('borrowing_id','N/A')), 
                data.get('book_number','N/A'), 
                data.get('book_title','N/A'), # Assuming this is in history_data
                data.get('library_card_no','N/A'), 
                str(data.get('borrow_date','N/A')),
                str(data.get('due_date','N/A')), 
                status_display
            ]
            for col, text in enumerate(items): 
                item = QTableWidgetItem()
                item.setText(str(text)) # Ensure text is string
                if "<font" in str(text): # For rich text
                    item.setText("") # Clear normal text
                    label = QLabel(str(text))
                    label.setOpenExternalLinks(False) # Prevent opening links if any
                    self.history_table.setCellWidget(row, col, label)
                else:
                    self.history_table.setItem(row, col, item)

    def load_overdue_books(self):
        if not (self.user_info and self.user_info.get('role') == 'admin'): return
        try:
            overdue = lib.get_overdue_books() # This should come from enhanced_library
            if hasattr(self, 'overdue_table'):
                self.overdue_table.setRowCount(0)
                if not overdue: return
                for row, data in enumerate(overdue):
                    self.overdue_table.insertRow(row)
                    items = [
                        data.get('book_number','N/A'), data.get('book_title','N/A'), 
                        data.get('library_card_no','N/A'), data.get('reader_name','N/A'), 
                        str(data.get('due_date','N/A')), str(data.get('days_overdue','N/A'))
                    ]
                    for col, text in enumerate(items): self.overdue_table.setItem(row, col, QTableWidgetItem(str(text)))
        except AttributeError:
             if self.parent_window: self.parent_window.show_status_message("功能缺失: 无法加载逾期图书 (get_overdue_books)", 3000, "danger")
        except Exception as e: 
            QMessageBox.critical(self, "加载失败", f"加载逾期列表失败: {e}")
            if self.parent_window: self.parent_window.show_status_message(f"错误: 加载逾期列表失败", 3000, "danger")

    def update_module_stats(self):
        """更新模块顶部的统计标签，如总借阅和逾期数"""
        if hasattr(self, 'stats_label') and (self.user_info and self.user_info.get('role') == 'admin'):
            try:
                # These need to be implemented in enhanced_library.py
                # total_borrowings = lib.get_total_active_borrowings_count()
                # overdue_count = lib.get_total_overdue_count()
                # self.stats_label.setText(f"当前借出: {total_borrowings} | 当前逾期: {overdue_count}")
                pass # Placeholder for now
            except AttributeError:
                 self.stats_label.setText("当前借出: N/A | 当前逾期: N/A (库函数缺失)")
            except Exception:
                 self.stats_label.setText("当前借出: N/A | 当前逾期: N/A (加载错误)")

    def refresh_data(self):
        self.load_initial_data() # This should call the correctly defined method
        if self.parent_window and hasattr(self.parent_window, 'show_status_message'):
            self.parent_window.show_status_message("🔄 借阅数据已刷新", 2000, "info")

# ====================== 查询统计模块 ======================
class QueryStatisticsWidget(QWidget):
    def __init__(self, parent=None, user_info: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.parent_window = parent
        self.user_info = user_info
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20,20,20,20); self.layout.setSpacing(15)
        
        self._build_ui()
        self.adjust_ui_for_role()

    def _build_ui(self):
        title_label = QLabel("📊 数据查询与统计分析")
        title_label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold)); title_label.setStyleSheet("color: #1976d2; margin-bottom:10px;")
        self.layout.addWidget(title_label)

        self.tabs = QTabWidget()
        self.tab_reader_rank = QWidget(); self.tab_book_rank = QWidget(); self.tab_comprehensive = QWidget(); self.tab_custom_query = QWidget()
        
        self.tabs.addTab(self.tab_reader_rank, "🏆 读者借阅排行")
        self.tabs.addTab(self.tab_book_rank, "⭐ 图书热门榜单")
        self.tabs.addTab(self.tab_comprehensive, "📈 综合统计报表")
        self.layout.addWidget(self.tabs)

        self.init_reader_rank_tab(); self.init_book_rank_tab(); self.init_comprehensive_tab()
    
    def init_reader_rank_tab(self):
        """初始化读者借阅排行标签页"""
        layout = QVBoxLayout(self.tab_reader_rank)
        
        # 读者排行表格
        self.reader_rank_table = QTableWidget()
        self.reader_rank_table.setColumnCount(3)
        self.reader_rank_table.setHorizontalHeaderLabels(["借书证号", "读者姓名", "借阅次数"])
        self.reader_rank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reader_rank_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reader_rank_table.setAlternatingRowColors(True)
        
        # 读者个人概览（当登录用户为读者时显示）
        self.reader_overview_label = QLabel()
        self.reader_overview_label.setWordWrap(True)
        self.reader_overview_label.setStyleSheet("padding: 20px; background-color: #f8f9fa; border-radius: 10px;")
        self.reader_overview_label.setText("请登录查看您的借阅概览")
        
        layout.addWidget(self.reader_overview_label)
        layout.addWidget(self.reader_rank_table)

    def init_book_rank_tab(self):
        """初始化图书热门榜单标签页"""
        layout = QVBoxLayout(self.tab_book_rank)
        
        # 创建图书排行表格
        self.book_rank_table = QTableWidget()
        self.book_rank_table.setColumnCount(3)
        self.book_rank_table.setHorizontalHeaderLabels(["ISBN", "图书名称", "借阅次数"])
        self.book_rank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.book_rank_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.book_rank_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.book_rank_table)

    def init_comprehensive_tab(self):
        """初始化综合统计报表标签页"""
        layout = QVBoxLayout(self.tab_comprehensive)
        
        # 统计概览框架
        stats_overview = QGroupBox("统计概览")
        stats_layout = QGridLayout(stats_overview)
        
        # 添加各类统计数据标签
        stats = [
            ("总图书种类", "N/A"), ("总藏书量", "N/A"),
            ("总注册读者", "N/A"), ("累计借阅次数", "N/A"),
            ("当前借出", "N/A"), ("当前逾期", "N/A")
        ]
        
        for i, (label_text, value) in enumerate(stats):
            row, col = divmod(i, 2)
            label = QLabel(f"{label_text}:")
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: bold;")
            stats_layout.addWidget(label, row, col*2)
            stats_layout.addWidget(value_label, row, col*2+1)
        
        # 添加刷新按钮
        refresh_btn = QPushButton("🔄 刷新统计数据")
        refresh_btn.clicked.connect(self.refresh_comprehensive_stats)
        
        layout.addWidget(stats_overview)
        layout.addWidget(refresh_btn)
        layout.addStretch()
    
    def refresh_comprehensive_stats(self):
        """刷新综合统计数据"""
        QMessageBox.information(self, "刷新统计", "正在实现综合统计功能...")
        # 这里可以添加从数据库获取最新统计数据的代码

    def adjust_ui_for_role(self):
        is_reader = self.user_info and self.user_info.get('role') == 'reader'
        
        # Tab visibility and naming
        self.tabs.setTabText(self.tabs.indexOf(self.tab_reader_rank), "我的借阅概览" if is_reader else "🏆 读者借阅排行")
        self.tabs.setTabText(self.tabs.indexOf(self.tab_book_rank), "⭐ 图书热门榜单" if is_reader else "⭐ 图书热门榜单")
        self.tabs.setTabVisible(self.tabs.indexOf(self.tab_comprehensive), not is_reader)

        self.load_initial_data()

    def load_initial_data(self):
        if self.user_info and self.user_info.get('role') == 'reader':
            self.load_reader_specific_data()
            self.load_book_ranking_data()
            if hasattr(self, 'reader_rank_table'): self.reader_rank_table.setVisible(False)
            if hasattr(self, 'reader_overview_label'): self.reader_overview_label.setVisible(True)
        else:
            self.load_admin_statistics()
            if hasattr(self, 'reader_rank_table'): self.reader_rank_table.setVisible(True)
            if hasattr(self, 'reader_overview_label'): self.reader_overview_label.setVisible(False)

    def load_reader_specific_data(self):
        if not (self.user_info and self.user_info.get('role') == 'reader'): return
        reader_card_no = self.user_info.get('library_card_no')
        if not reader_card_no: self.reader_overview_label.setText("无法加载您的借阅信息：借书证号未知。"); return
        
        try:
            current_borrows = lib.get_reader_current_borrow_count(reader_card_no) 
            total_history = lib.get_reader_total_borrow_history_count(reader_card_no) 
            
            overview_text = f"""
            <h3>您的借阅概览 ({self.user_info.get('name', reader_card_no)})</h3>
            <p><b>当前借阅数量:</b> {current_borrows} 本</p>
            <p><b>历史借阅总数:</b> {total_history} 本</p>
            <p><i>详细借阅历史请查看"借阅管理"模块。</i></p>
            """
            self.reader_overview_label.setText(overview_text)
        except Exception as e:
            self.reader_overview_label.setText(f"<font color='red'>加载您的借阅数据失败：{e}</font>")
            QMessageBox.warning(self, "加载失败", f"加载读者个人统计失败: {e}")
            
    def load_book_ranking_data(self):
        try:
            book_ranks = lib.get_book_borrowing_ranks()
            if hasattr(self, 'book_rank_table'):
                self.book_rank_table.setRowCount(0)
                for row, data in enumerate(book_ranks):
                    self.book_rank_table.insertRow(row)
                    items = [data.get('isbn', ''), data.get('title', ''), data.get('borrow_count', 0)]
                    for col, text in enumerate(items): self.book_rank_table.setItem(row, col, QTableWidgetItem(text))
        except Exception as e: QMessageBox.critical(self, "加载失败", f"加载图书排行失败: {e}")

    def load_admin_statistics(self):
        if not (self.user_info and self.user_info.get('role') == 'admin'): return
        try:
            reader_ranks = lib.get_reader_borrowing_ranks()
            if hasattr(self, 'reader_rank_table'):
                self.reader_rank_table.setRowCount(0)
                for row, data in enumerate(reader_ranks):
                    self.reader_rank_table.insertRow(row)
                    items = [data.get('library_card_no', ''), data.get('name', ''), str(data.get('borrow_count', 0))]
                    for col, text in enumerate(items): self.reader_rank_table.setItem(row, col, QTableWidgetItem(text))
        except Exception as e: QMessageBox.critical(self, "加载失败", f"加载读者排行失败: {e}")
        
    def refresh_data(self):
        """刷新所有统计数据"""
        try:
            if self.user_info and self.user_info.get('role') == 'reader':
                self.load_reader_specific_data()
            else:
                self.load_admin_statistics()
            
            # 刷新图书排行数据（对所有用户都显示）
            self.load_book_ranking_data()
            
            if self.parent_window and hasattr(self.parent_window, 'show_status_message'):
                self.parent_window.show_status_message("✅ 统计数据已刷新", 3000, "success")
        except Exception as e:
            QMessageBox.warning(self, "刷新失败", f"刷新统计数据时发生错误: {e}")
            if self.parent_window and hasattr(self.parent_window, 'show_status_message'):
                self.parent_window.show_status_message("❌ 统计数据刷新失败", 3000, "danger")
