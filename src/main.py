import logging
import os
import sys

# Add src to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import initialize_gui


# Logging configuration
def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, 'binance_terminal.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file_path, encoding='utf-8')
        ]
    )

def main():
    setup_logging()
    logging.info("Starting the application...")
    
    try:
        # PySide6 import kontrolü
        try:
            from PySide6.QtWidgets import QApplication
            logging.info("PySide6 imported successfully")
        except ImportError as e:
            logging.error(f"PySide6 import failed: {e}")
            print("Error: PySide6 is not installed. Please install it with: pip install PySide6")
            input("Press Enter to exit...")
            return
        
        # QApplication'ı oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("Binance Terminal")
        app.setApplicationVersion("1.0")
        logging.info("QApplication created")
        
        # Ana GUI'yi başlat
        exit_code = initialize_gui()
        logging.info(f"Application exited with code: {exit_code}")
        
        return exit_code
        
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        return 0
    except Exception as e:
        logging.exception("An error occurred while running the application.")
        print(f"Fatal Error: {e}")
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
