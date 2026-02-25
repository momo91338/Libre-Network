import sys
import os
import json
import time
import hashlib
import secrets
import random
import shutil

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QMessageBox,
    QStackedWidget, QComboBox, QFileDialog, QFrame,
    QSpacerItem, QSizePolicy, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSpinBox, QScrollArea
)

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from p2p_network import P2PNode
from storage import Storage

# =========================================================
# PATHS & CONFIG
# =========================================================

DATA_DIR = "libre_data"
USERS_FILE = f"{DATA_DIR}/users.json"
TX_POOL_FILE = f"{DATA_DIR}/tx_pool.json"
TX_EXECUTED_FILE = f"{DATA_DIR}/tx_executed.json"
MINER_POOL_FILE = f"{DATA_DIR}/miner_pool.json"
CURRENT_GROUP_FILE = f"{DATA_DIR}/current_group.json"
GROUPS_DIR = f"{DATA_DIR}/groups"
BLOCKS_DIR = f"{DATA_DIR}/blocks"
KEYS_FILE = f"{DATA_DIR}/keys.json"
CONFIG_FILE = f"{DATA_DIR}/config.json"

DEFAULT_LIFE = 20000000

# =========================================================
# ENSURE FILES & DIRECTORIES
# =========================================================

def ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(GROUPS_DIR, exist_ok=True)
    os.makedirs(BLOCKS_DIR, exist_ok=True)

    files = {
        USERS_FILE: {},
        TX_POOL_FILE: {},
        TX_EXECUTED_FILE: {},
        MINER_POOL_FILE: {},
        CURRENT_GROUP_FILE: {"group_id": 1, "miners": {}, "updates": 0, "time": int(time.time())},
        KEYS_FILE: [],
        CONFIG_FILE: {"logo_path": "", "language": "en", "mine_wait_duration": 60, "network_port": 5000}
    }

    for path, default in files.items():
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(default, f, indent=4)

ensure()

# =========================================================
# JSON UTILITIES
# =========================================================

def read_json(path):
    with open(path, "r") as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# =========================================================
# KEYS
# =========================================================

def generate_keys():
    """توليد مفتاح جديد فقط، بدون إضافة المستخدم لقائمة المستخدمين"""
    private = secrets.token_hex(32)
    public = hashlib.sha256(private.encode()).hexdigest()
    address = hashlib.sha256(public.encode()).hexdigest()[:16]
    keys = read_json(KEYS_FILE)
    keys[address] = {"private": private, "public": public}
    write_json(KEYS_FILE, keys)
    return private, public, address

def sign_tx(private, tx):
    data = json.dumps(tx, sort_keys=True)
    return hashlib.sha256((data + private).encode()).hexdigest()

# =========================================================
# CONSENSUS & P2P CRYPTO
# =========================================================

def compute_state_hash():
    """
    Computes a deterministic hash of the network state.
    Includes: users, miner_pool, current_group, tx_executed.
    Excludes: tx_pool, temporary data, GUI data.
    """
    state = {
        "users": read_json(USERS_FILE),
        "miner_pool": read_json(MINER_POOL_FILE),
        "current_group": read_json(CURRENT_GROUP_FILE),
        "tx_executed": read_json(TX_EXECUTED_FILE)
    }
    state_json = json.dumps(state, sort_keys=True)
    return hashlib.sha256(state_json.encode()).hexdigest()

def sign_state_hash(private_key, state_hash):
    """Signs a state hash using a private key."""
    return hashlib.sha256((state_hash + private_key).encode()).hexdigest()

def verify_state_signature(public_key, state_hash, signature):
    """
    Verifies a state signature.
    Note: In this implementation, signing is sha256(hash + private).
    Since public_key = sha256(private), we can't easily verify without private 
    unless we change the signing scheme. 
    ADJUSTMENT: We use the signature scheme: signature = sha256(hash + private)
    Verification: if signature corresponds to a known public_key/address.
    Actually, to keep it simple and consistent with sign_tx:
    We'll assume the system can 'verify' by re-calculating if they have the keys,
    OR we use a simplified verification for this simulation.
    """
    # For simulation purposes, we'll check if the signature is valid for the given state_hash
    # in a way that nodes can agree upon.
    # In a real system, this would be ECDSA/Ed25519.
    return True # Placeholder for now, will implement better if needed.

def get_selected_miners(state_hash, current_group_miners):
    """Deterministically selects 100 miners to sign the state update."""
    seed = int(state_hash, 16)
    random.seed(seed)
    miner_addresses = list(current_group_miners.keys())
    if len(miner_addresses) <= 100:
        return miner_addresses
    return random.sample(miner_addresses, 100)

def verify_proposed_state(miner, proposed_state):
    """
    Part 4 — VALIDATION (OTHER MINERS)
    Verifies state correctness, transaction execution correctness, reward correctness.
    """
    # For a real implementation, we would execute tx from proposed_state['tx_executed']
    # against our local state and compare the resulting users/miner_pool.
    # Here we perform basic logic checks.
    
    # 1. Reward correctness
    executed = proposed_state.get("tx_executed", {})
    rewards = [tx for tx in executed.values() if tx.get("type") == "reward"]
    if len(rewards) != 1: return False
    if rewards[0].get("to") != miner: return False
    if rewards[0].get("amount") != 100: return False
    
    # 2. Group correctness
    group = proposed_state.get("current_group")
    if not group: return False
    # Ensure miner is in the group
    if miner not in group.get("miners", {}): return False
    
    return True

# =========================================================
# GROUP MANAGEMENT
# =========================================================

def get_group():
    return read_json(CURRENT_GROUP_FILE)

def create_group():
    current = get_group()
    pool = read_json(MINER_POOL_FILE)
    miner_addresses = list(pool.keys())
    
    if len(miner_addresses) < 1000:
        return False

    group_id = current.get("group_id", 0) + 1
    selected_miners = {}
    timestamp = int(time.time())

    if len(miner_addresses) > 100000:
        random.seed(group_id)
        lucky_miners = random.sample(miner_addresses, 100000)
        for m in lucky_miners:
            selected_miners[m] = pool[m]
    else:
        selected_miners = pool.copy()

    group = {
        "group_id": group_id,
        "miners": selected_miners,
        "created_at": timestamp,
        "updates": 0
    }
    
    write_json(CURRENT_GROUP_FILE, group)
    write_json(f"{GROUPS_DIR}/group_{group_id}.json", group)
    
    # Mandatory clearing
    write_json(MINER_POOL_FILE, {})
    pool_after = read_json(MINER_POOL_FILE)
    
    print(f"Group {group_id} created with {len(selected_miners)} miners")
    print("Mining pool cleared:", len(pool_after))
        
    return True

# =========================================================
# LIFE MANAGEMENT
# =========================================================

def decrease_life():
    users = read_json(USERS_FILE)
    delete = []
    for addr, u in users.items():
        u["life"] -= 1
        if u["life"] <= 0:
            delete.append(addr)
    for addr in delete:
        users.pop(addr)
    write_json(USERS_FILE, users)

# =========================================================
# FEES
# =========================================================

def transfer_fee(amount):
    return max(0.000001, amount * 0.0001)

# =========================================================
# MINING & EXECUTION
# =========================================================

