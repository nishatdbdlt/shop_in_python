import tkinter as tk
from tkinter import ttk, messagebox, font
import sqlite3
import datetime
import os
import random
import string
import hashlib
import json
import calendar

try:
    from reportlab.lib.units import mm

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ─────────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────────
DB_FILE = "hospital.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'Staff',
        full_name TEXT,
        email TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        phone TEXT,
        email TEXT,
        experience INTEGER,
        status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        phone TEXT,
        address TEXT,
        blood_group TEXT,
        disease TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS cabins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cabin_number TEXT UNIQUE,
        cabin_type TEXT,
        floor INTEGER,
        price_per_day REAL,
        status TEXT DEFAULT 'Available',
        patient_id INTEGER,
        admitted_date TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date TEXT,
        appointment_time TEXT,
        reason TEXT,
        status TEXT DEFAULT 'Scheduled',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_number TEXT UNIQUE,
        patient_id INTEGER,
        doctor_fee REAL DEFAULT 0,
        cabin_charge REAL DEFAULT 0,
        medicine_charge REAL DEFAULT 0,
        lab_charge REAL DEFAULT 0,
        other_charge REAL DEFAULT 0,
        total REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
    )""")

    # NEW: Lab Tests
    c.execute("""CREATE TABLE IF NOT EXISTS lab_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_code TEXT UNIQUE,
        test_name TEXT NOT NULL,
        category TEXT,
        price REAL DEFAULT 0,
        normal_range TEXT,
        unit TEXT,
        status TEXT DEFAULT 'Active'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lab_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE,
        patient_id INTEGER,
        doctor_id INTEGER,
        test_id INTEGER,
        ordered_date TEXT,
        result_value TEXT,
        result_status TEXT DEFAULT 'Pending',
        remarks TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id),
        FOREIGN KEY(test_id) REFERENCES lab_tests(id)
    )""")

    # NEW: Medicines/Pharmacy
    c.execute("""CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_code TEXT UNIQUE,
        name TEXT NOT NULL,
        generic_name TEXT,
        category TEXT,
        unit TEXT,
        price REAL DEFAULT 0,
        stock_quantity INTEGER DEFAULT 0,
        reorder_level INTEGER DEFAULT 10,
        manufacturer TEXT,
        expiry_date TEXT,
        status TEXT DEFAULT 'Active'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS medicine_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_number TEXT UNIQUE,
        patient_id INTEGER,
        medicine_id INTEGER,
        quantity INTEGER,
        unit_price REAL,
        total_price REAL,
        sale_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id),
        FOREIGN KEY(medicine_id) REFERENCES medicines(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        movement_type TEXT,
        quantity INTEGER,
        note TEXT,
        moved_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(medicine_id) REFERENCES medicines(id)
    )""")

    # NEW: Prescriptions
    c.execute("""CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prescription_number TEXT UNIQUE,
        patient_id INTEGER,
        doctor_id INTEGER,
        diagnosis TEXT,
        notes TEXT,
        follow_up_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS prescription_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prescription_id INTEGER,
        medicine_name TEXT,
        dosage TEXT,
        frequency TEXT,
        duration TEXT,
        instructions TEXT,
        FOREIGN KEY(prescription_id) REFERENCES prescriptions(id)
    )""")

    # NEW: Medical History
    c.execute("""CREATE TABLE IF NOT EXISTS medical_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        visit_date TEXT,
        visit_type TEXT,
        doctor_id INTEGER,
        complaint TEXT,
        diagnosis TEXT,
        treatment TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    )""")

    # Seed users
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        doctor_hash = hashlib.sha256("doctor123".encode()).hexdigest()
        staff_hash = hashlib.sha256("staff123".encode()).hexdigest()
        c.executemany("INSERT INTO users (username,password_hash,role,full_name,email) VALUES (?,?,?,?,?)", [
            ("admin", admin_hash, "Admin", "System Administrator", "admin@hospital.com"),
            ("doctor1", doctor_hash, "Doctor", "Dr. Sarah Ahmed", "sarah@hospital.com"),
            ("staff1", staff_hash, "Staff", "Reception Staff", "staff@hospital.com"),
        ])

    c.execute("SELECT COUNT(*) FROM doctors")
    if c.fetchone()[0] == 0:
        doctors = [
            ("Dr. Sarah Ahmed", "Cardiology", "01711-111111", "sarah@hospital.com", 12),
            ("Dr. Rahim Khan", "Neurology", "01711-222222", "rahim@hospital.com", 8),
            ("Dr. Priya Das", "Orthopedics", "01711-333333", "priya@hospital.com", 15),
            ("Dr. Arif Hossain", "Pediatrics", "01711-444444", "arif@hospital.com", 6),
            ("Dr. Nadia Islam", "Gynecology", "01711-555555", "nadia@hospital.com", 10),
        ]
        c.executemany("INSERT INTO doctors (name,specialization,phone,email,experience) VALUES (?,?,?,?,?)", doctors)

    c.execute("SELECT COUNT(*) FROM cabins")
    if c.fetchone()[0] == 0:
        cabins = []
        types = [("General", 800), ("Semi-Private", 1500), ("Private", 2500), ("VIP", 4000)]
        num = 1
        for floor in range(1, 4):
            for t, price in types:
                cabins.append((f"C{num:03d}", t, floor, price, "Available"))
                num += 1
        c.executemany("INSERT INTO cabins (cabin_number,cabin_type,floor,price_per_day,status) VALUES (?,?,?,?,?)", cabins)

    # Seed lab tests
    c.execute("SELECT COUNT(*) FROM lab_tests")
    if c.fetchone()[0] == 0:
        tests = [
            ("CBC001", "Complete Blood Count (CBC)", "Hematology", 400, "RBC: 4.5-5.5 M/uL", "M/uL"),
            ("LFT001", "Liver Function Test (LFT)", "Biochemistry", 600, "ALT: 7-56 U/L", "U/L"),
            ("KFT001", "Kidney Function Test (KFT)", "Biochemistry", 550, "Creatinine: 0.6-1.2 mg/dL", "mg/dL"),
            ("BS001", "Blood Sugar (Fasting)", "Biochemistry", 150, "70-100 mg/dL", "mg/dL"),
            ("TSH001", "Thyroid Stimulating Hormone", "Endocrinology", 800, "0.4-4.0 mIU/L", "mIU/L"),
            ("URINE001", "Urine Routine Examination", "Microbiology", 200, "Normal", "-"),
            ("XR001", "Chest X-Ray", "Radiology", 500, "Normal", "-"),
            ("ECG001", "Electrocardiogram (ECG)", "Cardiology", 350, "Normal Sinus Rhythm", "-"),
            ("LIPID001", "Lipid Profile", "Biochemistry", 700, "Total Cholesterol < 200 mg/dL", "mg/dL"),
            ("HBA1C001", "HbA1c", "Biochemistry", 600, "< 5.7%", "%"),
        ]
        c.executemany("INSERT INTO lab_tests (test_code,test_name,category,price,normal_range,unit) VALUES (?,?,?,?,?,?)", tests)

    # Seed medicines
    c.execute("SELECT COUNT(*) FROM medicines")
    if c.fetchone()[0] == 0:
        meds = [
            ("MED001", "Paracetamol 500mg", "Paracetamol", "Analgesic", "Tablet", 2.5, 500, 50, "Square Pharma", "2026-12-31"),
            ("MED002", "Amoxicillin 250mg", "Amoxicillin", "Antibiotic", "Capsule", 8.0, 300, 30, "Beximco Pharma", "2026-06-30"),
            ("MED003", "Metformin 500mg", "Metformin", "Antidiabetic", "Tablet", 5.0, 400, 40, "ACI Limited", "2027-01-31"),
            ("MED004", "Amlodipine 5mg", "Amlodipine", "Antihypertensive", "Tablet", 6.0, 250, 25, "Renata Limited", "2026-09-30"),
            ("MED005", "Omeprazole 20mg", "Omeprazole", "Antacid", "Capsule", 7.5, 350, 35, "Incepta Pharma", "2026-11-30"),
            ("MED006", "Ceftriaxone 1g", "Ceftriaxone", "Antibiotic", "Injection", 120.0, 100, 20, "Square Pharma", "2025-12-31"),
            ("MED007", "Insulin Regular 100IU", "Insulin", "Antidiabetic", "Vial", 450.0, 50, 10, "Novo Nordisk", "2025-08-31"),
            ("MED008", "Atenolol 50mg", "Atenolol", "Beta Blocker", "Tablet", 4.0, 200, 20, "ACI Limited", "2027-03-31"),
        ]
        c.executemany("INSERT INTO medicines (medicine_code,name,generic_name,category,unit,price,stock_quantity,reorder_level,manufacturer,expiry_date) VALUES (?,?,?,?,?,?,?,?,?,?)", meds)

    conn.commit()
    conn.close()

def gen_patient_id():
    return "PT" + ''.join(random.choices(string.digits, k=6))

def gen_bill_number():
    return "BL" + ''.join(random.choices(string.digits, k=8))

def gen_order_number():
    return "LB" + ''.join(random.choices(string.digits, k=8))

def gen_prescription_number():
    return "RX" + ''.join(random.choices(string.digits, k=8))

def gen_sale_number():
    return "SL" + ''.join(random.choices(string.digits, k=8))

def gen_med_code():
    return "MED" + ''.join(random.choices(string.digits, k=4))

def validate_date(value):
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_time(value):
    try:
        datetime.datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        return False

# ─────────────────────────────────────────────
#  THEME / COLORS
# ─────────────────────────────────────────────
BG       = "#F4F7FB"
PANEL    = "#E4ECF8"
CARD     = "#FFFFFF"
ACCENT   = "#2D9CDB"
ACCENT2  = "#56CCF2"
DANGER   = "#EB5757"
WARNING  = "#F2C94C"
SUCCESS  = "#27AE60"
TEXT     = "#2D3748"
SUBTEXT  = "#556B8A"
WHITE    = "#FFFFFF"
PURPLE   = "#9B51E0"
ORANGE   = "#F2994A"
SIDEBAR_W = 220

THEMES = {
    "dark": {
        "BG": BG, "PANEL": PANEL, "CARD": CARD,
        "ACCENT": ACCENT, "ACCENT2": ACCENT2,
        "DANGER": DANGER, "WARNING": WARNING,
        "SUCCESS": SUCCESS, "TEXT": TEXT,
        "SUBTEXT": SUBTEXT, "WHITE": WHITE,
        "PURPLE": PURPLE, "ORANGE": ORANGE,
    },
    "light": {
        "BG": "#F4F7FB", "PANEL": "#E4ECF8", "CARD": "#FFFFFF",
        "ACCENT": "#2D9CDB", "ACCENT2": "#56CCF2",
        "DANGER": "#EB5757", "WARNING": "#F2C94C",
        "SUCCESS": "#27AE60", "TEXT": "#2D3748",
        "SUBTEXT": "#556B8A", "WHITE": "#FFFFFF",
        "PURPLE": "#9B51E0", "ORANGE": "#F2994A",
    },
}

# ─────────────────────────────────────────────
#  LOGIN WINDOW
# ─────────────────────────────────────────────
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MediCare — Login")
        self.geometry("460x520")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.logged_in_user = None
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        w, h = 460, 520
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # Header
        header = tk.Frame(self, bg=PANEL, pady=30)
        header.pack(fill="x")
        tk.Label(header, text="MediCare HMS", font=("Segoe UI", 24, "bold"), bg=PANEL, fg=TEXT).pack()
        tk.Label(header, text="Hospital Management System", font=("Segoe UI", 10), bg=PANEL, fg=SUBTEXT).pack()

        # Form
        form = tk.Frame(self, bg=BG, padx=50, pady=30)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Username", font=("Segoe UI", 10), bg=BG, fg=SUBTEXT).pack(anchor="w")
        self.username_e = tk.Entry(form, font=("Segoe UI", 12), bg=CARD, fg=TEXT,
                                    insertbackground=TEXT, relief="flat", bd=8)
        self.username_e.pack(fill="x", pady=(4, 16))
        self.username_e.insert(0, "admin")

        tk.Label(form, text="Password", font=("Segoe UI", 10), bg=BG, fg=SUBTEXT).pack(anchor="w")
        self.password_e = tk.Entry(form, font=("Segoe UI", 12), bg=CARD, fg=TEXT,
                                    insertbackground=TEXT, relief="flat", bd=8, show="●")
        self.password_e.pack(fill="x", pady=(4, 6))
        self.password_e.insert(0, "admin123")

        self.error_lbl = tk.Label(form, text="", font=("Segoe UI", 9), bg=BG, fg=DANGER)
        self.error_lbl.pack(pady=4)

        login_btn = tk.Button(form, text="LOGIN", command=self._login,
                               bg=ACCENT, fg=BG, font=("Segoe UI", 12, "bold"),
                               relief="flat", bd=0, pady=12, cursor="hand2")
        login_btn.pack(fill="x", pady=8)
        self.bind("<Return>", lambda e: self._login())

        # Default credentials hint
        hint = tk.Frame(form, bg=CARD, padx=12, pady=10)
        hint.pack(fill="x", pady=10)
        tk.Label(hint, text="Default Credentials:", font=("Segoe UI", 9, "bold"), bg=CARD, fg=SUBTEXT).pack(anchor="w")
        for role, user, pw in [("Admin", "admin", "admin123"), ("Doctor", "doctor1", "doctor123"), ("Staff", "staff1", "staff123")]:
            tk.Label(hint, text=f"  {role}: {user} / {pw}", font=("Segoe UI", 8), bg=CARD, fg=SUBTEXT).pack(anchor="w")

    def _login(self):
        username = self.username_e.get().strip()
        password = self.password_e.get().strip()
        if not username or not password:
            self.error_lbl.config(text="Please enter username and password.")
            return
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = get_conn()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password_hash=? AND status='Active'",
                             (username, pw_hash)).fetchone()
        conn.close()
        if user:
            self.logged_in_user = {"id": user[0], "username": user[1], "role": user[3], "full_name": user[4]}
            self.destroy()
        else:
            self.error_lbl.config(text="Invalid username or password.")


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class HospitalApp(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.theme_mode = "light"
        self.title(f"MediCare HMS — {user['full_name']} ({user['role']})")
        self.geometry("1366x800")
        self.minsize(1200, 700)
        self.configure(bg=BG)
        self.resizable(True, True)
        self._current_page = None
        self._build_layout()
        self.show_page("dashboard")

    def _build_layout(self):
        if hasattr(self, 'sidebar'):
            self.sidebar.destroy()
        if hasattr(self, 'content'):
            self.content.destroy()
        self.configure(bg=BG)
        self.sidebar = tk.Frame(self, bg=PANEL, width=SIDEBAR_W)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = tk.Frame(self.sidebar, bg=PANEL, pady=16)
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text="MediCare HMS", font=("Segoe UI", 16, "bold"), bg=PANEL, fg=TEXT).pack()
        tk.Label(logo_frame, text=f"{self.current_user['role']}", font=("Segoe UI", 9), bg=PANEL, fg=SUBTEXT).pack()

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=15, pady=4)

        self.nav_buttons = {}
        nav_items = [
            ("dashboard",    "", "Dashboard"),
            ("doctors",      "", "Doctors"),
            ("patients",     "", "Patients"),
            ("appointments", "", "Appointments"),
            ("cabins",       "", "Cabins"),
            ("billing",      "", "Billing"),
            ("lab",          "", "Lab Tests"),
            ("pharmacy",     "", "Pharmacy"),
            ("prescriptions","", "Prescriptions"),
            ("history",      "", "Medical History"),
            ("reports",      "", "Reports"),
        ]
        if self.current_user["role"] == "Admin":
            nav_items.append(("users", "🔐", "User Management"))

        self.nav_frame = tk.Frame(self.sidebar, bg=PANEL)
        self.nav_frame.pack(fill="both", expand=True, pady=4)

        for key, icon, label in nav_items:
            btn = self._nav_btn(self.nav_frame, icon, label, key)
            self.nav_buttons[key] = btn

        # User info footer
        user_frame = tk.Frame(self.sidebar, bg=CARD, padx=10, pady=8)
        user_frame.pack(fill="x", side="bottom", padx=8, pady=8)
        tk.Label(user_frame, text=f"👤 {self.current_user['full_name']}", font=("Segoe UI", 8, "bold"),
                 bg=CARD, fg=WHITE).pack(anchor="w")
        tk.Label(user_frame, text=self.current_user["role"], font=("Segoe UI", 7), bg=CARD, fg=SUBTEXT).pack(anchor="w")
        tk.Button(user_frame, text="Logout", command=self._logout,
                  bg=DANGER, fg=WHITE, font=("Segoe UI", 8, "bold"), relief="flat",
                  bd=0, padx=8, pady=3, cursor="hand2").pack(anchor="e", pady=(4, 0))

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(self.content, bg=PANEL, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self.page_title_lbl = tk.Label(topbar, text="Dashboard", font=("Segoe UI", 15, "bold"),
                                        bg=PANEL, fg=WHITE)
        self.page_title_lbl.pack(side="left", padx=24, pady=12)

        theme_btn = tk.Button(topbar, text="Theme", command=self._toggle_theme,
                               bg=ACCENT2, fg=BG, font=("Segoe UI", 10, "bold"), bd=0,
                               relief="flat", padx=12, pady=8, cursor="hand2",
                               activebackground=ACCENT, activeforeground=BG)
        theme_btn.pack(side="right", padx=10, pady=8)

        notif_btn = tk.Button(topbar, text="Alerts", command=self._show_reminders,
                               bg=WARNING, fg=BG, font=("Segoe UI", 10, "bold"), bd=0,
                               relief="flat", padx=12, pady=8, cursor="hand2",
                               activebackground=ACCENT2, activeforeground=BG)
        notif_btn.pack(side="right", padx=10, pady=8)

        refresh_btn = tk.Button(topbar, text="Refresh", command=self._refresh_page,
                                 bg=ACCENT, fg=BG, font=("Segoe UI", 10, "bold"), bd=0,
                                 relief="flat", padx=12, pady=8, cursor="hand2",
                                 activebackground=ACCENT2, activeforeground=BG)
        refresh_btn.pack(side="right", padx=(0, 10), pady=8)

        now = datetime.datetime.now().strftime("%A, %d %B %Y")
        tk.Label(topbar, text=now, font=("Segoe UI", 9), bg=PANEL, fg=SUBTEXT).pack(side="right", padx=24)

        self.page_area = tk.Frame(self.content, bg=BG)
        self.page_area.pack(fill="both", expand=True, padx=18, pady=16)

    def _nav_btn(self, parent, icon, label, key):
        frame = tk.Frame(parent, bg=PANEL, cursor="hand2")
        frame.pack(fill="x", padx=8, pady=1)

        def enter(e):
            if self._current_page != key:
                frame.config(bg=CARD); lbl_icon.config(bg=CARD); lbl_text.config(bg=CARD)

        def leave(e):
            if self._current_page != key:
                frame.config(bg=PANEL); lbl_icon.config(bg=PANEL); lbl_text.config(bg=PANEL)

        lbl_icon = tk.Label(frame, text=icon, font=("Segoe UI", 12), bg=PANEL, fg=ACCENT, width=3)
        lbl_icon.pack(side="left", padx=(8, 3), pady=8)
        lbl_text = tk.Label(frame, text=label, font=("Segoe UI", 10), bg=PANEL, fg=TEXT, anchor="w")
        lbl_text.pack(side="left", fill="x", expand=True)

        for w in (frame, lbl_icon, lbl_text):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", lambda e, k=key: self.show_page(k))

        return (frame, lbl_icon, lbl_text)

    def _set_active_nav(self, key):
        for k, (frame, lbl_icon, lbl_text) in self.nav_buttons.items():
            if k == key:
                frame.config(bg=ACCENT); lbl_icon.config(bg=ACCENT, fg=BG)
                lbl_text.config(bg=ACCENT, fg=BG, font=("Segoe UI", 10, "bold"))
            else:
                frame.config(bg=PANEL); lbl_icon.config(bg=PANEL, fg=ACCENT)
                lbl_text.config(bg=PANEL, fg=TEXT, font=("Segoe UI", 10))

    def show_page(self, key):
        self._current_page = key
        self._set_active_nav(key)
        titles = {
            "dashboard": "Dashboard", "doctors": "Doctor Management",
            "patients": "Patient Management", "appointments": "Appointments",
            "cabins": "Cabin Management", "billing": "Billing",
            "lab": "Lab Test Module", "pharmacy": "Pharmacy & Medicines",
            "prescriptions": "Prescription Management", "history": "Patient Medical History",
            "reports": "Reports & Analytics", "users": "User Management",
        }
        self.page_title_lbl.config(text=titles.get(key, key.title()))
        for w in self.page_area.winfo_children():
            w.destroy()
        pages = {
            "dashboard": DashboardPage, "doctors": DoctorsPage,
            "patients": PatientsPage, "appointments": AppointmentsPage,
            "cabins": CabinsPage, "billing": BillingPage,
            "lab": LabPage, "pharmacy": PharmacyPage,
            "prescriptions": PrescriptionsPage, "history": MedicalHistoryPage,
            "reports": ReportsPage, "users": UsersPage,
        }
        if key in pages:
            pages[key](self.page_area, self).pack(fill="both", expand=True)

    def _refresh_page(self):
        if self._current_page:
            self.show_page(self._current_page)

    def _toggle_theme(self):
        global BG, PANEL, CARD, ACCENT, ACCENT2, DANGER, WARNING, SUCCESS, TEXT, SUBTEXT, WHITE, PURPLE, ORANGE
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        theme = THEMES[self.theme_mode]
        BG = theme["BG"]; PANEL = theme["PANEL"]; CARD = theme["CARD"]
        ACCENT = theme["ACCENT"]; ACCENT2 = theme["ACCENT2"]
        DANGER = theme["DANGER"]; WARNING = theme["WARNING"]
        SUCCESS = theme["SUCCESS"]; TEXT = theme["TEXT"]
        SUBTEXT = theme["SUBTEXT"]; WHITE = theme["WHITE"]
        PURPLE = theme["PURPLE"]; ORANGE = theme["ORANGE"]
        self._build_layout()
        self.show_page(self._current_page or "dashboard")

    def _show_reminders(self):
        today = datetime.date.today().isoformat()
        conn = get_conn()
        appts = conn.execute("""SELECT p.name,d.name,a.appointment_time,a.reason FROM appointments a
                                JOIN patients p ON a.patient_id=p.id
                                JOIN doctors d ON a.doctor_id=d.id
                                WHERE a.appointment_date=? AND a.status='Scheduled' ORDER BY a.appointment_time""", (today,)).fetchall()
        bills = conn.execute("""SELECT b.bill_number,p.name,b.total FROM bills b
                                JOIN patients p ON b.patient_id=p.id
                                WHERE b.payment_status='Pending' ORDER BY b.created_at""").fetchall()
        conn.close()
        win = tk.Toplevel(self)
        win.title("Today's Reminders")
        win.geometry("540x520")
        win.configure(bg=PANEL)
        tk.Label(win, text="Today's Reminders", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).pack(pady=12)
        body = tk.Text(win, bg=CARD, fg=WHITE, font=("Segoe UI", 10), padx=14, pady=10, bd=0)
        body.pack(fill="both", expand=True, padx=16, pady=8)
        content = ""
        if appts:
            content += "Upcoming Appointments:\n"
            for a in appts:
                content += f" - {a[0]} with {a[1]} at {a[2]}: {a[3] or '-'}\n"
        else:
            content += "No scheduled appointments for today.\n"
        content += "\nPending Bills:\n"
        if bills:
            for b in bills:
                content += f" - {b[0]} ({b[1]}): ৳ {b[2]:,.2f}\n"
        else:
            content += "No pending bills.\n"
        content += "\nUse this panel to review today’s reminders and follow up quickly."
        body.insert("1.0", content)
        body.config(state="disabled")
        styled_button(win, "Close", win.destroy, bg=ACCENT, fg=BG).pack(pady=10)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            start_app()


# ─────────────────────────────────────────────
#  REUSABLE WIDGETS
# ─────────────────────────────────────────────
def card(parent, title, value, color, icon):
    f = tk.Frame(parent, bg=CARD, padx=16, pady=14, relief="flat")
    tk.Label(f, text=icon, font=("Segoe UI", 20), bg=CARD, fg=color).grid(row=0, column=0, rowspan=2, padx=(0,12))
    tk.Label(f, text=str(value), font=("Segoe UI", 22, "bold"), bg=CARD, fg=WHITE).grid(row=0, column=1, sticky="w")
    tk.Label(f, text=title, font=("Segoe UI", 9), bg=CARD, fg=SUBTEXT).grid(row=1, column=1, sticky="w")
    return f

def styled_button(parent, text, command, bg=ACCENT, fg=WHITE, **kw):
    return tk.Button(parent, text=text, command=command,
                     bg=bg, fg=fg, activebackground=ACCENT2, activeforeground=WHITE,
                     font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
                     padx=12, pady=6, cursor="hand2", **kw)

def make_treeview(parent, columns, show="headings", height=12):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview", background=CARD, foreground=TEXT,
                    fieldbackground=CARD, rowheight=28, font=("Segoe UI", 10))
    style.configure("Custom.Treeview.Heading", background=PANEL, foreground=TEXT,
                    font=("Segoe UI", 10, "bold"), relief="flat")
    style.map("Custom.Treeview", background=[("selected", ACCENT)], foreground=[("selected", BG)])
    frame = tk.Frame(parent, bg=BG)
    tree = ttk.Treeview(frame, columns=columns, show=show, height=height, style="Custom.Treeview")
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return frame, tree

def export_table_to_pdf(filename, title, headers, rows, column_widths=None):
    if not REPORTLAB_AVAILABLE:
        messagebox.showwarning("PDF Export", "ReportLab is required to generate PDF files.")
        return
    if not rows:
        messagebox.showinfo("PDF Export", "No data available to export.")
        return
    column_widths = column_widths or [None] * len(headers)
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet(); elements = []
    elements.append(Paragraph(title, ParagraphStyle('title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, textColor=colors.HexColor('#142850'))))
    elements.append(Spacer(1, 6*mm))
    data = [headers] + [[str(col) for col in row] for row in rows]
    table = Table(data, colWidths=column_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#142850')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
        ('FONT', (0,1), (-1,-1), 'Helvetica', 9),
        ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f7fb')]),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(table)
    doc.build(elements)
    messagebox.showinfo("PDF Exported", f"PDF saved as:\n{os.path.abspath(filename)}")

def labeled_entry(parent, label, row, col=0, width=22, colspan=1):
    tk.Label(parent, text=label, bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=row, column=col, sticky="w", padx=8, pady=3)
    e = tk.Entry(parent, width=width, bg=CARD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Segoe UI", 10), bd=4)
    e.grid(row=row+1, column=col, columnspan=colspan, sticky="ew", padx=8, pady=(0,5))
    return e

def labeled_combo(parent, label, values, row, col=0, width=20):
    tk.Label(parent, text=label, bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=row, column=col, sticky="w", padx=8, pady=3)
    cb = ttk.Combobox(parent, values=values, width=width, state="readonly")
    cb.grid(row=row+1, column=col, sticky="ew", padx=8, pady=(0,5))
    return cb


# ─────────────────────────────────────────────
#  DASHBOARD PAGE
# ─────────────────────────────────────────────
class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        conn = get_conn()
        c = conn.cursor()
        total_doctors  = c.execute("SELECT COUNT(*) FROM doctors WHERE status='Active'").fetchone()[0]
        total_patients = c.execute("SELECT COUNT(*) FROM patients WHERE status='Active'").fetchone()[0]
        total_appts    = c.execute("SELECT COUNT(*) FROM appointments WHERE date(appointment_date)=date('now')").fetchone()[0]
        occupied       = c.execute("SELECT COUNT(*) FROM cabins WHERE status='Occupied'").fetchone()[0]
        total_cabins   = c.execute("SELECT COUNT(*) FROM cabins").fetchone()[0]
        pending_bills  = c.execute("SELECT COUNT(*) FROM bills WHERE payment_status='Pending'").fetchone()[0]
        revenue        = c.execute("SELECT SUM(total) FROM bills WHERE payment_status='Paid'").fetchone()[0] or 0
        pending_labs   = c.execute("SELECT COUNT(*) FROM lab_orders WHERE result_status='Pending'").fetchone()[0]
        low_stock      = c.execute("SELECT COUNT(*) FROM medicines WHERE stock_quantity <= reorder_level").fetchone()[0]
        conn.close()

        cards_data = [
            ("Active Doctors",   total_doctors,          ACCENT,   "👨‍⚕️"),
            ("Active Patients",  total_patients,         ACCENT2,  "🧑"),
            ("Today's Appts",    total_appts,            WARNING,  "📅"),
            (f"Cabins {occupied}/{total_cabins}", occupied, SUCCESS, "🛏"),
            ("Pending Bills",    pending_bills,          DANGER,   "💳"),
            (f"Revenue (৳)",     f"{revenue:,.0f}",      PURPLE,   "💰"),
            ("Pending Labs",     pending_labs,           ORANGE,   "🧪"),
            ("Low Stock Items",  low_stock,              DANGER,   "💊"),
        ]

        cards_row = tk.Frame(self, bg=BG)
        cards_row.pack(fill="x")
        for i, (title, val, color, icon) in enumerate(cards_data):
            c_frame = card(cards_row, title, val, color, icon)
            c_frame.grid(row=0, column=i, padx=4, pady=4, sticky="nsew")
            cards_row.columnconfigure(i, weight=1)

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="both", expand=True, pady=8)
        bottom.columnconfigure(0, weight=2)
        bottom.columnconfigure(1, weight=1)

        left = tk.Frame(bottom, bg=CARD, padx=14, pady=14)
        left.grid(row=0, column=0, padx=(0,6), sticky="nsew")
        tk.Label(left, text="Recent Appointments", font=("Segoe UI", 11, "bold"), bg=CARD, fg=WHITE).pack(anchor="w", pady=(0,8))
        cols = ("Patient", "Doctor", "Date", "Status")
        tf, tree = make_treeview(left, cols, height=7)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tf.pack(fill="both", expand=True)

        conn = get_conn()
        rows = conn.execute("""
            SELECT p.name, d.name, a.appointment_date, a.status
            FROM appointments a
            JOIN patients p ON a.patient_id=p.id
            JOIN doctors d ON a.doctor_id=d.id
            ORDER BY a.id DESC LIMIT 7
        """).fetchall()

        right = tk.Frame(bottom, bg=CARD, padx=14, pady=14)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="Cabin Availability", font=("Segoe UI", 11, "bold"), bg=CARD, fg=WHITE).pack(anchor="w", pady=(0,8))
        cabin_rows = conn.execute("""
            SELECT cabin_type, COUNT(*) total,
                   SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) avail
            FROM cabins GROUP BY cabin_type
        """).fetchall()
        conn.close()

        for r in rows:
            tree.insert("", "end", values=r)

        for ctype, total, avail in cabin_rows:
            row_f = tk.Frame(right, bg=CARD)
            row_f.pack(fill="x", pady=3)
            pct = (avail / total * 100) if total else 0
            color = SUCCESS if pct > 50 else (WARNING if pct > 20 else DANGER)
            tk.Label(row_f, text=ctype, font=("Segoe UI", 9), bg=CARD, fg=TEXT, width=14, anchor="w").pack(side="left")
            tk.Label(row_f, text=f"{avail}/{total}", font=("Segoe UI", 9, "bold"), bg=CARD, fg=color).pack(side="right")
            bar_bg = tk.Frame(right, bg="#1a2a3a", height=5)
            bar_bg.pack(fill="x", pady=(0, 3))
            bar_bg.update_idletasks()
            tk.Frame(bar_bg, bg=color, height=5,
                     width=int(max(bar_bg.winfo_width(), 100) * pct / 100)).place(x=0, y=0)


# ─────────────────────────────────────────────
#  DOCTORS PAGE
# ─────────────────────────────────────────────
class DoctorsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.selected_id = None
        self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "+ Add Doctor", self._open_form).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Edit", self._edit, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "📄 Export PDF", self._export_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Search:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._load())
        tk.Entry(sf, textvariable=self.search_var, bg=CARD, fg=WHITE, insertbackground=WHITE,
                 relief="flat", font=("Segoe UI", 10), bd=4, width=30).pack(side="left", padx=8)

        cols = ("ID", "Name", "Specialization", "Phone", "Email", "Experience", "Status")
        tf, self.tree = make_treeview(self, cols, height=18)
        widths = [50, 200, 150, 130, 200, 100, 90]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        q = self.search_var.get().strip()
        conn = get_conn()
        if q:
            rows = conn.execute("SELECT id,name,specialization,phone,email,experience,status FROM doctors WHERE name LIKE ? OR specialization LIKE ?", (f"%{q}%", f"%{q}%")).fetchall()
        else:
            rows = conn.execute("SELECT id,name,specialization,phone,email,experience,status FROM doctors").fetchall()
        conn.close()
        for r in rows: self.tree.insert("", "end", values=r)

    def _on_select(self, e):
        sel = self.tree.selection()
        self.selected_id = self.tree.item(sel[0])["values"][0] if sel else None

    def _open_form(self, data=None): DoctorForm(self, data, self._load)

    def _edit(self):
        if not self.selected_id: messagebox.showwarning("Select", "Please select a doctor first."); return
        conn = get_conn(); row = conn.execute("SELECT * FROM doctors WHERE id=?", (self.selected_id,)).fetchone(); conn.close()
        self._open_form(row)

    def _delete(self):
        if not self.selected_id: messagebox.showwarning("Select", "Please select a doctor first."); return
        if messagebox.askyesno("Confirm", "Delete this doctor?"):
            conn = get_conn(); conn.execute("DELETE FROM doctors WHERE id=?", (self.selected_id,)); conn.commit(); conn.close()
            self._load()

    def _export_pdf(self):
        rows = []
        conn = get_conn(); rows = conn.execute("SELECT id,name,specialization,phone,email,experience,status FROM doctors ORDER BY id ASC").fetchall(); conn.close()
        export_table_to_pdf(f"Doctors_List_{datetime.date.today()}.pdf", "Doctors Directory", ["ID","Name","Specialization","Phone","Email","Experience","Status"], rows, [30*mm, 50*mm, 40*mm, 35*mm, 50*mm, 30*mm, 30*mm])


class DoctorForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("Add Doctor" if not data else "Edit Doctor")
        self.geometry("480x420"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Doctor Details", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.name = labeled_entry(self, "Full Name", 1, 0, 30, 1)
        self.spec = labeled_entry(self, "Specialization", 3, 0, 30, 1)
        self.phone = labeled_entry(self, "Phone", 5, 0, 30, 1)
        self.email = labeled_entry(self, "Email", 7, 0, 30, 1)
        self.exp = labeled_entry(self, "Experience (years)", 9, 0, 30, 1)
        self.status = labeled_combo(self, "Status", ["Active", "Inactive"], 11, 0, 28)
        self.columnconfigure(0, weight=1)
        if self.data:
            for w, v in zip([self.name, self.spec, self.phone, self.email, self.exp],
                            [self.data[1], self.data[2], self.data[3], self.data[4], self.data[5]]):
                w.insert(0, str(v) if v else "")
            self.status.set(self.data[6])
        else:
            self.status.set("Active")
        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=13, column=0, columnspan=2, pady=16)
        styled_button(btn_row, "💾 Save", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        name = self.name.get().strip()
        if not name: messagebox.showerror("Error", "Name is required."); return
        conn = get_conn()
        if self.data:
            conn.execute("UPDATE doctors SET name=?,specialization=?,phone=?,email=?,experience=?,status=? WHERE id=?",
                         (name, self.spec.get(), self.phone.get(), self.email.get(), self.exp.get() or 0, self.status.get(), self.data[0]))
        else:
            conn.execute("INSERT INTO doctors (name,specialization,phone,email,experience,status) VALUES (?,?,?,?,?,?)",
                         (name, self.spec.get(), self.phone.get(), self.email.get(), self.exp.get() or 0, self.status.get()))
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  PATIENTS PAGE
# ─────────────────────────────────────────────
class PatientsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None; self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG); toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "+ Add Patient", self._open_form).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Edit", self._edit, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "📋 History", self._view_history, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "📄 Export PDF", self._export_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(self, bg=BG); sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Search:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.search_var = tk.StringVar(); self.search_var.trace("w", lambda *a: self._load())
        tk.Entry(sf, textvariable=self.search_var, bg=CARD, fg=WHITE, insertbackground=WHITE,
                 relief="flat", font=("Segoe UI", 10), bd=4, width=30).pack(side="left", padx=8)

        cols = ("ID", "Patient ID", "Name", "Age", "Gender", "Phone", "Blood", "Disease", "Status")
        tf, self.tree = make_treeview(self, cols, height=18)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")
        self.tree.column("Name", width=150); self.tree.column("Disease", width=140)
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select); self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        q = self.search_var.get().strip(); conn = get_conn()
        if q:
            rows = conn.execute("SELECT id,patient_id,name,age,gender,phone,blood_group,disease,status FROM patients WHERE name LIKE ? OR patient_id LIKE ?", (f"%{q}%", f"%{q}%")).fetchall()
        else:
            rows = conn.execute("SELECT id,patient_id,name,age,gender,phone,blood_group,disease,status FROM patients").fetchall()
        conn.close()
        for r in rows: self.tree.insert("", "end", values=r)

    def _on_select(self, e):
        sel = self.tree.selection()
        self.selected_id = self.tree.item(sel[0])["values"][0] if sel else None

    def _open_form(self, data=None): PatientForm(self, data, self._load)

    def _edit(self):
        if not self.selected_id: messagebox.showwarning("Select", "Please select a patient first."); return
        conn = get_conn(); row = conn.execute("SELECT * FROM patients WHERE id=?", (self.selected_id,)).fetchone(); conn.close()
        self._open_form(row)

    def _delete(self):
        if not self.selected_id: messagebox.showwarning("Select", "Please select a patient first."); return
        if messagebox.askyesno("Confirm", "Delete this patient?"):
            conn = get_conn(); conn.execute("DELETE FROM patients WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load()

    def _export_pdf(self):
        rows = []
        conn = get_conn(); rows = conn.execute("SELECT id,patient_id,name,age,gender,phone,blood_group,disease,status FROM patients ORDER BY id ASC").fetchall(); conn.close()
        export_table_to_pdf(f"Patients_List_{datetime.date.today()}.pdf", "Patients Directory", ["ID","Patient ID","Name","Age","Gender","Phone","Blood","Disease","Status"], rows, [25*mm, 35*mm, 40*mm, 20*mm, 25*mm, 30*mm, 30*mm, 35*mm, 25*mm])

    def _view_history(self):
        if not self.selected_id: messagebox.showwarning("Select", "Please select a patient first."); return
        self.app.show_page("history")


class PatientForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("Add Patient" if not data else "Edit Patient")
        self.geometry("520x520"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Patient Details", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=4, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1, 2, 3), weight=1)
        self.name = labeled_entry(self, "Full Name *", 1, 0, 20, 3)
        self.age = labeled_entry(self, "Age", 3, 0, 8)
        self.gender = labeled_combo(self, "Gender", ["Male", "Female", "Other"], 3, 1)
        self.phone = labeled_entry(self, "Phone", 5, 0, 20, 1)
        self.blood = labeled_combo(self, "Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-"], 5, 2)
        self.disease = labeled_entry(self, "Disease / Diagnosis", 7, 0, 40, 3)
        tk.Label(self, text="Address", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=9, column=0, sticky="w", padx=8, pady=3)
        self.address = tk.Text(self, width=46, height=3, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 10), bd=4)
        self.address.grid(row=10, column=0, columnspan=4, sticky="ew", padx=8, pady=(0,5))
        self.status = labeled_combo(self, "Status", ["Active", "Discharged"], 11, 0)
        if self.data:
            for w, v in zip([self.name, self.age, self.phone], [self.data[2], self.data[3], self.data[5]]):
                w.insert(0, str(v) if v else "")
            self.gender.set(self.data[4] or ""); self.blood.set(self.data[7] or "")
            self.disease.insert(0, self.data[8] or ""); self.address.insert("1.0", self.data[6] or ""); self.status.set(self.data[9] or "Active")
        else:
            self.gender.set("Male"); self.blood.set("O+"); self.status.set("Active")
        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=13, column=0, columnspan=4, pady=16)
        styled_button(btn_row, "💾 Save", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        name = self.name.get().strip()
        if not name: messagebox.showerror("Error", "Name is required."); return
        conn = get_conn()
        if self.data:
            conn.execute("UPDATE patients SET name=?,age=?,gender=?,phone=?,address=?,blood_group=?,disease=?,status=? WHERE id=?",
                         (name, self.age.get() or 0, self.gender.get(), self.phone.get(), self.address.get("1.0","end").strip(), self.blood.get(), self.disease.get(), self.status.get(), self.data[0]))
        else:
            pid = gen_patient_id()
            conn.execute("INSERT INTO patients (patient_id,name,age,gender,phone,address,blood_group,disease,status) VALUES (?,?,?,?,?,?,?,?,?)",
                         (pid, name, self.age.get() or 0, self.gender.get(), self.phone.get(), self.address.get("1.0","end").strip(), self.blood.get(), self.disease.get(), self.status.get()))
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  APPOINTMENTS PAGE
# ─────────────────────────────────────────────
class AppointmentsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None; self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG); toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "+ New Appointment", self._open_form).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Edit", self._edit, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔔 Reminders", self.app._show_reminders, bg=WARNING, fg=BG).pack(side="left", padx=4)
        styled_button(toolbar, "📄 Export PDF", self._export_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(self, bg=BG); sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Filter:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        for opt in ["All", "Scheduled", "Completed", "Cancelled"]:
            tk.Radiobutton(sf, text=opt, variable=self.filter_var, value=opt, bg=BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=BG, font=("Segoe UI", 10), command=self._load).pack(side="left", padx=6)

        self.selected_date = datetime.date.today()
        self.cal_year = self.selected_date.year
        self.cal_month = self.selected_date.month
        self.calendar_frame = tk.Frame(self, bg=BG); self.calendar_frame.pack(fill="x", pady=(0, 8))
        nav = tk.Frame(self.calendar_frame, bg=BG); nav.pack(fill="x")
        tk.Button(nav, text="◀", command=self._prev_month, bg=CARD, fg=TEXT, bd=0, relief="flat", cursor="hand2").pack(side="left", padx=4)
        self.month_label = tk.Label(nav, text=self.selected_date.strftime("%B %Y"), bg=BG, fg=WHITE, font=("Segoe UI", 10, "bold"))
        self.month_label.pack(side="left", padx=8)
        tk.Button(nav, text="▶", command=self._next_month, bg=CARD, fg=TEXT, bd=0, relief="flat", cursor="hand2").pack(side="left", padx=4)
        tk.Button(nav, text="Today", command=self._select_today, bg=ACCENT, fg=BG, bd=0, relief="flat", cursor="hand2").pack(side="right", padx=4)
        self.calendar_days = tk.Frame(self.calendar_frame, bg=BG)
        self.calendar_days.pack(fill="x", pady=(6,0))
        self._draw_month_calendar()

        cols = ("ID", "Patient", "Doctor", "Date", "Time", "Reason", "Status")
        tf, self.tree = make_treeview(self, cols, height=18)
        for col in cols:
            self.tree.heading(col, text=col); self.tree.column(col, width=100, anchor="center")
        self.tree.column("Patient", width=160); self.tree.column("Doctor", width=160); self.tree.column("Reason", width=180)
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select); self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_conn(); f = self.filter_var.get()
        q = """SELECT a.id, p.name, d.name, a.appointment_date, a.appointment_time, a.reason, a.status
               FROM appointments a JOIN patients p ON a.patient_id=p.id JOIN doctors d ON a.doctor_id=d.id"""
        where_clauses = []
        params = []
        if f != "All":
            where_clauses.append("a.status=?")
            params.append(f)
        if self.selected_date:
            where_clauses.append("a.appointment_date=?")
            params.append(self.selected_date.isoformat())
        if where_clauses:
            q += " WHERE " + " AND ".join(where_clauses)
        q += " ORDER BY a.appointment_time ASC"
        rows = conn.execute(q, tuple(params)).fetchall()
        conn.close()
        for r in rows:
            tag = {"Scheduled": "sched", "Completed": "done", "Cancelled": "cancel"}.get(r[6], "")
            self.tree.insert("", "end", values=r, tags=(tag,))
        self.tree.tag_configure("done", foreground=SUCCESS)
        self.tree.tag_configure("cancel", foreground=DANGER)
        self.tree.tag_configure("sched", foreground=WARNING)

    def _on_select(self, e):
        sel = self.tree.selection()
        self.selected_id = self.tree.item(sel[0])["values"][0] if sel else None

    def _open_form(self, data=None): AppointmentForm(self, data, self._load)

    def _edit(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select an appointment."); return
        conn = get_conn(); row = conn.execute("SELECT * FROM appointments WHERE id=?", (self.selected_id,)).fetchone(); conn.close()
        self._open_form(row)

    def _delete(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select an appointment."); return
        if messagebox.askyesno("Confirm", "Delete this appointment?"):
            conn = get_conn(); conn.execute("DELETE FROM appointments WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load()

    def _export_pdf(self):
        conn = get_conn(); f = self.filter_var.get()
        q = """SELECT a.id,p.name,d.name,a.appointment_date,a.appointment_time,a.reason,a.status
               FROM appointments a JOIN patients p ON a.patient_id=p.id JOIN doctors d ON a.doctor_id=d.id"""
        where_clauses = []
        params = []
        if f != "All":
            where_clauses.append("a.status=?"); params.append(f)
        if self.selected_date:
            where_clauses.append("a.appointment_date=?"); params.append(self.selected_date.isoformat())
        if where_clauses:
            q += " WHERE " + " AND ".join(where_clauses)
        q += " ORDER BY a.appointment_time ASC"
        rows = conn.execute(q, tuple(params)).fetchall(); conn.close()
        export_table_to_pdf(f"Appointments_{datetime.date.today()}.pdf", "Appointment Schedule", ["ID","Patient","Doctor","Date","Time","Reason","Status"], rows, [20*mm, 35*mm, 35*mm, 25*mm, 20*mm, 45*mm, 25*mm])

    def _draw_month_calendar(self):
        for widget in self.calendar_days.winfo_children():
            widget.destroy()
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days_of_week):
            tk.Label(self.calendar_days, text=day, bg=BG, fg=SUBTEXT,
                     font=("Segoe UI", 8, "bold"), width=10, padx=2, pady=2).grid(row=0, column=i, padx=1, pady=1)
        first_weekday, total_days = calendar.monthrange(self.cal_year, self.cal_month)
        row, col = 1, first_weekday
        for day in range(1, total_days + 1):
            date_obj = datetime.date(self.cal_year, self.cal_month, day)
            selected = date_obj == self.selected_date
            btn_bg = ACCENT if selected else CARD
            btn_fg = BG if selected else TEXT
            btn = tk.Button(self.calendar_days, text=str(day), bg=btn_bg, fg=btn_fg,
                            relief="flat", bd=0, cursor="hand2",
                            activebackground=ACCENT2, activeforeground=BG,
                            command=lambda d=date_obj: self._select_date(d))
            btn.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
            self.calendar_days.grid_columnconfigure(col, weight=1)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _select_date(self, date_obj):
        self.selected_date = date_obj
        self.month_label.config(text=self.selected_date.strftime("%B %Y"))
        self._draw_month_calendar()
        self._load()

    def _prev_month(self):
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1
        self.month_label.config(text=datetime.date(self.cal_year, self.cal_month, 1).strftime("%B %Y"))
        self._draw_month_calendar()

    def _next_month(self):
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1
        self.month_label.config(text=datetime.date(self.cal_year, self.cal_month, 1).strftime("%B %Y"))
        self._draw_month_calendar()

    def _select_today(self):
        self.selected_date = datetime.date.today()
        self.cal_year = self.selected_date.year
        self.cal_month = self.selected_date.month
        self.month_label.config(text=self.selected_date.strftime("%B %Y"))
        self._draw_month_calendar()
        self._load()


class AppointmentForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("Book Appointment" if not data else "Edit Appointment")
        self.geometry("480x440"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Appointment Details", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1), weight=1)
        conn = get_conn()
        patients = conn.execute("SELECT id,name FROM patients WHERE status='Active'").fetchall()
        doctors  = conn.execute("SELECT id,name FROM doctors WHERE status='Active'").fetchall()
        conn.close()
        self.patient_map = {p[1]: p[0] for p in patients}
        self.doctor_map  = {d[1]: d[0] for d in doctors}

        tk.Label(self, text="Patient *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=8)
        self.patient_cb = ttk.Combobox(self, values=list(self.patient_map.keys()), width=26, state="readonly")
        self.patient_cb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))

        tk.Label(self, text="Doctor *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", padx=8)
        self.doctor_cb = ttk.Combobox(self, values=list(self.doctor_map.keys()), width=26, state="readonly")
        self.doctor_cb.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))

        self.date = labeled_entry(self, "Date (YYYY-MM-DD) *", 5, 0)
        self.time = labeled_entry(self, "Time (HH:MM) *", 5, 1)
        self.reason = labeled_entry(self, "Reason / Symptoms", 7, 0, 40, 2)
        self.status = labeled_combo(self, "Status", ["Scheduled", "Completed", "Cancelled"], 9, 0)

        if self.data:
            conn = get_conn()
            pt = conn.execute("SELECT name FROM patients WHERE id=?", (self.data[1],)).fetchone()
            dr = conn.execute("SELECT name FROM doctors WHERE id=?", (self.data[2],)).fetchone()
            conn.close()
            if pt: self.patient_cb.set(pt[0])
            if dr: self.doctor_cb.set(dr[0])
            self.date.insert(0, self.data[3] or ""); self.time.insert(0, self.data[4] or "")
            self.reason.insert(0, self.data[5] or ""); self.status.set(self.data[6] or "Scheduled")
        else:
            self.date.insert(0, datetime.date.today().isoformat()); self.time.insert(0, "10:00"); self.status.set("Scheduled")

        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=11, column=0, columnspan=2, pady=16)
        styled_button(btn_row, "💾 Save", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        pname = self.patient_cb.get(); dname = self.doctor_cb.get()
        date = self.date.get().strip(); time_ = self.time.get().strip()
        if not all([pname, dname, date, time_]):
            messagebox.showerror("Error", "All required fields must be filled.")
            return
        if not validate_date(date):
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return
        if not validate_time(time_):
            messagebox.showerror("Error", "Time must be in HH:MM format (24-hour).")
            return
        pid = self.patient_map.get(pname); did = self.doctor_map.get(dname)
        conn = get_conn()
        conflict_query = "SELECT id FROM appointments WHERE doctor_id=? AND appointment_date=? AND appointment_time=? AND status<>?"
        params = (did, date, time_, "Cancelled")
        if self.data:
            conflict_query += " AND id<>?"
            params = (did, date, time_, "Cancelled", self.data[0])
        conflict = conn.execute(conflict_query, params).fetchone()
        if conflict:
            messagebox.showerror("Error", "This doctor already has an appointment at the selected date and time.")
            conn.close()
            return
        if self.data:
            conn.execute("UPDATE appointments SET patient_id=?,doctor_id=?,appointment_date=?,appointment_time=?,reason=?,status=? WHERE id=?",
                         (pid, did, date, time_, self.reason.get(), self.status.get(), self.data[0]))
        else:
            conn.execute("INSERT INTO appointments (patient_id,doctor_id,appointment_date,appointment_time,reason,status) VALUES (?,?,?,?,?,?)",
                         (pid, did, date, time_, self.reason.get(), self.status.get()))
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  CABINS PAGE
# ─────────────────────────────────────────────
class CabinsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None; self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG); toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "✅ Admit Patient", self._admit).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "🚪 Discharge", self._discharge, bg=WARNING, fg=BG).pack(side="left", padx=4)
        styled_button(toolbar, "📄 Export PDF", self._export_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(self, bg=BG); sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Filter:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        for opt in ["All", "Available", "Occupied"]:
            tk.Radiobutton(sf, text=opt, variable=self.filter_var, value=opt, bg=BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=BG, font=("Segoe UI", 10), command=self._load).pack(side="left", padx=6)

        cols = ("ID", "Cabin No.", "Type", "Floor", "Price/Day (৳)", "Status", "Patient", "Admitted")
        tf, self.tree = make_treeview(self, cols, height=18)
        widths = [50, 90, 110, 60, 120, 100, 180, 120]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select); self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        f = self.filter_var.get(); conn = get_conn()
        base = "SELECT c.id,c.cabin_number,c.cabin_type,c.floor,c.price_per_day,c.status,p.name,c.admitted_date FROM cabins c LEFT JOIN patients p ON c.patient_id=p.id"
        rows = conn.execute(base + (" WHERE c.status=?" if f != "All" else ""), (f,) if f != "All" else ()).fetchall()
        conn.close()
        for r in rows:
            rv = list(r); rv[6] = rv[6] or "-"; rv[7] = rv[7] or "-"
            self.tree.insert("", "end", values=rv, tags=("avail" if r[5] == "Available" else "occ",))
        self.tree.tag_configure("avail", foreground=SUCCESS); self.tree.tag_configure("occ", foreground=WARNING)

    def _on_select(self, e):
        sel = self.tree.selection()
        self.selected_id = self.tree.item(sel[0])["values"][0] if sel else None

    def _admit(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a cabin first."); return
        conn = get_conn(); cabin = conn.execute("SELECT * FROM cabins WHERE id=?", (self.selected_id,)).fetchone(); conn.close()
        if cabin[5] == "Occupied": messagebox.showwarning("Occupied", "This cabin is already occupied."); return
        AdmitForm(self, self.selected_id, self._load)

    def _discharge(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a cabin first."); return
        conn = get_conn(); cabin = conn.execute("SELECT * FROM cabins WHERE id=?", (self.selected_id,)).fetchone()
        if cabin[5] != "Occupied": messagebox.showwarning("Not Occupied", "This cabin has no patient."); conn.close(); return
        if messagebox.askyesno("Discharge", f"Discharge patient from cabin {cabin[1]}?"):
            conn.execute("UPDATE cabins SET status='Available',patient_id=NULL,admitted_date=NULL WHERE id=?", (self.selected_id,)); conn.commit()
        conn.close(); self._load()

    def _export_pdf(self,mm):
        conn = get_conn(); f = self.filter_var.get()
        base = "SELECT c.id,c.cabin_number,c.cabin_type,c.floor,c.price_per_day,c.status,p.name,c.admitted_date FROM cabins c LEFT JOIN patients p ON c.patient_id=p.id"
        rows = conn.execute(base + (" WHERE c.status=? ORDER BY c.id ASC" if f != "All" else " ORDER BY c.id ASC"), (f,) if f != "All" else ()).fetchall()
        conn.close()
        formatted = [[r[0], r[1], r[2], r[3], f"৳ {r[4]:,.2f}", r[5], r[6] or "-", r[7] or "-"] for r in rows]
        export_table_to_pdf(f"Cabins_{datetime.date.today()}.pdf", "Cabin Availability", ["ID","Cabin","Type","Floor","Price","Status","Patient","Admitted"], formatted, [20*mm, 25*mm, 30*mm, 20*mm, 25*mm, 25*mm, 35*mm, 30*mm])


class AdmitForm(tk.Toplevel):
    def __init__(self, parent, cabin_id, callback):
        super().__init__(parent)
        self.cabin_id = cabin_id; self.callback = callback
        self.title("Admit Patient"); self.geometry("400x240"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Admit Patient to Cabin", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).pack(pady=14, padx=20, anchor="w")
        conn = get_conn(); patients = conn.execute("SELECT id,name FROM patients WHERE status='Active'").fetchall(); conn.close()
        self.patient_map = {p[1]: p[0] for p in patients}
        f = tk.Frame(self, bg=PANEL); f.pack(fill="x", padx=20)
        tk.Label(f, text="Select Patient *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).pack(anchor="w")
        self.patient_cb = ttk.Combobox(f, values=list(self.patient_map.keys()), width=36, state="readonly"); self.patient_cb.pack(fill="x", pady=4)
        tk.Label(f, text="Admit Date *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).pack(anchor="w", pady=(6,0))
        self.date_e = tk.Entry(f, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 10), bd=4)
        self.date_e.insert(0, datetime.date.today().isoformat()); self.date_e.pack(fill="x", pady=4)
        btn_row = tk.Frame(self, bg=PANEL); btn_row.pack(pady=14)
        styled_button(btn_row, "✅ Admit", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        pname = self.patient_cb.get(); date = self.date_e.get().strip()
        if not pname or not date: messagebox.showerror("Error", "All fields required."); return
        pid = self.patient_map.get(pname); conn = get_conn()
        conn.execute("UPDATE cabins SET status='Occupied',patient_id=?,admitted_date=? WHERE id=?", (pid, date, self.cabin_id)); conn.commit(); conn.close()
        self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  BILLING PAGE (with PDF export)
# ─────────────────────────────────────────────
class BillingPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None; self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG); toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "+ Create Bill", self._open_form).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Edit", self._edit, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "✅ Mark Paid", self._mark_paid, bg=SUCCESS, fg=BG).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🖨 Print/PDF", self._print_bill, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "📄 Export Report", self._export_billing_report, bg=ACCENT2, fg=BG).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(self, bg=BG); sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Filter:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        for opt in ["All", "Pending", "Paid"]:
            tk.Radiobutton(sf, text=opt, variable=self.filter_var, value=opt, bg=BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=BG, font=("Segoe UI", 10), command=self._load).pack(side="left", padx=6)

        cols = ("ID", "Bill No.", "Patient", "Doc Fee", "Cabin", "Medicine", "Lab", "Other", "Total ৳", "Status", "Date")
        tf, self.tree = make_treeview(self, cols, height=15)
        widths = [40, 100, 150, 80, 70, 80, 70, 70, 90, 80, 100]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.summary_lbl = tk.Label(self, text="", font=("Segoe UI", 10, "bold"), bg=PANEL, fg=WHITE, pady=6)
        self.summary_lbl.pack(fill="x", pady=(6, 0))
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        f = self.filter_var.get(); conn = get_conn()
        base = """SELECT b.id,b.bill_number,p.name,b.doctor_fee,b.cabin_charge,b.medicine_charge,
                  b.lab_charge,b.other_charge,b.total,b.payment_status,b.created_at
                  FROM bills b JOIN patients p ON b.patient_id=p.id"""
        rows = conn.execute(base + (" WHERE b.payment_status=? ORDER BY b.id DESC" if f != "All" else " ORDER BY b.id DESC"),
                             (f,) if f != "All" else ()).fetchall()
        total_rev = conn.execute("SELECT SUM(total) FROM bills WHERE payment_status='Paid'").fetchone()[0] or 0
        pending = conn.execute("SELECT COUNT(*) FROM bills WHERE payment_status='Pending'").fetchone()[0]
        conn.close()
        for r in rows:
            tag = "paid" if r[9] == "Paid" else "pend"
            self.tree.insert("", "end", values=r, tags=(tag,))
        self.tree.tag_configure("paid", foreground=SUCCESS); self.tree.tag_configure("pend", foreground=WARNING)
        self.summary_lbl.config(text=f"   💰 Total Revenue: ৳{total_rev:,.2f}   |   ⏳ Pending Bills: {pending}")

    def _on_select(self, e):
        sel = self.tree.selection()
        self.selected_id = self.tree.item(sel[0])["values"][0] if sel else None

    def _open_form(self, data=None): BillForm(self, data, self._load)

    def _edit(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a bill first."); return
        conn = get_conn(); row = conn.execute("SELECT * FROM bills WHERE id=?", (self.selected_id,)).fetchone(); conn.close()
        self._open_form(row)

    def _mark_paid(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a bill first."); return
        conn = get_conn(); conn.execute("UPDATE bills SET payment_status='Paid' WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a bill first."); return
        if messagebox.askyesno("Confirm", "Delete this bill?"):
            conn = get_conn(); conn.execute("DELETE FROM bills WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load()

    def _export_billing_report(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showwarning("PDF Export", "ReportLab is required to generate PDF reports.")
            return
        f = self.filter_var.get(); conn = get_conn()
        base = """SELECT b.bill_number,p.name,b.doctor_fee,b.cabin_charge,b.medicine_charge,b.lab_charge,b.other_charge,b.total,b.payment_status,b.created_at
                  FROM bills b JOIN patients p ON b.patient_id=p.id"""
        rows = conn.execute(base + (" WHERE b.payment_status=? ORDER BY b.id DESC" if f != "All" else " ORDER BY b.id DESC"),
                             (f,) if f != "All" else ()).fetchall()
        total_rev = conn.execute("SELECT SUM(total) FROM bills WHERE payment_status='Paid'").fetchone()[0] or 0
        pending = conn.execute("SELECT COUNT(*) FROM bills WHERE payment_status='Pending'").fetchone()[0]
        paid = conn.execute("SELECT COUNT(*) FROM bills WHERE payment_status='Paid'").fetchone()[0]
        conn.close()

        filename = f"Billing_Report_{datetime.date.today()}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet(); elements = []
        elements.append(Paragraph("🏥 MediCare Hospital Management", styles['Title']))
        elements.append(Paragraph(f"Billing Report ({f})", ParagraphStyle('subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=11, textColor=colors.HexColor('#4B6584'))))
        elements.append(Spacer(1, 6*mm))
        summary_data = [
            ["Filter", f],
            ["Total Bills", str(len(rows))],
            ["Paid Bills", str(paid)],
            ["Pending Bills", str(pending)],
            ["Total Revenue (Paid)", f"৳ {total_rev:,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[90*mm, 70*mm])
        summary_table.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), 'Helvetica', 10),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B2A3B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(summary_table); elements.append(Spacer(1, 8*mm))

        table_data = [["Bill No.", "Patient", "Total ৳", "Status", "Date"]]
        for row in rows:
            table_data.append([row[0], row[1], f"৳ {row[7]:,.2f}", row[8], row[9][:10] if row[9] else "-"])
        report_table = Table(table_data, colWidths=[40*mm, 50*mm, 30*mm, 30*mm, 40*mm])
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#142850')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
            ('FONT', (0,1), (-1,-1), 'Helvetica', 9),
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f4f8')]),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(report_table)
        doc.build(elements)
        messagebox.showinfo("PDF Exported", f"Billing report saved as:\n{os.path.abspath(filename)}")

    def _print_bill(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a bill first."); return
        conn = get_conn()
        bill = conn.execute("SELECT b.*,p.name,p.patient_id,p.phone,p.address FROM bills b JOIN patients p ON b.patient_id=p.id WHERE b.id=?", (self.selected_id,)).fetchone()
        conn.close()
        if not bill: return
        if REPORTLAB_AVAILABLE:
            self._export_pdf(bill)
        else:
            self._print_text(bill)

    def _print_text(self, bill):
        win = tk.Toplevel(self); win.title("Bill Preview"); win.geometry("500x600")
        win.configure(bg=PANEL)
        tk.Label(win, text="🖨 Bill Receipt", font=("Segoe UI", 16, "bold"), bg=PANEL, fg=WHITE).pack(pady=12)
        txt = tk.Text(win, bg=CARD, fg=WHITE, font=("Courier", 11), padx=20, pady=10)
        txt.pack(fill="both", expand=True, padx=16, pady=8)
        content = f"""
{'='*45}
         MediCare Hospital Management
              Bill Receipt
{'='*45}
Bill No    : {bill[2]}
Date       : {bill[11]}
Patient    : {bill[12]}
Patient ID : {bill[13]}
Phone      : {bill[14]}
{'-'*45}
Doctor Fee       : ৳ {bill[3]:>10,.2f}
Cabin Charge     : ৳ {bill[4]:>10,.2f}
Medicine Charge  : ৳ {bill[5]:>10,.2f}
Lab Charge       : ৳ {bill[6]:>10,.2f}
Other Charges    : ৳ {bill[7]:>10,.2f}
{'-'*45}
TOTAL            : ৳ {bill[8]:>10,.2f}
{'-'*45}
Payment Status   : {bill[9]}
{'='*45}
     Thank you for choosing MediCare!
{'='*45}
"""
        txt.insert("1.0", content); txt.config(state="disabled")
        styled_button(win, "Close", win.destroy, bg=DANGER, fg=WHITE).pack(pady=8)

    def _export_pdf(self, bill):
        filename = f"Bill_{bill[2]}_{datetime.date.today()}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        elements = []
        title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18, spaceAfter=4)
        sub_style = ParagraphStyle('sub', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, spaceAfter=12)
        elements.append(Paragraph("🏥 MediCare Hospital Management System", title_style))
        elements.append(Paragraph("Bill Receipt", sub_style))
        elements.append(Spacer(1, 5*mm))
        info_data = [
            ["Bill Number:", bill[2], "Date:", bill[11][:10] if bill[11] else ""],
            ["Patient:", bill[12], "Patient ID:", bill[13] or ""],
            ["Phone:", bill[14] or "", "Status:", bill[9]],
        ]
        info_table = Table(info_data, colWidths=[40*mm, 60*mm, 40*mm, 60*mm])
        info_table.setStyle(TableStyle([('FONT', (0,0), (-1,-1), 'Helvetica', 10), ('FONT', (0,0), (0,-1), 'Helvetica-Bold', 10), ('FONT', (2,0), (2,-1), 'Helvetica-Bold', 10), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')), ('BOX', (0,0), (-1,-1), 0.5, colors.grey), ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey), ('PADDING', (0,0), (-1,-1), 6)]))
        elements.append(info_table); elements.append(Spacer(1, 6*mm))
        charge_data = [["Description", "Amount (৳)"],
                       ["Doctor Fee", f"৳ {bill[3]:,.2f}"], ["Cabin Charge", f"৳ {bill[4]:,.2f}"],
                       ["Medicine Charge", f"৳ {bill[5]:,.2f}"], ["Lab Charge", f"৳ {bill[6]:,.2f}"],
                       ["Other Charges", f"৳ {bill[7]:,.2f}"], ["TOTAL", f"৳ {bill[8]:,.2f}"]]
        charge_table = Table(charge_data, colWidths=[120*mm, 60*mm])
        charge_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B2A3B')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 11), ('FONT', (0,1), (-1,-2), 'Helvetica', 10),
            ('FONT', (0,-1), (-1,-1), 'Helvetica-Bold', 12), ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#00C9A7')),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.white), ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BOX', (0,0), (-1,-1), 1, colors.grey), ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 8), ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f8f9fa')])]))
        elements.append(charge_table); elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("Thank you for choosing MediCare Hospital!", ParagraphStyle('footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)))
        doc.build(elements)
        messagebox.showinfo("PDF Exported", f"Bill saved as:\n{os.path.abspath(filename)}")


class BillForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("Create Bill" if not data else "Edit Bill")
        self.geometry("480x520"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Bill Details", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1), weight=1)
        conn = get_conn(); patients = conn.execute("SELECT id,name FROM patients").fetchall(); conn.close()
        self.patient_map = {p[1]: p[0] for p in patients}
        tk.Label(self, text="Patient *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=8)
        self.patient_cb = ttk.Combobox(self, values=list(self.patient_map.keys()), width=28, state="readonly")
        self.patient_cb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))
        self.doc_fee = labeled_entry(self, "Doctor Fee (৳)", 3, 0, 18)
        self.cabin_c = labeled_entry(self, "Cabin Charge (৳)", 3, 1, 18)
        self.med_c = labeled_entry(self, "Medicine Charge (৳)", 5, 0, 18)
        self.lab_c = labeled_entry(self, "Lab Charge (৳)", 5, 1, 18)
        self.other_c = labeled_entry(self, "Other Charges (৳)", 7, 0, 18)
        for e in [self.doc_fee, self.cabin_c, self.med_c, self.lab_c, self.other_c]:
            e.bind("<KeyRelease>", self._calc_total)
        tk.Label(self, text="Total Amount (৳)", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=9, column=0, sticky="w", padx=8, pady=(6,2))
        self.total_lbl = tk.Label(self, text="৳ 0.00", font=("Segoe UI", 18, "bold"), bg=PANEL, fg=ACCENT)
        self.total_lbl.grid(row=10, column=0, columnspan=2, padx=8, pady=(0,6), sticky="w")
        self.status = labeled_combo(self, "Payment Status", ["Pending", "Paid"], 11, 0)
        if self.data:
            conn = get_conn(); pt = conn.execute("SELECT name FROM patients WHERE id=?", (self.data[1],)).fetchone(); conn.close()
            if pt: self.patient_cb.set(pt[0])
            for w, v in zip([self.doc_fee, self.cabin_c, self.med_c, self.lab_c, self.other_c],
                             [self.data[3], self.data[4], self.data[5], self.data[6], self.data[7]]):
                w.insert(0, str(v))
            self.total_lbl.config(text=f"৳ {self.data[8]:,.2f}"); self.status.set(self.data[9])
        else:
            self.status.set("Pending")
            for e in [self.doc_fee, self.cabin_c, self.med_c, self.lab_c, self.other_c]: e.insert(0, "0")
        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=13, column=0, columnspan=2, pady=16)
        styled_button(btn_row, "💾 Save Bill", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _calc_total(self, *_):
        def val(e):
            try: return float(e.get())
            except: return 0.0
        total = val(self.doc_fee) + val(self.cabin_c) + val(self.med_c) + val(self.lab_c) + val(self.other_c)
        self.total_lbl.config(text=f"৳ {total:,.2f}")

    def _save(self):
        pname = self.patient_cb.get()
        if not pname: messagebox.showerror("Error", "Patient is required."); return
        pid = self.patient_map.get(pname)
        def val(e):
            try: return float(e.get())
            except: return 0.0
        df = val(self.doc_fee); cc = val(self.cabin_c); mc = val(self.med_c); lc = val(self.lab_c); oc = val(self.other_c)
        total = df + cc + mc + lc + oc
        conn = get_conn()
        if self.data:
            conn.execute("UPDATE bills SET patient_id=?,doctor_fee=?,cabin_charge=?,medicine_charge=?,lab_charge=?,other_charge=?,total=?,payment_status=? WHERE id=?",
                         (pid, df, cc, mc, lc, oc, total, self.status.get(), self.data[0]))
        else:
            bnum = gen_bill_number()
            conn.execute("INSERT INTO bills (bill_number,patient_id,doctor_fee,cabin_charge,medicine_charge,lab_charge,other_charge,total,payment_status) VALUES (?,?,?,?,?,?,?,?,?)",
                         (bnum, pid, df, cc, mc, lc, oc, total, self.status.get()))
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  LAB TEST PAGE
# ─────────────────────────────────────────────
class LabPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        style = ttk.Style(); style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT, padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", BG)])

        self.orders_tab = tk.Frame(nb, bg=BG); nb.add(self.orders_tab, text="  📋 Lab Orders  ")
        self.tests_tab = tk.Frame(nb, bg=BG); nb.add(self.tests_tab, text="  🧪 Test Catalog  ")
        self._build_orders(self.orders_tab)
        self._build_catalog(self.tests_tab)

    def _build_orders(self, parent):
        toolbar = tk.Frame(parent, bg=BG); toolbar.pack(fill="x", pady=(8, 6))
        styled_button(toolbar, "+ New Order", lambda: LabOrderForm(self, None, self._load_orders)).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Enter Result", self._enter_result, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete_order, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "📄 Export PDF", self._export_orders_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load_orders, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(parent, bg=BG); sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Filter:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.order_filter = tk.StringVar(value="All")
        for opt in ["All", "Pending", "Completed"]:
            tk.Radiobutton(sf, text=opt, variable=self.order_filter, value=opt, bg=BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=BG, font=("Segoe UI", 10), command=self._load_orders).pack(side="left", padx=6)

        cols = ("ID", "Order No.", "Patient", "Doctor", "Test", "Date", "Result", "Status")
        tf, self.orders_tree = make_treeview(parent, cols, height=15)
        widths = [40, 100, 160, 160, 200, 100, 120, 90]
        for col, w in zip(cols, widths):
            self.orders_tree.heading(col, text=col); self.orders_tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.orders_tree.bind("<<TreeviewSelect>>", lambda e: self._on_order_select(e))
        self._load_orders()

    def _load_orders(self):
        self.orders_tree.delete(*self.orders_tree.get_children())
        f = self.order_filter.get(); conn = get_conn()
        q = """SELECT o.id,o.order_number,p.name,d.name,t.test_name,o.ordered_date,o.result_value,o.result_status
               FROM lab_orders o JOIN patients p ON o.patient_id=p.id JOIN doctors d ON o.doctor_id=d.id
               JOIN lab_tests t ON o.test_id=t.id"""
        rows = conn.execute(q + (" WHERE o.result_status=? ORDER BY o.id DESC" if f != "All" else " ORDER BY o.id DESC"),
                             (f,) if f != "All" else ()).fetchall()
        conn.close()
        for r in rows:
            rv = list(r); rv[6] = rv[6] or "-"
            tag = "done" if r[7] == "Completed" else "pend"
            self.orders_tree.insert("", "end", values=rv, tags=(tag,))
        self.orders_tree.tag_configure("done", foreground=SUCCESS); self.orders_tree.tag_configure("pend", foreground=WARNING)

    def _export_orders_pdf(self):
        conn = get_conn(); f = self.order_filter.get()
        q = """SELECT o.id,o.order_number,p.name,d.name,t.test_name,o.ordered_date,o.result_value,o.result_status
               FROM lab_orders o JOIN patients p ON o.patient_id=p.id JOIN doctors d ON o.doctor_id=d.id
               JOIN lab_tests t ON o.test_id=t.id"""
        rows = conn.execute(q + (" WHERE o.result_status=? ORDER BY o.id DESC" if f != "All" else " ORDER BY o.id DESC"), (f,) if f != "All" else ()).fetchall()
        conn.close()
        formatted = [[r[0], r[1], r[2], r[3], r[4], r[5], r[6] or "-", r[7]] for r in rows]
        export_table_to_pdf(f"Lab_Orders_{datetime.date.today()}.pdf", "Lab Orders", ["ID","Order No.","Patient","Doctor","Test","Date","Result","Status"], formatted, [20*mm, 30*mm, 35*mm, 30*mm, 40*mm, 25*mm, 30*mm, 25*mm])

    def _on_order_select(self, e):
        sel = self.orders_tree.selection()
        self.selected_id = self.orders_tree.item(sel[0])["values"][0] if sel else None

    def _enter_result(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a lab order first."); return
        LabResultForm(self, self.selected_id, self._load_orders)

    def _delete_order(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a lab order first."); return
        if messagebox.askyesno("Confirm", "Delete this lab order?"):
            conn = get_conn(); conn.execute("DELETE FROM lab_orders WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load_orders()

    def _build_catalog(self, parent):
        toolbar = tk.Frame(parent, bg=BG); toolbar.pack(fill="x", pady=(8, 6))
        styled_button(toolbar, "+ Add Test", lambda: LabTestForm(self, None, self._load_catalog)).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Edit", self._edit_test, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete_test, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "📄 Export PDF", self._export_catalog_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load_catalog, bg=PANEL, fg=TEXT).pack(side="right")

        cols = ("ID", "Code", "Test Name", "Category", "Price (৳)", "Normal Range", "Unit", "Status")
        tf, self.catalog_tree = make_treeview(parent, cols, height=15)
        widths = [40, 80, 220, 130, 90, 200, 80, 80]
        for col, w in zip(cols, widths):
            self.catalog_tree.heading(col, text=col); self.catalog_tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.catalog_tree.bind("<<TreeviewSelect>>", lambda e: self._on_catalog_select(e))
        self._load_catalog()

    def _load_catalog(self):
        self.catalog_tree.delete(*self.catalog_tree.get_children())
        conn = get_conn(); rows = conn.execute("SELECT id,test_code,test_name,category,price,normal_range,unit,status FROM lab_tests").fetchall(); conn.close()
        for r in rows: self.catalog_tree.insert("", "end", values=r)

    def _export_catalog_pdf(self):
        conn = get_conn(); rows = conn.execute("SELECT id,test_code,test_name,category,price,normal_range,unit,status FROM lab_tests ORDER BY id ASC").fetchall(); conn.close()
        export_table_to_pdf(f"Lab_Test_Catalog_{datetime.date.today()}.pdf", "Lab Test Catalog", ["ID","Code","Test Name","Category","Price","Normal Range","Unit","Status"], rows, [20*mm, 25*mm, 55*mm, 35*mm, 25*mm, 40*mm, 25*mm, 25*mm])

    def _on_catalog_select(self, e):
        sel = self.catalog_tree.selection()
        self.selected_catalog_id = self.catalog_tree.item(sel[0])["values"][0] if sel else None

    def _edit_test(self):
        if not hasattr(self, 'selected_catalog_id') or not self.selected_catalog_id:
            messagebox.showwarning("Select", "Select a test first."); return
        conn = get_conn(); row = conn.execute("SELECT * FROM lab_tests WHERE id=?", (self.selected_catalog_id,)).fetchone(); conn.close()
        LabTestForm(self, row, self._load_catalog)

    def _delete_test(self):
        if not hasattr(self, 'selected_catalog_id') or not self.selected_catalog_id:
            messagebox.showwarning("Select", "Select a test first."); return
        if messagebox.askyesno("Confirm", "Delete this test?"):
            conn = get_conn(); conn.execute("DELETE FROM lab_tests WHERE id=?", (self.selected_catalog_id,)); conn.commit(); conn.close(); self._load_catalog()


class LabOrderForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("New Lab Order"); self.geometry("480x380"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="New Lab Order", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1), weight=1)
        conn = get_conn()
        patients = conn.execute("SELECT id,name FROM patients WHERE status='Active'").fetchall()
        doctors  = conn.execute("SELECT id,name FROM doctors WHERE status='Active'").fetchall()
        tests    = conn.execute("SELECT id,test_name,price FROM lab_tests WHERE status='Active'").fetchall()
        conn.close()
        self.patient_map = {p[1]: p[0] for p in patients}
        self.doctor_map  = {d[1]: d[0] for d in doctors}
        self.test_map    = {t[1]: (t[0], t[2]) for t in tests}

        tk.Label(self, text="Patient *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=8)
        self.patient_cb = ttk.Combobox(self, values=list(self.patient_map.keys()), width=26, state="readonly")
        self.patient_cb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))

        tk.Label(self, text="Doctor *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", padx=8)
        self.doctor_cb = ttk.Combobox(self, values=list(self.doctor_map.keys()), width=26, state="readonly")
        self.doctor_cb.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))

        tk.Label(self, text="Test *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=5, column=0, sticky="w", padx=8)
        self.test_cb = ttk.Combobox(self, values=list(self.test_map.keys()), width=26, state="readonly")
        self.test_cb.grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))
        self.test_cb.bind("<<ComboboxSelected>>", self._show_price)

        self.price_lbl = tk.Label(self, text="", font=("Segoe UI", 10, "bold"), bg=PANEL, fg=ACCENT)
        self.price_lbl.grid(row=7, column=0, columnspan=2, padx=8, sticky="w")

        self.date = labeled_entry(self, "Order Date *", 8, 0, 20, 2)
        self.date.insert(0, datetime.date.today().isoformat())

        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=10, column=0, columnspan=2, pady=16)
        styled_button(btn_row, "💾 Place Order", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _show_price(self, e):
        test_name = self.test_cb.get()
        if test_name in self.test_map:
            self.price_lbl.config(text=f"Test Price: ৳ {self.test_map[test_name][1]:,.2f}")

    def _save(self):
        pname = self.patient_cb.get(); dname = self.doctor_cb.get(); tname = self.test_cb.get(); date = self.date.get().strip()
        if not all([pname, dname, tname, date]): messagebox.showerror("Error", "All fields required."); return
        pid = self.patient_map.get(pname); did = self.doctor_map.get(dname); tid = self.test_map.get(tname, (None,))[0]
        conn = get_conn()
        conn.execute("INSERT INTO lab_orders (order_number,patient_id,doctor_id,test_id,ordered_date) VALUES (?,?,?,?,?)",
                     (gen_order_number(), pid, did, tid, date))
        conn.commit(); conn.close(); self.callback(); self.destroy()


class LabResultForm(tk.Toplevel):
    def __init__(self, parent, order_id, callback):
        super().__init__(parent)
        self.order_id = order_id; self.callback = callback
        self.title("Enter Lab Result"); self.geometry("420x280"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Enter Lab Result", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).pack(pady=14, padx=20, anchor="w")
        f = tk.Frame(self, bg=PANEL); f.pack(fill="x", padx=20)
        tk.Label(f, text="Result Value *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).pack(anchor="w")
        self.result_e = tk.Entry(f, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 11), bd=6)
        self.result_e.pack(fill="x", pady=4)
        tk.Label(f, text="Remarks (optional)", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).pack(anchor="w", pady=(8,0))
        self.remarks_e = tk.Entry(f, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 11), bd=6)
        self.remarks_e.pack(fill="x", pady=4)
        btn_row = tk.Frame(self, bg=PANEL); btn_row.pack(pady=14)
        styled_button(btn_row, "✅ Save Result", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        result = self.result_e.get().strip()
        if not result: messagebox.showerror("Error", "Result value is required."); return
        conn = get_conn()
        conn.execute("UPDATE lab_orders SET result_value=?,remarks=?,result_status='Completed' WHERE id=?",
                     (result, self.remarks_e.get(), self.order_id))
        conn.commit(); conn.close(); self.callback(); self.destroy()


class LabTestForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("Add Lab Test" if not data else "Edit Lab Test")
        self.geometry("420x400"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Lab Test Details", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1), weight=1)
        self.test_name = labeled_entry(self, "Test Name *", 1, 0, 32, 2)
        self.category = labeled_entry(self, "Category", 3, 0, 32, 2)
        self.price = labeled_entry(self, "Price (৳)", 5, 0)
        self.unit = labeled_entry(self, "Unit", 5, 1)
        self.normal_range = labeled_entry(self, "Normal Range", 7, 0, 32, 2)
        self.status = labeled_combo(self, "Status", ["Active", "Inactive"], 9, 0)
        if self.data:
            for w, v in zip([self.test_name, self.category, self.price, self.unit, self.normal_range],
                             [self.data[2], self.data[3], self.data[4], self.data[6], self.data[5]]):
                w.insert(0, str(v) if v else "")
            self.status.set(self.data[7])
        else:
            self.status.set("Active")
        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=11, column=0, columnspan=2, pady=14)
        styled_button(btn_row, "💾 Save", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        name = self.test_name.get().strip()
        if not name: messagebox.showerror("Error", "Test name is required."); return
        conn = get_conn()
        if self.data:
            conn.execute("UPDATE lab_tests SET test_name=?,category=?,price=?,normal_range=?,unit=?,status=? WHERE id=?",
                         (name, self.category.get(), self.price.get() or 0, self.normal_range.get(), self.unit.get(), self.status.get(), self.data[0]))
        else:
            tc = "LT" + ''.join(random.choices(string.digits, k=4))
            conn.execute("INSERT INTO lab_tests (test_code,test_name,category,price,normal_range,unit,status) VALUES (?,?,?,?,?,?,?)",
                         (tc, name, self.category.get(), self.price.get() or 0, self.normal_range.get(), self.unit.get(), self.status.get()))
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  PHARMACY PAGE
# ─────────────────────────────────────────────
class PharmacyPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_med_id = None; self._build()

    def _build(self):
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
        style = ttk.Style(); style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT, padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", BG)])

        self.inventory_tab = tk.Frame(nb, bg=BG); nb.add(self.inventory_tab, text="  📦 Inventory  ")
        self.sales_tab = tk.Frame(nb, bg=BG); nb.add(self.sales_tab, text="  💊 Sales  ")
        self._build_inventory(self.inventory_tab)
        self._build_sales(self.sales_tab)

    def _build_inventory(self, parent):
        toolbar = tk.Frame(parent, bg=BG); toolbar.pack(fill="x", pady=(8, 6))
        styled_button(toolbar, "+ Add Medicine", lambda: MedicineForm(self, None, self._load_inventory)).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Edit", self._edit_med, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "📦 Restock", self._restock, bg=SUCCESS, fg=BG).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete_med, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "� Export PDF", self._export_inventory_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "�🔄 Refresh", self._load_inventory, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(parent, bg=BG); sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Filter:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.inv_filter = tk.StringVar(value="All")
        for opt in ["All", "Low Stock", "Out of Stock"]:
            tk.Radiobutton(sf, text=opt, variable=self.inv_filter, value=opt, bg=BG, fg=TEXT, selectcolor=ACCENT,
                           activebackground=BG, font=("Segoe UI", 10), command=self._load_inventory).pack(side="left", padx=6)

        cols = ("ID", "Code", "Name", "Generic", "Category", "Unit", "Price ৳", "Stock", "Reorder", "Expiry", "Status")
        tf, self.inv_tree = make_treeview(parent, cols, height=14)
        widths = [40, 80, 180, 130, 110, 70, 80, 70, 70, 100, 80]
        for col, w in zip(cols, widths):
            self.inv_tree.heading(col, text=col); self.inv_tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.inv_tree.bind("<<TreeviewSelect>>", self._on_med_select)
        self._load_inventory()

    def _load_inventory(self):
        self.inv_tree.delete(*self.inv_tree.get_children())
        f = self.inv_filter.get(); conn = get_conn()
        if f == "Low Stock":
            rows = conn.execute("SELECT id,medicine_code,name,generic_name,category,unit,price,stock_quantity,reorder_level,expiry_date,status FROM medicines WHERE stock_quantity <= reorder_level AND stock_quantity > 0").fetchall()
        elif f == "Out of Stock":
            rows = conn.execute("SELECT id,medicine_code,name,generic_name,category,unit,price,stock_quantity,reorder_level,expiry_date,status FROM medicines WHERE stock_quantity = 0").fetchall()
        else:
            rows = conn.execute("SELECT id,medicine_code,name,generic_name,category,unit,price,stock_quantity,reorder_level,expiry_date,status FROM medicines").fetchall()
        conn.close()
        for r in rows:
            tag = "low" if r[7] <= r[8] and r[7] > 0 else ("out" if r[7] == 0 else "ok")
            self.inv_tree.insert("", "end", values=r, tags=(tag,))
        self.inv_tree.tag_configure("low", foreground=WARNING)
        self.inv_tree.tag_configure("out", foreground=DANGER)
        self.inv_tree.tag_configure("ok", foreground=SUCCESS)

    def _export_inventory_pdf(self):
        conn = get_conn(); rows = conn.execute("SELECT id,medicine_code,name,generic_name,category,unit,price,stock_quantity,reorder_level,expiry_date,status FROM medicines ORDER BY id ASC").fetchall(); conn.close()
        export_table_to_pdf(f"Medicine_Inventory_{datetime.date.today()}.pdf", "Medicine Inventory", ["ID","Code","Name","Generic","Category","Unit","Price","Stock","Reorder","Expiry","Status"], rows, [20*mm, 25*mm, 45*mm, 35*mm, 35*mm, 25*mm, 25*mm, 25*mm, 25*mm, 35*mm, 25*mm])

    def _on_med_select(self, e):
        sel = self.inv_tree.selection()
        self.selected_med_id = self.inv_tree.item(sel[0])["values"][0] if sel else None

    def _edit_med(self):
        if not self.selected_med_id: messagebox.showwarning("Select", "Select a medicine first."); return
        conn = get_conn(); row = conn.execute("SELECT * FROM medicines WHERE id=?", (self.selected_med_id,)).fetchone(); conn.close()
        MedicineForm(self, row, self._load_inventory)

    def _restock(self):
        if not self.selected_med_id: messagebox.showwarning("Select", "Select a medicine first."); return
        RestockForm(self, self.selected_med_id, self._load_inventory)

    def _delete_med(self):
        if not self.selected_med_id: messagebox.showwarning("Select", "Select a medicine first."); return
        if messagebox.askyesno("Confirm", "Delete this medicine?"):
            conn = get_conn(); conn.execute("DELETE FROM medicines WHERE id=?", (self.selected_med_id,)); conn.commit(); conn.close(); self._load_inventory()

    def _build_sales(self, parent):
        toolbar = tk.Frame(parent, bg=BG); toolbar.pack(fill="x", pady=(8, 6))
        styled_button(toolbar, "+ New Sale", lambda: SaleForm(self, self._load_sales)).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "� Export PDF", self._export_sales_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "�🔄 Refresh", self._load_sales, bg=PANEL, fg=TEXT).pack(side="right")

        cols = ("ID", "Sale No.", "Patient", "Medicine", "Qty", "Unit Price ৳", "Total ৳", "Date")
        tf, self.sales_tree = make_treeview(parent, cols, height=14)
        widths = [50, 110, 180, 200, 70, 100, 100, 110]
        for col, w in zip(cols, widths):
            self.sales_tree.heading(col, text=col); self.sales_tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)

        self.sales_summary_lbl = tk.Label(parent, text="", font=("Segoe UI", 10, "bold"), bg=PANEL, fg=WHITE, pady=6)
        self.sales_summary_lbl.pack(fill="x", pady=(6,0))
        self._load_sales()

    def _load_sales(self):
        self.sales_tree.delete(*self.sales_tree.get_children())
        conn = get_conn()
        rows = conn.execute("""SELECT s.id,s.sale_number,p.name,m.name,s.quantity,s.unit_price,s.total_price,s.sale_date
                               FROM medicine_sales s JOIN patients p ON s.patient_id=p.id JOIN medicines m ON s.medicine_id=m.id
                               ORDER BY s.id DESC""").fetchall()
        total = conn.execute("SELECT SUM(total_price) FROM medicine_sales").fetchone()[0] or 0
        conn.close()
        for r in rows: self.sales_tree.insert("", "end", values=r)
        self.sales_summary_lbl.config(text=f"   💊 Total Pharmacy Revenue: ৳{total:,.2f}")

    def _export_sales_pdf(self):
        conn = get_conn(); rows = conn.execute("SELECT s.id,s.sale_number,p.name,m.name,s.quantity,s.unit_price,s.total_price,s.sale_date FROM medicine_sales s JOIN patients p ON s.patient_id=p.id JOIN medicines m ON s.medicine_id=m.id ORDER BY s.id ASC").fetchall(); conn.close()
        formatted = [[r[0], r[1], r[2], r[3], r[4], f"৳ {r[5]:,.2f}", f"৳ {r[6]:,.2f}", r[7]] for r in rows]
        export_table_to_pdf(f"Medicine_Sales_{datetime.date.today()}.pdf", "Medicine Sales", ["ID","Sale No.","Patient","Medicine","Qty","Unit Price","Total","Date"], formatted, [20*mm, 30*mm, 40*mm, 40*mm, 20*mm, 30*mm, 30*mm, 30*mm])


class MedicineForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("Add Medicine" if not data else "Edit Medicine")
        self.geometry("520x500"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Medicine Details", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=4, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1, 2, 3), weight=1)
        self.name = labeled_entry(self, "Medicine Name *", 1, 0, 28, 3)
        self.generic = labeled_entry(self, "Generic Name", 3, 0, 20, 1)
        self.category = labeled_entry(self, "Category", 3, 2, 20, 1)
        self.unit_e = labeled_combo(self, "Unit", ["Tablet","Capsule","Syrup","Injection","Vial","Cream","Drop","Inhaler","Patch"], 5, 0)
        self.price = labeled_entry(self, "Price (৳)", 5, 2)
        self.stock = labeled_entry(self, "Initial Stock", 7, 0)
        self.reorder = labeled_entry(self, "Reorder Level", 7, 2)
        self.manufacturer = labeled_entry(self, "Manufacturer", 9, 0, 28, 3)
        self.expiry = labeled_entry(self, "Expiry Date (YYYY-MM-DD)", 11, 0, 28, 3)
        if self.data:
            for w, v in zip([self.name, self.generic, self.category, self.price, self.stock, self.reorder, self.manufacturer, self.expiry],
                             [self.data[2], self.data[3], self.data[4], self.data[6], self.data[7], self.data[8], self.data[9], self.data[10]]):
                w.insert(0, str(v) if v else "")
            self.unit_e.set(self.data[5] or "Tablet")
        else:
            self.unit_e.set("Tablet"); self.stock.insert(0, "0"); self.reorder.insert(0, "10")
        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=13, column=0, columnspan=4, pady=14)
        styled_button(btn_row, "💾 Save", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        name = self.name.get().strip()
        if not name: messagebox.showerror("Error", "Medicine name is required."); return
        conn = get_conn()
        if self.data:
            conn.execute("UPDATE medicines SET name=?,generic_name=?,category=?,unit=?,price=?,stock_quantity=?,reorder_level=?,manufacturer=?,expiry_date=? WHERE id=?",
                         (name, self.generic.get(), self.category.get(), self.unit_e.get(), self.price.get() or 0,
                          self.stock.get() or 0, self.reorder.get() or 10, self.manufacturer.get(), self.expiry.get(), self.data[0]))
        else:
            mc = gen_med_code()
            conn.execute("INSERT INTO medicines (medicine_code,name,generic_name,category,unit,price,stock_quantity,reorder_level,manufacturer,expiry_date) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (mc, name, self.generic.get(), self.category.get(), self.unit_e.get(), self.price.get() or 0,
                          self.stock.get() or 0, self.reorder.get() or 10, self.manufacturer.get(), self.expiry.get()))
        conn.commit(); conn.close(); self.callback(); self.destroy()


class RestockForm(tk.Toplevel):
    def __init__(self, parent, med_id, callback):
        super().__init__(parent)
        self.med_id = med_id; self.callback = callback
        self.title("Restock Medicine"); self.geometry("360x220"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        conn = get_conn(); med = conn.execute("SELECT name,stock_quantity FROM medicines WHERE id=?", (self.med_id,)).fetchone(); conn.close()
        tk.Label(self, text=f"Restock: {med[0]}", font=("Segoe UI", 13, "bold"), bg=PANEL, fg=WHITE).pack(pady=14, padx=20, anchor="w")
        tk.Label(self, text=f"Current Stock: {med[1]} units", font=("Segoe UI", 10), bg=PANEL, fg=ACCENT).pack(padx=20, anchor="w")
        f = tk.Frame(self, bg=PANEL); f.pack(fill="x", padx=20, pady=8)
        tk.Label(f, text="Add Quantity *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).pack(anchor="w")
        self.qty_e = tk.Entry(f, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 11), bd=6)
        self.qty_e.pack(fill="x", pady=4)
        btn_row = tk.Frame(self, bg=PANEL); btn_row.pack(pady=10)
        styled_button(btn_row, "✅ Restock", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        try: qty = int(self.qty_e.get())
        except: messagebox.showerror("Error", "Enter a valid quantity."); return
        if qty <= 0: messagebox.showerror("Error", "Quantity must be positive."); return
        conn = get_conn()
        conn.execute("UPDATE medicines SET stock_quantity = stock_quantity + ? WHERE id=?", (qty, self.med_id))
        conn.execute("INSERT INTO stock_movements (medicine_id,movement_type,quantity,note) VALUES (?,?,?,?)",
                     (self.med_id, "IN", qty, "Manual restock"))
        conn.commit(); conn.close(); self.callback(); self.destroy()


class SaleForm(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("New Medicine Sale"); self.geometry("460x360"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Medicine Sale", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1), weight=1)
        conn = get_conn()
        patients = conn.execute("SELECT id,name FROM patients WHERE status='Active'").fetchall()
        medicines = conn.execute("SELECT id,name,price,stock_quantity FROM medicines WHERE stock_quantity > 0").fetchall()
        conn.close()
        self.patient_map = {p[1]: p[0] for p in patients}
        self.medicine_map = {m[1]: (m[0], m[2], m[3]) for m in medicines}

        tk.Label(self, text="Patient *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=8)
        self.patient_cb = ttk.Combobox(self, values=list(self.patient_map.keys()), width=26, state="readonly")
        self.patient_cb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))

        tk.Label(self, text="Medicine *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", padx=8)
        self.med_cb = ttk.Combobox(self, values=list(self.medicine_map.keys()), width=26, state="readonly")
        self.med_cb.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))
        self.med_cb.bind("<<ComboboxSelected>>", self._on_med_select)

        self.stock_lbl = tk.Label(self, text="", font=("Segoe UI", 9), bg=PANEL, fg=SUBTEXT)
        self.stock_lbl.grid(row=5, column=0, columnspan=2, sticky="w", padx=8)

        self.qty = labeled_entry(self, "Quantity *", 6, 0)
        self.price_lbl = tk.Label(self, text="Unit Price: ৳ 0.00", font=("Segoe UI", 10, "bold"), bg=PANEL, fg=ACCENT)
        self.price_lbl.grid(row=7, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        self.qty.bind("<KeyRelease>", self._calc)

        self.total_lbl = tk.Label(self, text="Total: ৳ 0.00", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WARNING)
        self.total_lbl.grid(row=8, column=0, columnspan=2, sticky="w", padx=8, pady=4)

        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=10, column=0, columnspan=2, pady=14)
        styled_button(btn_row, "💾 Sell", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _on_med_select(self, e):
        mname = self.med_cb.get()
        if mname in self.medicine_map:
            mid, price, stock = self.medicine_map[mname]
            self.price_lbl.config(text=f"Unit Price: ৳ {price:,.2f}")
            self.stock_lbl.config(text=f"Available Stock: {stock} units")
            self._calc()

    def _calc(self, *_):
        mname = self.med_cb.get()
        if mname in self.medicine_map:
            try: qty = int(self.qty.get())
            except: qty = 0
            price = self.medicine_map[mname][1]
            self.total_lbl.config(text=f"Total: ৳ {qty * price:,.2f}")

    def _save(self):
        pname = self.patient_cb.get(); mname = self.med_cb.get()
        try: qty = int(self.qty.get())
        except: messagebox.showerror("Error", "Enter valid quantity."); return
        if not pname or not mname or qty <= 0: messagebox.showerror("Error", "All fields required and quantity > 0."); return
        mid, price, stock = self.medicine_map.get(mname, (None, 0, 0))
        if qty > stock: messagebox.showerror("Error", f"Insufficient stock! Available: {stock}"); return
        pid = self.patient_map.get(pname); total = qty * price
        conn = get_conn()
        conn.execute("INSERT INTO medicine_sales (sale_number,patient_id,medicine_id,quantity,unit_price,total_price,sale_date) VALUES (?,?,?,?,?,?,?)",
                     (gen_sale_number(), pid, mid, qty, price, total, datetime.date.today().isoformat()))
        conn.execute("UPDATE medicines SET stock_quantity = stock_quantity - ? WHERE id=?", (qty, mid))
        conn.execute("INSERT INTO stock_movements (medicine_id,movement_type,quantity,note) VALUES (?,?,?,?)", (mid, "OUT", qty, f"Sale to patient ID {pid}"))
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  PRESCRIPTIONS PAGE
# ─────────────────────────────────────────────
class PrescriptionsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None; self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG); toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "+ New Prescription", self._new).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "👁 View Details", self._view, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "🖨 Print", self._print, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "� Export PDF", self._export_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "�🗑 Delete", self._delete, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "🔄 Refresh", self._load, bg=PANEL, fg=TEXT).pack(side="right")

        sf = tk.Frame(self, bg=BG); sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Search:", bg=BG, fg=SUBTEXT, font=("Segoe UI", 10)).pack(side="left")
        self.search_var = tk.StringVar(); self.search_var.trace("w", lambda *a: self._load())
        tk.Entry(sf, textvariable=self.search_var, bg=CARD, fg=WHITE, insertbackground=WHITE,
                 relief="flat", font=("Segoe UI", 10), bd=4, width=30).pack(side="left", padx=8)

        cols = ("ID", "Rx No.", "Patient", "Doctor", "Diagnosis", "Follow-up", "Date")
        tf, self.tree = make_treeview(self, cols, height=18)
        widths = [50, 100, 180, 180, 220, 110, 110]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select); self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        q = self.search_var.get().strip(); conn = get_conn()
        base = """SELECT rx.id,rx.prescription_number,p.name,d.name,rx.diagnosis,rx.follow_up_date,rx.created_at
                  FROM prescriptions rx JOIN patients p ON rx.patient_id=p.id JOIN doctors d ON rx.doctor_id=d.id"""
        if q:
            rows = conn.execute(base + " WHERE p.name LIKE ? OR rx.diagnosis LIKE ? ORDER BY rx.id DESC", (f"%{q}%", f"%{q}%")).fetchall()
        else:
            rows = conn.execute(base + " ORDER BY rx.id DESC").fetchall()
        conn.close()
        for r in rows:
            rv = list(r); rv[5] = rv[5] or "-"; rv[6] = rv[6][:10] if rv[6] else ""
            self.tree.insert("", "end", values=rv)

    def _on_select(self, e):
        sel = self.tree.selection()
        self.selected_id = self.tree.item(sel[0])["values"][0] if sel else None

    def _new(self): PrescriptionForm(self, self._load)
    def _view(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a prescription first."); return
        PrescriptionViewer(self, self.selected_id)
    def _print(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a prescription first."); return
        PrescriptionPrinter(self, self.selected_id)
    def _delete(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a prescription first."); return
        if messagebox.askyesno("Confirm", "Delete this prescription?"):
            conn = get_conn(); conn.execute("DELETE FROM prescription_items WHERE prescription_id=?", (self.selected_id,))
            conn.execute("DELETE FROM prescriptions WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load()

    def _export_pdf(self):
        conn = get_conn(); rows = conn.execute("SELECT rx.prescription_number,p.name,d.name,rx.diagnosis,rx.follow_up_date,rx.created_at FROM prescriptions rx JOIN patients p ON rx.patient_id=p.id JOIN doctors d ON rx.doctor_id=d.id ORDER BY rx.id ASC").fetchall(); conn.close()
        formatted = [[r[0], r[1], r[2], r[3] or "-", r[4] or "-", r[5][:10] if r[5] else ""] for r in rows]
        export_table_to_pdf(f"Prescriptions_{datetime.date.today()}.pdf", "Prescription Records", ["Rx No.","Patient","Doctor","Diagnosis","Follow-up","Date"], formatted, [30*mm, 35*mm, 35*mm, 45*mm, 30*mm, 30*mm])


class PrescriptionForm(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback; self.items = []
        self.title("New Prescription"); self.geometry("700x620"); self.configure(bg=PANEL); self.resizable(True, True); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="New Prescription", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).pack(pady=12, padx=20, anchor="w")
        top = tk.Frame(self, bg=PANEL); top.pack(fill="x", padx=20)
        top.columnconfigure((0,1,2,3), weight=1)
        conn = get_conn()
        patients = conn.execute("SELECT id,name FROM patients WHERE status='Active'").fetchall()
        doctors  = conn.execute("SELECT id,name FROM doctors WHERE status='Active'").fetchall()
        conn.close()
        self.patient_map = {p[1]: p[0] for p in patients}
        self.doctor_map  = {d[1]: d[0] for d in doctors}

        tk.Label(top, text="Patient *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.patient_cb = ttk.Combobox(top, values=list(self.patient_map.keys()), width=22, state="readonly")
        self.patient_cb.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0,6), pady=(0,6))

        tk.Label(top, text="Doctor *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w")
        self.doctor_cb = ttk.Combobox(top, values=list(self.doctor_map.keys()), width=22, state="readonly")
        self.doctor_cb.grid(row=1, column=2, columnspan=2, sticky="ew", pady=(0,6))

        tk.Label(top, text="Diagnosis", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", columnspan=4)
        self.diag_e = tk.Entry(top, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 10), bd=4)
        self.diag_e.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0,6))

        tk.Label(top, text="Follow-up Date", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w")
        self.followup_e = tk.Entry(top, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 10), bd=4, width=16)
        self.followup_e.grid(row=5, column=0, sticky="ew", pady=(0,6))

        # Medicines section
        tk.Label(self, text="Medicines", font=("Segoe UI", 11, "bold"), bg=PANEL, fg=ACCENT).pack(anchor="w", padx=20, pady=(6,4))
        med_frame = tk.Frame(self, bg=PANEL); med_frame.pack(fill="x", padx=20)
        med_frame.columnconfigure(0, weight=3); med_frame.columnconfigure(1, weight=1); med_frame.columnconfigure(2, weight=1)
        med_frame.columnconfigure(3, weight=1); med_frame.columnconfigure(4, weight=2)
        for i, h in enumerate(["Medicine Name", "Dosage", "Frequency", "Duration", "Instructions"]):
            tk.Label(med_frame, text=h, bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8)).grid(row=0, column=i, sticky="w", padx=4)
        self.med_name_e = tk.Entry(med_frame, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 9), bd=4, width=20)
        self.med_name_e.grid(row=1, column=0, sticky="ew", padx=4, pady=2)
        self.dosage_e = tk.Entry(med_frame, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 9), bd=4, width=10)
        self.dosage_e.grid(row=1, column=1, sticky="ew", padx=4, pady=2); self.dosage_e.insert(0, "1 tab")
        self.freq_cb = ttk.Combobox(med_frame, values=["Once daily","Twice daily","3x daily","4x daily","SOS","Weekly","Monthly"], width=12, state="readonly")
        self.freq_cb.grid(row=1, column=2, sticky="ew", padx=4, pady=2); self.freq_cb.set("Once daily")
        self.dur_e = tk.Entry(med_frame, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 9), bd=4, width=10)
        self.dur_e.grid(row=1, column=3, sticky="ew", padx=4, pady=2); self.dur_e.insert(0, "7 days")
        self.instr_e = tk.Entry(med_frame, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 9), bd=4, width=16)
        self.instr_e.grid(row=1, column=4, sticky="ew", padx=4, pady=2); self.instr_e.insert(0, "After meals")
        styled_button(med_frame, "+ Add", self._add_med_item, bg=ACCENT2, fg=BG).grid(row=1, column=5, padx=4)

        # Items list
        cols = ("Medicine", "Dosage", "Frequency", "Duration", "Instructions")
        tf, self.items_tree = make_treeview(self, cols, height=6)
        for col in cols:
            self.items_tree.heading(col, text=col); self.items_tree.column(col, width=120, anchor="center")
        tf.pack(fill="x", expand=False, padx=20, pady=4)
        styled_button(self, "🗑 Remove Selected", self._remove_item, bg=DANGER, fg=WHITE).pack(anchor="w", padx=20)

        btn_row = tk.Frame(self, bg=PANEL); btn_row.pack(pady=12)
        styled_button(btn_row, "💾 Save Prescription", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _add_med_item(self):
        name = self.med_name_e.get().strip()
        if not name: messagebox.showerror("Error", "Medicine name required."); return
        item = (name, self.dosage_e.get(), self.freq_cb.get(), self.dur_e.get(), self.instr_e.get())
        self.items.append(item); self.items_tree.insert("", "end", values=item)
        self.med_name_e.delete(0, "end")

    def _remove_item(self):
        sel = self.items_tree.selection()
        if sel:
            idx = self.items_tree.index(sel[0]); self.items.pop(idx); self.items_tree.delete(sel[0])

    def _save(self):
        pname = self.patient_cb.get(); dname = self.doctor_cb.get()
        if not pname or not dname: messagebox.showerror("Error", "Patient and Doctor required."); return
        if not self.items: messagebox.showerror("Error", "Add at least one medicine."); return
        pid = self.patient_map.get(pname); did = self.doctor_map.get(dname)
        conn = get_conn()
        conn.execute("INSERT INTO prescriptions (prescription_number,patient_id,doctor_id,diagnosis,follow_up_date) VALUES (?,?,?,?,?)",
                     (gen_prescription_number(), pid, did, self.diag_e.get(), self.followup_e.get()))
        rx_id = conn.lastrowid
        for item in self.items:
            conn.execute("INSERT INTO prescription_items (prescription_id,medicine_name,dosage,frequency,duration,instructions) VALUES (?,?,?,?,?,?)",
                         (rx_id,) + item)
        conn.commit(); conn.close(); self.callback(); self.destroy()


class PrescriptionViewer(tk.Toplevel):
    def __init__(self, parent, rx_id):
        super().__init__(parent)
        self.rx_id = rx_id; self.title("Prescription Details"); self.geometry("600x500"); self.configure(bg=PANEL); self.grab_set(); self._build()

    def _build(self):
        conn = get_conn()
        rx = conn.execute("SELECT rx.*,p.name,p.age,p.phone,d.name FROM prescriptions rx JOIN patients p ON rx.patient_id=p.id JOIN doctors d ON rx.doctor_id=d.id WHERE rx.id=?", (self.rx_id,)).fetchone()
        items = conn.execute("SELECT medicine_name,dosage,frequency,duration,instructions FROM prescription_items WHERE prescription_id=?", (self.rx_id,)).fetchall()
        conn.close()
        if not rx: self.destroy(); return

        header = tk.Frame(self, bg=ACCENT, padx=16, pady=12); header.pack(fill="x")
        tk.Label(header, text="🏥 MediCare Hospital", font=("Segoe UI", 14, "bold"), bg=ACCENT, fg=BG).pack()
        tk.Label(header, text="PRESCRIPTION", font=("Segoe UI", 10), bg=ACCENT, fg=BG).pack()

        info = tk.Frame(self, bg=PANEL, padx=16, pady=10); info.pack(fill="x")
        info.columnconfigure((0,1,2,3), weight=1)
        for i, (label, val) in enumerate([("Rx No:", rx[2]), ("Date:", rx[8][:10] if rx[8] else ""), ("Patient:", rx[9]), ("Doctor:", rx[12])]):
            tk.Label(info, text=label, bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 8)).grid(row=0, column=i, sticky="w", padx=4)
            tk.Label(info, text=val or "", bg=PANEL, fg=WHITE, font=("Segoe UI", 9, "bold")).grid(row=1, column=i, sticky="w", padx=4)

        if rx[4]:
            d_frame = tk.Frame(self, bg=CARD, padx=14, pady=8); d_frame.pack(fill="x", padx=16, pady=(8,4))
            tk.Label(d_frame, text=f"Diagnosis: {rx[4]}", font=("Segoe UI", 10, "bold"), bg=CARD, fg=ACCENT).pack(anchor="w")

        tk.Label(self, text="Medicines", font=("Segoe UI", 11, "bold"), bg=PANEL, fg=WHITE).pack(anchor="w", padx=16, pady=(8,4))
        cols = ("Medicine", "Dosage", "Frequency", "Duration", "Instructions")
        tf, tree = make_treeview(self, cols, height=8)
        for col in cols: tree.heading(col, text=col); tree.column(col, width=110, anchor="center")
        tf.pack(fill="both", expand=True, padx=16)
        for item in items: tree.insert("", "end", values=item)

        if rx[7]:
            tk.Label(self, text=f"Follow-up: {rx[7]}", font=("Segoe UI", 10), bg=PANEL, fg=WARNING).pack(anchor="w", padx=16, pady=6)
        styled_button(self, "Close", self.destroy, bg=PANEL, fg=SUBTEXT).pack(pady=8)


class PrescriptionPrinter(tk.Toplevel):
    def __init__(self, parent, rx_id):
        super().__init__(parent)
        self.rx_id = rx_id; self.title("Print Prescription"); self.geometry("520x580"); self.configure(bg=PANEL); self.grab_set(); self._build()

    def _build(self):
        conn = get_conn()
        rx = conn.execute("SELECT rx.*,p.name,p.age,p.phone,d.name FROM prescriptions rx JOIN patients p ON rx.patient_id=p.id JOIN doctors d ON rx.doctor_id=d.id WHERE rx.id=?", (self.rx_id,)).fetchone()
        items = conn.execute("SELECT medicine_name,dosage,frequency,duration,instructions FROM prescription_items WHERE prescription_id=?", (self.rx_id,)).fetchall()
        conn.close()
        tk.Label(self, text="🖨 Prescription Preview", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).pack(pady=12)
        txt = tk.Text(self, bg=CARD, fg=WHITE, font=("Courier", 10), padx=16, pady=10)
        txt.pack(fill="both", expand=True, padx=16, pady=4)
        med_lines = "\n".join([f"  {i+1}. {it[0]} | {it[1]} | {it[2]} | {it[3]} | {it[4]}" for i, it in enumerate(items)])
        content = f"""
{'='*48}
            🏥 MediCare Hospital
              PRESCRIPTION
{'='*48}
Rx No   : {rx[2]}
Date    : {rx[8][:10] if rx[8] else ''}
Patient : {rx[9]}  (Age: {rx[10]})
Phone   : {rx[11] or '-'}
Doctor  : {rx[12]}
{'-'*48}
Diagnosis: {rx[4] or '-'}
{'-'*48}
MEDICINES:
{med_lines}
{'-'*48}
Notes       : {rx[5] or '-'}
Follow-up   : {rx[7] or '-'}
{'='*48}
"""
        txt.insert("1.0", content); txt.config(state="disabled")
        btn_row = tk.Frame(self, bg=PANEL); btn_row.pack(pady=8)
        if REPORTLAB_AVAILABLE:
            styled_button(btn_row, "📄 Export PDF", lambda: self._export_pdf(rx, items)).pack(side="left", padx=8)
        styled_button(btn_row, "Close", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left", padx=8)

    def _export_pdf(self, rx, items):
        filename = f"Rx_{rx[2]}_{datetime.date.today()}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet(); elements = []
        title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18, spaceAfter=4)
        elements.append(Paragraph("MediCare Hospital Management System", title_style))
        elements.append(Paragraph("PRESCRIPTION", ParagraphStyle('sub', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12, spaceAfter=12)))
        elements.append(Spacer(1, 4*mm))
        info_data = [["Rx Number:", rx[2], "Date:", rx[8][:10] if rx[8] else ""],
                     ["Patient:", rx[9], "Age:", str(rx[10])],
                     ["Doctor:", rx[12], "Phone:", rx[11] or "-"]]
        info_table = Table(info_data, colWidths=[40*mm, 70*mm, 30*mm, 60*mm])
        info_table.setStyle(TableStyle([('FONT',(0,0),(-1,-1),'Helvetica',10),('FONT',(0,0),(0,-1),'Helvetica-Bold',10),('FONT',(2,0),(2,-1),'Helvetica-Bold',10),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f4f8')),('BOX',(0,0),(-1,-1),0.5,colors.grey),('GRID',(0,0),(-1,-1),0.25,colors.lightgrey),('PADDING',(0,0),(-1,-1),6)]))
        elements.append(info_table)
        if rx[4]: elements.append(Spacer(1,4*mm)); elements.append(Paragraph(f"Diagnosis: {rx[4]}", ParagraphStyle('diag',parent=styles['Normal'],fontSize=11,textColor=colors.HexColor('#00C9A7'))))
        elements.append(Spacer(1,4*mm))
        med_data = [["Medicine", "Dosage", "Frequency", "Duration", "Instructions"]] + [[it[0],it[1],it[2],it[3],it[4]] for it in items]
        med_table = Table(med_data, colWidths=[50*mm,25*mm,35*mm,25*mm,45*mm])
        med_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1B2A3B')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONT',(0,0),(-1,0),'Helvetica-Bold',10),('FONT',(0,1),(-1,-1),'Helvetica',9),('BOX',(0,0),(-1,-1),1,colors.grey),('GRID',(0,0),(-1,-1),0.5,colors.lightgrey),('PADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')])]))
        elements.append(med_table)
        if rx[7]: elements.append(Spacer(1,4*mm)); elements.append(Paragraph(f"Follow-up Date: {rx[7]}", ParagraphStyle('fu',parent=styles['Normal'],fontSize=10)))
        doc.build(elements)
        messagebox.showinfo("PDF Exported", f"Prescription saved as:\n{os.path.abspath(filename)}")


# ─────────────────────────────────────────────
#  MEDICAL HISTORY PAGE
# ─────────────────────────────────────────────
class MedicalHistoryPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None; self._build()

    def _build(self):
        # Patient selector
        top = tk.Frame(self, bg=CARD, padx=16, pady=12); top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Select Patient to View History:", font=("Segoe UI", 11, "bold"), bg=CARD, fg=WHITE).pack(side="left")
        conn = get_conn(); patients = conn.execute("SELECT id,name FROM patients").fetchall(); conn.close()
        self.patient_map = {f"{p[1]} (ID:{p[0]})": p[0] for p in patients}
        self.patient_cb = ttk.Combobox(top, values=list(self.patient_map.keys()), width=30, state="readonly")
        self.patient_cb.pack(side="left", padx=12)
        self.patient_cb.bind("<<ComboboxSelected>>", lambda e: self._load())
        styled_button(top, "+ Add Record", self._add, bg=ACCENT).pack(side="left", padx=8)
        styled_button(top, "� Export PDF", self._export_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(top, "�🗑 Delete", self._delete, bg=DANGER, fg=WHITE).pack(side="left", padx=4)

        cols = ("ID", "Date", "Visit Type", "Doctor", "Complaint", "Diagnosis", "Treatment")
        tf, self.tree = make_treeview(self, cols, height=14)
        widths = [50, 100, 110, 160, 200, 200, 200]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Detail panel
        self.detail_frame = tk.Frame(self, bg=CARD, padx=16, pady=12); self.detail_frame.pack(fill="x", pady=(8,0))
        self.detail_lbl = tk.Label(self.detail_frame, text="Select a record to view details", font=("Segoe UI", 10), bg=CARD, fg=SUBTEXT, wraplength=900, justify="left")
        self.detail_lbl.pack(anchor="w")

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        key = self.patient_cb.get()
        if not key: return
        pid = self.patient_map.get(key)
        conn = get_conn()
        rows = conn.execute("""SELECT h.id,h.visit_date,h.visit_type,d.name,h.complaint,h.diagnosis,h.treatment
                               FROM medical_history h LEFT JOIN doctors d ON h.doctor_id=d.id
                               WHERE h.patient_id=? ORDER BY h.id DESC""", (pid,)).fetchall()
        conn.close()
        for r in rows: self.tree.insert("", "end", values=r)

    def _on_select(self, e):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0])["values"][0]
            conn = get_conn()
            row = conn.execute("SELECT * FROM medical_history WHERE id=?", (self.selected_id,)).fetchone()
            conn.close()
            if row:
                detail = f"Visit: {row[2]} | Complaint: {row[6] or '-'} | Diagnosis: {row[7] or '-'} | Treatment: {row[8] or '-'} | Notes: {row[9] or '-'}"
                self.detail_lbl.config(text=detail, fg=WHITE)

    def _add(self):
        key = self.patient_cb.get()
        if not key: messagebox.showwarning("Select", "Please select a patient first."); return
        pid = self.patient_map.get(key)
        MedicalHistoryForm(self, pid, self._load)

    def _delete(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a record first."); return
        if messagebox.askyesno("Confirm", "Delete this history record?"):
            conn = get_conn(); conn.execute("DELETE FROM medical_history WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load()

    def _export_pdf(self):
        key = self.patient_cb.get()
        if not key: messagebox.showwarning("Select", "Please select a patient first."); return
        pid = self.patient_map.get(key)
        conn = get_conn(); rows = conn.execute("SELECT id,visit_date,visit_type,doctor_id,complaint,diagnosis,treatment FROM medical_history WHERE patient_id=? ORDER BY id ASC", (pid,)).fetchall();
        doctor_cache = {d[0]: d[1] for d in conn.execute("SELECT id,name FROM doctors").fetchall()}
        conn.close()
        formatted = [[r[0], r[1], r[2], doctor_cache.get(r[3], "-"), r[4] or "-", r[5] or "-", r[6] or "-"] for r in rows]
        export_table_to_pdf(f"Medical_History_{datetime.date.today()}.pdf", f"Medical History for {key}", ["ID","Date","Visit","Doctor","Complaint","Diagnosis","Treatment"], formatted, [20*mm, 25*mm, 25*mm, 35*mm, 40*mm, 40*mm, 40*mm])


class MedicalHistoryForm(tk.Toplevel):
    def __init__(self, parent, patient_id, callback):
        super().__init__(parent)
        self.patient_id = patient_id; self.callback = callback
        self.title("Add Medical History Record"); self.geometry("520x480"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="Medical History Record", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.columnconfigure((0, 1), weight=1)
        conn = get_conn(); doctors = conn.execute("SELECT id,name FROM doctors WHERE status='Active'").fetchall(); conn.close()
        self.doctor_map = {d[1]: d[0] for d in doctors}

        tk.Label(self, text="Doctor", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", padx=8)
        self.doctor_cb = ttk.Combobox(self, values=list(self.doctor_map.keys()), width=26, state="readonly")
        self.doctor_cb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))

        self.date = labeled_entry(self, "Visit Date *", 3, 0)
        self.date.insert(0, datetime.date.today().isoformat())
        self.visit_type = labeled_combo(self, "Visit Type", ["OPD","IPD","Emergency","Follow-up","Surgery","Lab Visit"], 3, 1)
        self.visit_type.set("OPD")
        self.complaint = labeled_entry(self, "Chief Complaint", 5, 0, 40, 2)
        self.diagnosis = labeled_entry(self, "Diagnosis", 7, 0, 40, 2)
        self.treatment = labeled_entry(self, "Treatment Given", 9, 0, 40, 2)
        tk.Label(self, text="Notes", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=11, column=0, sticky="w", padx=8)
        self.notes = tk.Text(self, width=46, height=3, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 10), bd=4)
        self.notes.grid(row=12, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,6))

        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=13, column=0, columnspan=2, pady=14)
        styled_button(btn_row, "💾 Save", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        date = self.date.get().strip()
        if not date: messagebox.showerror("Error", "Date is required."); return
        dname = self.doctor_cb.get(); did = self.doctor_map.get(dname) if dname else None
        conn = get_conn()
        conn.execute("INSERT INTO medical_history (patient_id,visit_date,visit_type,doctor_id,complaint,diagnosis,treatment,notes) VALUES (?,?,?,?,?,?,?,?)",
                     (self.patient_id, date, self.visit_type.get(), did, self.complaint.get(), self.diagnosis.get(), self.treatment.get(), self.notes.get("1.0","end").strip()))
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  REPORTS & ANALYTICS PAGE
# ─────────────────────────────────────────────
class ReportsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG); toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "📄 Export Report PDF", self._export_reports_pdf, bg=PURPLE, fg=WHITE).pack(side="right", padx=16)
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
        style = ttk.Style(); style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT, padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", BG)])

        tabs = [("📊 Summary", self._build_summary), ("💰 Revenue", self._build_revenue), ("🧪 Lab Stats", self._build_lab_stats), ("💊 Medicine Stats", self._build_med_stats)]
        for label, builder in tabs:
            frame = tk.Frame(nb, bg=BG); nb.add(frame, text=f"  {label}  "); builder(frame)

    def _build_summary(self, parent):
        conn = get_conn()
        stats = {
            "Total Doctors": conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
            "Active Patients": conn.execute("SELECT COUNT(*) FROM patients WHERE status='Active'").fetchone()[0],
            "Total Appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
            "Completed Appts": conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Completed'").fetchone()[0],
            "Total Bills": conn.execute("SELECT COUNT(*) FROM bills").fetchone()[0],
            "Paid Bills": conn.execute("SELECT COUNT(*) FROM bills WHERE payment_status='Paid'").fetchone()[0],
            "Total Revenue ৳": f"{conn.execute('SELECT SUM(total) FROM bills WHERE payment_status=?',('Paid',)).fetchone()[0] or 0:,.0f}",
            "Lab Orders": conn.execute("SELECT COUNT(*) FROM lab_orders").fetchone()[0],
            "Medicine Sales": conn.execute("SELECT COUNT(*) FROM medicine_sales").fetchone()[0],
            "Prescriptions": conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0],
            "Occupied Cabins": conn.execute("SELECT COUNT(*) FROM cabins WHERE status='Occupied'").fetchone()[0],
            "Low Stock Meds": conn.execute("SELECT COUNT(*) FROM medicines WHERE stock_quantity <= reorder_level").fetchone()[0],
        }
        conn.close()

        tk.Label(parent, text="Hospital Summary", font=("Segoe UI", 13, "bold"), bg=BG, fg=WHITE).pack(anchor="w", pady=(12,8), padx=16)
        colors_list = [ACCENT, ACCENT2, SUCCESS, WARNING, PURPLE, ORANGE, DANGER, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER]
        icons_list = ["👨‍⚕️", "🧑", "📅", "✅", "💳", "💰", "📈", "🧪", "💊", "💉", "🛏", "⚠"]
        cards_row = tk.Frame(parent, bg=BG); cards_row.pack(fill="x", padx=16)
        for i, ((label, value), color, icon) in enumerate(zip(stats.items(), colors_list, icons_list)):
            row, col = divmod(i, 4)
            c_frame = card(cards_row, label, value, color, icon)
            c_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            cards_row.columnconfigure(col, weight=1)

        # Top doctors by appointments
        tk.Label(parent, text="Top Doctors by Appointments", font=("Segoe UI", 11, "bold"), bg=BG, fg=WHITE).pack(anchor="w", pady=(16,6), padx=16)
        conn = get_conn()
        top_docs = conn.execute("SELECT d.name,d.specialization,COUNT(a.id) cnt FROM appointments a JOIN doctors d ON a.doctor_id=d.id GROUP BY d.id ORDER BY cnt DESC LIMIT 5").fetchall()
        conn.close()
        for doc in top_docs:
            rf = tk.Frame(parent, bg=CARD, padx=14, pady=8); rf.pack(fill="x", padx=16, pady=2)
            tk.Label(rf, text=f"👨‍⚕️ {doc[0]}", font=("Segoe UI", 10, "bold"), bg=CARD, fg=WHITE).pack(side="left")
            tk.Label(rf, text=doc[1], font=("Segoe UI", 9), bg=CARD, fg=SUBTEXT).pack(side="left", padx=8)
            tk.Label(rf, text=f"{doc[2]} appointments", font=("Segoe UI", 10, "bold"), bg=CARD, fg=ACCENT).pack(side="right")

    def _build_revenue(self, parent):
        tk.Label(parent, text="Revenue Report", font=("Segoe UI", 13, "bold"), bg=BG, fg=WHITE).pack(anchor="w", pady=(12,8), padx=16)
        conn = get_conn()
        monthly = conn.execute("""SELECT strftime('%Y-%m', created_at) month, SUM(total) total, COUNT(*) cnt
                                  FROM bills WHERE payment_status='Paid' GROUP BY month ORDER BY month DESC LIMIT 12""").fetchall()
        by_type = conn.execute("SELECT SUM(doctor_fee),SUM(cabin_charge),SUM(medicine_charge),SUM(lab_charge),SUM(other_charge) FROM bills WHERE payment_status='Paid'").fetchone()
        conn.close()

        # Revenue breakdown
        type_frame = tk.Frame(parent, bg=CARD, padx=16, pady=14); type_frame.pack(fill="x", padx=16, pady=(0,10))
        tk.Label(type_frame, text="Revenue Breakdown", font=("Segoe UI", 11, "bold"), bg=CARD, fg=WHITE).pack(anchor="w", pady=(0,8))
        labels = ["Doctor Fees", "Cabin Charges", "Medicine", "Lab Tests", "Other"]
        for label, val in zip(labels, (by_type or [0,0,0,0,0])):
            rf = tk.Frame(type_frame, bg=CARD); rf.pack(fill="x", pady=2)
            tk.Label(rf, text=label, font=("Segoe UI", 10), bg=CARD, fg=TEXT, width=16, anchor="w").pack(side="left")
            tk.Label(rf, text=f"৳ {val or 0:,.2f}", font=("Segoe UI", 10, "bold"), bg=CARD, fg=ACCENT).pack(side="right")

        # Monthly table
        tk.Label(parent, text="Monthly Revenue", font=("Segoe UI", 11, "bold"), bg=BG, fg=WHITE).pack(anchor="w", pady=(8,6), padx=16)
        cols = ("Month", "Revenue ৳", "Bills Count")
        tf, tree = make_treeview(parent, cols, height=10)
        for col in cols: tree.heading(col, text=col); tree.column(col, width=200, anchor="center")
        tf.pack(fill="both", expand=True, padx=16)
        for r in monthly: tree.insert("", "end", values=(r[0], f"৳ {r[1]:,.2f}", r[2]))

    def _build_lab_stats(self, parent):
        tk.Label(parent, text="Lab Test Statistics", font=("Segoe UI", 13, "bold"), bg=BG, fg=WHITE).pack(anchor="w", pady=(12,8), padx=16)
        conn = get_conn()
        stats = conn.execute("""SELECT t.test_name, t.category, t.price, COUNT(o.id) orders, SUM(CASE WHEN o.result_status='Completed' THEN 1 ELSE 0 END) completed
                                FROM lab_tests t LEFT JOIN lab_orders o ON t.id=o.test_id GROUP BY t.id ORDER BY orders DESC""").fetchall()
        conn.close()
        cols = ("Test Name", "Category", "Price ৳", "Total Orders", "Completed")
        tf, tree = make_treeview(parent, cols, height=18)
        widths = [250, 150, 100, 120, 100]
        for col, w in zip(cols, widths): tree.heading(col, text=col); tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True, padx=16, pady=8)
        for r in stats: tree.insert("", "end", values=(r[0], r[1], f"৳{r[2]:,.0f}", r[3], r[4]))

    def _build_med_stats(self, parent):
        tk.Label(parent, text="Medicine & Pharmacy Statistics", font=("Segoe UI", 13, "bold"), bg=BG, fg=WHITE).pack(anchor="w", pady=(12,8), padx=16)
        conn = get_conn()
        stats = conn.execute("""SELECT m.name, m.category, m.stock_quantity, m.reorder_level,
                                SUM(COALESCE(s.quantity,0)) sold, SUM(COALESCE(s.total_price,0)) revenue
                                FROM medicines m LEFT JOIN medicine_sales s ON m.id=s.medicine_id GROUP BY m.id ORDER BY sold DESC""").fetchall()
        conn.close()
        cols = ("Medicine", "Category", "Stock", "Reorder Level", "Total Sold", "Revenue ৳")
        tf, tree = make_treeview(parent, cols, height=18)
        widths = [220, 130, 80, 110, 100, 120]
        for col, w in zip(cols, widths): tree.heading(col, text=col); tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True, padx=16, pady=8)
        for r in stats:
            tag = "low" if r[2] <= r[3] and r[2] > 0 else ("out" if r[2] == 0 else "")
            tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4] or 0, f"৳{r[5] or 0:,.2f}"), tags=(tag,))
        tree.tag_configure("low", foreground=WARNING); tree.tag_configure("out", foreground=DANGER)

    def _export_reports_pdf(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showwarning("PDF Export", "ReportLab is required to generate PDF reports.")
            return
        conn = get_conn()
        stats = {
            "Total Doctors": conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
            "Active Patients": conn.execute("SELECT COUNT(*) FROM patients WHERE status='Active'").fetchone()[0],
            "Total Appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
            "Completed Appointments": conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Completed'").fetchone()[0],
            "Total Bills": conn.execute("SELECT COUNT(*) FROM bills").fetchone()[0],
            "Paid Bills": conn.execute("SELECT COUNT(*) FROM bills WHERE payment_status='Paid'").fetchone()[0],
            "Total Revenue (Paid)": conn.execute("SELECT SUM(total) FROM bills WHERE payment_status='Paid'").fetchone()[0] or 0,
            "Lab Orders": conn.execute("SELECT COUNT(*) FROM lab_orders").fetchone()[0],
            "Medicine Sales": conn.execute("SELECT COUNT(*) FROM medicine_sales").fetchone()[0],
            "Prescriptions": conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0],
            "Occupied Cabins": conn.execute("SELECT COUNT(*) FROM cabins WHERE status='Occupied'").fetchone()[0],
            "Low Stock Meds": conn.execute("SELECT COUNT(*) FROM medicines WHERE stock_quantity <= reorder_level").fetchone()[0],
        }
        monthly = conn.execute("""SELECT strftime('%Y-%m', created_at) month, SUM(total) total, COUNT(*) cnt
                                  FROM bills WHERE payment_status='Paid' GROUP BY month ORDER BY month DESC LIMIT 12""").fetchall()
        conn.close()

        filename = f"Hospital_Report_{datetime.date.today()}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet(); elements = []
        elements.append(Paragraph("🏥 MediCare Hospital Management System", styles['Title']))
        elements.append(Paragraph("Comprehensive Hospital Report", ParagraphStyle('subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=11, textColor=colors.HexColor('#4B6584'))))
        elements.append(Spacer(1, 6*mm))

        summary_data = [["Metric", "Value"]] + [[k, f"৳ {v:,.2f}" if isinstance(v, (int, float)) and k.startswith("Total Revenue") else str(v)] for k, v in stats.items()]
        summary_table = Table(summary_data, colWidths=[80*mm, 80*mm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#142850')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
            ('FONT', (0,1), (-1,-1), 'Helvetica', 9),
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f4f8')]),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(summary_table); elements.append(Spacer(1, 8*mm))

        if monthly:
            elements.append(Paragraph("Monthly Paid Revenue", styles['Heading3']))
            revenue_data = [["Month", "Revenue ৳", "Bills"]] + [[r[0], f"৳ {r[1]:,.2f}", str(r[2])] for r in monthly]
            revenue_table = Table(revenue_data, colWidths=[60*mm, 60*mm, 50*mm])
            revenue_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B2A3B')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
                ('FONT', (0,1), (-1,-1), 'Helvetica', 9),
                ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(revenue_table)

        doc.build(elements)
        messagebox.showinfo("PDF Exported", f"Hospital report saved as:\n{os.path.abspath(filename)}")


# ─────────────────────────────────────────────
#  USER MANAGEMENT PAGE (Admin only)
# ─────────────────────────────────────────────
class UsersPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app; self.selected_id = None; self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG); toolbar.pack(fill="x", pady=(0, 8))
        styled_button(toolbar, "+ Add User", self._add).pack(side="left", padx=(0, 6))
        styled_button(toolbar, "✏ Edit", self._edit, bg=ACCENT2).pack(side="left", padx=4)
        styled_button(toolbar, "🔑 Reset Password", self._reset_pw, bg=WARNING, fg=BG).pack(side="left", padx=4)
        styled_button(toolbar, "🗑 Delete", self._delete, bg=DANGER, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "� Export PDF", self._export_pdf, bg=PURPLE, fg=WHITE).pack(side="left", padx=4)
        styled_button(toolbar, "�🔄 Refresh", self._load, bg=PANEL, fg=TEXT).pack(side="right")

        cols = ("ID", "Username", "Full Name", "Role", "Email", "Status", "Created")
        tf, self.tree = make_treeview(self, cols, height=18)
        widths = [50, 120, 200, 90, 200, 80, 140]
        for col, w in zip(cols, widths): self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center")
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select); self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_conn(); rows = conn.execute("SELECT id,username,full_name,role,email,status,created_at FROM users").fetchall(); conn.close()
        for r in rows: self.tree.insert("", "end", values=r)

    def _on_select(self, e):
        sel = self.tree.selection()
        self.selected_id = self.tree.item(sel[0])["values"][0] if sel else None

    def _add(self): UserForm(self, None, self._load)
    def _edit(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a user first."); return
        conn = get_conn(); row = conn.execute("SELECT * FROM users WHERE id=?", (self.selected_id,)).fetchone(); conn.close()
        UserForm(self, row, self._load)

    def _reset_pw(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a user first."); return
        new_pw = "password123"
        pw_hash = hashlib.sha256(new_pw.encode()).hexdigest()
        conn = get_conn(); conn.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, self.selected_id)); conn.commit(); conn.close()
        messagebox.showinfo("Reset", f"Password reset to: {new_pw}")

    def _delete(self):
        if not self.selected_id: messagebox.showwarning("Select", "Select a user first."); return
        if self.selected_id == self.app.current_user["id"]: messagebox.showerror("Error", "Cannot delete your own account."); return
        if messagebox.askyesno("Confirm", "Delete this user?"):
            conn = get_conn(); conn.execute("DELETE FROM users WHERE id=?", (self.selected_id,)); conn.commit(); conn.close(); self._load()

    def _export_pdf(self):
        conn = get_conn(); rows = conn.execute("SELECT id,username,full_name,role,email,status,created_at FROM users ORDER BY id ASC").fetchall(); conn.close()
        export_table_to_pdf(f"Users_{datetime.date.today()}.pdf", "User Accounts", ["ID","Username","Full Name","Role","Email","Status","Created"], rows, [20*mm, 30*mm, 45*mm, 30*mm, 55*mm, 25*mm, 30*mm])


class UserForm(tk.Toplevel):
    def __init__(self, parent, data, callback):
        super().__init__(parent)
        self.data = data; self.callback = callback
        self.title("Add User" if not data else "Edit User")
        self.geometry("420x400"); self.configure(bg=PANEL); self.resizable(False, False); self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="User Details", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).grid(row=0, column=0, columnspan=2, pady=14, padx=20, sticky="w")
        self.columnconfigure((0,1), weight=1)
        self.username = labeled_entry(self, "Username *", 1, 0, 28, 2)
        self.full_name = labeled_entry(self, "Full Name *", 3, 0, 28, 2)
        self.email = labeled_entry(self, "Email", 5, 0, 28, 2)
        self.role = labeled_combo(self, "Role", ["Admin", "Doctor", "Staff"], 7, 0)
        self.status = labeled_combo(self, "Status", ["Active", "Inactive"], 7, 1)
        if not self.data:
            tk.Label(self, text="Password *", bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 9)).grid(row=9, column=0, sticky="w", padx=8)
            self.pw_e = tk.Entry(self, bg=CARD, fg=WHITE, insertbackground=WHITE, relief="flat", font=("Segoe UI", 10), bd=4, show="●")
            self.pw_e.grid(row=10, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,5))
        if self.data:
            for w, v in zip([self.username, self.full_name, self.email], [self.data[1], self.data[4], self.data[5]]):
                w.insert(0, str(v) if v else "")
            self.role.set(self.data[3] or "Staff"); self.status.set(self.data[6] or "Active")
            if not hasattr(self, 'pw_e'): self.pw_e = None
        else:
            self.role.set("Staff"); self.status.set("Active")
        btn_row = tk.Frame(self, bg=PANEL); btn_row.grid(row=11, column=0, columnspan=2, pady=14)
        styled_button(btn_row, "💾 Save", self._save).pack(side="left", padx=8)
        styled_button(btn_row, "Cancel", self.destroy, bg=PANEL, fg=SUBTEXT).pack(side="left")

    def _save(self):
        username = self.username.get().strip(); full_name = self.full_name.get().strip()
        if not username or not full_name: messagebox.showerror("Error", "Username and full name required."); return
        conn = get_conn()
        if self.data:
            conn.execute("UPDATE users SET username=?,full_name=?,email=?,role=?,status=? WHERE id=?",
                         (username, full_name, self.email.get(), self.role.get(), self.status.get(), self.data[0]))
        else:
            pw = self.pw_e.get().strip() if hasattr(self, 'pw_e') and self.pw_e else "password123"
            if not pw: messagebox.showerror("Error", "Password required."); return
            pw_hash = hashlib.sha256(pw.encode()).hexdigest()
            try:
                conn.execute("INSERT INTO users (username,password_hash,role,full_name,email,status) VALUES (?,?,?,?,?,?)",
                             (username, pw_hash, self.role.get(), full_name, self.email.get(), self.status.get()))
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists."); conn.close(); return
        conn.commit(); conn.close(); self.callback(); self.destroy()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def start_app():
    init_db()
    login = LoginWindow()
    login.mainloop()
    if login.logged_in_user:
        app = HospitalApp(login.logged_in_user)
        app.mainloop()

if __name__ == "__main__":
    start_app()