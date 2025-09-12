"""
Base component class for all UI components in the Binance Terminal.
Provides common functionality and structure for all components.
"""

import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal


class BaseComponent(QWidget):
    """Base class for all UI components."""
    
    # Common signals that components can emit
    error_occurred = Signal(str)  # Error message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_logging()
        self.init_component()
    
    def setup_logging(self):
        """Setup logging for the component."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def init_component(self):
        """Initialize the component. Override in subclasses."""
        pass
    
    def log_info(self, message):
        """Log an info message."""
        self.logger.info(message)
    
    def log_error(self, message):
        """Log an error message and emit error signal."""
        self.logger.error(message)
        self.error_occurred.emit(message)
    
    def log_warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
    
    def handle_error(self, error, context=""):
        """Handle errors in a consistent way."""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.log_error(error_msg)
