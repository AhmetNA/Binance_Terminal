import json
import os
from datetime import datetime
import logging
from typing import Dict, Any, Optional

from core.paths import DATA_DIR

class DataLogger:
    """
    Service for logging user trades and application events (e.g., readiness).
    """

    def __init__(self):
        self.logs_dir = os.path.join(DATA_DIR, "logs")
        self.trades_dir = os.path.join(DATA_DIR, "trades")
        self._ensure_directories()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _ensure_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.trades_dir, exist_ok=True)

    def log_trade(self, order_data: Dict[str, Any], status: str, initial_balance: float, final_balance: float):
        """
        Log trade details to a JSON file.
        
        Args:
            order_data: The order response or details.
            status: final status of the trade (FILLED, FAILED, etc.)
            initial_balance: User balance before trade
            final_balance: User balance after trade
        """
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "status": status,
                "initial_balance": initial_balance,
                "final_balance": final_balance,
                "order_details": order_data
            }
            
            # Use a daily log file for trades
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(self.trades_dir, f"trades_{date_str}.json")
            
            self._append_to_json_file(file_path, log_entry)
            self.logger.info(f"Trade logged to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")

    def log_app_ready(self, start_time: float, ready_time: float, password_entry_duration: float = 0.0):
        """
        Log application readiness duration.
        
        Args:
            start_time: Timestamp when app started
            ready_time: Timestamp when app became ready
            password_entry_duration: Time spent entering password
        """
        try:
            total_duration = ready_time - start_time
            # Effective duration is total time minus user interaction time
            effective_duration = total_duration - password_entry_duration
            
            timestamp = datetime.fromtimestamp(ready_time).isoformat()
            
            log_entry = {
                "event": "APP_READY",
                "timestamp": timestamp,
                "total_duration_seconds": total_duration,
                "password_entry_duration_seconds": password_entry_duration,
                "effective_startup_duration_seconds": effective_duration,
                "start_timestamp": start_time,
                "ready_timestamp": ready_time
            }
            
            file_path = os.path.join(self.logs_dir, "app_performance.json")
            self._append_to_json_file(file_path, log_entry)
            self.logger.info(f"App readiness logged: {effective_duration:.4f}s (User interaction: {password_entry_duration:.4f}s)")
            
        except Exception as e:
            self.logger.error(f"Failed to log app readiness: {e}")

    def _append_to_json_file(self, file_path: str, data: Dict[str, Any]):
        """Append data to a JSON list in a file."""
        try:
            existing_data = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():
                            existing_data = json.loads(content)
                            if not isinstance(existing_data, list):
                                existing_data = [existing_data] # Convert to list if it was a single object (legacy support/safety)
                except json.JSONDecodeError:
                    self.logger.warning(f"Could not decode {file_path}, starting fresh.")
            
            existing_data.append(data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            # Fallback to appending line by line if JSON array fails/is too big (though for this app, JSON array is cleaner for reading back)
            # For now, just logging the error. 
            self.logger.error(f"Error writing to {file_path}: {e}")

# Global instance
_logger_instance = None

def get_data_logger():
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = DataLogger()
    return _logger_instance
