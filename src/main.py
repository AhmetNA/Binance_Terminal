import sys
import os

def main():
    import time
    start_time = time.time()
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

    # Imports moved inside main to avoid E402 (imports not at top)
    # caused by sys.path manipulation above
    from core.logger import setup_logging, get_main_logger
    from ui.main_window import initialize_gui
    from api import close_http_session
    
    # Setup Logging
    setup_logging()
    logger = get_main_logger()
    logger.info("Starting the application...")

    # Qt Application Setup
    # Force X11 backend on Linux to fix window positioning on Wayland/Ubuntu
    if sys.platform.startswith("linux"):
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "xcb"
            logger.info("Forced QT_QPA_PLATFORM=xcb for window positioning fix")

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        logger.error("PySide6 is not installed!")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("Binance Terminal")
    app.setApplicationVersion("1.0.0")

    # Path & Environment Check
    try:
        from core.paths import PROJECT_ROOT, SETTINGS_DIR
        # Log essential paths once for troubleshooting without verbosity
        logger.debug(f"Project Root: {PROJECT_ROOT}")
        logger.debug(f"Settings Dir: {SETTINGS_DIR}")
    except Exception as e:
        logger.error(f"Environment check error: {e}")

    # GUI Initialization
    # NOTE: initialize_gui processes splash screen and returns control when ready
    exit_code = initialize_gui(start_time=start_time) 
    
    # Event Loop
    try:
        return exit_code

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception:
        logger.exception("An error occurred in event loop.")
        return -1
    finally:
        # HTTP session cleanup
        import asyncio
        try:
             asyncio.run(close_http_session())
        except Exception:
             pass
        
        # Save prices
        try:
            from services.market import force_save_prices
            force_save_prices()
        except Exception:
            pass


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
