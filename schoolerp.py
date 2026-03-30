"""
╔══════════════════════════════════════════════════════╗
║      FULL SCHOOL ERP SYSTEM - SINGLE FILE v2.0       ║
║   Run: pip install customtkinter  then  python       ║
║   Login: admin / admin123                            ║
╚══════════════════════════════════════════════════════╝
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import random
import string
from datetime import date

# ─── DATABASE ────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "school.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        father_name TEXT,
        mother_name TEXT,
        dob TEXT,
        gender TEXT,
        class_name TEXT,
        section TEXT,
        roll_no TEXT,
        phone TEXT,
        address TEXT,
        photo_path TEXT,
        admission_date TEXT,
        status TEXT DEFAULT 'Active'
    );
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        subject TEXT,
        qualification TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        salary REAL,
        join_date TEXT,
        gender TEXT,
        photo_path TEXT,
        status TEXT DEFAULT 'Active'
    );
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        section TEXT NOT NULL,
        teacher_id TEXT,
        room_no TEXT,
        UNIQUE(class_name, section)
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        class_name TEXT,
        section TEXT,
        UNIQUE(student_id, date)
    );
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        fee_type TEXT NOT NULL,
        amount REAL NOT NULL,
        paid_amount REAL DEFAULT 0,
        due_date TEXT,
        paid_date TEXT,
        month TEXT,
        year TEXT,
        status TEXT DEFAULT 'Unpaid',
        receipt_no TEXT
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        recorded_by TEXT
    );
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        category TEXT,
        quantity INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Good'
    );
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_name TEXT NOT NULL,
        class_name TEXT,
        subject TEXT,
        exam_date TEXT,
        total_marks REAL,
        pass_marks REAL
    );
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        exam_id INTEGER,
        subject TEXT,
        marks_obtained REAL,
        grade TEXT,
        remarks TEXT,
        FOREIGN KEY(exam_id) REFERENCES exams(id)
    );
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT,
        class_name TEXT,
        section TEXT,
        description TEXT,
        due_date TEXT,
        assigned_by TEXT,
        created_date TEXT
    );
    CREATE TABLE IF NOT EXISTS library_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        author TEXT,
        category TEXT,
        total_copies INTEGER DEFAULT 1,
        available_copies INTEGER DEFAULT 1,
        isbn TEXT
    );
    CREATE TABLE IF NOT EXISTS library_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id TEXT,
        student_id TEXT,
        issue_date TEXT,
        due_date TEXT,
        return_date TEXT,
        fine REAL DEFAULT 0,
        status TEXT DEFAULT 'Issued'
    );
    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        target TEXT DEFAULT 'All',
        created_by TEXT,
        created_date TEXT
    );
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        name TEXT
    );
    INSERT OR IGNORE INTO users (username, password, role, name) VALUES ('admin','admin123','admin','Administrator');
    INSERT OR IGNORE INTO classes (class_name, section) VALUES
        ('Class 1','A'),('Class 1','B'),('Class 2','A'),('Class 2','B'),
        ('Class 3','A'),('Class 4','A'),('Class 5','A'),('Class 6','A'),
        ('Class 7','A'),('Class 8','A'),('Class 9','A'),('Class 10','A');
    """)
    conn.commit()
    conn.close()

# ─── COLORS & THEME ──────────────────────────────────────────────────────────

COLORS = {
    "sidebar":        "#0F2D25",
    "sidebar_hover":  "#1D9E75",
    "sidebar_active": "#1D9E75",
    "sidebar_text":   "#9FE1CB",
    "sidebar_active_text": "#FFFFFF",
    "header":         "#085041",
    "content":        "#F0F4F2",
    "primary":        "#1D9E75",
    "primary_dark":   "#085041",
    "accent":         "#534AB7",
    "text":           "#0F2D25",
    "muted":          "#6c757d",
    "danger":         "#D85A30",
    "warning":        "#BA7517",
    "success":        "#3B6D11",
    "border":         "#e0e0e0",
    "hover":          "#E1F5EE",
    "white":          "#FFFFFF",
}

MENU_ITEMS = [
    ("🏠", "Dashboard"),
    ("👨‍🎓", "Students"),
    ("👩‍🏫", "Teachers"),
    ("📋", "Attendance"),
    ("💰", "Fees"),
    ("📊", "Accounting"),   # NEW
    ("📦", "Inventory"),    # NEW
    ("📝", "Exams & Results"),
    ("📚", "Assignments"),
    ("📢", "Notices"),
    ("📖", "Library"),
    ("⚙️",  "Settings"),
]

def get_grade(marks, total):
    if total == 0: return "N/A"
    p = marks / total * 100
    if p >= 90: return "A+"
    if p >= 80: return "A"
    if p >= 70: return "A-"
    if p >= 60: return "B"
    if p >= 50: return "C"
    if p >= 40: return "D"
    return "F"

def style_treeview(heading_bg=None):
    bg = heading_bg or COLORS["primary_dark"]
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Treeview", rowheight=32, font=("Arial", 12),
                background="white", foreground=COLORS["text"], fieldbackground="white")
    s.configure("Treeview.Heading", font=("Arial", 12, "bold"),
                background=bg, foreground="white", relief="flat")
    s.map("Treeview", background=[("selected", COLORS["hover"])],
          foreground=[("selected", COLORS["text"])])

def make_scrolled_tree(parent, cols, widths, height=18):
    style_treeview()
    frame = ctk.CTkFrame(parent, fg_color=COLORS["white"], corner_radius=10,
                         border_width=1, border_color=COLORS["border"])
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=height)
    for col, w in zip(cols, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True, padx=4, pady=4)
    return frame, tree

# ─── REUSABLE WIDGETS ────────────────────────────────────────────────────────

def label(parent, text, font_size=13, bold=False, color=None, **kw):
    weight = "bold" if bold else "normal"
    return ctk.CTkLabel(parent, text=text,
                        font=("Arial", font_size, weight),
                        text_color=color or COLORS["text"], **kw)

def btn(parent, text, command, color=None, w=120, h=36, **kw):
    c = color or COLORS["primary"]
    dark = {COLORS["primary"]: COLORS["primary_dark"],
            COLORS["accent"]:  "#3C3489",
            COLORS["danger"]:  "#993C1D",
            COLORS["success"]: "#1a4d08",
            COLORS["warning"]: "#6b3a05"}.get(c, COLORS["primary_dark"])
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color=c, hover_color=dark,
                         width=w, height=h, font=("Arial", 13), **kw)

def entry(parent, placeholder="", width=220, **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width, height=34, **kw)

def combo(parent, values, width=220, **kw):
    return ctk.CTkComboBox(parent, values=values, width=width, height=34, **kw)

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

class DashboardModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()

    def build(self):
        label(self, "Dashboard Overview", 22, bold=True).pack(anchor="w", padx=25, pady=(20,2))
        label(self, "Welcome to School ERP System", 13, color=COLORS["muted"]).pack(anchor="w", padx=25, pady=(0,15))

        conn = get_connection()
        total_s  = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        active_t = conn.execute("SELECT COUNT(*) FROM teachers WHERE status='Active'").fetchone()[0]
        collected= conn.execute("SELECT COALESCE(SUM(paid_amount),0) FROM fees").fetchone()[0]
        expenses = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        net_profit = collected - expenses
        dues     = conn.execute("SELECT COUNT(*) FROM fees WHERE status!='Paid'").fetchone()[0]
        recent_s = conn.execute("SELECT name, class_name, section, status FROM students ORDER BY id DESC LIMIT 8").fetchall()
        notices  = conn.execute("SELECT title, created_date FROM notices ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()

        # Stat cards
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=25, pady=5)

        stats = [
            ("Total Students",   total_s,                 COLORS["accent"],   "👨‍🎓"),
            ("Active Teachers",  active_t,                COLORS["primary"],  "👩‍🏫"),
            ("Fee Collected",    f"৳{collected:,.0f}",    COLORS["success"],  "💰"),
            ("Total Expenses",   f"৳{expenses:,.0f}",     COLORS["danger"],   "📉"),
            ("Net Balance",      f"৳{net_profit:,.0f}",   COLORS["primary_dark"], "🏦"),
        ]

        for text, val, color, icon in stats:
            card = ctk.CTkFrame(sf, fg_color=color, corner_radius=14, width=150, height=105)
            card.pack(side="left", padx=6, expand=True, fill="both")
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=icon, font=("Arial",26)).pack(pady=(12,0))
            ctk.CTkLabel(card, text=str(val), font=("Arial",20,"bold"), text_color="white").pack()
            ctk.CTkLabel(card, text=text, font=("Arial",10), text_color="#ffffff99").pack()

        # Bottom row
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=25, pady=10)

        # Recent students
        rc = ctk.CTkFrame(row, fg_color=COLORS["white"], corner_radius=12,
                          border_width=1, border_color=COLORS["border"])
        rc.pack(side="left", fill="both", expand=True, padx=(0,8))
        label(rc, "Recent Students", 14, bold=True).pack(anchor="w", padx=15, pady=(12,5))
        for s in recent_s:
            r = ctk.CTkFrame(rc, fg_color="#f8f9fa", corner_radius=6)
            r.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(r, text=s[0], font=("Arial",12), anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(r, text=f"{s[1]}-{s[2]}", font=("Arial",11),
                         text_color=COLORS["muted"]).pack(side="right", padx=10)

        # Notices panel
        rp = ctk.CTkFrame(row, fg_color="transparent", width=290)
        rp.pack(side="right", fill="both")
        rp.pack_propagate(False)

        nc = ctk.CTkFrame(rp, fg_color=COLORS["white"], corner_radius=12,
                          border_width=1, border_color=COLORS["border"])
        nc.pack(fill="both", expand=True)
        label(nc, "Latest Notices", 13, bold=True).pack(anchor="w", padx=15, pady=(12,5))
        for n in notices:
            nr = ctk.CTkFrame(nc, fg_color="#f8f9fa", corner_radius=6)
            nr.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(nr, text=f"📢 {n[0]}", font=("Arial",11), anchor="w").pack(side="left", padx=8, pady=5)
            ctk.CTkLabel(nr, text=n[1] or "", font=("Arial",10),
                         text_color=COLORS["muted"]).pack(side="right", padx=8)

# ─── STUDENTS ────────────────────────────────────────────────────────────────

class StudentsModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()
        self.load()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15,5))
        label(top, "Student Management", 22, bold=True).pack(side="left")
        bf = ctk.CTkFrame(top, fg_color="transparent")
        bf.pack(side="right")
        btn(bf, "+ Add Student", self.open_add, w=140).pack(side="left", padx=4)
        btn(bf, "✏ Edit",       lambda: self.open_edit(), color=COLORS["accent"], w=90).pack(side="left", padx=4)
        btn(bf, "🗑 Delete",    self.delete, color=COLORS["danger"], w=90).pack(side="left", padx=4)

        sf = ctk.CTkFrame(self, fg_color=COLORS["white"], corner_radius=10,
                          border_width=1, border_color=COLORS["border"])
        sf.pack(fill="x", padx=20, pady=6)
        label(sf, "Search:", color=COLORS["muted"]).pack(side="left", padx=10, pady=8)
        self.sv = ctk.StringVar()
        self.sv.trace_add("write", lambda *_: self.load())
        entry(sf, "Name, ID, Class...", 280, textvariable=self.sv).pack(side="left", padx=4)
        label(sf, "Class:", color=COLORS["muted"]).pack(side="left", padx=(20,5))
        self.cf = combo(sf, self.get_classes(), 150)
        self.cf.set("All Classes")
        self.cf.pack(side="left", padx=4)
        self.cf.configure(command=lambda _: self.load())

        self.stats_row = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_row.pack(fill="x", padx=20, pady=4)

        tf, self.tree = make_scrolled_tree(self,
            ("ID","Name","Class","Section","Roll","Phone","Status"),
            [95,200,100,90,70,130,80])
        tf.pack(fill="both", expand=True, padx=20, pady=(4,15))
        self.tree.tag_configure("active",   foreground=COLORS["success"])
        self.tree.tag_configure("inactive", foreground=COLORS["danger"])
        self.tree.bind("<Double-1>", lambda _: self.open_edit())

    def get_classes(self):
        conn = get_connection()
        rows = conn.execute("SELECT DISTINCT class_name FROM students ORDER BY class_name").fetchall()
        conn.close()
        return ["All Classes"] + [r[0] for r in rows]

    def load(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        s = self.sv.get().strip(); cf = self.cf.get()
        conn = get_connection()
        q = "SELECT student_id,name,class_name,section,roll_no,phone,status FROM students WHERE 1=1"
        p = []
        if s:
            q += " AND (name LIKE ? OR student_id LIKE ? OR class_name LIKE ?)"
            p += [f"%{s}%"]*3
        if cf != "All Classes":
            q += " AND class_name=?"; p.append(cf)
        rows = conn.execute(q + " ORDER BY name", p).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        active= conn.execute("SELECT COUNT(*) FROM students WHERE status='Active'").fetchone()[0]
        conn.close()
        for r in rows:
            self.tree.insert("","end", values=tuple(r),
                             tags=("active" if r[6]=="Active" else "inactive",))
        for w in self.stats_row.winfo_children(): w.destroy()
        for lbl, val, col in [("Total",total,COLORS["accent"]),
                               ("Active",active,COLORS["success"]),
                               ("Showing",len(rows),COLORS["primary"])]:
            c = ctk.CTkFrame(self.stats_row, fg_color=col, corner_radius=8, width=130, height=48)
            c.pack(side="left", padx=4); c.pack_propagate(False)
            ctk.CTkLabel(c, text=str(val), font=("Arial",18,"bold"), text_color="white").pack(pady=(4,0))
            ctk.CTkLabel(c, text=lbl, font=("Arial",10), text_color="#ffffff99").pack()

    def get_sel(self):
        s = self.tree.selection()
        if not s: messagebox.showwarning("Select","Select a student first."); return None
        return self.tree.item(s[0])["values"]

    def open_add(self): self._form()
    def open_edit(self):
        r = self.get_sel()
        if r: self._form(r[0])

    def _form(self, sid=None):
        d = ctk.CTkToplevel(self)
        d.title("Add Student" if not sid else "Edit Student")
        d.geometry("640x660"); d.grab_set()
        label(d, "Student Information", 18, bold=True).pack(pady=(15,5))
        sc = ctk.CTkScrollableFrame(d, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=20)
        f = {}
        def er(lbl, key, row, col=0, vals=None):
            ctk.CTkLabel(sc, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(
                row=row, column=col*2, sticky="w", pady=5, padx=6)
            w = combo(sc, vals, 210) if vals else entry(sc, width=210)
            w.grid(row=row, column=col*2+1, pady=5, padx=6)
            f[key] = w
        er("Student ID *","student_id",0,0); er("Full Name *","name",0,1)
        er("Father's Name","father_name",1,0); er("Mother's Name","mother_name",1,1)
        er("Date of Birth","dob",2,0); er("Phone","phone",2,1)
        er("Roll No","roll_no",3,0); er("Admission Date","admission_date",3,1)
        er("Address","address",4,0)
        er("Gender","gender",5,0,["Male","Female","Other"])
        conn = get_connection()
        cls = [f"{r[0]} - {r[1]}" for r in conn.execute(
            "SELECT class_name,section FROM classes ORDER BY class_name,section").fetchall()]
        conn.close()
        er("Class","class_sec",5,1, cls)
        er("Status","status",6,0,["Active","Inactive","Transferred"])
        if sid:
            conn = get_connection()
            s = conn.execute("SELECT * FROM students WHERE student_id=?", (sid,)).fetchone()
            conn.close()
            if s:
                for k in ["student_id","name","father_name","mother_name","dob",
                          "phone","roll_no","admission_date","address"]:
                    if k in f and s[k]: f[k].insert(0, str(s[k]))
                f["gender"].set(s["gender"] or "Male")
                f["class_sec"].set(f"{s['class_name']} - {s['section']}" if s["class_name"] else "")
                f["status"].set(s["status"] or "Active")
        def save():
            data = {k: (v.get() if hasattr(v,"get") else "") for k,v in f.items()}
            if not data["student_id"] or not data["name"]:
                messagebox.showerror("Error","Student ID and Name required!"); return
            cs = data["class_sec"].split(" - ") if " - " in data["class_sec"] else ["",""]
            conn = get_connection()
            try:
                if sid:
                    conn.execute("""UPDATE students SET name=?,father_name=?,mother_name=?,dob=?,
                        phone=?,roll_no=?,admission_date=?,address=?,gender=?,class_name=?,section=?,status=?
                        WHERE student_id=?""",
                        (data["name"],data["father_name"],data["mother_name"],data["dob"],
                         data["phone"],data["roll_no"],data["admission_date"],data["address"],
                         data["gender"],cs[0],cs[1] if len(cs)>1 else "",data["status"],sid))
                else:
                    conn.execute("""INSERT INTO students
                        (student_id,name,father_name,mother_name,dob,phone,roll_no,admission_date,address,gender,class_name,section,status)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (data["student_id"],data["name"],data["father_name"],data["mother_name"],
                         data["dob"],data["phone"],data["roll_no"],data["admission_date"],
                         data["address"],data["gender"],cs[0],cs[1] if len(cs)>1 else "","Active"))
                conn.commit()
                messagebox.showinfo("Success","Student saved!")
                d.destroy(); self.load()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Student ID already exists!")
            finally: conn.close()
        btn(d, "💾 Save Student", save, w=200, h=42).pack(pady=15)

    def delete(self):
        r = self.get_sel()
        if r and messagebox.askyesno("Confirm", f"Delete student {r[1]}?"):
            conn = get_connection()
            conn.execute("DELETE FROM students WHERE student_id=?", (r[0],))
            conn.commit(); conn.close(); self.load()

# ─── TEACHERS ────────────────────────────────────────────────────────────────

class TeachersModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build(); self.load()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15,5))
        label(top, "Teacher Management", 22, bold=True).pack(side="left")
        bf = ctk.CTkFrame(top, fg_color="transparent")
        bf.pack(side="right")
        btn(bf, "+ Add Teacher", self.open_add, w=140).pack(side="left", padx=4)
        btn(bf, "✏ Edit",        lambda: self.open_edit(), color=COLORS["accent"], w=90).pack(side="left", padx=4)
        btn(bf, "🗑 Delete",     self.delete, color=COLORS["danger"], w=90).pack(side="left", padx=4)

        sf = ctk.CTkFrame(self, fg_color=COLORS["white"], corner_radius=10,
                          border_width=1, border_color=COLORS["border"])
        sf.pack(fill="x", padx=20, pady=6)
        label(sf, "Search:", color=COLORS["muted"]).pack(side="left", padx=10, pady=8)
        self.sv = ctk.StringVar()
        self.sv.trace_add("write", lambda *_: self.load())
        entry(sf, "Name, ID, Subject...", 300, textvariable=self.sv).pack(side="left", padx=4)

        tf, self.tree = make_scrolled_tree(self,
            ("ID","Name","Subject","Qualification","Phone","Salary","Status"),
            [95,200,150,150,120,100,80])
        tf.pack(fill="both", expand=True, padx=20, pady=(4,15))
        self.tree.bind("<Double-1>", lambda _: self.open_edit())

    def load(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        s = self.sv.get().strip()
        conn = get_connection()
        q = "SELECT teacher_id,name,subject,qualification,phone,salary,status FROM teachers WHERE 1=1"
        p = []
        if s:
            q += " AND (name LIKE ? OR teacher_id LIKE ? OR subject LIKE ?)"
            p += [f"%{s}%"]*3
        rows = conn.execute(q + " ORDER BY name", p).fetchall()
        conn.close()
        for r in rows: self.tree.insert("","end", values=tuple(r))

    def get_sel(self):
        s = self.tree.selection()
        if not s: messagebox.showwarning("Select","Select a teacher first."); return None
        return self.tree.item(s[0])["values"]

    def open_add(self): self._form()
    def open_edit(self):
        r = self.get_sel()
        if r: self._form(r[0])

    def _form(self, tid=None):
        d = ctk.CTkToplevel(self)
        d.title("Add Teacher" if not tid else "Edit Teacher")
        d.geometry("600x540"); d.grab_set()
        label(d, "Teacher Information", 18, bold=True).pack(pady=(15,5))
        fr = ctk.CTkFrame(d, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=30)
        f = {}
        def er(lbl, key, row, col=0, vals=None):
            ctk.CTkLabel(fr, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(
                row=row, column=col*2, sticky="w", pady=5, padx=6)
            w = combo(fr, vals, 200) if vals else entry(fr, width=200)
            w.grid(row=row, column=col*2+1, pady=5, padx=6)
            f[key] = w
        subjects = ["Mathematics","Physics","Chemistry","Biology","English",
                    "Bangla","History","Geography","ICT","Religion"]
        er("Teacher ID *","teacher_id",0,0); er("Full Name *","name",0,1)
        er("Subject","subject",1,0,subjects); er("Qualification","qualification",1,1)
        er("Phone","phone",2,0); er("Email","email",2,1)
        er("Salary (৳)","salary",3,0); er("Join Date","join_date",3,1)
        er("Gender","gender",4,0,["Male","Female","Other"])
        er("Address","address",4,1)
        er("Status","status",5,0,["Active","Inactive","On Leave"])
        f["join_date"].insert(0, date.today().isoformat())
        if tid:
            conn = get_connection()
            t = conn.execute("SELECT * FROM teachers WHERE teacher_id=?", (tid,)).fetchone()
            conn.close()
            if t:
                for k in ["teacher_id","name","qualification","phone","email","address","join_date"]:
                    if k in f and t[k]: f[k].insert(0, str(t[k]))
                if t["salary"]: f["salary"].insert(0, str(t["salary"]))
                f["subject"].set(t["subject"] or "")
                f["gender"].set(t["gender"] or "Male")
                f["status"].set(t["status"] or "Active")
        def save():
            data = {k: (v.get() if hasattr(v,"get") else "") for k,v in f.items()}
            if not data["teacher_id"] or not data["name"]:
                messagebox.showerror("Error","ID and Name required!"); return
            conn = get_connection()
            try:
                if tid:
                    conn.execute("""UPDATE teachers SET name=?,subject=?,qualification=?,phone=?,email=?,
                        salary=?,join_date=?,gender=?,address=?,status=? WHERE teacher_id=?""",
                        (data["name"],data["subject"],data["qualification"],data["phone"],data["email"],
                         data["salary"] or 0,data["join_date"],data["gender"],data["address"],data["status"],tid))
                else:
                    conn.execute("""INSERT INTO teachers
                        (teacher_id,name,subject,qualification,phone,email,salary,join_date,gender,address,status)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (data["teacher_id"],data["name"],data["subject"],data["qualification"],data["phone"],
                         data["email"],data["salary"] or 0,data["join_date"],data["gender"],data["address"],"Active"))
                conn.commit()
                messagebox.showinfo("Success","Teacher saved!")
                d.destroy(); self.load()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Teacher ID already exists!")
            finally: conn.close()
        btn(d, "💾 Save Teacher", save, w=200, h=42).pack(pady=15)

    def delete(self):
        r = self.get_sel()
        if r and messagebox.askyesno("Confirm", f"Delete {r[1]}?"):
            conn = get_connection()
            conn.execute("DELETE FROM teachers WHERE teacher_id=?", (r[0],))
            conn.commit(); conn.close(); self.load()

# ─── ATTENDANCE ──────────────────────────────────────────────────────────────

class AttendanceModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.att_data = {}
        self.build()

    def build(self):
        label(self, "Attendance Management", 22, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        tab = ctk.CTkTabview(self, fg_color=COLORS["white"], corner_radius=10,
                             segmented_button_fg_color=COLORS["primary_dark"],
                             segmented_button_selected_color=COLORS["primary"],
                             segmented_button_unselected_color="#aaa",
                             segmented_button_selected_hover_color=COLORS["primary"])
        tab.pack(fill="both", expand=True, padx=20, pady=10)
        tab.add("Mark Attendance"); tab.add("View Records"); tab.add("Monthly Summary")
        self._mark_tab(tab.tab("Mark Attendance"))
        self._view_tab(tab.tab("View Records"))
        self._summary_tab(tab.tab("Monthly Summary"))

    def _mark_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        label(ctrl, "Date:", color=COLORS["muted"]).pack(side="left", padx=10)
        self.att_date = entry(ctrl, "YYYY-MM-DD", 130)
        self.att_date.insert(0, date.today().isoformat())
        self.att_date.pack(side="left", padx=4)
        label(ctrl, "Class:", color=COLORS["muted"]).pack(side="left", padx=(15,4))
        conn = get_connection()
        cls = [f"{r[0]} - {r[1]}" for r in conn.execute(
            "SELECT DISTINCT class_name,section FROM students ORDER BY class_name,section").fetchall()]
        conn.close()
        self.att_cls = combo(ctrl, cls if cls else ["No classes"], 160)
        self.att_cls.pack(side="left", padx=4)
        btn(ctrl, "Load", self.load_for_att, w=110).pack(side="left", padx=10)

        mbf = ctk.CTkFrame(p, fg_color="transparent"); mbf.pack(fill="x", pady=4)
        btn(mbf, "✅ All Present", lambda: self.mark_all("Present"), color=COLORS["success"], w=140).pack(side="left", padx=10)
        btn(mbf, "❌ All Absent",  lambda: self.mark_all("Absent"),  color=COLORS["danger"],  w=140).pack(side="left", padx=4)

        self.att_scroll = ctk.CTkScrollableFrame(p, fg_color=COLORS["white"],
                                                  border_width=1, border_color=COLORS["border"], corner_radius=8)
        self.att_scroll.pack(fill="both", expand=True, pady=6)
        btn(p, "💾 Save Attendance", self.save_att, w=200, h=40).pack(pady=10)

    def load_for_att(self):
        for w in self.att_scroll.winfo_children(): w.destroy()
        self.att_data = {}
        cs = self.att_cls.get().split(" - ")
        if len(cs) < 2: return
        conn = get_connection()
        students = conn.execute(
            "SELECT student_id,name,roll_no FROM students WHERE class_name=? AND section=? AND status='Active' ORDER BY roll_no,name",
            (cs[0],cs[1])).fetchall()
        att_date = self.att_date.get()
        existing = {}
        for s in students:
            r = conn.execute("SELECT status FROM attendance WHERE student_id=? AND date=?", (s[0],att_date)).fetchone()
            existing[s[0]] = r[0] if r else "Present"
        conn.close()
        hdr = ctk.CTkFrame(self.att_scroll, fg_color=COLORS["primary_dark"], corner_radius=6)
        hdr.pack(fill="x", pady=(0,4))
        for txt, w in [("Roll",60),("Name",240),("Status",250)]:
            ctk.CTkLabel(hdr, text=txt, font=("Arial",12,"bold"), text_color="white", width=w).pack(side="left", padx=5, pady=6)
        for s in students:
            rf = ctk.CTkFrame(self.att_scroll, fg_color="transparent"); rf.pack(fill="x", pady=2)
            ctk.CTkLabel(rf, text=str(s[2] or "-"), width=60, font=("Arial",12)).pack(side="left", padx=5)
            ctk.CTkLabel(rf, text=s[1], width=240, font=("Arial",12), anchor="w").pack(side="left", padx=5)
            var = ctk.StringVar(value=existing.get(s[0], "Present"))
            self.att_data[s[0]] = var
            for status, col in [("Present",COLORS["success"]),("Absent",COLORS["danger"]),("Late",COLORS["warning"])]:
                ctk.CTkRadioButton(rf, text=status, variable=var, value=status,
                                   fg_color=col, font=("Arial",12)).pack(side="left", padx=12)

    def mark_all(self, status):
        for v in self.att_data.values(): v.set(status)

    def save_att(self):
        if not self.att_data: messagebox.showwarning("Warning","Load students first!"); return
        cs = self.att_cls.get().split(" - ")
        att_date = self.att_date.get()
        conn = get_connection()
        for sid, var in self.att_data.items():
            conn.execute("INSERT OR REPLACE INTO attendance (student_id,date,status,class_name,section) VALUES (?,?,?,?,?)",
                         (sid, att_date, var.get(), cs[0], cs[1] if len(cs)>1 else ""))
        conn.commit(); conn.close()
        messagebox.showinfo("Success", f"Attendance saved for {att_date}!")

    def _view_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        label(ctrl, "From:", color=COLORS["muted"]).pack(side="left", padx=10)
        self.vf = entry(ctrl, "YYYY-MM-DD", 120); self.vf.pack(side="left", padx=4)
        self.vf.insert(0, date.today().isoformat()[:8]+"01")
        label(ctrl, "To:", color=COLORS["muted"]).pack(side="left", padx=6)
        self.vt = entry(ctrl, "YYYY-MM-DD", 120); self.vt.pack(side="left", padx=4)
        self.vt.insert(0, date.today().isoformat())
        btn(ctrl, "Search", self.view_att, w=100).pack(side="left", padx=10)
        tf, self.vtree = make_scrolled_tree(p,
            ("Date","Student ID","Name","Status","Class"),
            [110,110,180,100,130])
        tf.pack(fill="both", expand=True, pady=8)

    def view_att(self):
        for r in self.vtree.get_children(): self.vtree.delete(r)
        conn = get_connection()
        rows = conn.execute("""SELECT a.date,a.student_id,s.name,a.status,a.class_name
            FROM attendance a LEFT JOIN students s ON a.student_id=s.student_id
            WHERE a.date BETWEEN ? AND ? ORDER BY a.date DESC""",
            (self.vf.get(), self.vt.get())).fetchall()
        conn.close()
        for r in rows: self.vtree.insert("","end", values=tuple(r))

    def _summary_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        label(ctrl, "Month:", color=COLORS["muted"]).pack(side="left", padx=10)
        self.sm = entry(ctrl, "YYYY-MM", 100); self.sm.insert(0, date.today().strftime("%Y-%m"))
        self.sm.pack(side="left", padx=4)
        btn(ctrl, "Generate", self.gen_summary, w=120).pack(side="left", padx=10)
        tf, self.stree = make_scrolled_tree(p,
            ("Student ID","Name","Class","Total","Present","Absent","Late","Percentage"),
            [100,180,100,80,80,80,70,100])
        tf.pack(fill="both", expand=True, pady=8)

    def gen_summary(self):
        for r in self.stree.get_children(): self.stree.delete(r)
        month = self.sm.get()
        conn = get_connection()
        students = conn.execute("SELECT student_id,name,class_name FROM students WHERE status='Active'").fetchall()
        for s in students:
            rows = conn.execute("SELECT status FROM attendance WHERE student_id=? AND date LIKE ?",
                                (s[0], f"{month}%")).fetchall()
            total = len(rows)
            present = sum(1 for r in rows if r[0]=="Present")
            absent  = sum(1 for r in rows if r[0]=="Absent")
            late    = sum(1 for r in rows if r[0]=="Late")
            pct = f"{present/total*100:.1f}%" if total > 0 else "N/A"
            self.stree.insert("","end", values=(s[0],s[1],s[2],total,present,absent,late,pct))
        conn.close()

# ─── FEES ────────────────────────────────────────────────────────────────────

class FeesModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.due_vars = {}
        self.build(); self.load_fees()

    def build(self):
        label(self, "Fees Management", 22, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        tab = ctk.CTkTabview(self, fg_color=COLORS["white"], corner_radius=10,
                             segmented_button_fg_color=COLORS["primary_dark"],
                             segmented_button_selected_color=COLORS["primary"],
                             segmented_button_unselected_color="#aaa",
                             segmented_button_selected_hover_color=COLORS["primary"])
        tab.pack(fill="both", expand=True, padx=20, pady=10)
        tab.add("Fee Records"); tab.add("Collect Fee"); tab.add("Due Report")
        self._records_tab(tab.tab("Fee Records"))
        self._collect_tab(tab.tab("Collect Fee"))
        self._due_tab(tab.tab("Due Report"))

    def _records_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        self.fsearch = entry(ctrl, "Search student ID or name...", 260)
        self.fsearch.pack(side="left", padx=10)
        btn(ctrl, "Search", self.load_fees, w=90).pack(side="left", padx=4)
        btn(ctrl, "+ Add Fee", self.add_fee_dialog, color=COLORS["accent"], w=110).pack(side="left", padx=10)
        tf, self.ftree = make_scrolled_tree(p,
            ("Receipt","Student ID","Name","Fee Type","Amount","Paid","Due Date","Month","Status"),
            [90,95,150,120,80,80,100,80,90])
        tf.pack(fill="both", expand=True, pady=6)
        self.ftree.tag_configure("paid",    foreground=COLORS["success"])
        self.ftree.tag_configure("unpaid",  foreground=COLORS["danger"])
        self.ftree.tag_configure("partial", foreground=COLORS["warning"])

    def load_fees(self):
        for r in self.ftree.get_children(): self.ftree.delete(r)
        s = self.fsearch.get().strip()
        conn = get_connection()
        q = """SELECT f.receipt_no,f.student_id,s.name,f.fee_type,f.amount,f.paid_amount,
               f.due_date,f.month,f.status FROM fees f
               LEFT JOIN students s ON f.student_id=s.student_id WHERE 1=1"""
        p = []
        if s:
            q += " AND (f.student_id LIKE ? OR s.name LIKE ?)"; p += [f"%{s}%"]*2
        rows = conn.execute(q + " ORDER BY f.id DESC", p).fetchall()
        conn.close()
        for r in rows:
            tag = "paid" if r[8]=="Paid" else ("partial" if r[8]=="Partial" else "unpaid")
            self.ftree.insert("","end", values=tuple(r), tags=(tag,))

    def add_fee_dialog(self):
        d = ctk.CTkToplevel(self); d.title("Add Fee"); d.geometry("480x440"); d.grab_set()
        label(d, "Add Fee Record", 18, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=30)
        f = {}
        def er(lbl, key, row, vals=None):
            ctk.CTkLabel(fr, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(row=row, column=0, sticky="w", pady=6)
            w = combo(fr, vals, 260) if vals else entry(fr, width=260)
            w.grid(row=row, column=1, pady=6, padx=10); f[key] = w
        er("Student ID *","student_id",0)
        er("Fee Type *","fee_type",1,["Tuition Fee","Exam Fee","Library Fee","Sports Fee","Transport Fee","Miscellaneous"])
        er("Amount (৳) *","amount",2)
        er("Month","month",3,["January","February","March","April","May","June",
                               "July","August","September","October","November","December"])
        er("Year","year",4); er("Due Date","due_date",5)
        f["year"].insert(0, str(date.today().year))
        f["due_date"].insert(0, date.today().isoformat())
        def save():
            sid = f["student_id"].get().strip()
            ft = f["fee_type"].get()
            amt = f["amount"].get().strip()
            if not sid or not ft or not amt:
                messagebox.showerror("Error","Student ID, Fee Type and Amount required!"); return
            try: amt = float(amt)
            except: messagebox.showerror("Error","Invalid amount!"); return
            receipt = "RCP-" + "".join(random.choices(string.ascii_uppercase+string.digits, k=6))
            conn = get_connection()
            conn.execute("INSERT INTO fees (student_id,fee_type,amount,month,year,due_date,receipt_no,status) VALUES (?,?,?,?,?,?,?,'Unpaid')",
                         (sid,ft,amt,f["month"].get(),f["year"].get(),f["due_date"].get(),receipt))
            conn.commit(); conn.close()
            messagebox.showinfo("Success", f"Fee added! Receipt: {receipt}")
            d.destroy(); self.load_fees()
        btn(d, "Add Fee", save, w=180, h=42).pack(pady=20)

    def _collect_tab(self, p):
        label(p, "Collect Fee Payment", 15, bold=True).pack(pady=12)
        fr = ctk.CTkFrame(p, fg_color=COLORS["white"], corner_radius=10,
                          border_width=1, border_color=COLORS["border"])
        fr.pack(fill="x", padx=30, pady=8)
        ctk.CTkLabel(fr, text="Student ID:", font=("Arial",13), text_color=COLORS["muted"]).grid(row=0,column=0,padx=15,pady=10,sticky="w")
        self.pay_sid = entry(fr, width=200); self.pay_sid.grid(row=0,column=1,padx=10,pady=10)
        btn(fr, "Load Dues", self.load_dues, color=COLORS["accent"], w=110).grid(row=0,column=2,padx=10)
        self.due_scroll = ctk.CTkScrollableFrame(p, height=220, fg_color=COLORS["white"],
                                                  border_width=1, border_color=COLORS["border"], corner_radius=8)
        self.due_scroll.pack(fill="x", padx=30, pady=6)
        pr = ctk.CTkFrame(p, fg_color="transparent"); pr.pack(fill="x", padx=30, pady=4)
        label(pr, "Pay Amount (৳):").pack(side="left")
        self.pay_amt = entry(pr, width=150); self.pay_amt.pack(side="left", padx=10)
        btn(pr, "💳 Collect", self.collect, color=COLORS["success"], w=150).pack(side="left", padx=8)
        self.pay_msg = label(p, ""); self.pay_msg.pack(pady=4)

    def load_dues(self):
        for w in self.due_scroll.winfo_children(): w.destroy()
        self.due_vars = {}
        sid = self.pay_sid.get().strip()
        if not sid: return
        conn = get_connection()
        student = conn.execute("SELECT name FROM students WHERE student_id=?", (sid,)).fetchone()
        dues = conn.execute("SELECT id,fee_type,amount,paid_amount,month,status FROM fees WHERE student_id=? AND status!='Paid'", (sid,)).fetchall()
        conn.close()
        if student:
            label(self.due_scroll, f"Student: {student[0]}", 13, bold=True, color=COLORS["primary"]).pack(anchor="w", padx=10, pady=6)
        total_due = 0
        for d in dues:
            remaining = d[2] - d[3]; total_due += remaining
            rf = ctk.CTkFrame(self.due_scroll, fg_color="transparent"); rf.pack(fill="x", padx=5, pady=2)
            var = ctk.BooleanVar(value=True); self.due_vars[d[0]] = (var, remaining)
            ctk.CTkCheckBox(rf, text=f"{d[1]} ({d[4]}) — Due: ৳{remaining:.2f}",
                            variable=var, font=("Arial",12), fg_color=COLORS["primary"]).pack(side="left", padx=8)
        label(self.due_scroll, f"Total Due: ৳{total_due:.2f}", 13, bold=True, color=COLORS["danger"]).pack(anchor="w", padx=10, pady=6)
        self.pay_amt.delete(0,"end"); self.pay_amt.insert(0, str(round(total_due,2)))

    def collect(self):
        sid = self.pay_sid.get().strip()
        if not sid or not self.due_vars:
            messagebox.showwarning("Warning","Load student dues first!"); return
        try: pay = float(self.pay_amt.get())
        except: messagebox.showerror("Error","Invalid amount!"); return
        conn = get_connection()
        for fid, (var, remaining) in self.due_vars.items():
            if var.get() and pay > 0:
                paid = min(pay, remaining); pay -= paid
                new_paid = conn.execute("SELECT paid_amount FROM fees WHERE id=?", (fid,)).fetchone()[0] + paid
                total_amt = conn.execute("SELECT amount FROM fees WHERE id=?", (fid,)).fetchone()[0]
                status = "Paid" if new_paid >= total_amt else "Partial"
                conn.execute("UPDATE fees SET paid_amount=?,status=?,paid_date=? WHERE id=?",
                             (new_paid, status, date.today().isoformat(), fid))
        conn.commit(); conn.close()
        self.pay_msg.configure(text="✅ Payment collected!", text_color=COLORS["success"])
        self.load_fees(); self.load_dues()

    def _due_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        btn(ctrl, "Load All Dues", self.load_all_dues, color=COLORS["danger"], w=140).pack(side="left", padx=10)
        tf, self.dtree = make_scrolled_tree(p,
            ("Student ID","Name","Class","Fee Type","Amount","Paid","Remaining","Due Date","Status"),
            [95,150,90,120,80,80,90,100,90])
        tf.pack(fill="both", expand=True, pady=6)

    def load_all_dues(self):
        for r in self.dtree.get_children(): self.dtree.delete(r)
        conn = get_connection()
        rows = conn.execute("""SELECT f.student_id,s.name,s.class_name,f.fee_type,f.amount,
               f.paid_amount,(f.amount-f.paid_amount) as rem,f.due_date,f.status
               FROM fees f LEFT JOIN students s ON f.student_id=s.student_id
               WHERE f.status!='Paid' ORDER BY rem DESC""").fetchall()
        conn.close()
        for r in rows: self.dtree.insert("","end", values=tuple(r))

# ─── ACCOUNTING & FINANCE (NEW MODULE) ───────────────────────────────────────

class AccountingModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build(); self.load_expenses()

    def build(self):
        label(self, "Accounting & Finance", 22, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        tab = ctk.CTkTabview(self, fg_color=COLORS["white"], corner_radius=10,
                             segmented_button_fg_color=COLORS["primary_dark"],
                             segmented_button_selected_color=COLORS["primary"],
                             segmented_button_unselected_color="#aaa",
                             segmented_button_selected_hover_color=COLORS["primary"])
        tab.pack(fill="both", expand=True, padx=20, pady=10)
        tab.add("Expenses"); tab.add("Financial Summary")
        self._expenses_tab(tab.tab("Expenses"))
        self._summary_tab(tab.tab("Financial Summary"))

    def _expenses_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        btn(ctrl, "+ Add Expense", self.add_expense_dialog, w=140).pack(side="left", padx=10)

        tf, self.etree = make_scrolled_tree(p,
            ("ID", "Expense Title", "Category", "Amount", "Date", "Recorded By"),
            [60, 250, 150, 100, 120, 150])
        tf.pack(fill="both", expand=True, pady=6)

    def load_expenses(self):
        for r in self.etree.get_children(): self.etree.delete(r)
        conn = get_connection()
        rows = conn.execute("SELECT id, title, category, amount, expense_date, recorded_by FROM expenses ORDER BY id DESC").fetchall()
        conn.close()
        for r in rows: self.etree.insert("","end", values=tuple(r))

    def add_expense_dialog(self):
        d = ctk.CTkToplevel(self); d.title("Add Expense"); d.geometry("400x380"); d.grab_set()
        label(d, "Record Expense", 18, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=30)
        f = {}
        def er(lbl, key, row, vals=None):
            ctk.CTkLabel(fr, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(row=row, column=0, sticky="w", pady=6)
            w = combo(fr, vals, 200) if vals else entry(fr, width=200)
            w.grid(row=row, column=1, pady=6, padx=10); f[key] = w

        er("Title *", "title", 0)
        er("Category", "category", 1, ["Salary", "Utilities", "Maintenance", "Supplies", "Events", "Other"])
        er("Amount (৳) *", "amount", 2)
        er("Date", "date", 3)
        er("Recorded By", "recorded_by", 4)

        f["date"].insert(0, date.today().isoformat())
        f["recorded_by"].insert(0, "Admin")

        def save():
            title = f["title"].get().strip()
            amt = f["amount"].get().strip()
            if not title or not amt: messagebox.showerror("Error", "Title and Amount required!"); return
            try: amt = float(amt)
            except: messagebox.showerror("Error", "Invalid amount!"); return

            conn = get_connection()
            conn.execute("INSERT INTO expenses (title, category, amount, expense_date, recorded_by) VALUES (?,?,?,?,?)",
                         (title, f["category"].get(), amt, f["date"].get(), f["recorded_by"].get()))
            conn.commit(); conn.close()
            messagebox.showinfo("Success", "Expense recorded!"); d.destroy(); self.load_expenses()

        btn(d, "Save Expense", save, w=160, h=40).pack(pady=15)

    def _summary_tab(self, p):
        self.sum_frame = ctk.CTkFrame(p, fg_color="transparent")
        self.sum_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.load_summary()

    def load_summary(self):
        for w in self.sum_frame.winfo_children(): w.destroy()
        conn = get_connection()
        total_income = conn.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM fees").fetchone()[0]
        total_expense = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]
        conn.close()

        net_profit = total_income - total_expense

        label(self.sum_frame, "School Financial Summary", 18, bold=True).pack(pady=10)

        cards = ctk.CTkFrame(self.sum_frame, fg_color="transparent")
        cards.pack(fill="x", pady=20)

        for title, val, col in [
            ("Total Income (Fees)", total_income, COLORS["success"]),
            ("Total Expenses", total_expense, COLORS["danger"]),
            ("Net Balance", net_profit, COLORS["primary_dark"])
        ]:
            c = ctk.CTkFrame(cards, fg_color=col, corner_radius=12, width=200, height=100)
            c.pack(side="left", padx=15, expand=True, fill="both")
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=title, font=("Arial", 14), text_color="#ffffffcc").pack(pady=(15,5))
            ctk.CTkLabel(c, text=f"৳ {val:,.2f}", font=("Arial", 22, "bold"), text_color="white").pack()

# ─── INVENTORY MODULE (NEW MODULE) ───────────────────────────────────────────

class InventoryModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build(); self.load_items()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15,5))
        label(top, "Inventory & Asset Management", 22, bold=True).pack(side="left")
        btn(top, "+ Add Item", self.add_item_dialog, w=140).pack(side="right")

        tf, self.tree = make_scrolled_tree(self,
            ("ID", "Item Name", "Category", "Quantity", "Status"),
            [80, 250, 180, 100, 150])
        tf.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-1>", self.edit_item)

    def load_items(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        rows = conn.execute("SELECT id, item_name, category, quantity, status FROM inventory ORDER BY item_name").fetchall()
        conn.close()
        for r in rows: self.tree.insert("", "end", values=tuple(r))

    def add_item_dialog(self):
        self._form()

    def edit_item(self, _):
        s = self.tree.selection()
        if not s: return
        item_id = self.tree.item(s[0])["values"][0]
        self._form(item_id)

    def _form(self, iid=None):
        d = ctk.CTkToplevel(self); d.title("Add Asset" if not iid else "Edit Asset"); d.geometry("400x320"); d.grab_set()
        label(d, "Asset Information", 16, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=30)
        f = {}
        def er(lbl, key, row, vals=None):
            ctk.CTkLabel(fr, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(row=row, column=0, sticky="w", pady=6)
            w = combo(fr, vals, 200) if vals else entry(fr, width=200)
            w.grid(row=row, column=1, pady=6, padx=10); f[key] = w

        er("Item Name *", "name", 0)
        er("Category", "category", 1, ["Furniture", "Electronics", "Lab Equipment", "Sports", "Stationery", "Other"])
        er("Quantity *", "quantity", 2)
        er("Status", "status", 3, ["Good", "Needs Repair", "Damaged", "Lost"])

        if iid:
            conn = get_connection()
            item = conn.execute("SELECT * FROM inventory WHERE id=?", (iid,)).fetchone()
            conn.close()
            f["name"].insert(0, item["item_name"])
            f["category"].set(item["category"])
            f["quantity"].insert(0, str(item["quantity"]))
            f["status"].set(item["status"])

        def save():
            name = f["name"].get().strip()
            try: qty = int(f["quantity"].get())
            except: messagebox.showerror("Error", "Invalid quantity!"); return
            if not name: messagebox.showerror("Error", "Item name required!"); return

            conn = get_connection()
            if iid:
                conn.execute("UPDATE inventory SET item_name=?, category=?, quantity=?, status=? WHERE id=?",
                             (name, f["category"].get(), qty, f["status"].get(), iid))
            else:
                conn.execute("INSERT INTO inventory (item_name, category, quantity, status) VALUES (?,?,?,?)",
                             (name, f["category"].get(), qty, f["status"].get()))
            conn.commit(); conn.close()
            messagebox.showinfo("Success", "Asset saved!"); d.destroy(); self.load_items()

        btn(d, "Save Item", save, w=160, h=40).pack(pady=15)

# ─── EXAMS & RESULTS ─────────────────────────────────────────────────────────

class ExamsModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.marks_entries = {}
        self.build()

    def build(self):
        label(self, "Exams & Results", 22, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        tab = ctk.CTkTabview(self, fg_color=COLORS["white"], corner_radius=10,
                             segmented_button_fg_color=COLORS["primary_dark"],
                             segmented_button_selected_color=COLORS["primary"],
                             segmented_button_unselected_color="#aaa",
                             segmented_button_selected_hover_color=COLORS["primary"])
        tab.pack(fill="both", expand=True, padx=20, pady=10)
        tab.add("Exams"); tab.add("Enter Marks"); tab.add("Results"); tab.add("Report Card")
        self._exams_tab(tab.tab("Exams"))
        self._marks_tab(tab.tab("Enter Marks"))
        self._results_tab(tab.tab("Results"))
        self._report_tab(tab.tab("Report Card"))

    def _exams_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        btn(ctrl, "+ Create Exam", self.create_exam, w=140).pack(side="left", padx=10)
        tf, self.etree = make_scrolled_tree(p,
            ("ID","Exam Name","Class","Subject","Date","Total Marks","Pass Marks"),
            [50,200,120,130,110,110,100])
        tf.pack(fill="both", expand=True, pady=6)
        self.load_exams()

    def load_exams(self):
        for r in self.etree.get_children(): self.etree.delete(r)
        conn = get_connection()
        rows = conn.execute("SELECT id,exam_name,class_name,subject,exam_date,total_marks,pass_marks FROM exams ORDER BY id DESC").fetchall()
        conn.close()
        for r in rows: self.etree.insert("","end", values=tuple(r))

    def create_exam(self):
        d = ctk.CTkToplevel(self); d.title("Create Exam"); d.geometry("480x420"); d.grab_set()
        label(d, "Create Exam", 18, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=30)
        f = {}
        def er(lbl, key, row, vals=None):
            ctk.CTkLabel(fr, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(row=row, column=0, sticky="w", pady=6)
            w = combo(fr, vals, 260) if vals else entry(fr, width=260)
            w.grid(row=row, column=1, pady=6, padx=10); f[key] = w
        subjects = ["Mathematics","Physics","Chemistry","Biology","English","Bangla","History","Geography","ICT","All Subjects"]
        er("Exam Name *","exam_name",0); er("Class","class_name",1)
        er("Subject","subject",2,subjects); er("Exam Date","exam_date",3)
        er("Total Marks","total_marks",4); er("Pass Marks","pass_marks",5)
        f["exam_date"].insert(0, date.today().isoformat())
        f["total_marks"].insert(0,"100"); f["pass_marks"].insert(0,"33")
        def save():
            name = f["exam_name"].get().strip()
            if not name: messagebox.showerror("Error","Exam name required!"); return
            try:
                total = float(f["total_marks"].get()); pass_m = float(f["pass_marks"].get())
            except: messagebox.showerror("Error","Invalid marks!"); return
            conn = get_connection()
            conn.execute("INSERT INTO exams (exam_name,class_name,subject,exam_date,total_marks,pass_marks) VALUES (?,?,?,?,?,?)",
                         (name,f["class_name"].get(),f["subject"].get(),f["exam_date"].get(),total,pass_m))
            conn.commit(); conn.close()
            messagebox.showinfo("Success","Exam created!"); d.destroy(); self.load_exams()
        btn(d, "Create Exam", save, w=180, h=42).pack(pady=20)

    def _marks_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        label(ctrl, "Exam:", color=COLORS["muted"]).pack(side="left", padx=10)
        conn = get_connection()
        exams = [f"{r[0]}: {r[1]}" for r in conn.execute("SELECT id,exam_name FROM exams ORDER BY id DESC").fetchall()]
        conn.close()
        self.me = combo(ctrl, exams if exams else ["No exams"], 220)
        self.me.pack(side="left", padx=4)
        label(ctrl, "Class:", color=COLORS["muted"]).pack(side="left", padx=(15,4))
        self.mc = entry(ctrl, "e.g. Class 10", 130); self.mc.pack(side="left", padx=4)
        btn(ctrl, "Load", self.load_for_marks, w=110).pack(side="left", padx=10)
        self.ms = ctk.CTkScrollableFrame(p, fg_color=COLORS["white"],
                                          border_width=1, border_color=COLORS["border"], corner_radius=8)
        self.ms.pack(fill="both", expand=True, pady=6)
        btn(p, "💾 Save Marks", self.save_marks, w=180, h=40).pack(pady=10)

    def load_for_marks(self):
        for w in self.ms.winfo_children(): w.destroy()
        self.marks_entries = {}
        cn = self.mc.get().strip()
        conn = get_connection()
        students = conn.execute("SELECT student_id,name FROM students WHERE class_name=? AND status='Active' ORDER BY name", (cn,)).fetchall()
        conn.close()
        hdr = ctk.CTkFrame(self.ms, fg_color=COLORS["primary_dark"], corner_radius=4)
        hdr.pack(fill="x", pady=(0,4))
        for txt, w in [("Student ID",130),("Name",250),("Marks",160),("Grade",80)]:
            ctk.CTkLabel(hdr, text=txt, font=("Arial",12,"bold"), text_color="white", width=w).pack(side="left", padx=5, pady=6)
        for s in students:
            rf = ctk.CTkFrame(self.ms, fg_color="transparent"); rf.pack(fill="x", pady=2)
            ctk.CTkLabel(rf, text=s[0], width=130, font=("Arial",11)).pack(side="left", padx=5)
            ctk.CTkLabel(rf, text=s[1], width=250, font=("Arial",11), anchor="w").pack(side="left", padx=5)
            e = entry(rf, width=130, h=30); e.pack(side="left", padx=5)
            gl = ctk.CTkLabel(rf, text="-", width=80, font=("Arial",11)); gl.pack(side="left", padx=5)
            self.marks_entries[s[0]] = (e, gl)
            def upd(_, sid=s[0]):
                try:
                    es = self.me.get()
                    if ":" not in es: return
                    eid = int(es.split(":")[0])
                    conn2 = get_connection()
                    tot = conn2.execute("SELECT total_marks FROM exams WHERE id=?", (eid,)).fetchone()
                    conn2.close()
                    marks = float(self.marks_entries[sid][0].get())
                    self.marks_entries[sid][1].configure(text=get_grade(marks, tot[0] if tot else 100))
                except: pass
            e.bind("<KeyRelease>", upd)

    def save_marks(self):
        es = self.me.get()
        if not es or ":" not in es: messagebox.showerror("Error","Select an exam!"); return
        eid = int(es.split(":")[0])
        conn = get_connection()
        total = conn.execute("SELECT total_marks FROM exams WHERE id=?", (eid,)).fetchone()[0]
        saved = 0
        for sid, (e, _) in self.marks_entries.items():
            ms = e.get().strip()
            if ms:
                try:
                    m = float(ms)
                    conn.execute("INSERT OR REPLACE INTO results (student_id,exam_id,marks_obtained,grade) VALUES (?,?,?,?)",
                                 (sid,eid,m,get_grade(m,total))); saved += 1
                except: pass
        conn.commit(); conn.close()
        messagebox.showinfo("Success", f"Marks saved for {saved} students!")

    def _results_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        label(ctrl, "Exam:", color=COLORS["muted"]).pack(side="left", padx=10)
        conn = get_connection()
        exams = [f"{r[0]}: {r[1]}" for r in conn.execute("SELECT id,exam_name FROM exams ORDER BY id DESC").fetchall()]
        conn.close()
        self.re = combo(ctrl, exams if exams else ["No exams"], 220)
        self.re.pack(side="left", padx=4)
        btn(ctrl, "Show Results", self.show_results, w=130).pack(side="left", padx=10)
        tf, self.rtree = make_scrolled_tree(p,
            ("Rank","Student ID","Name","Marks","Total","Percentage","Grade","Status"),
            [60,100,180,80,80,100,70,80])
        tf.pack(fill="both", expand=True, pady=6)

    def show_results(self):
        for r in self.rtree.get_children(): self.rtree.delete(r)
        es = self.re.get()
        if ":" not in es: return
        eid = int(es.split(":")[0])
        conn = get_connection()
        exam = conn.execute("SELECT total_marks,pass_marks FROM exams WHERE id=?", (eid,)).fetchone()
        rows = conn.execute("""SELECT r.student_id,s.name,r.marks_obtained,r.grade
            FROM results r LEFT JOIN students s ON r.student_id=s.student_id
            WHERE r.exam_id=? ORDER BY r.marks_obtained DESC""", (eid,)).fetchall()
        conn.close()
        for rank, r in enumerate(rows, 1):
            pct = f"{r[2]/exam[0]*100:.1f}%" if exam and exam[0] else "N/A"
            status = "Pass" if exam and r[2] >= exam[1] else "Fail"
            self.rtree.insert("","end", values=(rank,r[0],r[1],r[2],exam[0] if exam else "-",pct,r[3],status))

    def _report_tab(self, p):
        label(p, "Student Report Card", 15, bold=True).pack(pady=10)
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", padx=20, pady=4)
        label(ctrl, "Student ID:").pack(side="left", padx=10)
        self.rc_sid = entry(ctrl, width=160); self.rc_sid.pack(side="left", padx=4)
        btn(ctrl, "Generate", self.gen_report, w=120).pack(side="left", padx=10)
        self.rcf = ctk.CTkScrollableFrame(p, fg_color=COLORS["white"],
                                           border_width=1, border_color=COLORS["border"], corner_radius=8)
        self.rcf.pack(fill="both", expand=True, padx=20, pady=10)

    def gen_report(self):
        for w in self.rcf.winfo_children(): w.destroy()
        sid = self.rc_sid.get().strip()
        if not sid: return
        conn = get_connection()
        s = conn.execute("SELECT * FROM students WHERE student_id=?", (sid,)).fetchone()
        if not s:
            label(self.rcf, "Student not found!", color=COLORS["danger"]).pack(pady=20)
            conn.close(); return
        ctk.CTkLabel(self.rcf, text="ACADEMIC REPORT CARD",
                     font=("Georgia",18,"bold"), text_color=COLORS["primary_dark"]).pack(pady=10)
        ctk.CTkLabel(self.rcf, text=f"Name: {s['name']}   |   Class: {s['class_name']}-{s['section']}   |   Roll: {s['roll_no']}",
                     font=("Arial",13), text_color=COLORS["text"]).pack()
        ctk.CTkLabel(self.rcf, text="━"*55, text_color=COLORS["border"]).pack(pady=5)
        results = conn.execute("""SELECT e.exam_name,e.subject,r.marks_obtained,e.total_marks,r.grade
            FROM results r JOIN exams e ON r.exam_id=e.id WHERE r.student_id=? ORDER BY e.exam_date""", (sid,)).fetchall()
        conn.close()
        total_o = total_f = 0
        for res in results:
            rf = ctk.CTkFrame(self.rcf, fg_color="#f8f9fa", corner_radius=6)
            rf.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(rf, text=f"{res[0]} — {res[1]}", width=280, font=("Arial",12), anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(rf, text=f"{res[2]}/{res[3]}", width=100, font=("Arial",12)).pack(side="left")
            col = COLORS["success"] if res[4] not in ["F","D"] else COLORS["danger"]
            ctk.CTkLabel(rf, text=res[4], width=60, font=("Arial",12,"bold"), text_color=col).pack(side="left")
            total_o += res[2]; total_f += res[3]
        if total_f > 0:
            pct = total_o/total_f*100
            ctk.CTkLabel(self.rcf,
                         text=f"Overall: {total_o}/{total_f} = {pct:.1f}%  |  Grade: {get_grade(total_o,total_f)}",
                         font=("Arial",14,"bold"), text_color=COLORS["primary_dark"]).pack(pady=15)

# ─── ASSIGNMENTS ─────────────────────────────────────────────────────────────

class AssignmentsModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build(); self.load()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15,5))
        label(top, "Assignments", 22, bold=True).pack(side="left")
        btn(top, "+ New Assignment", self.new_dialog, w=160).pack(side="right")
        tf, self.tree = make_scrolled_tree(self,
            ("ID","Title","Subject","Class","Section","Due Date","Assigned By","Created"),
            [50,200,130,100,80,110,130,110])
        tf.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-1>", self.view_detail)

    def load(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        rows = conn.execute("SELECT id,title,subject,class_name,section,due_date,assigned_by,created_date FROM assignments ORDER BY id DESC").fetchall()
        conn.close()
        for r in rows: self.tree.insert("","end", values=tuple(r))

    def new_dialog(self):
        d = ctk.CTkToplevel(self); d.title("New Assignment"); d.geometry("520x500"); d.grab_set()
        label(d, "Create Assignment", 18, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=30)
        f = {}
        subjects = ["Mathematics","Physics","Chemistry","Biology","English","Bangla","History","Geography","ICT"]
        def er(lbl, key, row, vals=None, is_text=False):
            ctk.CTkLabel(fr, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(row=row, column=0, sticky="nw", pady=6)
            if is_text:
                w = ctk.CTkTextbox(fr, width=300, height=80)
            elif vals:
                w = combo(fr, vals, 300)
            else:
                w = entry(fr, width=300)
            w.grid(row=row, column=1, pady=6, padx=10); f[key] = w
        er("Title *","title",0); er("Subject","subject",1,subjects)
        er("Class","class_name",2); er("Section","section",3,["A","B","C","D","All"])
        er("Due Date","due_date",4); er("Assigned By","assigned_by",5)
        er("Description","description",6,is_text=True)
        f["due_date"].insert(0, date.today().isoformat())
        def save():
            title = f["title"].get().strip()
            if not title: messagebox.showerror("Error","Title required!"); return
            desc = f["description"].get("1.0","end").strip()
            conn = get_connection()
            conn.execute("INSERT INTO assignments (title,subject,class_name,section,due_date,assigned_by,description,created_date) VALUES (?,?,?,?,?,?,?,?)",
                         (title,f["subject"].get(),f["class_name"].get(),f["section"].get(),
                          f["due_date"].get(),f["assigned_by"].get(),desc,date.today().isoformat()))
            conn.commit(); conn.close()
            messagebox.showinfo("Success","Assignment created!"); d.destroy(); self.load()
        btn(d, "Create", save, w=160, h=42).pack(pady=15)

    def view_detail(self, _=None):
        sel = self.tree.selection()
        if not sel: return
        row = self.tree.item(sel[0])["values"]
        conn = get_connection()
        a = conn.execute("SELECT * FROM assignments WHERE id=?", (row[0],)).fetchone()
        conn.close()
        if not a: return
        d = ctk.CTkToplevel(self); d.title("Assignment Detail"); d.geometry("480x360"); d.grab_set()
        label(d, a["title"], 16, bold=True, color=COLORS["primary_dark"]).pack(pady=15)
        for lbl, val in [("Subject",a["subject"]),("Class",f"{a['class_name']}-{a['section']}"),
                         ("Due Date",a["due_date"]),("Assigned By",a["assigned_by"])]:
            rf = ctk.CTkFrame(d, fg_color="transparent"); rf.pack(fill="x", padx=30, pady=3)
            ctk.CTkLabel(rf, text=f"{lbl}:", width=120, font=("Arial",13,"bold"), text_color=COLORS["muted"]).pack(side="left")
            ctk.CTkLabel(rf, text=val or "-", font=("Arial",13)).pack(side="left")
        label(d, "Description:", 13, bold=True, color=COLORS["muted"]).pack(anchor="w", padx=30, pady=(10,2))
        tb = ctk.CTkTextbox(d, height=120); tb.pack(fill="x", padx=30)
        if a["description"]: tb.insert("1.0", a["description"])
        tb.configure(state="disabled")

# ─── NOTICES ─────────────────────────────────────────────────────────────────

class NoticesModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build(); self.load()

    def build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15,5))
        label(top, "Notice Board", 22, bold=True).pack(side="left")
        btn(top, "+ New Notice", self.new_dialog, w=140).pack(side="right")
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

    def load(self):
        for w in self.scroll.winfo_children(): w.destroy()
        conn = get_connection()
        notices = conn.execute("SELECT * FROM notices ORDER BY id DESC").fetchall()
        conn.close()
        if not notices:
            label(self.scroll, "No notices yet. Create one!", 14, color=COLORS["muted"]).pack(pady=40)
            return
        for n in notices:
            card = ctk.CTkFrame(self.scroll, fg_color=COLORS["white"], corner_radius=10,
                                border_width=1, border_color=COLORS["border"])
            card.pack(fill="x", pady=6)
            hdr = ctk.CTkFrame(card, fg_color=COLORS["primary_dark"], corner_radius=8)
            hdr.pack(fill="x")
            ctk.CTkLabel(hdr, text=n["title"], font=("Arial",14,"bold"),
                         text_color="white", anchor="w").pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(hdr, text=f"For: {n['target']}  |  {n['created_date']}",
                         font=("Arial",11), text_color="#9FE1CB").pack(side="right", padx=12)
            if n["content"]:
                ctk.CTkLabel(card, text=n["content"], font=("Arial",12), wraplength=700,
                             anchor="w", justify="left").pack(fill="x", padx=12, pady=8)
            btn(card, "🗑 Delete", lambda nid=n["id"]: self.delete(nid),
                color=COLORS["danger"], w=90, h=28).pack(anchor="e", padx=10, pady=6)

    def new_dialog(self):
        d = ctk.CTkToplevel(self); d.title("New Notice"); d.geometry("500x420"); d.grab_set()
        label(d, "Create Notice", 18, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=30)
        label(fr, "Title *", color=COLORS["muted"]).pack(anchor="w")
        te = entry(fr, width=420); te.pack(pady=5)
        label(fr, "For", color=COLORS["muted"]).pack(anchor="w")
        tge = combo(fr, ["All","Students","Teachers","Parents"], 200)
        tge.pack(anchor="w", pady=5)
        label(fr, "Content", color=COLORS["muted"]).pack(anchor="w")
        ce = ctk.CTkTextbox(fr, width=420, height=120); ce.pack(pady=5)
        label(fr, "Created By", color=COLORS["muted"]).pack(anchor="w")
        be = entry(fr, width=200); be.pack(anchor="w", pady=5)
        def save():
            title = te.get().strip()
            if not title: messagebox.showerror("Error","Title required!"); return
            conn = get_connection()
            conn.execute("INSERT INTO notices (title,content,target,created_by,created_date) VALUES (?,?,?,?,?)",
                         (title, ce.get("1.0","end").strip(), tge.get(), be.get(), date.today().isoformat()))
            conn.commit(); conn.close(); d.destroy(); self.load()
        btn(d, "Post Notice", save, w=160, h=42).pack(pady=15)

    def delete(self, nid):
        if messagebox.askyesno("Confirm","Delete this notice?"):
            conn = get_connection()
            conn.execute("DELETE FROM notices WHERE id=?", (nid,))
            conn.commit(); conn.close(); self.load()

# ─── LIBRARY ─────────────────────────────────────────────────────────────────

class LibraryModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build(); self.load_books()

    def build(self):
        label(self, "Library Management", 22, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        tab = ctk.CTkTabview(self, fg_color=COLORS["white"], corner_radius=10,
                             segmented_button_fg_color=COLORS["primary_dark"],
                             segmented_button_selected_color=COLORS["primary"],
                             segmented_button_unselected_color="#aaa",
                             segmented_button_selected_hover_color=COLORS["primary"])
        tab.pack(fill="both", expand=True, padx=20, pady=10)
        tab.add("Books"); tab.add("Issue / Return")
        self._books_tab(tab.tab("Books"))
        self._issue_tab(tab.tab("Issue / Return"))

    def _books_tab(self, p):
        ctrl = ctk.CTkFrame(p, fg_color="transparent"); ctrl.pack(fill="x", pady=8)
        btn(ctrl, "+ Add Book", self.add_book_dialog, w=130).pack(side="left", padx=10)
        tf, self.btree = make_scrolled_tree(p,
            ("Book ID","Title","Author","Category","Total","Available"),
            [90,220,160,130,70,80])
        tf.pack(fill="both", expand=True, pady=6)

    def load_books(self):
        for r in self.btree.get_children(): self.btree.delete(r)
        conn = get_connection()
        rows = conn.execute("SELECT book_id,title,author,category,total_copies,available_copies FROM library_books ORDER BY title").fetchall()
        conn.close()
        for r in rows: self.btree.insert("","end", values=tuple(r))

    def add_book_dialog(self):
        d = ctk.CTkToplevel(self); d.title("Add Book"); d.geometry("460x400"); d.grab_set()
        label(d, "Add Book", 18, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=30)
        f = {}
        def er(lbl, key, row, vals=None):
            ctk.CTkLabel(fr, text=lbl, font=("Arial",12), text_color=COLORS["muted"]).grid(row=row, column=0, sticky="w", pady=6)
            w = combo(fr, vals, 260) if vals else entry(fr, width=260)
            w.grid(row=row, column=1, pady=6, padx=10); f[key] = w
        er("Book ID *","book_id",0); er("Title *","title",1); er("Author","author",2)
        er("Category","category",3,["Fiction","Non-Fiction","Science","History","Math","Literature","Reference","Other"])
        er("Total Copies","copies",4); f["copies"].insert(0,"1")
        def save():
            bid = f["book_id"].get().strip(); title = f["title"].get().strip()
            if not bid or not title: messagebox.showerror("Error","Book ID and Title required!"); return
            try: copies = int(f["copies"].get())
            except: copies = 1
            conn = get_connection()
            try:
                conn.execute("INSERT INTO library_books (book_id,title,author,category,total_copies,available_copies) VALUES (?,?,?,?,?,?)",
                             (bid,title,f["author"].get(),f["category"].get(),copies,copies))
                conn.commit(); messagebox.showinfo("Success","Book added!")
                d.destroy(); self.load_books()
            except sqlite3.IntegrityError: messagebox.showerror("Error","Book ID exists!")
            finally: conn.close()
        btn(d, "Add Book", save, w=160, h=42).pack(pady=15)

    def _issue_tab(self, p):
        fr = ctk.CTkFrame(p, fg_color=COLORS["white"], corner_radius=10,
                          border_width=1, border_color=COLORS["border"])
        fr.pack(fill="x", padx=20, pady=10)
        label(fr, "Issue Book", 14, bold=True).grid(row=0,column=0,columnspan=4,sticky="w",padx=15,pady=(12,5))

        ctk.CTkLabel(fr, text="Student ID:", font=("Arial",12), text_color=COLORS["muted"]).grid(row=1,column=0,padx=10,pady=8,sticky="w")
        self.is_sid = entry(fr, width=160); self.is_sid.grid(row=1,column=1,padx=8,pady=8)
        ctk.CTkLabel(fr, text="Book ID:", font=("Arial",12), text_color=COLORS["muted"]).grid(row=1,column=2,padx=10,pady=8,sticky="w")
        self.is_bid = entry(fr, width=160); self.is_bid.grid(row=1,column=3,padx=8,pady=8)
        btn(fr, "Issue Book", self.issue_book, color=COLORS["accent"], w=130).grid(row=2,column=0,columnspan=2,padx=15,pady=8,sticky="w")
        btn(fr, "Return Book", self.return_dialog, color=COLORS["success"], w=130).grid(row=2,column=2,columnspan=2,padx=15,pady=8,sticky="w")

        label(p, "Issued Books", 14, bold=True).pack(anchor="w", padx=20, pady=(10,4))
        tf, self.itree = make_scrolled_tree(p,
            ("Issue ID","Book ID","Title","Student ID","Issue Date","Due Date","Status"),
            [70,90,200,100,110,110,80])
        tf.pack(fill="both", expand=True, padx=20, pady=6)
        self.load_issues()

    def issue_book(self):
        sid = self.is_sid.get().strip(); bid = self.is_bid.get().strip()
        if not sid or not bid: messagebox.showerror("Error","Student ID and Book ID required!"); return
        conn = get_connection()
        book = conn.execute("SELECT available_copies FROM library_books WHERE book_id=?", (bid,)).fetchone()
        if not book: messagebox.showerror("Error","Book not found!"); conn.close(); return
        if book[0] <= 0: messagebox.showerror("Error","No copies available!"); conn.close(); return
        from datetime import timedelta
        due = (date.today() + timedelta(days=14)).isoformat()
        conn.execute("INSERT INTO library_issues (book_id,student_id,issue_date,due_date,status) VALUES (?,?,?,?,'Issued')",
                     (bid,sid,date.today().isoformat(),due))
        conn.execute("UPDATE library_books SET available_copies=available_copies-1 WHERE book_id=?", (bid,))
        conn.commit(); conn.close()
        messagebox.showinfo("Success",f"Book issued! Due date: {due}")
        self.load_issues(); self.load_books()

    def return_dialog(self):
        d = ctk.CTkToplevel(self); d.title("Return Book"); d.geometry("380x220"); d.grab_set()
        label(d, "Return Book", 16, bold=True).pack(pady=15)
        fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(padx=30)
        label(fr, "Issue ID:").pack(anchor="w")
        iid_e = entry(fr, width=260); iid_e.pack(pady=5)
        def ret():
            try: iid = int(iid_e.get())
            except: messagebox.showerror("Error","Invalid Issue ID"); return
            conn = get_connection()
            issue = conn.execute("SELECT book_id,status FROM library_issues WHERE id=?", (iid,)).fetchone()
            if not issue: messagebox.showerror("Error","Issue not found!"); conn.close(); return
            if issue[1] == "Returned": messagebox.showinfo("Info","Already returned!"); conn.close(); return
            conn.execute("UPDATE library_issues SET return_date=?,status='Returned' WHERE id=?",
                         (date.today().isoformat(), iid))
            conn.execute("UPDATE library_books SET available_copies=available_copies+1 WHERE book_id=?", (issue[0],))
            conn.commit(); conn.close()
            messagebox.showinfo("Success","Book returned!"); d.destroy()
            self.load_issues(); self.load_books()
        btn(d, "Return", ret, w=160, h=40).pack(pady=15)

    def load_issues(self):
        for r in self.itree.get_children(): self.itree.delete(r)
        conn = get_connection()
        rows = conn.execute("""SELECT li.id,li.book_id,lb.title,li.student_id,li.issue_date,li.due_date,li.status
            FROM library_issues li LEFT JOIN library_books lb ON li.book_id=lb.book_id
            WHERE li.status='Issued' ORDER BY li.id DESC""").fetchall()
        conn.close()
        for r in rows: self.itree.insert("","end", values=tuple(r))

# ─── SETTINGS ────────────────────────────────────────────────────────────────

class SettingsModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.build()

    def build(self):
        label(self, "Settings", 22, bold=True).pack(anchor="w", padx=25, pady=(20,10))

        # Password card
        c1 = ctk.CTkFrame(self, fg_color=COLORS["white"], corner_radius=12,
                          border_width=1, border_color=COLORS["border"])
        c1.pack(fill="x", padx=25, pady=8)
        label(c1, "Change Password", 15, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        self.npw = entry(c1, "New Password", 280); self.npw.pack(anchor="w", padx=20, pady=5)
        def ch_pw():
            pw = self.npw.get().strip()
            if not pw: messagebox.showerror("Error","Enter new password!"); return
            conn = get_connection()
            conn.execute("UPDATE users SET password=? WHERE username='admin'", (pw,))
            conn.commit(); conn.close()
            messagebox.showinfo("Success","Password updated!")
        btn(c1, "Update Password", ch_pw, color=COLORS["accent"], w=180).pack(anchor="w", padx=20, pady=(5,15))

        # Theme card
        c2 = ctk.CTkFrame(self, fg_color=COLORS["white"], corner_radius=12,
                          border_width=1, border_color=COLORS["border"])
        c2.pack(fill="x", padx=25, pady=8)
        label(c2, "Appearance", 15, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        tv = ctk.StringVar(value="Light")
        for t in ["Light","Dark","System"]:
            ctk.CTkRadioButton(c2, text=t, variable=tv, value=t,
                               command=lambda v=t: ctk.set_appearance_mode(v.lower()),
                               fg_color=COLORS["primary"]).pack(anchor="w", padx=30, pady=4)
        ctk.CTkLabel(c2, text="").pack()

        # About card
        c3 = ctk.CTkFrame(self, fg_color=COLORS["white"], corner_radius=12,
                          border_width=1, border_color=COLORS["border"])
        c3.pack(fill="x", padx=25, pady=8)
        label(c3, "About", 15, bold=True).pack(anchor="w", padx=20, pady=(15,5))
        label(c3, "School ERP System v2.0", 13).pack(anchor="w", padx=20, pady=2)
        label(c3, "Built with Python + CustomTkinter + SQLite", 12, color=COLORS["muted"]).pack(anchor="w", padx=20, pady=2)
        label(c3, "All data stored locally — no internet required.", 12, color=COLORS["muted"]).pack(anchor="w", padx=20, pady=(2,15))

# ─── LOGIN ───────────────────────────────────────────────────────────────────

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("School ERP — Login")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color="#0F2D25")
        self._build()
        self._center()

    def _center(self):
        self.update_idletasks()
        w,h = self.winfo_width(), self.winfo_height()
        sw,sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        ctk.CTkLabel(self, text="🏫", font=("Arial",64)).pack(pady=(50,5))
        ctk.CTkLabel(self, text="School ERP System",
                     font=("Georgia",22,"bold"), text_color="#E1F5EE").pack()
        ctk.CTkLabel(self, text="Complete School Management v2.0",
                     font=("Arial",13), text_color="#5DCAA5").pack(pady=(2,20))

        card = ctk.CTkFrame(self, fg_color="#1a3d2f", corner_radius=16,
                            border_width=1, border_color="#1D9E75")
        card.pack(padx=40, fill="x")
        ctk.CTkLabel(card, text="Login to Continue", font=("Arial",15,"bold"),
                     text_color="#9FE1CB").pack(pady=(20,12))

        self.uname = ctk.CTkEntry(card, placeholder_text="Username", width=300, height=44,
                                   font=("Arial",14), fg_color="#0F2D25",
                                   border_color="#1D9E75", text_color="white",
                                   placeholder_text_color="#5DCAA5")
        self.uname.pack(pady=4); self.uname.insert(0,"admin")

        self.pwd = ctk.CTkEntry(card, placeholder_text="Password", show="*",
                                 width=300, height=44, font=("Arial",14),
                                 fg_color="#0F2D25", border_color="#1D9E75",
                                 text_color="white", placeholder_text_color="#5DCAA5")
        self.pwd.pack(pady=4); self.pwd.insert(0,"admin123")

        self.err = ctk.CTkLabel(card, text="", font=("Arial",12), text_color="#ff6b6b")
        self.err.pack(pady=2)

        ctk.CTkButton(card, text="Login →", width=300, height=44,
                      fg_color="#1D9E75", hover_color="#085041",
                      font=("Arial",15,"bold"), command=self._login).pack(pady=(4,20))
        self.pwd.bind("<Return>", lambda _: self._login())

        ctk.CTkLabel(self, text="Default: admin / admin123",
                     font=("Arial",11), text_color="#5DCAA5").pack(pady=8)

    def _login(self):
        conn = get_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                            (self.uname.get().strip(), self.pwd.get().strip())).fetchone()
        conn.close()
        if user:
            self.destroy()
            MainApp().mainloop()
        else:
            self.err.configure(text="❌ Invalid username or password!")

# ─── MAIN APP ────────────────────────────────────────────────────────────────

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("School ERP System v2.0")
        self.geometry("1300x800")
        self.minsize(1100,680)
        self.configure(fg_color=COLORS["content"])
        self.current_page = None
        self.nav_btns = {}
        self._build()
        self.show("Dashboard")
        self._center()

    def _center(self):
        self.update_idletasks()
        w,h = self.winfo_width(), self.winfo_height()
        sw,sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        # Sidebar
        sb = ctk.CTkFrame(self, width=225, fg_color=COLORS["sidebar"], corner_radius=0)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)

        logo = ctk.CTkFrame(sb, fg_color="#0a1f18", corner_radius=0, height=90)
        logo.pack(fill="x"); logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="🏫  School ERP",
                     font=("Georgia",18,"bold"), text_color="#E1F5EE").pack(expand=True)

        nav = ctk.CTkScrollableFrame(sb, fg_color="transparent",
                                      scrollbar_button_color=COLORS["sidebar"])
        nav.pack(fill="both", expand=True, pady=8)

        for icon, label_text in MENU_ITEMS:
            b = ctk.CTkButton(nav, text=f"  {icon}  {label_text}", width=205, height=44,
                              anchor="w", fg_color="transparent",
                              hover_color=COLORS["sidebar_hover"],
                              text_color=COLORS["sidebar_text"],
                              font=("Arial",13), corner_radius=8,
                              command=lambda l=label_text: self.show(l))
            b.pack(pady=2, padx=8)
            self.nav_btns[label_text] = b

        ctk.CTkButton(sb, text="🚪  Logout", width=205, height=40,
                      fg_color="#1a3d2f", hover_color=COLORS["danger"],
                      text_color="#9FE1CB", font=("Arial",13),
                      command=self._logout).pack(side="bottom", pady=12, padx=8)

        # Header
        hdr = ctk.CTkFrame(self, height=56, fg_color=COLORS["header"], corner_radius=0)
        hdr.pack(fill="x", side="top"); hdr.pack_propagate(False)
        self.hdr_lbl = ctk.CTkLabel(hdr, text="Dashboard",
                                     font=("Georgia",17,"bold"), text_color="#E1F5EE")
        self.hdr_lbl.pack(side="left", padx=25)
        ctk.CTkLabel(hdr, text="School Management System v2.0",
                     font=("Arial",12), text_color="#5DCAA5").pack(side="right", padx=20)

        # Content
        self.cf = ctk.CTkFrame(self, fg_color=COLORS["content"], corner_radius=0)
        self.cf.pack(fill="both", expand=True)

    def show(self, page):
        if self.current_page:
            self.current_page.pack_forget()
        for name, b in self.nav_btns.items():
            b.configure(fg_color="transparent", text_color=COLORS["sidebar_text"])
        if page in self.nav_btns:
            self.nav_btns[page].configure(fg_color=COLORS["sidebar_active"],
                                          text_color=COLORS["sidebar_active_text"])
        self.hdr_lbl.configure(text=page)
        pages = {
            "Dashboard":     DashboardModule,
            "Students":      StudentsModule,
            "Teachers":      TeachersModule,
            "Attendance":    AttendanceModule,
            "Fees":          FeesModule,
            "Accounting":    AccountingModule, # NEW
            "Inventory":     InventoryModule,  # NEW
            "Exams & Results": ExamsModule,
            "Assignments":   AssignmentsModule,
            "Notices":       NoticesModule,
            "Library":       LibraryModule,
            "Settings":      SettingsModule,
        }
        cls = pages.get(page)
        if cls:
            p = cls(self.cf)
            p.pack(fill="both", expand=True)
            self.current_page = p

    def _logout(self):
        if messagebox.askyesno("Logout","Are you sure you want to logout?"):
            self.destroy(); LoginWindow().mainloop()

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
    initialize_database()
    LoginWindow().mainloop()