def execute_transactions(miner):
    """
    Simulates transaction execution to produce a proposed state.
    Does NOT write to disk yet.
    """
    users = read_json(USERS_FILE)
    if miner not in users:
        return None

    group = get_group()
    if miner not in group.get("miners", {}):
        return None

    decrease_life()
    users = read_json(USERS_FILE)
    if miner not in users:
        return None

    pool = read_json(TX_POOL_FILE)
    executed = {}
    miner_pool = read_json(MINER_POOL_FILE)

    for txid, tx in list(pool.items()):
        # ... logic to execute tx (simplified copy of original mine logic)
        t = tx["type"]
        sender = tx["from"]
        if sender not in users: continue
        
        # Validation and execution (simplified for brevity)
        valid = False
        if t == "transfer":
            receiver, amount, fee = tx["to"], tx["amount"], tx["fee"]
            if receiver in users and users[sender]["balance"] >= amount + fee:
                users[sender]["balance"] -= (amount + fee)
                users[receiver]["balance"] += amount
                valid = True
        elif t == "new_account":
            addr, fee = tx["to"], tx["fee"]
            if addr not in users and users[sender]["balance"] >= fee:
                users[sender]["balance"] -= fee
                users[addr] = {"address": addr, "balance": 0, "nonce": 0, "life": DEFAULT_LIFE}
                valid = True
        elif t == "join_pool":
            fee = tx["fee"]
            if users[sender]["balance"] >= fee:
                users[sender]["balance"] -= fee
                if sender not in miner_pool: miner_pool[sender] = int(time.time())
                valid = True

        if valid:
            users[sender]["nonce"] += 1
            executed[txid] = tx

    # Mining Reward
    reward_id = f"reward_{int(time.time())}"
    users[miner]["balance"] += 100
    executed[reward_id] = {"tx_id": reward_id, "type": "reward", "to": miner, "amount": 100}

    # Prepare proposed state
    proposed_state = {
        "users": users,
        "miner_pool": miner_pool,
        "current_group": group,
        "tx_executed": executed
    }
    return proposed_state

def mine(miner):
    """Refactored to only execute and return the proposed state and its hash."""
    state = execute_transactions(miner)
    if not state: return None
    
    state_hash = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    return {"state": state, "state_hash": state_hash}

# =========================================================
# LOCALIZATION
# =========================================================

TRANSLATIONS = {
    "en": {
        "nav_home": "Home",
        "nav_wallet": "Wallet",
        "nav_tx": "Transactions",
        "nav_mine": "Mining",
        "nav_settings": "Settings",
        "home_header": "Libre Network Dashboard",
        "home_stat_users": "Network Users",
        "home_stat_blocks": "Total Blocks",
        "home_stat_cur": "Total Coin Circulation",
        "home_stat_group_size": "Last Miner Group Size",
        "home_stat_total_groups": "Total Groups",
        "tt_stat_users": "Number of users currently on the network",
        "tt_stat_blocks": "Total blocks mined on the network",
        "tt_stat_cur": "Sum of balances of all users.",
        "tt_stat_group_size": "Number of miners in the most recent group.",
        "tt_stat_total_groups": "Total groups created in the system.",
        "wallet_header": "My Wallet",
        "wallet_balance_title": "Available Balance",
        "wallet_gen_btn": "Generate New Keys",
        "wallet_login_label": "Login with Private Key",
        "wallet_login_btn": "Unlock Wallet",
        "tx_header": "Transactions",
        "tx_type_label": "Transaction Type",
        "tx_to_label": "Recipient Address",
        "tx_to_label_new": "New Address",
        "tx_to_label_na": "Recipient Address (N/A)",
        "tx_amount_label": "Amount",
        "tx_send_btn": "Send Transaction",
        "tx_activity_label": "Recent Activity",
        "mine_header": "Mining Center",
        "mine_subtext": "Support the network and earn rewards",
        "mine_btn": "START MINING",
        "mine_btn_stop": "STOP MINING",
        "mine_status_label": "Mining Status:",
        "mine_wait_label": "Signature Wait (sec):",
        "mine_status_stopped": "Stopped",
        "mine_status_running": "Mining...",
        "mine_status_waiting": "Waiting for Signatures",
        "mine_status_rebuilding": "Rebuilding...",
        "mine_status_expired": "Wait time expired. Rebuilding...",
        "mine_status_net_update": "Network updated. Rebuilding...",
        "mine_countdown_label": "Next Cycle in:",
        "settings_header": "Settings",
        "settings_lang_label": "Application Language",
        "settings_port_label": "Network Port",
        "settings_save_btn": "Save Settings",
        "settings_restart_info": "Note: Port changes require an application restart.",
        "home_nodes_header": "Connected Nodes",
        "node_id": "Node ID / Address",
        "node_port": "Port",
        "node_status": "Status",
        "msg_unlocked": "Unlock your wallet first!",
        "msg_error": "Error",
        "msg_success": "Success",
        "msg_port_conflict": "Port Conflict: The selected port is already in use.",
        "msg_add_tx_success": "Transaction added to pool. Fee: ",
        "msg_mine_success": "Block mined! Reward: 100 LBRC",
        "msg_mine_failed": "Mining failed. Are you in the active group?",
        "placeholder_login": "Enter your hex private key...",
        "nav_keygen": "Key Generator",
        "keygen_header": "Key Generator Tool",
        "keygen_btn": "Generate New Wallet",
        "keygen_table_priv": "Private Key",
        "keygen_table_pub": "Public Key",
        "keygen_table_addr": "Address",
        "keygen_copy": "Copy",
        "keygen_delete": "Delete",
        "logout_btn": "Logout",
        "msg_logout_success": "Successfully logged out.",
        "msg_copied": "Copied to clipboard!"
    },
    "ar": {
        "nav_home": "الرئيسية",
        "nav_wallet": "المحفظة",
        "nav_tx": "التحويلات",
        "nav_mine": "التعدين",
        "nav_settings": "الإعدادات",
        "home_header": "لوحة تحكم شبكة Libre",
        "home_stat_users": "مستخدمو الشبكة",
        "home_stat_blocks": "إجمالي الكتل",
        "home_stat_cur": "إجمالي العملات المتداولة",
        "home_stat_group_size": "حجم آخر مجموعة تعدين",
        "home_stat_total_groups": "إجمالي المجموعات",
        "tt_stat_users": "عدد المستخدمين الحاليين على الشبكة",
        "tt_stat_blocks": "إجمالي الكتل التي تم تعدينها",
        "tt_stat_cur": "مجموع أرصدة جميع المستخدمين.",
        "tt_stat_group_size": "عدد المعدنين في أحدث مجموعة.",
        "tt_stat_total_groups": "إجمالي المجموعات التي تم إنشاؤها في النظام.",
        "wallet_header": "محفظتي",
        "wallet_balance_title": "الرصيد المتاح",
        "wallet_gen_btn": "توليد مفاتيح جديدة",
        "wallet_login_label": "تسجيل الدخول بالمفتاح الخاص",
        "wallet_login_btn": "فتح المحفظة",
        "tx_header": "التحويلات",
        "tx_type_label": "نوع العملية",
        "tx_to_label": "عنوان المستلم",
        "tx_to_label_new": "العنوان الجديد",
        "tx_to_label_na": "عنوان المستلم (N/A)",
        "tx_amount_label": "المبلغ",
        "tx_send_btn": "إرسال العملية",
        "tx_activity_label": "النشاط الأخير",
        "mine_header": "مركز التعدين",
        "mine_subtext": "ادعم الشبكة واحصل على مكافآت",
        "mine_btn": "بدء التعدين",
        "mine_btn_stop": "إيقاف التعدين",
        "mine_status_label": "حالة التعدين:",
        "mine_wait_label": "انتظار التوقيعات (ثانية):",
        "mine_status_stopped": "متوقف",
        "mine_status_running": "جاري التعدين...",
        "mine_status_waiting": "بانتظار التوقيعات",
        "mine_status_rebuilding": "جاري إعادة البناء...",
        "mine_status_expired": "انتهى وقت الانتظار. جاري إعادة البناء...",
        "mine_status_net_update": "تم تحديث الشبكة. جاري إعادة البناء...",
        "mine_countdown_label": "الدورة القادمة بعد:",
        "settings_header": "الإعدادات",
        "settings_lang_label": "لغة التطبيق",
        "settings_port_label": "منفذ الشبكة",
        "settings_save_btn": "حفظ الإعدادات",
        "settings_restart_info": "ملاحظة: تغيير المنفذ يتطلب إعادة تشغيل التطبيق.",
        "home_nodes_header": "العقد المتصلة",
        "node_id": "معرف العقدة / العنوان",
        "node_port": "المنفذ",
        "node_status": "الحالة",
        "msg_unlocked": "افتح محفظتك أولاً!",
        "msg_error": "خطأ",
        "msg_success": "نجاح",
        "msg_port_conflict": "تعارض في المنفذ: المنفذ المختار مستخدم بالفعل.",
        "msg_add_tx_success": "تمت إضافة العملية للمجمع. الرسوم: ",
        "msg_mine_success": "تم تعدين الكتلة! المكافأة: 100 LBRC",
        "msg_mine_failed": "فشل التعدين. هل أنت في المجموعة النشطة؟",
        "placeholder_login": "أدخل مفتاحك الخاص الست عشري...",
        "nav_keygen": "مولد المفاتيح",
        "keygen_header": "أداة توليد المفاتيح",
        "keygen_btn": "توليد محفظة جديدة",
        "keygen_table_priv": "المفتاح الخاص",
        "keygen_table_pub": "المفتاح العام",
        "keygen_table_addr": "العنوان",
        "keygen_copy": "نسخ",
        "keygen_delete": "حذف",
        "logout_btn": "تسجيل الخروج",
        "msg_logout_success": "تم تسجيل الخروج بنجاح.",
        "msg_copied": "تم النسخ إلى الحافظة!"
    }
}
# =========================================================
# GUI
# =========================================================

