import sys
import os
import logging

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def test_basic_gui():
    """Test very basic GUI functionality"""
    setup_logging()
    logging.info("Starting basic GUI test...")
    
    try:
        # Test PySide6 import
        logging.info("Testing PySide6 import...")
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
        from PySide6.QtCore import QTimer
        logging.info("✅ PySide6 imported successfully")
        
        # Create application
        logging.info("Creating QApplication...")
        app = QApplication(sys.argv)
        logging.info("✅ QApplication created")
        
        # Create simple window
        logging.info("Creating main window...")
        window = QMainWindow()
        window.setWindowTitle("Binance Terminal - Test")
        window.resize(600, 400)
        
        # Create central widget
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Add labels
        title_label = QLabel("🚀 Binance Terminal Test")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E8B57; padding: 20px;")
        
        status_label = QLabel("✅ GUI System Working!")
        status_label.setStyleSheet("font-size: 16px; color: #333; padding: 10px;")
        
        info_label = QLabel("This window will close automatically in 5 seconds...")
        info_label.setStyleSheet("font-size: 12px; color: #666; padding: 10px;")
        
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addWidget(info_label)
        
        window.setCentralWidget(central_widget)
        logging.info("✅ Window setup complete")
        
        # Show window
        logging.info("Showing window...")
        window.show()
        logging.info("✅ Window displayed")
        
        # Auto-close timer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(5000)  # 5 seconds
        logging.info("✅ Auto-close timer started")
        
        # Start event loop
        logging.info("Starting event loop...")
        result = app.exec()
        logging.info(f"✅ Event loop finished with code: {result}")
        
        return result
        
    except Exception as e:
        logging.exception(f"❌ Basic GUI test failed: {e}")
        return -1

if __name__ == "__main__":
    print("🔧 Running Basic GUI Test...")
    print("=" * 50)
    
    exit_code = test_basic_gui()
    
    print("=" * 50)
    if exit_code == 0:
        print("🎉 Basic GUI test PASSED!")
        print("The GUI system is working correctly.")
    else:
        print("❌ Basic GUI test FAILED!")
        print("There are issues with the GUI system.")
    
    print(f"Exit code: {exit_code}")
