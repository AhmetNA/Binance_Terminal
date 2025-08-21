import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QProgressBar)
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
import datetime

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from services.portfolio_tracker import portfolio_tracker

"""
portfolio_widget.py
Portföy durumunu gösteren GUI widget'ı.
"""

class PortfolioWidget(QWidget):
    refresh_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Portföy Durumu")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.clicked.connect(self.refresh_portfolio)
        
        self.auto_refresh_btn = QPushButton("Otomatik: KAPALI")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        self.auto_refresh = False
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.auto_refresh_btn)
        header_layout.addWidget(self.refresh_btn)
        
        # Portfolio Summary
        summary_group = QGroupBox("Özet")
        summary_layout = QVBoxLayout()
        
        # Value displays
        values_layout = QHBoxLayout()
        
        self.total_value_label = QLabel("Toplam Değer: 0.00 USDT")
        self.usdt_balance_label = QLabel("USDT Bakiye: 0.00")
        self.daily_pnl_label = QLabel("Günlük K/Z: 0.00 USDT")
        
        values_layout.addWidget(self.total_value_label)
        values_layout.addWidget(self.usdt_balance_label)
        values_layout.addWidget(self.daily_pnl_label)
        
        summary_layout.addLayout(values_layout)
        
        # Progress bar for portfolio diversity
        self.diversity_label = QLabel("Diversifikasyon:")
        self.diversity_bar = QProgressBar()
        self.diversity_bar.setMaximum(100)
        
        summary_layout.addWidget(self.diversity_label)
        summary_layout.addWidget(self.diversity_bar)
        
        summary_group.setLayout(summary_layout)
        
        # Holdings Table
        holdings_group = QGroupBox("Holdings")
        holdings_layout = QVBoxLayout()
        
        self.holdings_table = QTableWidget()
        self.holdings_table.setColumnCount(5)
        self.holdings_table.setHorizontalHeaderLabels([
            "Coin", "Miktar", "Fiyat", "Değer (USDT)", "Oran (%)"
        ])
        
        holdings_layout.addWidget(self.holdings_table)
        holdings_group.setLayout(holdings_layout)
        
        # Recent Activity
        activity_group = QGroupBox("Son İşlemler")
        activity_layout = QVBoxLayout()
        
        self.activity_label = QLabel("Son 24 saat: 0 işlem")
        self.last_update_label = QLabel("Son güncelleme: -")
        
        activity_layout.addWidget(self.activity_label)
        activity_layout.addWidget(self.last_update_label)
        
        activity_group.setLayout(activity_layout)
        
        # Add all groups to main layout
        layout.addLayout(header_layout)
        layout.addWidget(summary_group)
        layout.addWidget(holdings_group)
        layout.addWidget(activity_group)
        
        self.setLayout(layout)
        
        # Initial data load
        self.refresh_portfolio()
    
    def setup_timer(self):
        """Otomatik yenileme timer'ını ayarlar."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_portfolio)
        # 30 saniye interval
        self.timer.setInterval(30000)
    
    def toggle_auto_refresh(self):
        """Otomatik yenilemeyi açar/kapatır."""
        self.auto_refresh = not self.auto_refresh
        
        if self.auto_refresh:
            self.auto_refresh_btn.setText("Otomatik: AÇIK")
            self.auto_refresh_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            self.timer.start()
        else:
            self.auto_refresh_btn.setText("Otomatik: KAPALI")
            self.auto_refresh_btn.setStyleSheet("")
            self.timer.stop()
    
    def refresh_portfolio(self):
        """Portföy verilerini yeniler."""
        try:
            # Get portfolio summary
            summary = portfolio_tracker.get_portfolio_summary()
            
            if summary:
                self.update_summary_display(summary)
                self.update_holdings_table(summary)
                self.update_activity_display(summary)
            
            self.last_update_label.setText(
                f"Son güncelleme: {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            print(f"Error refreshing portfolio: {e}")
    
    def update_summary_display(self, summary):
        """Özet bilgileri günceller."""
        current_value = summary.get('current_value', 0)
        current_usdt = summary.get('current_usdt', 0)
        daily_pnl = summary.get('daily_pnl', 0)
        
        self.total_value_label.setText(f"Toplam Değer: {current_value:.2f} USDT")
        self.usdt_balance_label.setText(f"USDT Bakiye: {current_usdt:.2f}")
        
        # Color code P&L
        pnl_color = "green" if daily_pnl >= 0 else "red"
        pnl_sign = "+" if daily_pnl >= 0 else ""
        self.daily_pnl_label.setText(f"Günlük K/Z: {pnl_sign}{daily_pnl:.2f} USDT")
        self.daily_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")
        
        # Update diversity (USDT percentage)
        if current_value > 0:
            usdt_percentage = (current_usdt / current_value) * 100
            diversity_score = min(100 - usdt_percentage, 100)
            self.diversity_bar.setValue(int(diversity_score))
            self.diversity_label.setText(f"Diversifikasyon: {diversity_score:.1f}%")
        else:
            self.diversity_bar.setValue(0)
    
    def update_holdings_table(self, summary):
        """Holdings tablosunu günceller."""
        try:
            current_portfolio = portfolio_tracker.get_current_portfolio()
            holdings = current_portfolio.get('holdings', {})
            
            self.holdings_table.setRowCount(len(holdings))
            
            row = 0
            for symbol, data in holdings.items():
                amount = data.get('amount', 0)
                price = data.get('price', 0)
                value_usdt = data.get('value_usdt', 0)
                
                # Calculate percentage
                total_value = current_portfolio.get('total_value_usdt', 1)
                percentage = (value_usdt / total_value) * 100 if total_value > 0 else 0
                
                # Add to table
                self.holdings_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.holdings_table.setItem(row, 1, QTableWidgetItem(f"{amount:.6f}"))
                self.holdings_table.setItem(row, 2, QTableWidgetItem(f"{price:.6f}"))
                self.holdings_table.setItem(row, 3, QTableWidgetItem(f"{value_usdt:.2f}"))
                self.holdings_table.setItem(row, 4, QTableWidgetItem(f"{percentage:.1f}%"))
                
                row += 1
            
            # Resize columns to content
            self.holdings_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating holdings table: {e}")
    
    def update_activity_display(self, summary):
        """Aktivite bilgilerini günceller."""
        try:
            trades_summary = summary.get('trades_summary', {})
            today_trades = trades_summary.get('today_count', 0)
            
            self.activity_label.setText(f"Bugün: {today_trades} işlem")
            
        except Exception as e:
            print(f"Error updating activity display: {e}")
    
    def closeEvent(self, event):
        """Widget kapatılırken timer'ı durdur."""
        if hasattr(self, 'timer'):
            self.timer.stop()
        event.accept()