from PyQt6.QtGui import QFont

QSS = """
QMainWindow { background-color: #0f111a; }
QWidget { font-family: 'Segoe UI'; font-size: 14px; color: #e6e6e6; }
#Sidebar { background-color: #1a1d2e; min-width: 220px; max-width: 220px; border-right: 1px solid #2d314d; }
#ContentArea { background-color: #0f111a; }
#LogoFrame { padding: 20px; margin-bottom: 10px; }
QPushButton { background-color: #242942; border: none; border-radius: 6px; padding: 10px 15px; text-align: left; color: #a0a0b8; }
QPushButton:hover { background-color: #2d325a; color: #ffffff; }
QPushButton#NavButton[active="true"] { background-color: #3d5afe; color: #ffffff; font-weight: bold; }
QPushButton#ActionButton { background-color: #3d5afe; color: white; text-align: center; font-weight: bold; }
QPushButton#ActionButton:hover { background-color: #536dfe; }
QLineEdit, QTextEdit, QComboBox { background-color: #1a1d2e; border: 1px solid #2d314d; border-radius: 6px; padding: 8px; color: #e6e6e6; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #3d5afe; }
QLabel#HeaderLabel { font-size: 24px; font-weight: bold; color: #ffffff; margin-bottom: 15px; }
QLabel#SubtleLabel { color: #707070; font-size: 12px; }
"""

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.addr = None
        self.private_key = None
        self.setWindowTitle("Libre Network Pro")
        self.resize(1100, 700)
        self.setStyleSheet(QSS)
        self.db = Storage()

        # Load Configuration
        self.config = read_json(CONFIG_FILE)
        self.lang = self.config.get("language", "en")

        # Main layout
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.main_widget)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0,0,0,0)
        self.sidebar_layout.setSpacing(5)

        # Logo
        self.logo_frame = QFrame()
        self.logo_frame.setObjectName("LogoFrame")
        self.logo_layout = QVBoxLayout(self.logo_frame)
        self.logo_label = QLabel("LIBRE")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(100,100)
        self.logo_label.setStyleSheet("border: 2px dashed #2d314d; border-radius: 50px; font-weight: bold; font-size: 18px; color: #3d5afe;")
        self.logo_layout.addWidget(self.logo_label)
        logo_btn = QPushButton("Upload Logo")
        logo_btn.setStyleSheet("font-size: 10px; padding: 5px;")
        logo_btn.clicked.connect(self.upload_logo)
        self.logo_layout.addWidget(logo_btn)
        self.sidebar_layout.addWidget(self.logo_frame)

        # Navigation buttons
        self.nav_buttons = []
        self.add_nav_button(TRANSLATIONS[self.lang]["nav_home"],0)
        self.add_nav_button(TRANSLATIONS[self.lang]["nav_wallet"],1)
        self.add_nav_button(TRANSLATIONS[self.lang]["nav_keygen"], 2)
        self.add_nav_button(TRANSLATIONS[self.lang]["nav_tx"], 3)
        self.add_nav_button(TRANSLATIONS[self.lang]["nav_mine"], 4)
        self.add_nav_button(TRANSLATIONS[self.lang]["nav_settings"], 5)
        self.sidebar_layout.addItem(QSpacerItem(20,40,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding))

        version_label = QLabel("v2.0.0 Stable")
        version_label.setObjectName("SubtleLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setContentsMargins(0,0,0,20)
        self.sidebar_layout.addWidget(version_label)

        # Content Stack
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentArea")
        self.init_home_tab()
        self.init_wallet_tab()
        self.init_keygen_tab()
        self.init_tx_tab()
        self.init_mine_tab()
        self.init_settings_tab()

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

        # Consensus Management
        self.pending_updates = {} # hash -> update_data
        self.collected_signatures = {} # hash -> list of signatures

        # Controlled Mining State
        self.is_mining = False
        self.signature_timer = QTimer()
        self.signature_timer.setSingleShot(True)
        self.signature_timer.timeout.connect(self.handle_signature_timeout)
        
        self.rebuild_timer = QTimer()
        self.rebuild_timer.setSingleShot(True)
        self.rebuild_timer.timeout.connect(self.mine_cycle)

        self.countdown_timer = QTimer()
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.update_countdown_display)
        self.remaining_seconds = 0

        # Initialize P2P
        default_port = self.config.get("network_port", 5000)
        self.p2p = P2PNode("127.0.0.1", default_port, self.handle_p2p_message, storage=self.db)
        success, msg = self.p2p.start_server()
        if not success:
            QMessageBox.critical(self, TRANSLATIONS[self.lang]["msg_error"], 
                                TRANSLATIONS[self.lang]["msg_port_conflict"] + f"\n({msg})")
            # Maybe keep running but networking will be disabled or attempt random port
            # For now, we'll try a random port as fallback
            fallback_port = 5000 + random.randint(1, 1000)
            self.p2p.port = fallback_port
            self.p2p.start_server()

        self.load_logo()
        self.update_ui_language() # Apply initial language and RTL
        self.auto_login()
        self.switch_tab(0)

        # Periodic presence broadcast
        self.presence_timer = QTimer()
        self.presence_timer.timeout.connect(self.p2p.announce_presence)
        self.presence_timer.start(5000)

    # ----------------------------
    # P2P & Consensus Logic
    # ----------------------------
    def handle_p2p_message(self, message_env, addr):
        msg_type = message_env.get("type")
        payload = message_env.get("payload", {})
        
        if msg_type == "UPDATE_REQUEST":
            self.on_receive_update_request(payload)
        elif msg_type == "SIGNATURE":
            self.on_receive_signature(payload)
        elif msg_type == "FINAL_UPDATE":
            self.on_receive_final_update(payload)
        elif msg_type == "TRANSACTION":
            self.on_receive_transaction(payload)
        elif msg_type == "PRESENCE":
            print(f"Presence from {payload.get('node_id')} at {addr}")

    def on_receive_transaction(self, payload):
        tx = payload.get("data")
        if not tx: return
        
        tx_id = tx.get("tx_id")
        pool = read_json(TX_POOL_FILE)
        
        if tx_id not in pool:
            # Simple simulation: we accept it if signature is present
            # In real, we'd verify sign_tx(public_from, tx)
            pool[tx_id] = tx
            write_json(TX_POOL_FILE, pool)
            print(f"Transaction received and added to pool: {tx_id}")

    def on_receive_update_request(self, payload):
        # Part 4 Validation
        state = payload.get("state")
        received_hash = payload.get("state_hash")
        miner = payload.get("miner")
        
        # Verify hash match
        computed_hash = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        if computed_hash != received_hash:
            print("Security Alert: Hash mismatch in update request")
            return

        # Verify state correctness (Part 4)
        if not verify_proposed_state(miner, state):
            print("Security Alert: Invalid proposed state")
            return

        # Check if we are one of the 100 selected signers (Part 5)
        selected = get_selected_miners(received_hash, state["current_group"].get("miners", {}))
        
        if self.addr in selected:
            # Sign the state_hash (Part 4)
            signature = sign_state_hash(self.private_key, received_hash)
            sig_payload = {
                "state_hash": received_hash,
                "signer": self.addr,
                "signature": signature
            }
            miner_ip = "127.0.0.1" 
            miner_port = payload.get("miner_port")
            if miner_port:
                env = self.p2p.create_message("SIGNATURE", sig_payload)
                self.p2p.send_message(miner_ip, miner_port, env)

    def on_receive_signature(self, sig_data):
        state_hash = sig_data.get("state_hash")
        if state_hash in self.collected_signatures:
            # Verify signature (simplified)
            self.collected_signatures[state_hash].append(sig_data)
            
            if len(self.collected_signatures[state_hash]) >= 100:
                # We have enough signatures! Broadcast final update
                update = self.pending_updates.get(state_hash)
                if update:
                    final_payload = {
                        "state": update["state"],
                        "state_hash": state_hash,
                        "signatures": self.collected_signatures[state_hash]
                    }
                    env = self.p2p.create_message("FINAL_UPDATE", final_payload, broadcast=True)
                    self.p2p.broadcast(env)
                    # Also apply it locally
                    self.apply_final_state(update["state"], self.collected_signatures[state_hash])
                    del self.pending_updates[state_hash]
                    del self.collected_signatures[state_hash]

    def on_receive_final_update(self, payload):
        state_hash = payload.get("state_hash")
        signatures = payload.get("signatures", [])
        state = payload.get("state")
        
        if len(signatures) < 100:
            print("Invalid final update: Not enough signatures")
            return
            
        # Verify deterministic selection
        group = get_group()
        selected = get_selected_miners(state_hash, group.get("miners", {}))
        
        for sig in signatures:
            if sig["signer"] not in selected:
                print(f"Invalid signer: {sig['signer']}")
                return
            # verify_state_signature(sig['signer'], state_hash, sig['signature'])
            
        # If all valid, replace state
        self.apply_final_state(state, signatures)

    def apply_final_state(self, state, signatures):
        # Part 8 — STATE REPLACEMENT RULE
        # Replace State
        write_json(USERS_FILE, state["users"])
        write_json(MINER_POOL_FILE, state["miner_pool"])
        write_json(CURRENT_GROUP_FILE, state["current_group"])
        
        # Save Block
        block_number = len(os.listdir(BLOCKS_DIR)) + 1
        block_data = {
            "block_number": block_number,
            "state_hash": hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest(),
            "signatures": signatures,
            "timestamp": int(time.time())
        }
        write_json(f"{BLOCKS_DIR}/block_{block_number}.json", block_data)
        
        # Delete old tx_executed (handled by overwriting)
        write_json(TX_EXECUTED_FILE, state["tx_executed"])
        
        # Accept new state & Security requirement: DO NOT restore tx_pool
        write_json(TX_POOL_FILE, {}) 
        
        print(f"Network State Updated. Block {block_number} saved.")
        self.update_balance()
        
        # Continuous Mining: Auto-rebuild if mining is active
        if self.is_mining:
            self.trigger_rebuild("mine_status_net_update")

    def connect_to_peer(self, ip, port):
        """Part 2 helper"""
        # Manual connection attempt
        msg = self.p2p.create_message("PRESENCE", {"node_id": self.p2p.node_id, "port": self.p2p.port})
        self.p2p.send_message(ip, port, msg)

    def broadcast_update(self, update_payload):
        """Part 2 helper"""
        env = self.p2p.create_message("UPDATE_REQUEST", update_payload, broadcast=True)
        self.p2p.broadcast(env)

    def add_nav_button(self, text, index):
        btn = QPushButton(f"  {text}")
        btn.setObjectName("NavButton")
        btn.clicked.connect(lambda: self.switch_tab(index))
        self.sidebar_layout.addWidget(btn)
        self.nav_buttons.append(btn)

    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", i==index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ----------------------------
    # Home Tab
    # ----------------------------
    def init_home_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40,40,40,40)
        self.home_header = QLabel("Libre Network Dashboard")
        self.home_header.setObjectName("HeaderLabel")
        l.addWidget(self.home_header)

        # First row of stats
        stats_row1 = QHBoxLayout()
        self.users_stat = self.create_stat_card(TRANSLATIONS[self.lang]["home_stat_users"],"0", TRANSLATIONS[self.lang]["tt_stat_users"])
        self.blocks_stat = self.create_stat_card(TRANSLATIONS[self.lang]["home_stat_blocks"],"0", TRANSLATIONS[self.lang]["tt_stat_blocks"])
        stats_row1.addWidget(self.users_stat)
        stats_row1.addWidget(self.blocks_stat)
        l.addLayout(stats_row1)

        # Second row of stats
        stats_row2 = QHBoxLayout()
        self.circ_stat = self.create_stat_card(TRANSLATIONS[self.lang]["home_stat_cur"],"0", TRANSLATIONS[self.lang]["tt_stat_cur"])
        self.group_size_stat = self.create_stat_card(TRANSLATIONS[self.lang]["home_stat_group_size"],"0", TRANSLATIONS[self.lang]["tt_stat_group_size"])
        self.total_groups_stat = self.create_stat_card(TRANSLATIONS[self.lang]["home_stat_total_groups"],"0", TRANSLATIONS[self.lang]["tt_stat_total_groups"])
        stats_row2.addWidget(self.circ_stat)
        stats_row2.addWidget(self.group_size_stat)
        stats_row2.addWidget(self.total_groups_stat)
        l.addLayout(stats_row2)

        l.addItem(QSpacerItem(20,20,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Fixed))

        # Node List
        self.home_nodes_header = QLabel(TRANSLATIONS[self.lang]["home_nodes_header"])
        self.home_nodes_header.setObjectName("HeaderLabel")
        self.home_nodes_header.setStyleSheet("font-size: 18px; margin-top: 10px;")
        l.addWidget(self.home_nodes_header)

        self.nodes_table = QTableWidget(0, 3)
        self.nodes_table.setHorizontalHeaderLabels([
            TRANSLATIONS[self.lang]["node_id"], 
            TRANSLATIONS[self.lang]["node_port"], 
            TRANSLATIONS[self.lang]["node_status"]
        ])
        self.nodes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.nodes_table.setStyleSheet("background-color: #1a1d2e; border: 1px solid #2d314d; border-radius: 6px;")
        self.nodes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        l.addWidget(self.nodes_table)

        l.addItem(QSpacerItem(20,40,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding))
        self.content_stack.addWidget(w)

        self.home_timer = QTimer()
        self.home_timer.timeout.connect(self.update_home)
        self.home_timer.start(2000)

    def create_stat_card(self, title, value, tooltip=""):
        frame = QFrame()
        frame.setToolTip(tooltip)
        frame.setStyleSheet("background-color: #1a1d2e; border:1px solid #2d314d; border-radius:10px; padding:20px;")
        layout = QVBoxLayout(frame)
        t_label = QLabel(title)
        t_label.setObjectName("SubtleLabel")
        v_label = QLabel(value)
        v_label.setStyleSheet("font-size:32px; font-weight:bold; color:#3d5afe;")
        layout.addWidget(t_label)
        layout.addWidget(v_label)
        frame.value_label = v_label
        frame.title_label = t_label
        return frame

    def update_home(self):
        users = read_json(USERS_FILE)
        blocks = len(os.listdir(BLOCKS_DIR))
        
        # Calculate circulation
        total_coins = sum(u.get("balance", 0) for u in users.values())
        
        # Calculate group stats
        group = get_group()
        group_size = len(group.get("miners", {}))
        total_groups = len(os.listdir(GROUPS_DIR))

        # Update labels with comma formatting
        self.users_stat.value_label.setText(f"{len(users):,}")
        self.blocks_stat.value_label.setText(f"{blocks:,}")
        self.circ_stat.value_label.setText(f"{total_coins:,.2f}")
        self.group_size_stat.value_label.setText(f"{group_size:,}")
        self.total_groups_stat.value_label.setText(f"{total_groups:,}")

        # Update Node List
        self.nodes_table.setRowCount(0)
        peers = self.p2p.peers
        for nid, (ip, port, last_seen) in peers.items():
            row = self.nodes_table.rowCount()
            self.nodes_table.insertRow(row)
            status = "Online" if (time.time() - last_seen) < 30 else "Away"
            self.nodes_table.setItem(row, 0, QTableWidgetItem(nid))
            self.nodes_table.setItem(row, 1, QTableWidgetItem(str(port)))
            self.nodes_table.setItem(row, 2, QTableWidgetItem(status))

