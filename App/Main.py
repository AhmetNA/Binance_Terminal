import logging
import os
from packages.GUI import initialize_gui


# Logging configuration
def setup_logging():
    log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'binance_terminal.log')
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
        initialize_gui()  # intentionally commented out to cause an error
    except Exception as e:
        logging.exception("An error occurred while initializing the GUI.")

if __name__ == "__main__":
    main()