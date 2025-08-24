#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for ReaderManagementWidget functionality
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Add the current directory to path
sys.path.insert(0, '/home/runner/work/LMS/LMS')

from additional_widgets import ReaderManagementWidget
import enhanced_library as lib

def test_reader_widget():
    """Test the ReaderManagementWidget with mock user info"""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Reader Management Widget Test")
    main_window.setGeometry(100, 100, 1200, 800)
    
    # Create central widget
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Test with admin user info
    admin_user_info = {
        'user_id': 1,
        'username': 'admin',
        'role': 'admin',
        'full_name': 'System Administrator',
        'email': 'admin@example.com'
    }
    
    # Create reader management widget
    reader_widget = ReaderManagementWidget(parent=main_window, user_info=admin_user_info)
    layout.addWidget(reader_widget)
    
    main_window.setCentralWidget(central_widget)
    main_window.show()
    
    return app.exec_()

if __name__ == "__main__":
    # First, test if we can import the necessary modules
    try:
        print("Testing imports...")
        import enhanced_library as lib
        print("✓ Enhanced library imported successfully")
        
        # Test some key functions
        missing_funcs = []
        required_funcs = [
            'search_readers', 'add_reader', 'update_reader_info',
            'delete_reader_by_card_no', 'get_reader_statistics_summary',
            'get_available_copies', 'get_book_copies'
        ]
        
        for func in required_funcs:
            if not hasattr(lib, func):
                missing_funcs.append(func)
        
        if missing_funcs:
            print(f"✗ Missing functions: {missing_funcs}")
        else:
            print("✓ All required functions available")
            
        print("Starting GUI test...")
        exit_code = test_reader_widget()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)