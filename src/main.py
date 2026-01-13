import os
import sys

# Add src to path to allow imports - ensure it's at the beginning to override any other paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Clear any cached preferences to ensure we use the correct ones
try:
    import config.preferences_manager as pm

    pm._CACHED_PREFERENCES = None
    pm._CACHED_ORDER_TYPE = None
    pm._CACHED_RISK_TYPE = None
except ImportError:
    pass  # Module not yet available

from core.logger import setup_logging, get_main_logger
from ui.main_window import initialize_gui
from api import close_http_session


def main():
    # Logging'i başlat
    setup_logging()
    logger = get_main_logger()
    logger.info("Starting the application...")
    
    # Capture application start time
    import time
    app_start_time = time.time()

    # Force X11 backend on Linux to fix window positioning on Wayland/Ubuntu
    # This must be done before creating QApplication
    if sys.platform.startswith("linux"):
        # check if not already set to avoid overriding user preference if they set it explicitly
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "xcb"
            logger.info("Forced QT_QPA_PLATFORM=xcb for window positioning fix")

    # Verify preferences are loaded correctly
    try:
        from config.preferences_manager import get_buy_preferences
        from core.paths import PREFERENCES_FILE

        preferences = get_buy_preferences()
        logger.info(f"Loaded preferences: {preferences}")
        logger.info(f"Preferences file: {PREFERENCES_FILE}")
        logger.info(f"File exists: {os.path.exists(PREFERENCES_FILE)}")
    except Exception as e:
        logger.error(f"Error loading preferences: {e}")

    try:
        # PySide6 import kontrolü
        try:
            from PySide6.QtWidgets import QApplication

            logger.debug("PySide6 imported successfully")
        except ImportError as e:
            logger.error(f"PySide6 import failed: {e}")
            print(
                "Error: PySide6 is not installed. Please install it with: pip install PySide6"
            )
            input("Press Enter to exit...")
            return

        # QApplication'ı oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("Binance Terminal")
        app.setApplicationVersion("1.0")
        logger.debug("QApplication created")

        # Ana GUI'yi başlat
        exit_code = initialize_gui(start_time=app_start_time)
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
    finally:
        # HTTP session'ı temizle
        import asyncio

        try:
            # Modern asyncio approach - avoid deprecated get_event_loop()
            try:
                # Try to get existing loop if available
                loop = asyncio.get_running_loop()
                # If we're in a running loop, we can't use run_until_complete
                # Schedule the cleanup as a task instead
                asyncio.create_task(close_http_session())
            except RuntimeError:
                # No running loop, so we can safely use asyncio.run()
                asyncio.run(close_http_session())
        except Exception:
            # Fallback: try the old method for compatibility
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(close_http_session())
                loop.close()
            except Exception:
                pass

        # Save any cached price data before exit
        try:
            from services.market import force_save_prices

            force_save_prices()
            logger.debug("Saved cached price data before exit")
        except Exception as e:
            logger.warning(f"Could not save cached prices: {e}")


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
