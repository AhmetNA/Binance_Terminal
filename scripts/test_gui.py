import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
sys.path.insert(0, src_dir)

def test_imports():
    """Test all critical imports"""
    print("🔧 Testing imports...")
    
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
        print("✅ PySide6 import successful")
    except ImportError as e:
        print(f"❌ PySide6 import failed: {e}")
        return False
    
    try:
        from ui.main_window import MainWindow, initialize_gui
        print("✅ Main window import successful")
    except ImportError as e:
        print(f"❌ Main window import failed: {e}")
        return False
    
    try:
        from services.order_service import prepare_client
        print("✅ Order service import successful")
    except ImportError as e:
        print(f"❌ Order service import failed: {e}")
        return False
    
    return True

def test_simple_gui():
    """Test a simple GUI window"""
    print("🖥️ Testing simple GUI...")
    
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
        
        app = QApplication(sys.argv)
        
        window = QMainWindow()
        window.setWindowTitle("Test Window")
        window.resize(400, 300)
        
        label = QLabel("GUI Test Successful!")
        label.setStyleSheet("font-size: 16px; padding: 20px;")
        window.setCentralWidget(label)
        
        window.show()
        print("✅ Simple GUI window created successfully")
        
        # Show for 3 seconds then close
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)  # 3 seconds
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Simple GUI test failed: {e}")
        return False

def test_main_window():
    """Test the actual main window"""
    print("🏢 Testing main window...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        
        # Create main window without client (demo mode)
        window = MainWindow(None)
        window.setWindowTitle("Binance Terminal - Test Mode")
        window.resize(800, 600)
        window.show()
        
        print("✅ Main window created successfully")
        
        # Show for 5 seconds then close
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(5000)  # 5 seconds
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Main window test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Binance Terminal GUI Test")
    print("=" * 40)
    
    if not test_imports():
        print("❌ Import tests failed")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("Running simple GUI test...")
    if test_simple_gui() == 0:
        print("✅ Simple GUI test passed")
    else:
        print("❌ Simple GUI test failed")
    
    print("\n" + "=" * 40)
    print("Running main window test...")
    if test_main_window() == 0:
        print("✅ Main window test passed")
    else:
        print("❌ Main window test failed")
    
    print("\n" + "=" * 40)
    print("🎉 GUI tests completed!")
