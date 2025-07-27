#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for ReaderManagementWidget functionality (no GUI)
"""

import sys
sys.path.insert(0, '/home/runner/work/LMS/LMS')

def test_library_functions():
    """Test the library functions needed by ReaderManagementWidget"""
    print("Testing enhanced_library functions...")
    
    try:
        import enhanced_library as lib
        print("✓ Enhanced library imported successfully")
        
        # Test key functions exist
        required_functions = [
            'search_readers', 'add_reader', 'update_reader_info',
            'delete_reader_by_card_no', 'get_reader_statistics_summary',
            'get_available_copies', 'get_book_copies',
            'get_total_active_borrowings_count', 'get_total_overdue_count',
            'get_all_borrowing_history'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if hasattr(lib, func_name):
                print(f"✓ {func_name} - Available")
            else:
                print(f"✗ {func_name} - MISSING")
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"\nMissing functions: {missing_functions}")
            return False
        else:
            print("\n✓ All required functions are available!")
            return True
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_widget_class():
    """Test if the ReaderManagementWidget class can be imported and instantiated"""
    print("\nTesting ReaderManagementWidget class...")
    
    try:
        # We can't test PyQt5 components in headless mode, but we can check imports
        from additional_widgets import ReaderManagementWidget
        print("✓ ReaderManagementWidget class imported successfully")
        
        # Check if the class has the required methods
        required_methods = [
            'add_reader', 'search_readers', 'update_reader', 'delete_reader',
            'clear_reader_form', 'load_reader_to_form', 'load_all_readers',
            'populate_reader_table', 'validate_reader_input', 'adjust_ui_for_role'
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if hasattr(ReaderManagementWidget, method_name):
                print(f"✓ {method_name} - Available")
            else:
                print(f"✗ {method_name} - MISSING")
                missing_methods.append(method_name)
        
        if missing_methods:
            print(f"\nMissing methods: {missing_methods}")
            return False
        else:
            print("\n✓ All required methods are available!")
            return True
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("ReaderManagementWidget Test Suite")
    print("=" * 60)
    
    test1_passed = test_library_functions()
    test2_passed = test_widget_class()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Library Functions Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Widget Class Test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests PASSED! The ReaderManagementWidget should work correctly.")
        return 0
    else:
        print("\n❌ Some tests FAILED. Please fix the issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())