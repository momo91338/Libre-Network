import sys
import os
import json
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QFrame, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from main import LibreNode

class LibreGUI(QMainWindow):
    def __init__(self, node: LibreNode):
        super().__init__()
        self.node = node
        self.setWindowTitle("Libre Network - Architectural Upgrade")
        self.resize(1100, 700)
        self.setup_ui()
        
        # Timers for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_ui)
        self.update_timer.start(2000)

    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0f111a; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #e6e6e6; }
            #Sidebar { background-color: #1a1d2e; border-right: 1px solid #2d314d; min-width: 220px; }
            QPushButton#NavBtn { text-align: left; padding: 12px; border: none; border-radius: 5px; color: #a0a0b8; }
            QPushButton#NavBtn:hover { background-color: #2d325a; color: #fff; }
            QPushButton#NavBtn[active="true"] { background-color: #3d5afe; color: #fff; }
            #Card { background-color: #1a1d2e; border: 1px solid #2d314d; border-radius: 10px; padding: 15px; }
            QLabel#Header { font-size: 24px; font-weight: bold; }
            QLabel#StatVal { font-size: 28px; font-weight: bold; color: #3d5afe; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("LIBRE")
        logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #3d5afe; padding: 20px;")
        sidebar_layout.addWidget(logo)

        self.nav_btns = []
        for name in ["Dashboard", "Wallet", "Mining", "Settings"]:
            btn = QPushButton(f"  {name}")
            btn.setObjectName("NavBtn")
            btn.clicked.connect(self.show_page)
            sidebar_layout.addWidget(btn)
            self.nav_btns.append(btn)
        
        sidebar_layout.addStretch()
        layout.addWidget(sidebar)

        # Content Area
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.init_dashboard()
        self.init_settings()
        
        self.nav_btns[0].setProperty("active", True)

    def init_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        header = QLabel("Network Dashboard")
        header.setObjectName("Header")
        layout.addWidget(header)

        # Stats Cards
        stats_layout = QHBoxLayout()
        self.height_card = self.create_stat_card("Block Height", "0")
        self.peer_card = self.create_stat_card("Connected Peers", "0")
        self.state_card = self.create_stat_card("State Hash", "0x000...")
        stats_layout.addWidget(self.height_card)
        stats_layout.addWidget(stats_layout.itemAt(stats_layout.count()-1).widget()) # Dummy
        stats_layout.addWidget(self.peer_card)
        layout.addLayout(stats_layout)

        # Peers Table
        layout.addWidget(QLabel("Active Peers"))
        self.peers_table = QTableWidget(0, 3)
        self.peers_table.setHorizontalHeaderLabels(["Node ID", "Address", "Last Seen"])
        self.peers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.peers_table)

        self.stack.addWidget(page)

    def init_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        layout.addWidget(QLabel("Node Configuration"))
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Network Port:"))
        self.port_input = QLineEdit(str(self.node.port))
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)

        save_btn = QPushButton("Save & Restart Network")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        self.stack.addWidget(page)

    def create_stat_card(self, title, val):
        card = QFrame()
        card.setObjectName("Card")
        l = QVBoxLayout(card)
        l.addWidget(QLabel(title))
        v = QLabel(val)
        v.setObjectName("StatVal")
        l.addWidget(v)
        card.val_label = v
        return card

    def show_page(self):
        sender = self.sender()
        idx = self.nav_btns.index(sender)
        self.stack.setCurrentIndex(idx if idx < self.stack.count() else 0)
        for btn in self.nav_btns:
            btn.setProperty("active", btn == sender)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def refresh_ui(self):
        # Update Stats
        height = self.node.blockchain.get_height()
        peers = self.node.p2p.get_peer_count()
        latest = self.node.storage.get_latest_block()
        
        self.height_card.val_label.setText(str(height))
        self.peer_card.val_label.setText(str(peers))
        
        # Update Peers Table
        peer_list = self.node.p2p.get_peer_list()
        self.peers_table.setRowCount(0)
        for p in peer_list:
            row = self.peers_table.rowCount()
            self.peers_table.insertRow(row)
            self.peers_table.setItem(row, 0, QTableWidgetItem(p["node_id"][:12] + "..."))
            self.peers_table.setItem(row, 1, QTableWidgetItem(f"{p['ip']}:{p['port']}"))
            self.peers_table.setItem(row, 2, QTableWidgetItem("Just now"))

    def save_settings(self):
        try:
            new_port = int(self.port_input.text())
            self.node.config.port = new_port
            QMessageBox.information(self, "Settings Saved", "Port updated. Please restart the application.")
        except:
            QMessageBox.warning(self, "Invalid Port", "Please enter a valid numeric port.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    node = LibreNode()
    node.start()
    gui = LibreGUI(node)
    gui.show()
    sys.exit(app.exec())