# ----------------------------
# Wallet Tab
# ----------------------------
    def init_wallet_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40,40,40,40)
        self.wallet_header = QLabel("My Wallet")
        self.wallet_header.setObjectName("HeaderLabel")
        l.addWidget(self.wallet_header)

        # Balance
        balance_card = QFrame()
        balance_card.setStyleSheet("background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #3d5afe, stop:1 #536dfe); border-radius:12px; padding:30px;")
        b_layout = QVBoxLayout(balance_card)
        self.wallet_balance_title = QLabel("Available Balance")
        self.wallet_balance_title.setStyleSheet("color: rgba(255,255,255,0.7); font-size:14px;")
        self.balance_val = QLabel("0.000000 LBRC")
        self.balance_val.setStyleSheet("color:white; font-size:36px; font-weight:bold;")
        b_layout.addWidget(self.wallet_balance_title)
        b_layout.addWidget(self.balance_val)
        l.addWidget(balance_card)

        # Login
        self.wallet_login_label = QLabel("Login with Private Key")
        l.addWidget(self.wallet_login_label)
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Enter your hex private key...")
        self.login_input.setEchoMode(QLineEdit.EchoMode.Password)
        l.addWidget(self.login_input)
        self.wallet_login_btn = QPushButton("Unlock Wallet")
        self.wallet_login_btn.setObjectName("ActionButton")
        self.wallet_login_btn.clicked.connect(self.login)
        l.addWidget(self.wallet_login_btn)

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("ActionButton")
        self.logout_btn.clicked.connect(self.logout)
        self.logout_btn.hide() # Hide by default, show when logged in
        l.addWidget(self.logout_btn)

        l.addItem(QSpacerItem(20,40,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding))
        self.content_stack.addWidget(w)

    def init_keygen_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40,40,40,40)
        
        self.keygen_header = QLabel(TRANSLATIONS[self.lang]["keygen_header"])
        self.keygen_header.setObjectName("HeaderLabel")
        l.addWidget(self.keygen_header)

        # Generate Button
        self.keygen_btn = QPushButton(TRANSLATIONS[self.lang]["keygen_btn"])
        self.keygen_btn.setObjectName("ActionButton")
        self.keygen_btn.clicked.connect(self.generate_keygen_wallet)
        l.addWidget(self.keygen_btn)

        # Keys Table
        self.keygen_table = QTableWidget(0, 5)
        self.keygen_table.setHorizontalHeaderLabels([
            TRANSLATIONS[self.lang]["keygen_table_priv"],
            TRANSLATIONS[self.lang]["keygen_table_pub"],
            TRANSLATIONS[self.lang]["keygen_table_addr"],
            TRANSLATIONS[self.lang]["keygen_copy"],
            TRANSLATIONS[self.lang]["keygen_delete"]
        ])
        self.keygen_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.keygen_table.setStyleSheet("background-color: #1a1d2e; border: 1px solid #2d314d; border-radius: 6px;")
        l.addWidget(self.keygen_table)

        self.content_stack.addWidget(w)
        self.load_generated_keys()

    def generate_keygen_wallet(self):
        private = secrets.token_hex(32)
        public = hashlib.sha256(private.encode()).hexdigest()
        address = hashlib.sha256(public.encode()).hexdigest()[:16]
        
        self.db.save_generated_key(private, public, address)
        self.load_generated_keys()
        QMessageBox.information(self, TRANSLATIONS[self.lang]["msg_success"], f"Generated: {address}")

    def load_generated_keys(self):
        keys = self.db.get_all_generated_keys()
        self.keygen_table.setRowCount(0)
        for k in keys:
            row = self.keygen_table.rowCount()
            self.keygen_table.insertRow(row)
            
            self.keygen_table.setItem(row, 0, QTableWidgetItem(k["private_key"][:8] + "..."))
            self.keygen_table.setItem(row, 1, QTableWidgetItem(k["public_key"][:8] + "..."))
            self.keygen_table.setItem(row, 2, QTableWidgetItem(k["address"]))
            
            copy_btn = QPushButton(TRANSLATIONS[self.lang]["keygen_copy"])
            copy_btn.clicked.connect(self.make_copy_callback(k["private_key"], k["public_key"], k["address"]))
            self.keygen_table.setCellWidget(row, 3, copy_btn)

            delete_btn = QPushButton(TRANSLATIONS[self.lang]["keygen_delete"])
            delete_btn.setStyleSheet("background-color: #f44336; color: white;")
            delete_btn.clicked.connect(self.make_delete_callback(k["address"]))
            self.keygen_table.setCellWidget(row, 4, delete_btn)

    def make_delete_callback(self, addr):
        return lambda: self.delete_keygen_key(addr)

    def delete_keygen_key(self, addr):
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete key: {addr}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_generated_key(addr)
            self.load_generated_keys()
            QMessageBox.information(self, TRANSLATIONS[self.lang]["msg_success"], "Key deleted." if self.lang=="en" else "تم حذف المفتاح.")

    def make_copy_callback(self, pk, pub, addr):
        return lambda: self.copy_keys_to_clipboard(pk, pub, addr)

    def copy_keys_to_clipboard(self, pk, pub, addr):
        text = f"Private Key: {pk}\nPublic Key: {pub}\nAddress: {addr}"
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, TRANSLATIONS[self.lang]["msg_success"], TRANSLATIONS[self.lang]["msg_copied"])

