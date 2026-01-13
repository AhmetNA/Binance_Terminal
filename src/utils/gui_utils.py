from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def move_window_to_top_center(window, parent=None, top_percent=0.15):
    """
    Moves the given window to the top-center of the screen.
    Uses delayed execution to override Window Manager initial placement
    (critical for Linux/Wayland/Ubuntu).
    
    Args:
        window: The QWidget/QMainWindow to move.
        parent: Ignored (kept for compatibility), effectively uses screen.
        top_percent: Float (0.0 - 1.0) indicating how far from top to place.
    """
    def perform_move(attempt=1):
        try:
            # Get the screen the window is associated with, or primary
            screen = window.screen()
            if not screen:
                screen = QApplication.primaryScreen()
                
            if not screen:
                return

            # Get available geometry (excludes dock/taskbar)
            available_geom = screen.availableGeometry()
            
            # Use frame geometry if valid (includes title bar), else component size
            frame_geom = window.frameGeometry()
            if frame_geom.width() > 100 and frame_geom.height() > 100:
                width = frame_geom.width()
            else:
                width = window.width()
                # processing events can help update geometry
                QApplication.processEvents()

            # Calculate X to center horizontally
            target_x = available_geom.x() + (available_geom.width() - width) // 2
            
            # Calculate Y for top-offset
            # If window is very tall (> 80% screen height), force 5% margin
            screen_height = available_geom.height()
            if window.height() > (screen_height * 0.8):
                target_y = available_geom.y() + int(screen_height * 0.05)
            else:
                target_y = available_geom.y() + int(screen_height * top_percent)
                
            # Ensure y is within bounds (never above screen top)
            target_y = max(available_geom.y(), target_y)
            
            # Apply move
            window.move(target_x, target_y)
            
            # Check if move was successful (tolerance of 50px for WM decorations)
            current_pos = window.pos()
            distance = ((current_pos.x() - target_x)**2 + (current_pos.y() - target_y)**2)**0.5
            
            if distance > 50 and attempt < 3:
                # If we are far from target, try again with a delay
                QTimer.singleShot(250 * attempt, lambda: perform_move(attempt + 1))
            
        except Exception:
            # Fail silently to avoid crashing app on geometry error
            pass

    # Method 1: Execute immediate logic
    perform_move(1)
    
    # Method 2: Delayed execution to override WM placement (Critical for Ubuntu/Wayland)
    # Increased delays to give WM time to settle
    QTimer.singleShot(100, lambda: perform_move(1))
    QTimer.singleShot(500, lambda: perform_move(1))
