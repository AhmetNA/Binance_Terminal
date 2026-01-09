"""
Terminal Widget Component.
Manages the terminal display for logs and messages.
"""

from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout
from PySide6.QtCore import Signal

from .base_component import BaseComponent
from ..styles.panel_styles import TERMINAL_STYLE, PanelSizes


class TerminalWidget(BaseComponent):
    """Terminal widget for displaying logs and messages."""

    # Signals
    message_added = Signal(str)  # message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.terminal = None
        self.setup_ui()

    def init_component(self):
        """Initialize the terminal widget."""
        self.logger.debug("Initializing Terminal Widget")

    def setup_ui(self):
        """Set up the UI for the terminal widget."""
        try:
            # Create the terminal text widget
            self.terminal = QPlainTextEdit()
            self.terminal.setReadOnly(True)
            self.terminal.setFixedHeight(PanelSizes.TERMINAL_HEIGHT)
            self.terminal.setStyleSheet(TERMINAL_STYLE)

            # Set the main layout
            layout = QVBoxLayout(self)
            layout.addWidget(self.terminal)
            layout.setContentsMargins(0, 0, 0, 0)

            self.logger.debug("Terminal Widget UI setup completed")

        except Exception as e:
            self.handle_error(e, "Error setting up Terminal Widget UI")

    def append_message(self, message):
        """Append a message to the terminal."""
        try:
            if self.terminal:
                self.terminal.appendPlainText(message)
                self.message_added.emit(message)
                # Auto-scroll to bottom
                self.terminal.verticalScrollBar().setValue(
                    self.terminal.verticalScrollBar().maximum()
                )
        except Exception as e:
            self.handle_error(e, f"Error appending message to terminal: {message}")

    def clear_terminal(self):
        """Clear all content from the terminal."""
        try:
            if self.terminal:
                self.terminal.clear()
                self.logger.debug("Terminal cleared")
        except Exception as e:
            self.handle_error(e, "Error clearing terminal")

    def get_text(self):
        """Get all text from the terminal."""
        try:
            if self.terminal:
                return self.terminal.toPlainText()
            return ""
        except Exception as e:
            self.handle_error(e, "Error getting terminal text")
            return ""

    def set_text(self, text):
        """Set the terminal text content."""
        try:
            if self.terminal:
                self.terminal.setPlainText(text)
        except Exception as e:
            self.handle_error(e, f"Error setting terminal text: {text}")

    def get_widget(self):
        """Get the main widget for this component."""
        return self.terminal