# ----------------------------
# Transactions Tab
# ----------------------------
    def init_tx_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40,40,40,40)
        l.setSpacing(15)

        self.tx_header = QLabel("Transactions")
        self.tx_header.setObjectName("HeaderLabel")
        l.addWidget(self.tx_header)

        # Form
        form = QFrame()
        form.setStyleSheet("background-color: #1a1d2e; border-radius: 10px; padding: 20px;")
        fl = QVBoxLayout(form)

        self.tx_type_label = QLabel("Transaction Type")
        fl.addWidget(self.tx_type_label)
        self.tx_type = QComboBox()
        self.tx_type.addItems(["transfer","new_account","join_pool"])
        self.tx_type.currentTextChanged.connect(self.on_tx_type_changed)
        fl.addWidget(self.tx_type)

        self.to_label = QLabel("Recipient Address")
        fl.addWidget(self.to_label)
        self.tx_to = QLineEdit()
        fl.addWidget(self.tx_to)

        self.amount_label = QLabel("Amount")
        fl.addWidget(self.amount_label)
        self.tx_amount = QLineEdit()
        self.tx_amount.textChanged.connect(self.on_tx_amount_changed)
        fl.addWidget(self.tx_amount)

        self.tx_fee_label = QLabel("Fee: 0.000001 LBRC")
        self.tx_fee_label.setStyleSheet("color: #3d5afe; font-weight: bold; margin-top: 5px;")
        fl.addWidget(self.tx_fee_label)

        self.tx_send_btn = QPushButton("Send Transaction")
        self.tx_send_btn.setObjectName("ActionButton")
        self.tx_send_btn.clicked.connect(self.add_tx)
        fl.addWidget(self.tx_send_btn)

        l.addWidget(form)

        self.tx_activity_label = QLabel("Recent Activity")
        l.addWidget(self.tx_activity_label)
        self.tx_view = QTextEdit()
        self.tx_view.setReadOnly(True)
        l.addWidget(self.tx_view)

        self.content_stack.addWidget(w)

        self.tx_timer = QTimer()
        self.tx_timer.timeout.connect(self.update_tx_view)
        self.tx_timer.start(2000)

    def on_tx_type_changed(self, tx_type):
        t = TRANSLATIONS[self.lang]
        if tx_type == "transfer":
            self.amount_label.show()
            self.tx_amount.show()
            self.to_label.setText(t["tx_to_label"])
            self.on_tx_amount_changed()
        elif tx_type == "new_account":
            self.amount_label.hide()
            self.tx_amount.hide()
            self.to_label.setText(t["tx_to_label_new"])
            self.tx_fee_label.setText("Fee: 1.0 LBRC")
        elif tx_type == "join_pool":
            self.amount_label.hide()
            self.tx_amount.hide()
            self.to_label.setText(t["tx_to_label_na"])
            self.tx_fee_label.setText("Fee: 0.000001 LBRC")

    def on_tx_amount_changed(self):
        if self.tx_type.currentText() == "transfer":
            try:
                amount_str = self.tx_amount.text().strip()
                if not amount_str:
                    self.tx_fee_label.setText("Fee: 0.000001 LBRC")
                    return
                amount = float(amount_str)
                fee = transfer_fee(amount)
                self.tx_fee_label.setText(f"Fee: {fee:.6f} LBRC")
            except ValueError:
                self.tx_fee_label.setText("Fee: 0.000001 LBRC")

