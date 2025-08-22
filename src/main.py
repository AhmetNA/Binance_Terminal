import os
import sys

# Add src to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logging, get_main_logger
from ui.main_window import initialize_gui

def main():
    # Logging'i başlat
    setup_logging()
    logger = get_main_logger()
    logger.info("Starting the application...")
    
    try:
        # PySide6 import kontrolü
        try:
            from PySide6.QtWidgets import QApplication
            logger.info("PySide6 imported successfully")
        except ImportError as e:
            logger.error(f"PySide6 import failed: {e}")
            print("Error: PySide6 is not installed. Please install it with: pip install PySide6")
            input("Press Enter to exit...")
            return
        
        # QApplication'ı oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("Binance Terminal")
        app.setApplicationVersion("1.0")
        logger.info("QApplication created")
        
        # Ana GUI'yi başlat
        exit_code = initialize_gui()
        logger.info(f"Application exited with code: {exit_code}")
        
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.exception("An error occurred while running the application.")
        logger.info(f"Fatal Error: {e}")
        input("Press Enter to exit...")
        return -1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code if exit_code is not None else 0)
    except Exception as e:
        print(f"Fatal error in main: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(-1)
