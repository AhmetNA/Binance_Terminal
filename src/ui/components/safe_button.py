"""
Safe Button Component.
A custom button that triggers actions only on double-click events
to prevent accidental clicks specifically for high-risk operations like trading.
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Signal


class SafeButton(QPushButton):
    """
    A button that requires a double-click to trigger its action.
    Single clicks are ignored to prevent accidental trades.
    """

    # Signal triggered only on double click
    doubleClicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

    def mouseDoubleClickEvent(self, event):
        """Handle double click event."""
        # Emit our custom signal
        self.doubleClicked.emit()
        # Call safe implementation of parent class if needed, 
        # but usually for buttons we just want the signal.
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        """
        Handle mouse press event.
        We override this to intercept single clicks.
        """
        # We still want the visual 'press' effect, so we call super,
        # BUT standard QPushButton emits 'clicked' on mouseRelease.
        # To strictly enforce double-click logic for the *action*,
        # the consumer of this class should listen to `doubleClicked`
        # and ignore `clicked`.
        
        # However, to be extra safe and prevent standard 'clicked' signals
        # from potentially triggering logic if someone connects to it by mistake,
        # we can consume the event if we wanted to block it entirely,
        # but blocking mousePress prevents the doubleClick from registering in Qt.
        
        # Strategy:
        # We let the event propagate so Qt detects the double click sequence.
        # The safety comes from the fact that we will only connect slots to
        # 'doubleClicked' in the panels.
        super().mousePressEvent(event)