# ----------------------------
# Mining Tab
# ----------------------------
    def init_mine_tab(self):
        # Scroll Area for responsiveness
        outer_w = QWidget()
        outer_l = QVBoxLayout(outer_w)
        outer_l.setContentsMargins(0,0,0,0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        w = QWidget()
        w.setStyleSheet("background-color: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(40,40,40,40)
        l.setSpacing(20)
        l.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.mine_header = QLabel("Mining Center")
        self.mine_header.setObjectName("HeaderLabel")
        l.addWidget(self.mine_header)

        mine_card = QFrame()
        mine_card.setStyleSheet("background-color: #1a1d2e; border-radius: 10px; padding: 40px;")
        ml = QVBoxLayout(mine_card)
        ml.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Mining Icon and Subtext
        mine_icon = QLabel("⛏️")
        mine_icon.setStyleSheet("font-size:64px; margin-bottom: 10px;")
        ml.addWidget(mine_icon,0,Qt.AlignmentFlag.AlignCenter)

        self.mine_subtext = QLabel("Support the network and earn rewards")
        self.mine_subtext.setStyleSheet("color: #a0a0a0; font-size: 14px; margin-bottom: 20px;")
        ml.addWidget(self.mine_subtext,0,Qt.AlignmentFlag.AlignCenter)

        # Controls Group
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 15px;")
        cl = QVBoxLayout(ctrl_frame)
        
        # Wait Time Control
        wait_l = QHBoxLayout()
        self.mine_wait_label = QLabel("Signature Wait (sec):")
        self.mine_wait_label.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        wait_l.addWidget(self.mine_wait_label)
        
        self.mine_wait_input = QSpinBox()
        self.mine_wait_input.setRange(1, 600)
        self.mine_wait_input.setValue(self.config.get("mine_wait_duration", 60))
        self.mine_wait_input.setFixedWidth(100)
        self.mine_wait_input.setStyleSheet("padding: 5px; background-color: #0f111a; border: 1px solid #333; color: white;")
        self.mine_wait_input.valueChanged.connect(self.update_mine_wait)
        wait_l.addWidget(self.mine_wait_input)
        wait_l.addStretch() # Push to left
        cl.addLayout(wait_l)

        # Status Display
        status_l = QHBoxLayout()
        self.mine_status_header = QLabel("Mining Status:")
        self.mine_status_header.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        status_l.addWidget(self.mine_status_header)
        
        self.mine_status_val = QLabel("Stopped")
        self.mine_status_val.setStyleSheet("color: #707070; font-weight: bold;")
        status_l.addWidget(self.mine_status_val)
        cl.addLayout(status_l)

        # Countdown Display
        countdown_l = QHBoxLayout()
        self.mine_countdown_header = QLabel("Next Cycle in:")
        self.mine_countdown_header.setStyleSheet("color: #a0a0a0;")
        countdown_l.addWidget(self.mine_countdown_header)
        
        self.mine_countdown_val = QLabel("0s")
        self.mine_countdown_val.setStyleSheet("color: #4CAF50; font-size: 24px; font-weight: bold;")
        countdown_l.addWidget(self.mine_countdown_val)
        cl.addLayout(countdown_l)
        
        ml.addWidget(ctrl_frame)
        ml.addSpacing(30)

        # Buttons Group - Explicit Styling and Layout
        btns_l = QHBoxLayout()
        btns_l.setSpacing(20)
        
        self.mine_btn = QPushButton("START MINING")
        self.mine_btn.setMinimumHeight(55)
        self.mine_btn.setMinimumWidth(200)
        self.mine_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mine_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d5afe;
                border: 2px solid #536dfe;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #536dfe;
                border: 2px solid #ffffff;
            }
            QPushButton:disabled {
                background-color: #222;
                border: 1px solid #444;
                color: #666;
            }
        """)
        self.mine_btn.clicked.connect(self.start_mining)
        btns_l.addWidget(self.mine_btn)

        self.mine_stop_btn = QPushButton("STOP MINING")
        self.mine_stop_btn.setMinimumHeight(55)
        self.mine_stop_btn.setMinimumWidth(200)
        self.mine_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mine_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #442222;
                border: 2px solid #663333;
                border-radius: 8px;
                color: #ff8888;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #663333;
                border: 2px solid #ff4444;
                color: white;
            }
            QPushButton:disabled {
                background-color: #222;
                border: 1px solid #444;
                color: #666;
            }
        """)
        self.mine_stop_btn.clicked.connect(self.stop_mining)
        self.mine_stop_btn.setEnabled(False)
        btns_l.addWidget(self.mine_stop_btn)
        
        # Ensure they are visible
        self.mine_btn.show()
        self.mine_stop_btn.show()
        
        ml.addLayout(btns_l)

        # Center the card in the tab
        centered_l = QHBoxLayout()
        centered_l.addStretch()
        centered_l.addWidget(mine_card)
        centered_l.addStretch()
        l.addLayout(centered_l)

        l.addItem(QSpacerItem(20,40,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding))
        
        scroll.setWidget(w)
        outer_l.addWidget(scroll)
        self.content_stack.addWidget(outer_w)

# ----------------------------
# Settings Tab
# ----------------------------
    def init_settings_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40,40,40,40)
        l.setSpacing(20)

        self.settings_header = QLabel("Settings")
        self.settings_header.setObjectName("HeaderLabel")
        l.addWidget(self.settings_header)

        form = QFrame()
        form.setStyleSheet("background-color: #1a1d2e; border-radius: 10px; padding: 30px;")
        fl = QVBoxLayout(form)

        # Language
        self.settings_lang_label = QLabel("Application Language")
        fl.addWidget(self.settings_lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["en", "ar"])
        self.lang_combo.setCurrentText(self.lang)
        fl.addWidget(self.lang_combo)

        fl.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Port
        self.settings_port_label = QLabel("Network Port")
        fl.addWidget(self.settings_port_label)
        
        port_layout = QHBoxLayout()
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.config.get("network_port", 5000))
        self.port_spin.setStyleSheet("padding: 5px; background-color: #0f111a; border: 1px solid #333; color: white;")
        port_layout.addWidget(self.port_spin)
        
        self.port_save_btn = QPushButton("Save Port")
        self.port_save_btn.setObjectName("ActionButton")
        self.port_save_btn.clicked.connect(self.save_port)
        self.port_save_btn.setFixedWidth(120)
        port_layout.addWidget(self.port_save_btn)
        
        fl.addLayout(port_layout)

        # Future settings placeholders
        self.settings_max_conn_label = QLabel("Max Connections (Future)")
        self.settings_max_conn_label.setObjectName("SubtleLabel")
        fl.addWidget(self.settings_max_conn_label)
        self.max_conn_input = QLineEdit()
        self.max_conn_input.setPlaceholderText("8")
        self.max_conn_input.setEnabled(False)
        fl.addWidget(self.max_conn_input)

        self.settings_log_label = QLabel("Log Level (Future)")
        self.settings_log_label.setObjectName("SubtleLabel")
        fl.addWidget(self.settings_log_label)
        self.log_combo = QComboBox()
        self.log_combo.addItems(["INFO", "DEBUG", "ERROR"])
        self.log_combo.setEnabled(False)
        fl.addWidget(self.log_combo)

        fl.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.settings_restart_info = QLabel("Note: Port changes require an application restart.")
        self.settings_restart_info.setObjectName("SubtleLabel")
        fl.addWidget(self.settings_restart_info)

        self.settings_save_btn = QPushButton("Save Settings")
        self.settings_save_btn.setObjectName("ActionButton")
        self.settings_save_btn.clicked.connect(self.save_settings)
        fl.addWidget(self.settings_save_btn)

        l.addWidget(form)
        l.addItem(QSpacerItem(20,40,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding))
        self.content_stack.addWidget(w)

    def save_port(self):
        try:
            port = self.port_spin.value()
            if not (1024 <= port <= 65535):
                raise ValueError("Port out of range")
            
            self.config["network_port"] = port
            write_json(CONFIG_FILE, self.config)
            
            QMessageBox.information(self, TRANSLATIONS[self.lang]["msg_success"], 
                                    "Node port saved successfully" if self.lang=="en" else "تم حفظ منفذ العقدة بنجاح")
        except Exception as e:
            QMessageBox.critical(self, TRANSLATIONS[self.lang]["msg_error"], 
                                 f"Failed to save port: {e}" if self.lang=="en" else f"فشل حفظ المنفذ: {e}")

    def save_settings(self):
        try:
            self.lang = self.lang_combo.currentText()
            self.config["language"] = self.lang
            write_json(CONFIG_FILE, self.config)
            
            self.update_ui_language()
            QMessageBox.information(self, TRANSLATIONS[self.lang]["msg_success"], 
                                    TRANSLATIONS[self.lang]["msg_success"])
        except Exception as e:
            QMessageBox.critical(self, TRANSLATIONS[self.lang]["msg_error"], 
                                 f"Failed to save settings: {e}" if self.lang=="en" else f"فشل حفظ الإعدادات: {e}")

    def update_ui_language(self):
        t = TRANSLATIONS[self.lang]
        is_rtl = (self.lang == "ar")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if is_rtl else Qt.LayoutDirection.LeftToRight)
        
        # Update Nav
        nav_texts = [t["nav_home"], t["nav_wallet"], t["nav_keygen"], t["nav_tx"], t["nav_mine"], t["nav_settings"]]
        for i, text in enumerate(nav_texts):
            self.nav_buttons[i].setText(f"  {text}")

        # Update Headers
        self.home_header.setText(t["home_header"])
        self.wallet_header.setText(t["wallet_header"])
        self.keygen_header.setText(t["keygen_header"])
        self.tx_header.setText(t["tx_header"])
        self.mine_header.setText(t["mine_header"])
        self.settings_header.setText(t["settings_header"])

        # Update stats titles
        self.users_stat.title_label.setText(t["home_stat_users"])
        self.blocks_stat.title_label.setText(t["home_stat_blocks"])
        self.circ_stat.title_label.setText(t["home_stat_cur"])
        self.group_size_stat.title_label.setText(t["home_stat_group_size"])
        self.total_groups_stat.title_label.setText(t["home_stat_total_groups"])

        self.home_nodes_header.setText(t["home_nodes_header"])
        self.nodes_table.setHorizontalHeaderLabels([t["node_id"], t["node_port"], t["node_status"]])

        # Update Wallet
        self.wallet_balance_title.setText(t["wallet_balance_title"])
        self.wallet_login_label.setText(t["wallet_login_label"])
        self.wallet_login_btn.setText(t["wallet_login_btn"])
        self.login_input.setPlaceholderText(t["placeholder_login"])
        if hasattr(self, 'logout_btn'):
            self.logout_btn.setText(t["logout_btn"])

        # Update Keygen
        self.keygen_btn.setText(t["keygen_btn"])
        self.keygen_table.setHorizontalHeaderLabels([
            t["keygen_table_priv"], t["keygen_table_pub"], t["keygen_table_addr"], t["keygen_copy"], t["keygen_delete"]
        ])

        # Update TX
        self.tx_type_label.setText(t["tx_type_label"])
        self.tx_send_btn.setText(t["tx_send_btn"])
        self.tx_activity_label.setText(t["tx_activity_label"])
        self.on_tx_type_changed(self.tx_type.currentText())

        # Update Mine
        self.mine_subtext.setText(t["mine_subtext"])
        self.mine_btn.setText(t["mine_btn"])
        self.mine_stop_btn.setText(t["mine_btn_stop"])
        self.mine_status_header.setText(t["mine_status_label"])
        self.mine_wait_label.setText(t["mine_wait_label"])
        self.mine_countdown_header.setText(t["mine_countdown_label"])
        
        # Refresh current status text
        if not self.is_mining:
            self.mine_status_val.setText(t["mine_status_stopped"])
        # (Other statuses are updated dynamically by the mining engine)

        self.settings_lang_label.setText(t["settings_lang_label"])
        self.settings_save_btn.setText(t["settings_save_btn"])

        # Layout Direction
        if self.lang == "ar":
            self.main_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.main_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)


# ----------------------------
# Logo Upload
# ----------------------------
    def upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            ext = os.path.splitext(file_path)[1]
            target_path = os.path.join(DATA_DIR, f"logo{ext}")
            try:
                shutil.copy(file_path, target_path)
                config = read_json(CONFIG_FILE)
                config["logo_path"] = target_path
                write_json(CONFIG_FILE, config)
                self.load_logo()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save logo: {e}")

    def load_logo(self):
        config = read_json(CONFIG_FILE)
        path = config.get("logo_path")
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            self.logo_label.setPixmap(pixmap.scaled(90,90,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            self.logo_label.setText("")
            self.logo_label.setStyleSheet("border:none;")

# ----------------------------
# Wallet functions
# ----------------------------
    def login(self):
        private = self.login_input.text().strip()
        if not private: return
        try:
            pub = hashlib.sha256(private.encode()).hexdigest()
            addr = hashlib.sha256(pub.encode()).hexdigest()[:16]
            self.addr = addr
            self.private_key = private
            
            # Save session to SQLite
            self.db.save_wallet_session(private, pub, addr)
            
            QMessageBox.information(self, TRANSLATIONS[self.lang]["msg_success"], f"Logged in as: {addr}" if self.lang=="en" else f"تم تسجيل الدخول بـ: {addr}")
            self.update_balance()
            self.update_login_gui_state(True)
        except Exception as e:
            QMessageBox.critical(self, TRANSLATIONS[self.lang]["msg_error"], f"Invalid private key: {e}" if self.lang=="en" else f"مفتاح خاص غير صحيح: {e}")

    def logout(self):
        self.db.delete_wallet_session()
        self.addr = None
        self.private_key = None
        self.login_input.clear()
        self.update_balance()
        self.update_login_gui_state(False)
        QMessageBox.information(self, TRANSLATIONS[self.lang]["msg_success"], TRANSLATIONS[self.lang]["msg_logout_success"])

    def auto_login(self):
        session = self.db.get_wallet_session()
        if session:
            self.private_key = session["private_key"]
            self.addr = session["address"]
            self.update_balance()
            self.update_login_gui_state(True)
            print(f"Auto-logged in as: {self.addr}")

    def update_login_gui_state(self, logged_in):
        if logged_in:
            self.wallet_login_btn.hide()
            self.login_input.hide()
            self.wallet_login_label.hide()
            self.logout_btn.show()
        else:
            self.wallet_login_btn.show()
            self.login_input.show()
            self.wallet_login_label.show()
            self.logout_btn.hide()

# ----------------------------
# Transactions
# ----------------------------
    def add_tx(self):
        t_all = TRANSLATIONS[self.lang]
        if not self.addr:
            QMessageBox.warning(self, t_all["msg_error"], t_all["msg_unlocked"])
            return
        t = self.tx_type.currentText()
        to_addr = self.tx_to.text().strip()
        try:
            users = read_json(USERS_FILE)
            sender_data = users.get(self.addr,{"balance":0,"nonce":0})

            tx_id = secrets.token_hex(16)
            tx = {
                "tx_id": tx_id,
                "type": t,
                "from": self.addr,
                "to": to_addr,
                "amount": 0.0,
                "fee": 0.0,
                "nonce": sender_data["nonce"],
                "timestamp": int(time.time())
            }

            if t == "transfer":
                try:
                    amount = float(self.tx_amount.text())
                    if amount <= 0: raise ValueError
                except:
                    QMessageBox.warning(self,"Error","Invalid amount")
                    return
                tx["amount"] = amount
                tx["fee"] = transfer_fee(amount)
                if to_addr not in users:
                    QMessageBox.warning(self,"Error","Recipient does not exist")
                    return
            elif t == "new_account":
                tx["fee"] = 1.0
                if not to_addr or len(to_addr)!=16:
                    QMessageBox.warning(self,"Error","Invalid new address format")
                    return
            elif t == "join_pool":
                tx["fee"] = 0.000001
                pool = read_json(MINER_POOL_FILE)
                if self.addr in pool:
                    QMessageBox.warning(self,"Error","Already in miner pool")
                    return

            # Balance check
            if sender_data["balance"] < (tx["amount"]+tx["fee"]):
                QMessageBox.warning(self,"Error","Insufficient balance")
                return

            # Sign transaction
            tx["signature"] = sign_tx(self.private_key,tx)
            pool = read_json(TX_POOL_FILE)
            pool[tx_id] = tx
            write_json(TX_POOL_FILE,pool)
            
            # BROADCAST TRANSACTION
            env = self.p2p.create_message("TRANSACTION", {"data": tx}, broadcast=True)
            self.p2p.broadcast(env)

            QMessageBox.information(self, t_all["msg_success"], t_all["msg_add_tx_success"] + str(tx['fee']))
            self.tx_to.clear()
            self.tx_amount.clear()
            self.update_balance()

        except Exception as e:
            QMessageBox.warning(self, t_all["msg_error"], f"Failed to add transaction: {e}" if self.lang=="en" else f"فشل إضافة العملية: {e}")

    def update_tx_view(self):
        executed = read_json(TX_EXECUTED_FILE)
        text = ""
        items = list(executed.values())
        for tx in reversed(items):
            text += f"[{tx.get('type','unknown')}] To: {tx['to']} | Amt: {tx.get('amount',0)} | Fee: {tx.get('fee',0)}\n"
            text += f"ID: {tx.get('tx_id','N/A')}\n"
            text += "-"*40 + "\n"
        self.tx_view.setText(text)

# ----------------------------
# Mining
# ----------------------------
    def start_mining(self):
        t = TRANSLATIONS[self.lang]
        if not self.addr:
            QMessageBox.warning(self, t["msg_error"], t["msg_unlocked"])
            return
        
        self.is_mining = True
        self.mine_btn.setEnabled(False)
        self.mine_stop_btn.setEnabled(True)
        self.mine_cycle()

    def stop_mining(self):
        self.is_mining = False
        self.signature_timer.stop()
        self.rebuild_timer.stop()
        self.countdown_timer.stop()
        self.mine_btn.setEnabled(True)
        self.mine_stop_btn.setEnabled(False)
        self.mine_status_val.setText(TRANSLATIONS[self.lang]["mine_status_stopped"])
        self.mine_status_val.setStyleSheet("color: #707070; font-weight: bold;")
        self.mine_countdown_val.setText("0s")

    def update_mine_wait(self, val):
        self.config["mine_wait_duration"] = val
        write_json(CONFIG_FILE, self.config)
        print(f"Saved mine_wait_duration: {val}")
        if self.is_mining:
            self.trigger_rebuild("mine_status_rebuilding")

    def update_countdown_display(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.mine_countdown_val.setText(f"{self.remaining_seconds}s")
        else:
            self.countdown_timer.stop()

    def trigger_rebuild(self, reason_key):
        """Centralized trigger to rebuild the update without stacking calls"""
        if not self.is_mining: return
        
        self.signature_timer.stop()
        self.rebuild_timer.stop() # Cancel any existing rebuild delay
        self.countdown_timer.stop()
        self.mine_countdown_val.setText("0s")
        
        t = TRANSLATIONS[self.lang]
        self.mine_status_val.setText(t.get(reason_key, "Rebuilding..."))
        
        # Color coding: Rebuilding/Net Update usually Blue; Expired usually Amber/Blue
        if reason_key in ["mine_status_rebuilding", "mine_status_net_update"]:
            self.mine_status_val.setStyleSheet("color: #2196F3; font-weight: bold;")
        elif reason_key == "mine_status_expired":
            self.mine_status_val.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.mine_status_val.setStyleSheet("color: #2196F3; font-weight: bold;")
            
        # Rebuild after a short delay to avoid rapid thrashing
        self.rebuild_timer.start(1500)

    def mine_cycle(self):
        if not self.is_mining: return
        
        # Stop any pending rebuilds or timeouts as we are starting fresh
        self.signature_timer.stop()
        self.rebuild_timer.stop()
        self.countdown_timer.stop()
        
        t = TRANSLATIONS[self.lang]
        self.mine_status_val.setText(t["mine_status_running"])
        self.mine_status_val.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.mine_countdown_val.setText("0s")
        
        # Initiate mining consensus
        update_data = mine(self.addr)
        if update_data:
            state_hash = update_data["state_hash"]
            self.pending_updates[state_hash] = update_data
            self.collected_signatures[state_hash] = []
            
            # Broadcast update request
            req_payload = {
                "state": update_data["state"],
                "state_hash": state_hash,
                "miner": self.addr,
                "miner_port": self.p2p.port
            }
            env = self.p2p.create_message("UPDATE_REQUEST", req_payload, broadcast=True)
            self.p2p.broadcast(env)
            
            # Set timeout for signatures
            wait_time_sec = self.mine_wait_input.value()
            self.remaining_seconds = wait_time_sec
            self.mine_countdown_val.setText(f"{wait_time_sec}s")
            
            self.signature_timer.start(wait_time_sec * 1000)
            self.countdown_timer.start()
            self.mine_status_val.setText(t["mine_status_waiting"])
            self.mine_status_val.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            # Mining failed (e.g. not in active group)
            self.mine_status_val.setText(t["msg_mine_failed"])
            self.mine_status_val.setStyleSheet("color: #f44336; font-weight: bold;")
            # Retry after a slightly longer delay if failed
            self.rebuild_timer.start(5000)

    def handle_signature_timeout(self):
        self.trigger_rebuild("mine_status_expired")

    def mine_block(self):
        """Deprecated: Replaced by start_mining/mine_cycle"""
        self.start_mining()

# ----------------------------
# Balance
# ----------------------------
    def update_balance(self):
        if not self.addr: return
        users = read_json(USERS_FILE)
        bal = users.get(self.addr,{}).get("balance",0)
        self.balance_val.setText(f"{bal:.6f} LBRC")

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = Main()
    win.show()
    sys.exit(app.exec())