import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime


# ====================== DATABASE SETUP ======================
def init_db():
    conn = sqlite3.connect('shop_erp.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    buy_price REAL DEFAULT 0,
                    sell_price REAL DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    alert_qty INTEGER DEFAULT 10)''')

    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT,
                    due REAL DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    customer_id INTEGER,
                    customer_name TEXT,
                    total REAL,
                    discount REAL DEFAULT 0,
                    final_total REAL,
                    paid REAL DEFAULT 0,
                    due REAL DEFAULT 0,
                    items TEXT,
                    FOREIGN KEY(customer_id) REFERENCES customers(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS stock_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    product_id INTEGER,
                    product_name TEXT,
                    type TEXT,
                    qty INTEGER,
                    note TEXT,
                    FOREIGN KEY(product_id) REFERENCES products(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    category TEXT,
                    description TEXT,
                    amount REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS due_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    customer_id INTEGER,
                    customer_name TEXT,
                    amount REAL,
                    note TEXT,
                    FOREIGN KEY(customer_id) REFERENCES customers(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT,
                    due REAL DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    supplier_id INTEGER,
                    supplier_name TEXT,
                    total REAL,
                    paid REAL DEFAULT 0,
                    due REAL DEFAULT 0,
                    items TEXT,
                    FOREIGN KEY(supplier_id) REFERENCES suppliers(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS warranties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    sale_date TEXT,
                    customer_name TEXT,
                    customer_phone TEXT,
                    product_name TEXT,
                    serial_no TEXT,
                    warranty_months INTEGER DEFAULT 12,
                    expiry_date TEXT,
                    note TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    type TEXT,
                    customer_name TEXT,
                    product_name TEXT,
                    qty INTEGER,
                    price REAL,
                    refund REAL,
                    reason TEXT,
                    note TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'staff')''')

    # Default admin user
    c.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
              ("admin", "admin123", "admin"))

    conn.commit()
    conn.close()


# ====================== INVOICE WINDOW ======================
def show_invoice(sale_id):
    conn = sqlite3.connect('shop_erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sales WHERE id=?", (sale_id,))
    sale = c.fetchone()
    conn.close()

    if not sale:
        return

    win = tk.Toplevel()
    win.title(f"Invoice #{sale[0]}")
    win.geometry("500x600")
    win.configure(bg="white")

    tk.Label(win, text="SHOP MANAGEMENT ERP", font=("Arial", 16, "bold"), bg="white").pack(pady=5)
    tk.Label(win, text="Md. Hasibul", font=("Arial", 11), bg="white").pack()
    tk.Label(win, text="-" * 60, bg="white").pack()

    tk.Label(win, text=f"Invoice No : #{sale[0]}", font=("Arial", 10), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text=f"Date       : {sale[1]}", font=("Arial", 10), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text=f"Customer   : {sale[3]}", font=("Arial", 10), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text="-" * 60, bg="white").pack()

    tk.Label(win, text="Items Purchased:", font=("Arial", 10, "bold"), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    for item in sale[9].split("|"):
        if item.strip():
            tk.Label(win, text=f"  • {item.strip()}", font=("Arial", 10), bg="white", anchor="w").pack(fill=tk.X, padx=20)

    tk.Label(win, text="-" * 60, bg="white").pack()
    tk.Label(win, text=f"Sub Total  : {sale[4]:.2f} Tk", font=("Arial", 10), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text=f"Discount   : {sale[5]:.2f} Tk", font=("Arial", 10), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text=f"Total      : {sale[6]:.2f} Tk", font=("Arial", 12, "bold"), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text=f"Paid       : {sale[7]:.2f} Tk", font=("Arial", 10), bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text=f"Due        : {sale[8]:.2f} Tk", font=("Arial", 10, "bold"), fg="red" if sale[8] > 0 else "green", bg="white", anchor="w").pack(fill=tk.X, padx=20)
    tk.Label(win, text="-" * 60, bg="white").pack()
    tk.Label(win, text="Thank You for Shopping!", font=("Arial", 11, "italic"), bg="white").pack(pady=10)

    tk.Button(win, text="Close", command=win.destroy, bg="#f44336", fg="white", width=15).pack(pady=10)


# ====================== MAIN APPLICATION ======================
class ShopERP:
    def __init__(self, root, logged_user="admin", logged_role="admin"):
        self.root = root
        self.logged_user = logged_user
        self.logged_role = logged_role
        self.root.title(f"Shop Management ERP - Md. Hasibul  |  User: {logged_user} ({logged_role})")
        self.root.geometry("1280x780")
        self.root.configure(bg="#f0f0f0")

        init_db()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=[10, 5], font=("Arial", 9, "bold"))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.dashboard_tab  = ttk.Frame(self.notebook)
        self.product_tab    = ttk.Frame(self.notebook)
        self.stock_tab      = ttk.Frame(self.notebook)
        self.customer_tab   = ttk.Frame(self.notebook)
        self.sales_tab      = ttk.Frame(self.notebook)
        self.history_tab    = ttk.Frame(self.notebook)
        self.expense_tab    = ttk.Frame(self.notebook)
        self.due_tab        = ttk.Frame(self.notebook)
        self.report_tab     = ttk.Frame(self.notebook)
        self.supplier_tab   = ttk.Frame(self.notebook)
        self.purchase_tab   = ttk.Frame(self.notebook)
        self.warranty_tab   = ttk.Frame(self.notebook)
        self.return_tab     = ttk.Frame(self.notebook)
        self.user_tab       = ttk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab,  text=" Dashboard ")
        self.notebook.add(self.product_tab,    text=" Products ")
        self.notebook.add(self.stock_tab,      text=" Stock In/Out ")
        self.notebook.add(self.supplier_tab,   text=" Suppliers ")
        self.notebook.add(self.purchase_tab,   text=" Purchases ")
        self.notebook.add(self.customer_tab,   text=" Customers ")
        self.notebook.add(self.sales_tab,      text=" Sales/Billing ")
        self.notebook.add(self.history_tab,    text=" Sales History ")
        self.notebook.add(self.warranty_tab,   text=" Warranty ")
        self.notebook.add(self.return_tab,     text=" Returns ")
        self.notebook.add(self.expense_tab,    text=" Expenses ")
        self.notebook.add(self.due_tab,        text=" Due Payments ")
        self.notebook.add(self.report_tab,     text=" Reports ")
        if logged_role == "admin":
            self.notebook.add(self.user_tab,   text=" Users ")

        self.create_dashboard()
        self.create_product_tab()
        self.create_stock_tab()
        self.create_supplier_tab()
        self.create_purchase_tab()
        self.create_customer_tab()
        self.create_sales_tab()
        self.create_history_tab()
        self.create_warranty_tab()
        self.create_return_tab()
        self.create_expense_tab()
        self.create_due_tab()
        self.create_report_tab()
        if logged_role == "admin":
            self.create_user_tab()

    # ======================== DASHBOARD ========================
    def create_dashboard(self):
        tk.Label(self.dashboard_tab, text="Dashboard", font=("Arial", 20, "bold"), bg="#f0f0f0").pack(pady=10)

        card_frame = tk.Frame(self.dashboard_tab, bg="#f0f0f0")
        card_frame.pack(pady=10, fill=tk.X, padx=20)

        self.dash_today_sales     = self._dash_card(card_frame, "Today's Sales",    "0.00 Tk", "#4CAF50", 0)
        self.dash_today_profit    = self._dash_card(card_frame, "Today's Profit",   "0.00 Tk", "#2196F3", 1)
        self.dash_today_expense   = self._dash_card(card_frame, "Today's Expense",  "0.00 Tk", "#FF5722", 2)
        self.dash_total_due       = self._dash_card(card_frame, "Total Due",        "0.00 Tk", "#f44336", 3)
        self.dash_total_products  = self._dash_card(card_frame, "Total Products",   "0",       "#FF9800", 4)
        self.dash_total_customers = self._dash_card(card_frame, "Total Customers",  "0",       "#9C27B0", 5)

        tk.Label(self.dashboard_tab, text="Low Stock Items", font=("Arial", 14, "bold")).pack(pady=(15, 5))

        self.low_stock_tree = ttk.Treeview(self.dashboard_tab, columns=("ID", "Name", "Stock", "Alert"), show="headings", height=10)
        for col, w in zip(("ID", "Name", "Stock", "Alert"), (60, 300, 100, 100)):
            self.low_stock_tree.heading(col, text=col)
            self.low_stock_tree.column(col, width=w)
        self.low_stock_tree.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        self.low_stock_tree.tag_configure("danger", foreground="red")

        tk.Button(self.dashboard_tab, text="Refresh Dashboard", command=self.refresh_dashboard,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5).pack(pady=10)

        self.refresh_dashboard()

    def _dash_card(self, parent, title, value, color, col):
        frame = tk.Frame(parent, bg=color, padx=20, pady=15)
        frame.grid(row=0, column=col, padx=10, pady=5, sticky="ew")
        parent.columnconfigure(col, weight=1)
        tk.Label(frame, text=title, font=("Arial", 10), bg=color, fg="white").pack()
        lbl = tk.Label(frame, text=value, font=("Arial", 16, "bold"), bg=color, fg="white")
        lbl.pack()
        return lbl

    def refresh_dashboard(self):
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()

        today = datetime.date.today().isoformat()

        c.execute("SELECT SUM(final_total) FROM sales WHERE date=?", (today,))
        sales_total = c.fetchone()[0] or 0.0
        self.dash_today_sales.config(text=f"{sales_total:.2f} Tk")

        # Profit calculation from today's sales
        c.execute("SELECT items FROM sales WHERE date=?", (today,))
        rows = c.fetchall()
        profit = 0.0
        for row in rows:
            for item in row[0].split("|"):
                parts = item.strip().split("||")
                if len(parts) == 4:
                    try:
                        qty = int(parts[1])
                        sell = float(parts[2])
                        buy = float(parts[3])
                        profit += (sell - buy) * qty
                    except:
                        pass
        self.dash_today_profit.config(text=f"{profit:.2f} Tk")

        c.execute("SELECT SUM(amount) FROM expenses WHERE date=?", (today,))
        exp_total = c.fetchone()[0] or 0.0
        self.dash_today_expense.config(text=f"{exp_total:.2f} Tk")

        c.execute("SELECT SUM(due) FROM customers")
        total_due = c.fetchone()[0] or 0.0
        self.dash_total_due.config(text=f"{total_due:.2f} Tk")

        c.execute("SELECT COUNT(*) FROM products")
        self.dash_total_products.config(text=str(c.fetchone()[0]))

        c.execute("SELECT COUNT(*) FROM customers")
        self.dash_total_customers.config(text=str(c.fetchone()[0]))

        for item in self.low_stock_tree.get_children():
            self.low_stock_tree.delete(item)
        c.execute("SELECT id, name, stock, alert_qty FROM products WHERE stock <= alert_qty ORDER BY stock")
        for row in c.fetchall():
            self.low_stock_tree.insert("", "end", values=row, tags=("danger",))

        conn.close()

    # ======================== PRODUCT TAB ========================
    def create_product_tab(self):
        left = tk.Frame(self.product_tab, padx=20, pady=20)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Product Management", font=("Arial", 15, "bold")).pack(pady=10)

        fields = [("Product Name:", "p_name"), ("Category:", "p_category"),
                  ("Buy Price:", "p_buy"), ("Sell Price:", "p_sell"),
                  ("Stock:", "p_stock"), ("Alert Qty:", "p_alert")]
        for lbl, attr in fields:
            tk.Label(left, text=lbl, anchor="w").pack(fill=tk.X)
            entry = tk.Entry(left, width=30)
            entry.pack(pady=3)
            setattr(self, attr, entry)

        btn_frame = tk.Frame(left)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Add",    command=self.add_product,    bg="#4CAF50", fg="white", width=10).grid(row=0, column=0, padx=3, pady=3)
        tk.Button(btn_frame, text="Update", command=self.update_product, bg="#2196F3", fg="white", width=10).grid(row=0, column=1, padx=3, pady=3)
        tk.Button(btn_frame, text="Delete", command=self.delete_product, bg="#f44336", fg="white", width=10).grid(row=0, column=2, padx=3, pady=3)
        tk.Button(btn_frame, text="Clear",  command=self.clear_product_form, bg="#9E9E9E", fg="white", width=10).grid(row=1, column=1, padx=3, pady=3)

        right = tk.Frame(self.product_tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right, text="Product List", font=("Arial", 13, "bold")).pack()

        cols = ("ID", "Name", "Category", "Buy Price", "Sell Price", "Stock", "Alert Qty")
        self.product_tree = ttk.Treeview(right, columns=cols, show="headings", height=22)
        for col in cols:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=100)
        self.product_tree.column("Name", width=180)

        sb = ttk.Scrollbar(right, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=sb.set)
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.product_tree.bind("<<TreeviewSelect>>", self.load_product_to_form)
        self.product_tree.tag_configure("low", foreground="red")

        tk.Button(right, text="Refresh List", command=self.load_products, bg="#607D8B", fg="white").pack(pady=5)
        self.load_products()

    def add_product(self):
        name = self.p_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Product name required!")
            return
        try:
            conn = sqlite3.connect('shop_erp.db')
            c = conn.cursor()
            c.execute("INSERT INTO products (name,category,buy_price,sell_price,stock,alert_qty) VALUES(?,?,?,?,?,?)",
                      (name, self.p_category.get(), float(self.p_buy.get() or 0),
                       float(self.p_sell.get() or 0), int(self.p_stock.get() or 0), int(self.p_alert.get() or 10)))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Product Added!")
            self.load_products()
            self.clear_product_form()
            self.load_stock_products()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_products(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id,name,category,buy_price,sell_price,stock,alert_qty FROM products ORDER BY name")
        for row in c.fetchall():
            tag = ("low",) if row[5] <= row[6] else ()
            self.product_tree.insert("", "end", values=row, tags=tag)
        conn.close()

    def load_product_to_form(self, event):
        sel = self.product_tree.selection()
        if not sel:
            return
        v = self.product_tree.item(sel[0])['values']
        for entry, val in zip([self.p_name, self.p_category, self.p_buy, self.p_sell, self.p_stock, self.p_alert], v[1:]):
            entry.delete(0, tk.END)
            entry.insert(0, val)

    def update_product(self):
        sel = self.product_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a product!")
            return
        pid = self.product_tree.item(sel[0])['values'][0]
        try:
            conn = sqlite3.connect('shop_erp.db')
            c = conn.cursor()
            c.execute("UPDATE products SET name=?,category=?,buy_price=?,sell_price=?,stock=?,alert_qty=? WHERE id=?",
                      (self.p_name.get(), self.p_category.get(), float(self.p_buy.get() or 0),
                       float(self.p_sell.get() or 0), int(self.p_stock.get() or 0), int(self.p_alert.get() or 10), pid))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Product Updated!")
            self.load_products()
            self.load_stock_products()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_product(self):
        sel = self.product_tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete this product?"):
            pid = self.product_tree.item(sel[0])['values'][0]
            conn = sqlite3.connect('shop_erp.db')
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            self.load_products()
            self.clear_product_form()

    def clear_product_form(self):
        for e in [self.p_name, self.p_category, self.p_buy, self.p_sell, self.p_stock, self.p_alert]:
            e.delete(0, tk.END)

    # ======================== STOCK IN / OUT TAB ========================
    def create_stock_tab(self):
        top = tk.Frame(self.stock_tab, padx=20, pady=15)
        top.pack(fill=tk.X)

        tk.Label(top, text="Stock In / Out Management", font=("Arial", 15, "bold")).grid(row=0, column=0, columnspan=6, pady=10)

        tk.Label(top, text="Product:").grid(row=1, column=0, sticky="w", padx=5)
        self.stock_product_var = tk.StringVar()
        self.stock_product_cb = ttk.Combobox(top, textvariable=self.stock_product_var, width=30, state="readonly")
        self.stock_product_cb.grid(row=1, column=1, padx=5)

        tk.Label(top, text="Qty:").grid(row=1, column=2, sticky="w", padx=5)
        self.stock_qty = tk.Entry(top, width=10)
        self.stock_qty.grid(row=1, column=3, padx=5)

        tk.Label(top, text="Note:").grid(row=1, column=4, sticky="w", padx=5)
        self.stock_note = tk.Entry(top, width=25)
        self.stock_note.grid(row=1, column=5, padx=5)

        btn_frame = tk.Frame(self.stock_tab)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Stock IN (+)", command=self.stock_in, bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold"), padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Stock OUT (-)", command=self.stock_out, bg="#f44336", fg="white",
                  font=("Arial", 11, "bold"), padx=20, pady=5).pack(side=tk.LEFT, padx=10)

        tk.Label(self.stock_tab, text="Stock Movement Log", font=("Arial", 13, "bold")).pack(pady=(15, 5))

        cols = ("ID", "Date", "Product", "Type", "Qty", "Note")
        self.stock_log_tree = ttk.Treeview(self.stock_tab, columns=cols, show="headings", height=18)
        widths = (50, 120, 250, 80, 80, 250)
        for col, w in zip(cols, widths):
            self.stock_log_tree.heading(col, text=col)
            self.stock_log_tree.column(col, width=w)
        self.stock_log_tree.tag_configure("in",  foreground="#1B5E20")
        self.stock_log_tree.tag_configure("out", foreground="#B71C1C")

        sb = ttk.Scrollbar(self.stock_tab, orient="vertical", command=self.stock_log_tree.yview)
        self.stock_log_tree.configure(yscrollcommand=sb.set)
        self.stock_log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        sb.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        self.load_stock_products()
        self.load_stock_log()

    def load_stock_products(self):
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id, name, stock FROM products ORDER BY name")
        rows = c.fetchall()
        conn.close()
        self.stock_products = {f"{r[1]} (Stock: {r[2]})": r[0] for r in rows}
        self.stock_product_cb['values'] = list(self.stock_products.keys())

    def stock_in(self):
        self._do_stock("IN")

    def stock_out(self):
        self._do_stock("OUT")

    def _do_stock(self, stype):
        product_label = self.stock_product_var.get()
        if not product_label:
            messagebox.showwarning("Warning", "Select a product!")
            return
        try:
            qty = int(self.stock_qty.get())
            if qty <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Enter valid quantity!")
            return

        pid = self.stock_products[product_label]
        note = self.stock_note.get()
        today = datetime.date.today().isoformat()

        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT name, stock FROM products WHERE id=?", (pid,))
        product = c.fetchone()

        if stype == "OUT" and product[1] < qty:
            messagebox.showerror("Error", f"Not enough stock! Available: {product[1]}")
            conn.close()
            return

        change = qty if stype == "IN" else -qty
        c.execute("UPDATE products SET stock = stock + ? WHERE id=?", (change, pid))
        c.execute("INSERT INTO stock_log (date,product_id,product_name,type,qty,note) VALUES(?,?,?,?,?,?)",
                  (today, pid, product[0], stype, qty, note))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Stock {stype} done! {product[0]}: {'+' if stype=='IN' else '-'}{qty}")
        self.stock_qty.delete(0, tk.END)
        self.stock_note.delete(0, tk.END)
        self.load_stock_products()
        self.load_stock_log()
        self.load_products()
        self.refresh_dashboard()

    def load_stock_log(self):
        for item in self.stock_log_tree.get_children():
            self.stock_log_tree.delete(item)
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id,date,product_name,type,qty,note FROM stock_log ORDER BY id DESC LIMIT 200")
        for row in c.fetchall():
            tag = ("in",) if row[3] == "IN" else ("out",)
            self.stock_log_tree.insert("", "end", values=row, tags=tag)
        conn.close()

    # ======================== CUSTOMER TAB ========================
    def create_customer_tab(self):
        left = tk.Frame(self.customer_tab, padx=20, pady=20)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Customer Management", font=("Arial", 15, "bold")).pack(pady=10)

        for lbl, attr in [("Name:", "c_name"), ("Phone:", "c_phone"), ("Address:", "c_address")]:
            tk.Label(left, text=lbl, anchor="w").pack(fill=tk.X)
            entry = tk.Entry(left, width=28)
            entry.pack(pady=3)
            setattr(self, attr, entry)

        btn_frame = tk.Frame(left)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Add",    command=self.add_customer,    bg="#4CAF50", fg="white", width=10).grid(row=0, column=0, padx=3, pady=3)
        tk.Button(btn_frame, text="Update", command=self.update_customer, bg="#2196F3", fg="white", width=10).grid(row=0, column=1, padx=3, pady=3)
        tk.Button(btn_frame, text="Delete", command=self.delete_customer, bg="#f44336", fg="white", width=10).grid(row=1, column=0, padx=3, pady=3)
        tk.Button(btn_frame, text="Clear",  command=self.clear_customer_form, bg="#9E9E9E", fg="white", width=10).grid(row=1, column=1, padx=3, pady=3)

        tk.Button(left, text="View Customer History", command=self.view_customer_history,
                  bg="#FF9800", fg="white", width=22).pack(pady=5)

        right = tk.Frame(self.customer_tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(right, text="Customer List", font=("Arial", 13, "bold")).pack()

        cols = ("ID", "Name", "Phone", "Address", "Total Due")
        self.customer_tree = ttk.Treeview(right, columns=cols, show="headings", height=22)
        for col, w in zip(cols, (60, 180, 120, 250, 100)):
            self.customer_tree.heading(col, text=col)
            self.customer_tree.column(col, width=w)
        self.customer_tree.tag_configure("due", foreground="red")

        sb = ttk.Scrollbar(right, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=sb.set)
        self.customer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.customer_tree.bind("<<TreeviewSelect>>", self.load_customer_to_form)
        tk.Button(right, text="Refresh", command=self.load_customers, bg="#607D8B", fg="white").pack(pady=5)
        self.load_customers()

    def add_customer(self):
        name = self.c_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Name required!")
            return
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("INSERT INTO customers (name,phone,address) VALUES(?,?,?)",
                  (name, self.c_phone.get(), self.c_address.get()))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Customer Added!")
        self.load_customers()
        self.clear_customer_form()

    def load_customers(self):
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id,name,phone,address,due FROM customers ORDER BY name")
        for row in c.fetchall():
            tag = ("due",) if row[4] and row[4] > 0 else ()
            self.customer_tree.insert("", "end", values=row, tags=tag)
        conn.close()
        self._refresh_customer_combobox()

    def load_customer_to_form(self, event):
        sel = self.customer_tree.selection()
        if not sel:
            return
        v = self.customer_tree.item(sel[0])['values']
        for entry, val in zip([self.c_name, self.c_phone, self.c_address], v[1:4]):
            entry.delete(0, tk.END)
            entry.insert(0, val if val else "")

    def update_customer(self):
        sel = self.customer_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a customer!")
            return
        cid = self.customer_tree.item(sel[0])['values'][0]
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("UPDATE customers SET name=?,phone=?,address=? WHERE id=?",
                  (self.c_name.get(), self.c_phone.get(), self.c_address.get(), cid))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Customer Updated!")
        self.load_customers()

    def delete_customer(self):
        sel = self.customer_tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete this customer?"):
            cid = self.customer_tree.item(sel[0])['values'][0]
            conn = sqlite3.connect('shop_erp.db')
            c = conn.cursor()
            c.execute("DELETE FROM customers WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self.load_customers()
            self.clear_customer_form()

    def clear_customer_form(self):
        for e in [self.c_name, self.c_phone, self.c_address]:
            e.delete(0, tk.END)

    def view_customer_history(self):
        sel = self.customer_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a customer!")
            return
        cid = self.customer_tree.item(sel[0])['values'][0]
        cname = self.customer_tree.item(sel[0])['values'][1]

        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id,date,final_total,paid,due FROM sales WHERE customer_id=? ORDER BY id DESC", (cid,))
        rows = c.fetchall()
        conn.close()

        win = tk.Toplevel()
        win.title(f"Sales History - {cname}")
        win.geometry("600x400")

        tree = ttk.Treeview(win, columns=("Invoice", "Date", "Total", "Paid", "Due"), show="headings", height=15)
        for col, w in zip(("Invoice", "Date", "Total", "Paid", "Due"), (80, 120, 100, 100, 100)):
            tree.heading(col, text=col)
            tree.column(col, width=w)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for row in rows:
            tree.insert("", "end", values=(f"#{row[0]}", row[1], f"{row[2]:.2f} Tk", f"{row[3]:.2f} Tk", f"{row[4]:.2f} Tk"))

        def view_invoice():
            sel2 = tree.selection()
            if sel2:
                inv_id = int(tree.item(sel2[0])['values'][0].replace("#", ""))
                show_invoice(inv_id)

        tk.Button(win, text="View Invoice", command=view_invoice, bg="#4CAF50", fg="white").pack(pady=5)

    def _refresh_customer_combobox(self):
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM customers ORDER BY name")
        rows = c.fetchall()
        conn.close()
        self.customers_dict = {f"{r[1]}": r[0] for r in rows}
        self.customers_dict["Walk-in Customer"] = None
        customer_names = ["Walk-in Customer"] + [r[1] for r in rows]
        if hasattr(self, 'sales_customer_cb'):
            self.sales_customer_cb['values'] = customer_names

    # ======================== SALES / BILLING TAB ========================
    def create_sales_tab(self):
        left = tk.Frame(self.sales_tab, width=450)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="Sales / Billing", font=("Arial", 15, "bold")).pack(pady=10)

        # Customer selection
        cust_frame = tk.Frame(left)
        cust_frame.pack(fill=tk.X, pady=5)
        tk.Label(cust_frame, text="Customer:").pack(side=tk.LEFT)
        self.sales_customer_var = tk.StringVar(value="Walk-in Customer")
        self.sales_customer_cb = ttk.Combobox(cust_frame, textvariable=self.sales_customer_var, width=28, state="readonly")
        self.sales_customer_cb.pack(side=tk.LEFT, padx=5)

        tk.Label(left, text="Search Product:").pack(anchor="w")
        self.search_entry = tk.Entry(left, width=40)
        self.search_entry.pack(pady=3)
        self.search_entry.bind("<KeyRelease>", self.search_product)

        cols = ("ID", "Name", "Price", "Stock")
        self.search_result = ttk.Treeview(left, columns=cols, show="headings", height=7)
        for col, w in zip(cols, (50, 200, 80, 70)):
            self.search_result.heading(col, text=col)
            self.search_result.column(col, width=w)
        self.search_result.pack(pady=5, fill=tk.X)
        self.search_result.bind("<Double-1>", self.add_to_cart)

        tk.Label(left, text="Cart", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 3))

        cols2 = ("ID", "Name", "Qty", "Price", "Total")
        self.cart_tree = ttk.Treeview(left, columns=cols2, show="headings", height=10)
        for col, w in zip(cols2, (50, 170, 60, 80, 80)):
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=w)
        self.cart_tree.pack(fill=tk.BOTH, expand=True)

        btn_row = tk.Frame(left)
        btn_row.pack(pady=5)
        tk.Button(btn_row, text="Remove Item", command=self.remove_from_cart, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text="Clear Cart",  command=self.clear_cart,       bg="#9E9E9E", fg="white").pack(side=tk.LEFT, padx=5)

        # Right: Billing
        right = tk.Frame(self.sales_tab, padx=20)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=20)

        tk.Label(right, text="Billing Summary", font=("Arial", 15, "bold")).pack(pady=10)

        self.total_label = tk.Label(right, text="Total: 0.00 Tk", font=("Arial", 18, "bold"), fg="#2E7D32")
        self.total_label.pack(pady=10)

        # Discount & Paid
        grid = tk.Frame(right)
        grid.pack(pady=5)

        tk.Label(grid, text="Discount (Tk):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.discount_var = tk.StringVar(value="0")
        tk.Entry(grid, textvariable=self.discount_var, width=12).grid(row=0, column=1, padx=5)

        tk.Label(grid, text="Paid Amount (Tk):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.paid_var = tk.StringVar(value="0")
        tk.Entry(grid, textvariable=self.paid_var, width=12).grid(row=1, column=1, padx=5)

        self.final_label = tk.Label(right, text="Final Total: 0.00 Tk", font=("Arial", 14))
        self.final_label.pack(pady=5)
        self.due_label   = tk.Label(right, text="Due: 0.00 Tk", font=("Arial", 13), fg="red")
        self.due_label.pack(pady=5)

        tk.Button(right, text="Calculate", command=self.calculate_bill, bg="#607D8B", fg="white", width=20).pack(pady=5)
        tk.Button(right, text="Complete Sale & Print Invoice", command=self.complete_sale,
                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2).pack(pady=10, fill=tk.X)
        tk.Button(right, text="Reset Sale (Clear All)", command=self.reset_sale,
                  bg="#FF5722", fg="white", font=("Arial", 10, "bold")).pack(pady=5, fill=tk.X)

        self._refresh_customer_combobox()
        self.load_search_results()

    def search_product(self, event=None):
        term = self.search_entry.get()
        for item in self.search_result.get_children():
            self.search_result.delete(item)
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        if term:
            c.execute("SELECT id,name,sell_price,stock FROM products WHERE name LIKE ? LIMIT 20", (f"%{term}%",))
        else:
            c.execute("SELECT id,name,sell_price,stock FROM products LIMIT 30")
        for row in c.fetchall():
            self.search_result.insert("", "end", values=row)
        conn.close()

    def load_search_results(self):
        self.search_product()

    def add_to_cart(self, event=None):
        sel = self.search_result.selection()
        if not sel:
            return
        values = self.search_result.item(sel[0])['values']
        pid, name, price, stock = values
        price = float(price)
        stock = int(stock)

        if stock <= 0:
            messagebox.showwarning("Out of Stock", f"{name} is out of stock!")
            return

        # Check if already in cart
        for child in self.cart_tree.get_children():
            if self.cart_tree.item(child)['values'][0] == pid:
                messagebox.showinfo("Info", "Product already in cart! Remove it first to change qty.")
                return

        qty = simpledialog.askinteger("Quantity", f"Enter quantity for {name}\n(Available: {stock}):", minvalue=1, maxvalue=stock)
        if not qty:
            return

        # Fetch buy price for profit calculation
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT buy_price FROM products WHERE id=?", (pid,))
        buy_price = c.fetchone()[0]
        conn.close()

        total = price * qty
        self.cart_tree.insert("", "end", values=(pid, name, qty, f"{price:.2f}", f"{total:.2f}"),
                              tags=(f"buy:{buy_price}",))
        self.update_total()

    def remove_from_cart(self):
        sel = self.cart_tree.selection()
        if sel:
            self.cart_tree.delete(sel[0])
            self.update_total()

    def clear_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        self.update_total()

    def reset_sale(self):
        """Full reset: cart + customer + discount + paid"""
        self.clear_cart()
        self.sales_customer_var.set("Walk-in Customer")
        self.discount_var.set("0")
        self.paid_var.set("0")
        self.search_entry.delete(0, tk.END)
        self.load_search_results()
        self.total_label.config(text="Total: 0.00 Tk")
        self.final_label.config(text="Final Total: 0.00 Tk")
        self.due_label.config(text="Due: 0.00 Tk", fg="red")

    def update_total(self):
        total = sum(float(self.cart_tree.item(c)['values'][4]) for c in self.cart_tree.get_children())
        self.total_label.config(text=f"Total: {total:.2f} Tk")
        self.calculate_bill()

    def calculate_bill(self):
        total = sum(float(self.cart_tree.item(c)['values'][4]) for c in self.cart_tree.get_children())
        try:
            discount = float(self.discount_var.get() or 0)
            paid     = float(self.paid_var.get() or 0)
        except:
            discount = paid = 0
        final = total - discount
        if final < 0:
            final = 0
        due = final - paid
        self.final_label.config(text=f"Final Total: {final:.2f} Tk")
        self.due_label.config(text=f"Due: {due:.2f} Tk", fg="red" if due > 0 else "green")

    def complete_sale(self):
        if not self.cart_tree.get_children():
            messagebox.showwarning("Empty Cart", "Cart is empty!")
            return

        total = sum(float(self.cart_tree.item(c)['values'][4]) for c in self.cart_tree.get_children())
        try:
            discount = float(self.discount_var.get() or 0)
            paid     = float(self.paid_var.get() or 0)
        except:
            discount = paid = 0

        final = total - discount
        if final < 0:
            final = 0
        due = final - paid

        if not messagebox.askyesno("Confirm Sale", f"Final Total: {final:.2f} Tk\nPaid: {paid:.2f} Tk\nDue: {due:.2f} Tk\n\nComplete Sale?"):
            return

        customer_name = self.sales_customer_var.get()
        customer_id   = self.customers_dict.get(customer_name)

        items_parts = []
        for child in self.cart_tree.get_children():
            v = self.cart_tree.item(child)['values']
            tags = self.cart_tree.item(child)['tags']
            buy_price = 0
            for tag in tags:
                if str(tag).startswith("buy:"):
                    try:
                        buy_price = float(str(tag).split("buy:")[1])
                    except:
                        pass
            # Format: name||qty||sell_price||buy_price
            items_parts.append(f"{v[1]}||{v[2]}||{v[3]}||{buy_price}")

        items_str = "|".join(items_parts)

        try:
            conn = sqlite3.connect('shop_erp.db')
            c = conn.cursor()
            today = datetime.date.today().isoformat()

            c.execute("INSERT INTO sales (date,customer_id,customer_name,total,discount,final_total,paid,due,items) VALUES(?,?,?,?,?,?,?,?,?)",
                      (today, customer_id, customer_name, total, discount, final, paid, due, items_str))
            sale_id = c.lastrowid

            # Update stock
            for child in self.cart_tree.get_children():
                v = self.cart_tree.item(child)['values']
                pid = v[0]
                qty = int(v[2])
                c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, pid))
                pname = v[1]
                c.execute("INSERT INTO stock_log (date,product_id,product_name,type,qty,note) VALUES(?,?,?,?,?,?)",
                          (today, pid, pname, "OUT", qty, f"Sale #{sale_id}"))

            # Update customer due
            if customer_id and due > 0:
                c.execute("UPDATE customers SET due = due + ? WHERE id=?", (due, customer_id))

            conn.commit()
            conn.close()

            self.clear_cart()
            self.refresh_dashboard()
            self.load_products()
            self.load_customers()
            self.load_stock_products()
            self.load_stock_log()
            # Auto reset billing fields
            self.discount_var.set("0")
            self.paid_var.set("0")
            self.sales_customer_var.set("Walk-in Customer")
            self.total_label.config(text="Total: 0.00 Tk")
            self.final_label.config(text="Final Total: 0.00 Tk")
            self.due_label.config(text="Due: 0.00 Tk", fg="red")

            show_invoice(sale_id)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ======================== SALES HISTORY TAB ========================
    def create_history_tab(self):
        tk.Label(self.history_tab, text="Sales History", font=("Arial", 15, "bold")).pack(pady=10)

        filter_frame = tk.Frame(self.history_tab)
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="From:").pack(side=tk.LEFT)
        self.hist_from = tk.Entry(filter_frame, width=12)
        self.hist_from.insert(0, datetime.date.today().replace(day=1).isoformat())
        self.hist_from.pack(side=tk.LEFT, padx=5)
        tk.Label(filter_frame, text="To:").pack(side=tk.LEFT)
        self.hist_to = tk.Entry(filter_frame, width=12)
        self.hist_to.insert(0, datetime.date.today().isoformat())
        self.hist_to.pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Filter", command=self.load_history, bg="#2196F3", fg="white", padx=10).pack(side=tk.LEFT, padx=5)

        cols = ("Invoice", "Date", "Customer", "Total", "Discount", "Final Total", "Paid", "Due")
        self.history_tree = ttk.Treeview(self.history_tab, columns=cols, show="headings", height=20)
        widths = (70, 100, 180, 100, 90, 110, 90, 90)
        for col, w in zip(cols, widths):
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=w)
        self.history_tree.tag_configure("due", foreground="red")

        sb = ttk.Scrollbar(self.history_tab, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=sb.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self.history_tree.bind("<Double-1>", lambda e: self._open_invoice_from_history())

        summary_frame = tk.Frame(self.history_tab, padx=20)
        summary_frame.pack(side=tk.RIGHT, fill=tk.Y, pady=20)
        tk.Label(summary_frame, text="Summary", font=("Arial", 13, "bold")).pack()
        self.hist_total_lbl  = tk.Label(summary_frame, text="Total Revenue: 0.00 Tk", font=("Arial", 11))
        self.hist_total_lbl.pack(pady=5)
        self.hist_profit_lbl = tk.Label(summary_frame, text="Total Profit: 0.00 Tk",  font=("Arial", 11), fg="#2E7D32")
        self.hist_profit_lbl.pack(pady=5)
        self.hist_due_lbl    = tk.Label(summary_frame, text="Total Due: 0.00 Tk",     font=("Arial", 11), fg="red")
        self.hist_due_lbl.pack(pady=5)
        tk.Label(summary_frame, text="\nDouble-click a row\nto view invoice", fg="gray", font=("Arial", 9)).pack()

        self.load_history()

    def load_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id,date,customer_name,total,discount,final_total,paid,due,items FROM sales WHERE date BETWEEN ? AND ? ORDER BY id DESC",
                  (self.hist_from.get(), self.hist_to.get()))
        rows = c.fetchall()
        conn.close()

        total_rev = 0
        total_due = 0
        total_profit = 0

        for row in rows:
            tag = ("due",) if row[7] > 0 else ()
            self.history_tree.insert("", "end",
                values=(f"#{row[0]}", row[1], row[2], f"{row[3]:.2f}", f"{row[4]:.2f}",
                        f"{row[5]:.2f}", f"{row[6]:.2f}", f"{row[7]:.2f}"), tags=tag)
            total_rev += row[5]
            total_due += row[7]
            # Calculate profit from items
            for item in row[8].split("|"):
                parts = item.strip().split("||")
                if len(parts) == 4:
                    try:
                        qty = int(parts[1])
                        sell = float(parts[2])
                        buy  = float(parts[3])
                        total_profit += (sell - buy) * qty
                    except:
                        pass

        self.hist_total_lbl.config( text=f"Total Revenue: {total_rev:.2f} Tk")
        self.hist_profit_lbl.config(text=f"Total Profit: {total_profit:.2f} Tk")
        self.hist_due_lbl.config(   text=f"Total Due: {total_due:.2f} Tk")

    def _open_invoice_from_history(self):
        sel = self.history_tree.selection()
        if not sel:
            return
        inv_str = self.history_tree.item(sel[0])['values'][0]
        try:
            inv_id = int(str(inv_str).replace("#", ""))
            show_invoice(inv_id)
        except:
            pass


    # ======================== EXPENSE TAB ========================
    def create_expense_tab(self):
        left = tk.Frame(self.expense_tab, padx=20, pady=20)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Expense Management", font=("Arial", 15, "bold")).pack(pady=10)

        tk.Label(left, text="Category:").pack(anchor="w")
        self.exp_category = ttk.Combobox(left, width=27, state="normal",
            values=["Rent", "Electricity", "Salary", "Purchase", "Transport", "Maintenance", "Other"])
        self.exp_category.pack(pady=3)

        tk.Label(left, text="Description:").pack(anchor="w")
        self.exp_desc = tk.Entry(left, width=30)
        self.exp_desc.pack(pady=3)

        tk.Label(left, text="Amount (Tk):").pack(anchor="w")
        self.exp_amount = tk.Entry(left, width=30)
        self.exp_amount.pack(pady=3)

        tk.Label(left, text="Date (YYYY-MM-DD):").pack(anchor="w")
        self.exp_date = tk.Entry(left, width=30)
        self.exp_date.insert(0, datetime.date.today().isoformat())
        self.exp_date.pack(pady=3)

        btn_frame = tk.Frame(left)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Add Expense", command=self.add_expense,
                  bg="#f44336", fg="white", width=14).grid(row=0, column=0, padx=4)
        tk.Button(btn_frame, text="Delete",      command=self.delete_expense,
                  bg="#9E9E9E", fg="white", width=10).grid(row=0, column=1, padx=4)

        self.exp_summary_lbl = tk.Label(left, text="This Month: 0.00 Tk",
                                        font=("Arial", 12, "bold"), fg="#f44336")
        self.exp_summary_lbl.pack(pady=10)

        right = tk.Frame(self.expense_tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        filter_f = tk.Frame(right)
        filter_f.pack(pady=5)
        tk.Label(filter_f, text="From:").pack(side=tk.LEFT)
        self.exp_from = tk.Entry(filter_f, width=12)
        self.exp_from.insert(0, datetime.date.today().replace(day=1).isoformat())
        self.exp_from.pack(side=tk.LEFT, padx=4)
        tk.Label(filter_f, text="To:").pack(side=tk.LEFT)
        self.exp_to = tk.Entry(filter_f, width=12)
        self.exp_to.insert(0, datetime.date.today().isoformat())
        self.exp_to.pack(side=tk.LEFT, padx=4)
        tk.Button(filter_f, text="Filter", command=self.load_expenses,
                  bg="#2196F3", fg="white", padx=8).pack(side=tk.LEFT, padx=4)

        cols = ("ID", "Date", "Category", "Description", "Amount")
        self.expense_tree = ttk.Treeview(right, columns=cols, show="headings", height=22)
        for col, w in zip(cols, (50, 110, 130, 280, 110)):
            self.expense_tree.heading(col, text=col)
            self.expense_tree.column(col, width=w)

        sb = ttk.Scrollbar(right, orient="vertical", command=self.expense_tree.yview)
        self.expense_tree.configure(yscrollcommand=sb.set)
        self.expense_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_expenses()

    def add_expense(self):
        cat    = self.exp_category.get().strip()
        desc   = self.exp_desc.get().strip()
        date   = self.exp_date.get().strip()
        try:
            amount = float(self.exp_amount.get())
            if amount <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Valid amount required!")
            return
        if not cat:
            messagebox.showerror("Error", "Category required!")
            return

        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("INSERT INTO expenses (date,category,description,amount) VALUES(?,?,?,?)",
                  (date, cat, desc, amount))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Expense of {amount:.2f} Tk added!")
        self.exp_amount.delete(0, tk.END)
        self.exp_desc.delete(0, tk.END)
        self.load_expenses()
        self.refresh_dashboard()

    def delete_expense(self):
        sel = self.expense_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an expense to delete!")
            return
        if messagebox.askyesno("Confirm", "Delete this expense?"):
            eid = self.expense_tree.item(sel[0])['values'][0]
            conn = sqlite3.connect('shop_erp.db')
            c = conn.cursor()
            c.execute("DELETE FROM expenses WHERE id=?", (eid,))
            conn.commit()
            conn.close()
            self.load_expenses()
            self.refresh_dashboard()

    def load_expenses(self):
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id,date,category,description,amount FROM expenses WHERE date BETWEEN ? AND ? ORDER BY id DESC",
                  (self.exp_from.get(), self.exp_to.get()))
        total = 0
        for row in c.fetchall():
            self.expense_tree.insert("", "end", values=(row[0], row[1], row[2], row[3], f"{row[4]:.2f} Tk"))
            total += row[4]
        conn.close()
        self.exp_summary_lbl.config(text=f"Period Total: {total:.2f} Tk")

    # ======================== DUE PAYMENT TAB ========================
    def create_due_tab(self):
        left = tk.Frame(self.due_tab, padx=20, pady=20)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Due Payment Collection", font=("Arial", 15, "bold")).pack(pady=10)

        tk.Label(left, text="Select Customer:").pack(anchor="w")
        self.due_customer_var = tk.StringVar()
        self.due_customer_cb = ttk.Combobox(left, textvariable=self.due_customer_var, width=28, state="readonly")
        self.due_customer_cb.pack(pady=5)
        self.due_customer_cb.bind("<<ComboboxSelected>>", self.show_customer_due)

        self.due_current_lbl = tk.Label(left, text="Current Due: — Tk",
                                        font=("Arial", 12, "bold"), fg="red")
        self.due_current_lbl.pack(pady=5)

        tk.Label(left, text="Payment Amount (Tk):").pack(anchor="w")
        self.due_pay_amount = tk.Entry(left, width=30)
        self.due_pay_amount.pack(pady=3)

        tk.Label(left, text="Note:").pack(anchor="w")
        self.due_note = tk.Entry(left, width=30)
        self.due_note.pack(pady=3)

        tk.Button(left, text="Collect Payment", command=self.collect_due,
                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                  width=22, pady=6).pack(pady=10)
        tk.Button(left, text="Reset Form", command=self.reset_due_form,
                  bg="#9E9E9E", fg="white", width=22).pack(pady=5)

        right = tk.Frame(self.due_tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right, text="Due Payment History", font=("Arial", 13, "bold")).pack()

        cols = ("ID", "Date", "Customer", "Amount Paid", "Note")
        self.due_log_tree = ttk.Treeview(right, columns=cols, show="headings", height=25)
        for col, w in zip(cols, (50, 110, 200, 120, 250)):
            self.due_log_tree.heading(col, text=col)
            self.due_log_tree.column(col, width=w)
        self.due_log_tree.tag_configure("paid", foreground="#1B5E20")

        sb = ttk.Scrollbar(right, orient="vertical", command=self.due_log_tree.yview)
        self.due_log_tree.configure(yscrollcommand=sb.set)
        self.due_log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_due_customers()
        self.load_due_log()

    def _load_due_customers(self):
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id, name, due FROM customers WHERE due > 0 ORDER BY name")
        rows = c.fetchall()
        conn.close()
        self.due_customers = {f"{r[1]} (Due: {r[2]:.2f} Tk)": (r[0], r[2]) for r in rows}
        self.due_customer_cb['values'] = list(self.due_customers.keys())

    def show_customer_due(self, event=None):
        key = self.due_customer_var.get()
        if key in self.due_customers:
            _, due = self.due_customers[key]
            self.due_current_lbl.config(text=f"Current Due: {due:.2f} Tk")

    def collect_due(self):
        key = self.due_customer_var.get()
        if not key:
            messagebox.showwarning("Warning", "Select a customer!")
            return
        cid, current_due = self.due_customers[key]

        try:
            amount = float(self.due_pay_amount.get())
            if amount <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Enter valid amount!")
            return

        if amount > current_due:
            messagebox.showerror("Error", f"Payment ({amount:.2f}) exceeds due ({current_due:.2f})!")
            return

        note  = self.due_note.get()
        today = datetime.date.today().isoformat()

        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT name FROM customers WHERE id=?", (cid,))
        cname = c.fetchone()[0]

        c.execute("UPDATE customers SET due = due - ? WHERE id=?", (amount, cid))
        c.execute("INSERT INTO due_payments (date,customer_id,customer_name,amount,note) VALUES(?,?,?,?,?)",
                  (today, cid, cname, amount, note))
        conn.commit()
        conn.close()

        remaining = current_due - amount
        messagebox.showinfo("Success",
            f"Payment of {amount:.2f} Tk collected from {cname}!\nRemaining Due: {remaining:.2f} Tk")

        self.due_pay_amount.delete(0, tk.END)
        self.due_note.delete(0, tk.END)
        self._load_due_customers()
        self.due_customer_var.set("")
        self.due_current_lbl.config(text="Current Due: — Tk")
        self.load_due_log()
        self.load_customers()
        self.refresh_dashboard()

    def load_due_log(self):
        for item in self.due_log_tree.get_children():
            self.due_log_tree.delete(item)
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id,date,customer_name,amount,note FROM due_payments ORDER BY id DESC LIMIT 200")
        for row in c.fetchall():
            self.due_log_tree.insert("", "end",
                values=(row[0], row[1], row[2], f"{row[3]:.2f} Tk", row[4] or ""),
                tags=("paid",))
        conn.close()

    def reset_due_form(self):
        self.due_customer_var.set("")
        self.due_pay_amount.delete(0, tk.END)
        self.due_note.delete(0, tk.END)
        self.due_current_lbl.config(text="Current Due: — Tk")
        self._load_due_customers()

    # ======================== MONTHLY REPORT TAB ========================
    def create_report_tab(self):
        tk.Label(self.report_tab, text="Monthly Report & Chart", font=("Arial", 15, "bold")).pack(pady=10)

        filter_f = tk.Frame(self.report_tab)
        filter_f.pack(pady=5)
        tk.Label(filter_f, text="Year:").pack(side=tk.LEFT)
        self.report_year = tk.Entry(filter_f, width=6)
        self.report_year.insert(0, str(datetime.date.today().year))
        self.report_year.pack(side=tk.LEFT, padx=4)
        tk.Button(filter_f, text="Generate Report", command=self.generate_report,
                  bg="#4CAF50", fg="white", padx=10).pack(side=tk.LEFT, padx=8)

        # Summary cards row
        self.rpt_card_frame = tk.Frame(self.report_tab)
        self.rpt_card_frame.pack(pady=10, fill=tk.X, padx=20)
        self.rpt_sales_lbl   = self._rpt_card(self.rpt_card_frame, "Annual Sales",   "0.00 Tk", "#4CAF50", 0)
        self.rpt_expense_lbl = self._rpt_card(self.rpt_card_frame, "Annual Expense", "0.00 Tk", "#f44336", 1)
        self.rpt_profit_lbl  = self._rpt_card(self.rpt_card_frame, "Annual Profit",  "0.00 Tk", "#2196F3", 2)
        self.rpt_due_lbl     = self._rpt_card(self.rpt_card_frame, "Total Collected Due", "0.00 Tk", "#FF9800", 3)

        # Chart canvas
        self.chart_canvas = tk.Canvas(self.report_tab, bg="white", height=280)
        self.chart_canvas.pack(fill=tk.X, padx=20, pady=5)

        # Monthly table
        cols = ("Month", "Sales (Tk)", "Expense (Tk)", "Profit (Tk)", "Due Collected (Tk)")
        self.report_tree = ttk.Treeview(self.report_tab, columns=cols, show="headings", height=8)
        for col, w in zip(cols, (100, 150, 150, 150, 170)):
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=w)
        self.report_tree.tag_configure("profit",  foreground="#1B5E20")
        self.report_tree.tag_configure("loss",    foreground="#B71C1C")
        self.report_tree.pack(fill=tk.X, padx=20, pady=5)

        self.generate_report()

    def _rpt_card(self, parent, title, value, color, col):
        frame = tk.Frame(parent, bg=color, padx=15, pady=10)
        frame.grid(row=0, column=col, padx=8, pady=5, sticky="ew")
        parent.columnconfigure(col, weight=1)
        tk.Label(frame, text=title, font=("Arial", 9), bg=color, fg="white").pack()
        lbl = tk.Label(frame, text=value, font=("Arial", 13, "bold"), bg=color, fg="white")
        lbl.pack()
        return lbl

    def generate_report(self):
        year = self.report_year.get().strip()
        if not year.isdigit():
            messagebox.showerror("Error", "Enter valid year!")
            return

        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()

        month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly_sales    = [0.0] * 12
        monthly_expenses = [0.0] * 12
        monthly_profit   = [0.0] * 12
        monthly_due_coll = [0.0] * 12

        # Sales per month
        c.execute("SELECT date, final_total, items FROM sales WHERE date LIKE ?", (f"{year}-%",))
        for row in c.fetchall():
            try:
                m = int(row[0].split("-")[1]) - 1
                monthly_sales[m] += row[1] or 0
                for item in row[2].split("|"):
                    parts = item.strip().split("||")
                    if len(parts) == 4:
                        qty  = int(parts[1])
                        sell = float(parts[2])
                        buy  = float(parts[3])
                        monthly_profit[m] += (sell - buy) * qty
            except:
                pass

        # Expenses per month
        c.execute("SELECT date, amount FROM expenses WHERE date LIKE ?", (f"{year}-%",))
        for row in c.fetchall():
            try:
                m = int(row[0].split("-")[1]) - 1
                monthly_expenses[m] += row[1] or 0
            except:
                pass

        # Due collections per month
        c.execute("SELECT date, amount FROM due_payments WHERE date LIKE ?", (f"{year}-%",))
        for row in c.fetchall():
            try:
                m = int(row[0].split("-")[1]) - 1
                monthly_due_coll[m] += row[1] or 0
            except:
                pass

        conn.close()

        # Update summary cards
        self.rpt_sales_lbl.config(  text=f"{sum(monthly_sales):.2f} Tk")
        self.rpt_expense_lbl.config(text=f"{sum(monthly_expenses):.2f} Tk")
        self.rpt_profit_lbl.config( text=f"{sum(monthly_profit):.2f} Tk")
        self.rpt_due_lbl.config(    text=f"{sum(monthly_due_coll):.2f} Tk")

        # Update table
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        for i in range(12):
            profit = monthly_profit[i]
            tag = ("profit",) if profit >= 0 else ("loss",)
            self.report_tree.insert("", "end", values=(
                month_names[i],
                f"{monthly_sales[i]:.2f}",
                f"{monthly_expenses[i]:.2f}",
                f"{profit:.2f}",
                f"{monthly_due_coll[i]:.2f}"
            ), tags=tag)

        # Draw bar chart
        self._draw_chart(month_names, monthly_sales, monthly_expenses, monthly_profit)

    def _draw_chart(self, labels, sales, expenses, profits):
        canvas = self.chart_canvas
        canvas.delete("all")
        canvas.update_idletasks()

        W = canvas.winfo_width() or 900
        H = 280
        pad_left = 60
        pad_right = 20
        pad_top = 30
        pad_bottom = 50

        chart_w = W - pad_left - pad_right
        chart_h = H - pad_top - pad_bottom
        n = 12

        all_vals = sales + expenses + [abs(p) for p in profits]
        max_val  = max(all_vals) if max(all_vals) > 0 else 1
        bar_group_w = chart_w / n
        bar_w = bar_group_w / 4

        # Y axis grid lines & labels
        for i in range(5):
            y_val = max_val * i / 4
            y_px  = pad_top + chart_h - (chart_h * i / 4)
            canvas.create_line(pad_left, y_px, W - pad_right, y_px, fill="#e0e0e0", dash=(4, 2))
            canvas.create_text(pad_left - 5, y_px, text=f"{y_val/1000:.0f}k" if y_val >= 1000 else f"{y_val:.0f}",
                               anchor="e", font=("Arial", 8), fill="#555")

        # Bars
        colors = {"Sales": "#4CAF50", "Expense": "#f44336", "Profit": "#2196F3"}
        data_sets = [("Sales", sales), ("Expense", expenses), ("Profit", profits)]

        for gi in range(n):
            gx = pad_left + gi * bar_group_w
            for bi, (label, data) in enumerate(data_sets):
                val = data[gi]
                bar_h = abs(val) / max_val * chart_h
                x1 = gx + bi * bar_w + 2
                x2 = x1 + bar_w - 2
                if val >= 0:
                    y1 = pad_top + chart_h - bar_h
                    y2 = pad_top + chart_h
                else:
                    y1 = pad_top + chart_h
                    y2 = pad_top + chart_h + bar_h

                col = colors[label]
                if label == "Profit" and val < 0:
                    col = "#FF5722"
                canvas.create_rectangle(x1, y1, x2, y2, fill=col, outline="")

            # X label
            canvas.create_text(gx + bar_group_w / 2, H - pad_bottom + 12,
                                text=labels[gi], font=("Arial", 8), fill="#333")

        # Legend
        legend_x = pad_left
        for label, color in colors.items():
            canvas.create_rectangle(legend_x, 8, legend_x + 12, 20, fill=color, outline="")
            canvas.create_text(legend_x + 16, 14, text=label, anchor="w", font=("Arial", 9), fill="#333")
            legend_x += 80

        # Axes
        canvas.create_line(pad_left, pad_top, pad_left, pad_top + chart_h, fill="#333", width=2)
        canvas.create_line(pad_left, pad_top + chart_h, W - pad_right, pad_top + chart_h, fill="#333", width=2)


    # ======================== SUPPLIER TAB ========================
    def create_supplier_tab(self):
        left = tk.Frame(self.supplier_tab, padx=20, pady=20)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Supplier Management", font=("Arial", 15, "bold")).pack(pady=10)

        for lbl, attr in [("Name:", "s_name"), ("Phone:", "s_phone"), ("Address:", "s_address")]:
            tk.Label(left, text=lbl, anchor="w").pack(fill=tk.X)
            e = tk.Entry(left, width=28)
            e.pack(pady=3)
            setattr(self, attr, e)

        bf = tk.Frame(left); bf.pack(pady=12)
        tk.Button(bf, text="Add",    command=self.add_supplier,    bg="#4CAF50", fg="white", width=10).grid(row=0, column=0, padx=3)
        tk.Button(bf, text="Update", command=self.update_supplier, bg="#2196F3", fg="white", width=10).grid(row=0, column=1, padx=3)
        tk.Button(bf, text="Delete", command=self.delete_supplier, bg="#f44336", fg="white", width=10).grid(row=1, column=0, padx=3, pady=4)
        tk.Button(bf, text="Clear",  command=self.clear_supplier_form, bg="#9E9E9E", fg="white", width=10).grid(row=1, column=1, padx=3, pady=4)

        right = tk.Frame(self.supplier_tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(right, text="Supplier List", font=("Arial", 13, "bold")).pack()

        cols = ("ID", "Name", "Phone", "Address", "Total Due")
        self.supplier_tree = ttk.Treeview(right, columns=cols, show="headings", height=24)
        for col, w in zip(cols, (50, 180, 120, 280, 110)):
            self.supplier_tree.heading(col, text=col)
            self.supplier_tree.column(col, width=w)
        self.supplier_tree.tag_configure("due", foreground="red")
        sb = ttk.Scrollbar(right, orient="vertical", command=self.supplier_tree.yview)
        self.supplier_tree.configure(yscrollcommand=sb.set)
        self.supplier_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.supplier_tree.bind("<<TreeviewSelect>>", self.load_supplier_to_form)
        tk.Button(right, text="Refresh", command=self.load_suppliers, bg="#607D8B", fg="white").pack(pady=5)
        self.load_suppliers()

    def add_supplier(self):
        name = self.s_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Name required!"); return
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("INSERT INTO suppliers (name,phone,address) VALUES(?,?,?)",
                  (name, self.s_phone.get(), self.s_address.get()))
        conn.commit(); conn.close()
        messagebox.showinfo("Success", "Supplier Added!")
        self.load_suppliers(); self.clear_supplier_form()
        self._refresh_supplier_combobox()

    def load_suppliers(self):
        for i in self.supplier_tree.get_children(): self.supplier_tree.delete(i)
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("SELECT id,name,phone,address,due FROM suppliers ORDER BY name")
        for row in c.fetchall():
            tag = ("due",) if row[4] > 0 else ()
            self.supplier_tree.insert("", "end", values=row, tags=tag)
        conn.close()

    def load_supplier_to_form(self, event):
        sel = self.supplier_tree.selection()
        if not sel: return
        v = self.supplier_tree.item(sel[0])['values']
        for e, val in zip([self.s_name, self.s_phone, self.s_address], v[1:4]):
            e.delete(0, tk.END); e.insert(0, val if val else "")

    def update_supplier(self):
        sel = self.supplier_tree.selection()
        if not sel: messagebox.showwarning("Warning", "Select a supplier!"); return
        sid = self.supplier_tree.item(sel[0])['values'][0]
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("UPDATE suppliers SET name=?,phone=?,address=? WHERE id=?",
                  (self.s_name.get(), self.s_phone.get(), self.s_address.get(), sid))
        conn.commit(); conn.close()
        messagebox.showinfo("Success", "Supplier Updated!"); self.load_suppliers()

    def delete_supplier(self):
        sel = self.supplier_tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirm", "Delete this supplier?"):
            sid = self.supplier_tree.item(sel[0])['values'][0]
            conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
            c.execute("DELETE FROM suppliers WHERE id=?", (sid,))
            conn.commit(); conn.close()
            self.load_suppliers(); self.clear_supplier_form()

    def clear_supplier_form(self):
        for e in [self.s_name, self.s_phone, self.s_address]: e.delete(0, tk.END)

    def _refresh_supplier_combobox(self):
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("SELECT id,name FROM suppliers ORDER BY name")
        rows = c.fetchall(); conn.close()
        self.suppliers_dict = {r[1]: r[0] for r in rows}
        if hasattr(self, 'pur_supplier_cb'):
            self.pur_supplier_cb['values'] = list(self.suppliers_dict.keys())

    # ======================== PURCHASE TAB ========================
    def create_purchase_tab(self):
        left = tk.Frame(self.purchase_tab, padx=15, pady=15, width=420)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        tk.Label(left, text="Purchase Order", font=("Arial", 15, "bold")).pack(pady=8)

        sf = tk.Frame(left); sf.pack(fill=tk.X, pady=4)
        tk.Label(sf, text="Supplier:").pack(side=tk.LEFT)
        self.pur_supplier_var = tk.StringVar()
        self.pur_supplier_cb  = ttk.Combobox(sf, textvariable=self.pur_supplier_var, width=24, state="readonly")
        self.pur_supplier_cb.pack(side=tk.LEFT, padx=5)

        tk.Label(left, text="Search Product:").pack(anchor="w")
        self.pur_search = tk.Entry(left, width=38)
        self.pur_search.pack(pady=3)
        self.pur_search.bind("<KeyRelease>", self.pur_search_product)

        cols = ("ID", "Name", "Buy Price", "Stock")
        self.pur_search_tree = ttk.Treeview(left, columns=cols, show="headings", height=6)
        for col, w in zip(cols, (40, 190, 80, 70)):
            self.pur_search_tree.heading(col, text=col)
            self.pur_search_tree.column(col, width=w)
        self.pur_search_tree.pack(fill=tk.X, pady=4)
        self.pur_search_tree.bind("<Double-1>", self.pur_add_to_cart)

        tk.Label(left, text="Purchase Cart", font=("Arial", 11, "bold")).pack(anchor="w", pady=(8,2))
        cols2 = ("ID", "Name", "Qty", "Buy Price", "Total")
        self.pur_cart = ttk.Treeview(left, columns=cols2, show="headings", height=8)
        for col, w in zip(cols2, (40, 170, 55, 80, 75)):
            self.pur_cart.heading(col, text=col)
            self.pur_cart.column(col, width=w)
        self.pur_cart.pack(fill=tk.BOTH, expand=True)

        br = tk.Frame(left); br.pack(pady=4)
        tk.Button(br, text="Remove", command=self.pur_remove_item, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=4)
        tk.Button(br, text="Clear",  command=self.pur_clear_cart,  bg="#9E9E9E", fg="white").pack(side=tk.LEFT, padx=4)

        right = tk.Frame(self.purchase_tab, padx=20)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=20)

        tk.Label(right, text="Purchase Summary", font=("Arial", 14, "bold")).pack(pady=8)
        self.pur_total_lbl = tk.Label(right, text="Total: 0.00 Tk", font=("Arial", 16, "bold"), fg="#1565C0")
        self.pur_total_lbl.pack(pady=8)

        gf = tk.Frame(right); gf.pack(pady=5)
        tk.Label(gf, text="Paid Amount (Tk):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.pur_paid_var = tk.StringVar(value="0")
        tk.Entry(gf, textvariable=self.pur_paid_var, width=14).grid(row=0, column=1, padx=5)

        self.pur_due_lbl = tk.Label(right, text="Due to Supplier: 0.00 Tk", font=("Arial", 12), fg="red")
        self.pur_due_lbl.pack(pady=5)

        tk.Button(right, text="Calculate", command=self.pur_calculate,
                  bg="#607D8B", fg="white", width=22).pack(pady=5)
        tk.Button(right, text="Complete Purchase", command=self.complete_purchase,
                  bg="#1565C0", fg="white", font=("Arial", 12, "bold"), height=2).pack(pady=8, fill=tk.X)
        tk.Button(right, text="Reset", command=self.pur_reset,
                  bg="#FF5722", fg="white").pack(pady=3, fill=tk.X)

        tk.Label(right, text="Recent Purchases", font=("Arial", 12, "bold")).pack(pady=(15,3))
        cols3 = ("ID", "Date", "Supplier", "Total", "Paid", "Due")
        self.pur_history = ttk.Treeview(right, columns=cols3, show="headings", height=10)
        for col, w in zip(cols3, (50, 100, 160, 90, 90, 90)):
            self.pur_history.heading(col, text=col)
            self.pur_history.column(col, width=w)
        self.pur_history.tag_configure("due", foreground="red")
        self.pur_history.pack(fill=tk.BOTH, expand=True)

        self._refresh_supplier_combobox()
        self.pur_load_search()
        self.pur_load_history()

    def pur_search_product(self, event=None):
        term = self.pur_search.get()
        for i in self.pur_search_tree.get_children(): self.pur_search_tree.delete(i)
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        if term:
            c.execute("SELECT id,name,buy_price,stock FROM products WHERE name LIKE ? LIMIT 20", (f"%{term}%",))
        else:
            c.execute("SELECT id,name,buy_price,stock FROM products LIMIT 30")
        for row in c.fetchall():
            self.pur_search_tree.insert("", "end", values=row)
        conn.close()

    def pur_load_search(self): self.pur_search_product()

    def pur_add_to_cart(self, event=None):
        sel = self.pur_search_tree.selection()
        if not sel: return
        v = self.pur_search_tree.item(sel[0])['values']
        pid, name, buy_price, stock = v
        buy_price = float(buy_price)
        qty = simpledialog.askinteger("Quantity", f"Enter quantity for {name}:", minvalue=1)
        if not qty: return
        total = buy_price * qty
        self.pur_cart.insert("", "end", values=(pid, name, qty, f"{buy_price:.2f}", f"{total:.2f}"))
        self.pur_update_total()

    def pur_remove_item(self):
        sel = self.pur_cart.selection()
        if sel: self.pur_cart.delete(sel[0]); self.pur_update_total()

    def pur_clear_cart(self):
        for i in self.pur_cart.get_children(): self.pur_cart.delete(i)
        self.pur_update_total()

    def pur_update_total(self):
        total = sum(float(self.pur_cart.item(c)['values'][4]) for c in self.pur_cart.get_children())
        self.pur_total_lbl.config(text=f"Total: {total:.2f} Tk")
        self.pur_calculate()

    def pur_calculate(self):
        total = sum(float(self.pur_cart.item(c)['values'][4]) for c in self.pur_cart.get_children())
        try: paid = float(self.pur_paid_var.get() or 0)
        except: paid = 0
        due = total - paid
        self.pur_due_lbl.config(text=f"Due to Supplier: {due:.2f} Tk", fg="red" if due > 0 else "green")

    def pur_reset(self):
        self.pur_clear_cart()
        self.pur_supplier_var.set("")
        self.pur_paid_var.set("0")
        self.pur_total_lbl.config(text="Total: 0.00 Tk")
        self.pur_due_lbl.config(text="Due to Supplier: 0.00 Tk")

    def complete_purchase(self):
        if not self.pur_cart.get_children():
            messagebox.showwarning("Warning", "Cart is empty!"); return
        sup_name = self.pur_supplier_var.get()
        if not sup_name:
            messagebox.showwarning("Warning", "Select a supplier!"); return

        total = sum(float(self.pur_cart.item(c)['values'][4]) for c in self.pur_cart.get_children())
        try: paid = float(self.pur_paid_var.get() or 0)
        except: paid = 0
        due = total - paid

        if not messagebox.askyesno("Confirm", f"Total: {total:.2f} Tk\nPaid: {paid:.2f} Tk\nDue: {due:.2f} Tk\n\nComplete Purchase?"): return

        sup_id = self.suppliers_dict.get(sup_name)
        today  = datetime.date.today().isoformat()
        items_parts = []
        for child in self.pur_cart.get_children():
            v = self.pur_cart.item(child)['values']
            items_parts.append(f"{v[1]}||{v[2]}||{v[3]}")

        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("INSERT INTO purchases (date,supplier_id,supplier_name,total,paid,due,items) VALUES(?,?,?,?,?,?,?)",
                  (today, sup_id, sup_name, total, paid, due, "|".join(items_parts)))

        # Update stock & buy price for each item
        for child in self.pur_cart.get_children():
            v = self.pur_cart.item(child)['values']
            pid = v[0]; qty = int(v[2]); buy_p = float(v[3])
            c.execute("UPDATE products SET stock=stock+?, buy_price=? WHERE id=?", (qty, buy_p, pid))
            c.execute("INSERT INTO stock_log (date,product_id,product_name,type,qty,note) VALUES(?,?,?,?,?,?)",
                      (today, pid, v[1], "IN", qty, f"Purchase from {sup_name}"))

        if sup_id and due > 0:
            c.execute("UPDATE suppliers SET due=due+? WHERE id=?", (due, sup_id))

        conn.commit(); conn.close()
        messagebox.showinfo("Success", f"Purchase recorded! Stock updated.")
        self.pur_reset()
        self.load_products(); self.load_stock_log(); self.load_stock_products()
        self.load_suppliers(); self.pur_load_history()
        self.refresh_dashboard()

    def pur_load_history(self):
        for i in self.pur_history.get_children(): self.pur_history.delete(i)
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("SELECT id,date,supplier_name,total,paid,due FROM purchases ORDER BY id DESC LIMIT 50")
        for row in c.fetchall():
            tag = ("due",) if row[5] > 0 else ()
            self.pur_history.insert("", "end",
                values=(f"#{row[0]}", row[1], row[2], f"{row[3]:.2f}", f"{row[4]:.2f}", f"{row[5]:.2f}"), tags=tag)
        conn.close()

    # ======================== WARRANTY TAB ========================
    def create_warranty_tab(self):
        top = tk.Frame(self.warranty_tab, padx=15, pady=12)
        top.pack(fill=tk.X)

        tk.Label(top, text="Warranty Management", font=("Arial", 15, "bold")).grid(row=0, column=0, columnspan=8, pady=8)

        fields = [("Customer Name:", "war_cust"), ("Phone:", "war_phone"),
                  ("Product:", "war_product"), ("Serial No:", "war_serial")]
        for i, (lbl, attr) in enumerate(fields):
            tk.Label(top, text=lbl).grid(row=1, column=i*2, sticky="w", padx=5)
            e = tk.Entry(top, width=18)
            e.grid(row=1, column=i*2+1, padx=5, pady=4)
            setattr(self, attr, e)

        f2 = tk.Frame(self.warranty_tab, padx=15); f2.pack(fill=tk.X)
        tk.Label(f2, text="Warranty (Months):").grid(row=0, column=0, sticky="w", padx=5)
        self.war_months = ttk.Combobox(f2, values=["3","6","12","18","24","36"], width=8, state="readonly")
        self.war_months.set("12"); self.war_months.grid(row=0, column=1, padx=5)

        tk.Label(f2, text="Sale Date:").grid(row=0, column=2, sticky="w", padx=5)
        self.war_date = tk.Entry(f2, width=14)
        self.war_date.insert(0, datetime.date.today().isoformat())
        self.war_date.grid(row=0, column=3, padx=5)

        tk.Label(f2, text="Note:").grid(row=0, column=4, sticky="w", padx=5)
        self.war_note = tk.Entry(f2, width=25)
        self.war_note.grid(row=0, column=5, padx=5)

        bf = tk.Frame(self.warranty_tab, padx=15); bf.pack(pady=8)
        tk.Button(bf, text="Add Warranty", command=self.add_warranty,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Check Expiry (Today)", command=self.check_warranty_expiry,
                  bg="#FF9800", fg="white", padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Delete Selected", command=self.delete_warranty,
                  bg="#f44336", fg="white", padx=10).pack(side=tk.LEFT, padx=5)

        search_f = tk.Frame(self.warranty_tab, padx=15); search_f.pack(fill=tk.X, pady=3)
        tk.Label(search_f, text="Search:").pack(side=tk.LEFT)
        self.war_search = tk.Entry(search_f, width=30)
        self.war_search.pack(side=tk.LEFT, padx=5)
        self.war_search.bind("<KeyRelease>", self.search_warranty)
        tk.Button(search_f, text="All", command=self.load_warranties,
                  bg="#607D8B", fg="white", padx=8).pack(side=tk.LEFT, padx=5)

        cols = ("ID", "Sale Date", "Customer", "Phone", "Product", "Serial", "Months", "Expiry", "Status")
        self.warranty_tree = ttk.Treeview(self.warranty_tab, columns=cols, show="headings", height=18)
        widths = (40, 100, 150, 110, 180, 120, 70, 100, 80)
        for col, w in zip(cols, widths):
            self.warranty_tree.heading(col, text=col)
            self.warranty_tree.column(col, width=w)
        self.warranty_tree.tag_configure("expired", foreground="red")
        self.warranty_tree.tag_configure("expiring", foreground="#FF8F00")
        self.warranty_tree.tag_configure("valid",   foreground="#2E7D32")

        sb = ttk.Scrollbar(self.warranty_tab, orient="vertical", command=self.warranty_tree.yview)
        self.warranty_tree.configure(yscrollcommand=sb.set)
        self.warranty_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0))
        sb.pack(side=tk.LEFT, fill=tk.Y, padx=(0,15))
        self.load_warranties()

    def add_warranty(self):
        cust = self.war_cust.get().strip()
        prod = self.war_product.get().strip()
        if not cust or not prod:
            messagebox.showerror("Error", "Customer and Product required!"); return
        try:
            months = int(self.war_months.get())
            sale_date = self.war_date.get().strip()
            sd = datetime.date.fromisoformat(sale_date)
            expiry = (sd.replace(month=sd.month + months) if sd.month + months <= 12
                      else sd.replace(year=sd.year + (sd.month+months-1)//12,
                                      month=(sd.month+months-1)%12+1)).isoformat()
        except Exception as e:
            messagebox.showerror("Error", f"Date error: {e}"); return

        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("INSERT INTO warranties (sale_id,sale_date,customer_name,customer_phone,product_name,serial_no,warranty_months,expiry_date,note) VALUES(?,?,?,?,?,?,?,?,?)",
                  (0, sale_date, cust, self.war_phone.get(), prod,
                   self.war_serial.get(), months, expiry, self.war_note.get()))
        conn.commit(); conn.close()
        messagebox.showinfo("Success", f"Warranty added! Expires: {expiry}")
        for e in [self.war_cust, self.war_phone, self.war_product, self.war_serial, self.war_note]:
            e.delete(0, tk.END)
        self.load_warranties()

    def load_warranties(self):
        for i in self.warranty_tree.get_children(): self.warranty_tree.delete(i)
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("SELECT id,sale_date,customer_name,customer_phone,product_name,serial_no,warranty_months,expiry_date FROM warranties ORDER BY expiry_date")
        today = datetime.date.today()
        for row in c.fetchall():
            try:
                exp = datetime.date.fromisoformat(row[7])
                days_left = (exp - today).days
                if days_left < 0: status = "Expired"; tag = "expired"
                elif days_left <= 30: status = f"{days_left}d left"; tag = "expiring"
                else: status = "Valid"; tag = "valid"
            except: status = "?"; tag = ""
            self.warranty_tree.insert("", "end", values=(*row, status), tags=(tag,))
        conn.close()

    def search_warranty(self, event=None):
        term = self.war_search.get().lower()
        for i in self.warranty_tree.get_children(): self.warranty_tree.delete(i)
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("SELECT id,sale_date,customer_name,customer_phone,product_name,serial_no,warranty_months,expiry_date FROM warranties WHERE customer_name LIKE ? OR product_name LIKE ? OR serial_no LIKE ?",
                  (f"%{term}%", f"%{term}%", f"%{term}%"))
        today = datetime.date.today()
        for row in c.fetchall():
            try:
                exp = datetime.date.fromisoformat(row[7])
                days_left = (exp - today).days
                if days_left < 0: status = "Expired"; tag = "expired"
                elif days_left <= 30: status = f"{days_left}d left"; tag = "expiring"
                else: status = "Valid"; tag = "valid"
            except: status = "?"; tag = ""
            self.warranty_tree.insert("", "end", values=(*row, status), tags=(tag,))
        conn.close()

    def check_warranty_expiry(self):
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        today = datetime.date.today().isoformat()
        in30  = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        c.execute("SELECT customer_name, product_name, expiry_date FROM warranties WHERE expiry_date <= ?", (in30,))
        rows = c.fetchall(); conn.close()
        if not rows:
            messagebox.showinfo("All Good!", "No warranties expiring in 30 days."); return
        msg = "Expiring within 30 days:\n\n"
        for r in rows:
            msg += f"• {r[0]} — {r[1]} (Expires: {r[2]})\n"
        messagebox.showwarning("Warranty Alert!", msg)

    def delete_warranty(self):
        sel = self.warranty_tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirm", "Delete this warranty record?"):
            wid = self.warranty_tree.item(sel[0])['values'][0]
            conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
            c.execute("DELETE FROM warranties WHERE id=?", (wid,))
            conn.commit(); conn.close()
            self.load_warranties()

    # ======================== RETURN / EXCHANGE TAB ========================
    def create_return_tab(self):
        top = tk.Frame(self.return_tab, padx=15, pady=12)
        top.pack(fill=tk.X)

        tk.Label(top, text="Product Return / Exchange", font=("Arial", 15, "bold")).pack(pady=8)

        form = tk.Frame(self.return_tab, padx=20); form.pack(fill=tk.X)

        # Row 1
        r1 = tk.Frame(form); r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="Type:", width=14, anchor="w").pack(side=tk.LEFT)
        self.ret_type = ttk.Combobox(r1, values=["Return (Refund)", "Exchange"], width=18, state="readonly")
        self.ret_type.set("Return (Refund)"); self.ret_type.pack(side=tk.LEFT, padx=5)
        tk.Label(r1, text="Date:", width=8, anchor="w").pack(side=tk.LEFT)
        self.ret_date = tk.Entry(r1, width=14)
        self.ret_date.insert(0, datetime.date.today().isoformat())
        self.ret_date.pack(side=tk.LEFT, padx=5)

        # Row 2
        r2 = tk.Frame(form); r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="Customer Name:", width=14, anchor="w").pack(side=tk.LEFT)
        self.ret_customer = tk.Entry(r2, width=22); self.ret_customer.pack(side=tk.LEFT, padx=5)
        tk.Label(r2, text="Product:", width=8, anchor="w").pack(side=tk.LEFT)
        self.ret_product = tk.Entry(r2, width=22); self.ret_product.pack(side=tk.LEFT, padx=5)

        # Row 3
        r3 = tk.Frame(form); r3.pack(fill=tk.X, pady=3)
        tk.Label(r3, text="Qty:", width=14, anchor="w").pack(side=tk.LEFT)
        self.ret_qty = tk.Entry(r3, width=8); self.ret_qty.insert(0, "1"); self.ret_qty.pack(side=tk.LEFT, padx=5)
        tk.Label(r3, text="Unit Price:", width=10, anchor="w").pack(side=tk.LEFT)
        self.ret_price = tk.Entry(r3, width=12); self.ret_price.pack(side=tk.LEFT, padx=5)
        tk.Label(r3, text="Refund Amt:", width=10, anchor="w").pack(side=tk.LEFT)
        self.ret_refund = tk.Entry(r3, width=12); self.ret_refund.pack(side=tk.LEFT, padx=5)

        # Row 4
        r4 = tk.Frame(form); r4.pack(fill=tk.X, pady=3)
        tk.Label(r4, text="Reason:", width=14, anchor="w").pack(side=tk.LEFT)
        self.ret_reason = ttk.Combobox(r4, values=["Defective","Wrong Item","Customer Changed Mind","Warranty Claim","Other"], width=20, state="normal")
        self.ret_reason.set("Defective"); self.ret_reason.pack(side=tk.LEFT, padx=5)
        tk.Label(r4, text="Note:", width=8, anchor="w").pack(side=tk.LEFT)
        self.ret_note = tk.Entry(r4, width=30); self.ret_note.pack(side=tk.LEFT, padx=5)

        bf = tk.Frame(self.return_tab, padx=20); bf.pack(pady=8)
        tk.Button(bf, text="Record Return/Exchange", command=self.add_return,
                  bg="#E65100", fg="white", font=("Arial", 11, "bold"), padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Clear Form", command=self.clear_return_form,
                  bg="#9E9E9E", fg="white", padx=10).pack(side=tk.LEFT, padx=5)

        tk.Label(self.return_tab, text="Return / Exchange History", font=("Arial", 12, "bold")).pack(pady=(10,3))

        cols = ("ID", "Date", "Type", "Customer", "Product", "Qty", "Price", "Refund", "Reason")
        self.return_tree = ttk.Treeview(self.return_tab, columns=cols, show="headings", height=14)
        widths = (40, 100, 120, 150, 180, 50, 80, 80, 130)
        for col, w in zip(cols, widths):
            self.return_tree.heading(col, text=col)
            self.return_tree.column(col, width=w)
        self.return_tree.tag_configure("return",   foreground="#B71C1C")
        self.return_tree.tag_configure("exchange", foreground="#1565C0")

        sb = ttk.Scrollbar(self.return_tab, orient="vertical", command=self.return_tree.yview)
        self.return_tree.configure(yscrollcommand=sb.set)
        self.return_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0))
        sb.pack(side=tk.LEFT, fill=tk.Y, padx=(0,15))
        self.load_returns()

    def add_return(self):
        cust = self.ret_customer.get().strip()
        prod = self.ret_product.get().strip()
        if not cust or not prod:
            messagebox.showerror("Error", "Customer and Product required!"); return
        try:
            qty    = int(self.ret_qty.get() or 1)
            price  = float(self.ret_price.get() or 0)
            refund = float(self.ret_refund.get() or 0)
        except:
            messagebox.showerror("Error", "Invalid qty/price!"); return

        rtype = self.ret_type.get()
        conn  = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("INSERT INTO returns (date,type,customer_name,product_name,qty,price,refund,reason,note) VALUES(?,?,?,?,?,?,?,?,?)",
                  (self.ret_date.get(), rtype, cust, prod, qty, price, refund,
                   self.ret_reason.get(), self.ret_note.get()))

        # If return, add stock back
        if "Return" in rtype:
            c.execute("UPDATE products SET stock=stock+? WHERE name LIKE ?", (qty, f"%{prod}%"))
            today = datetime.date.today().isoformat()
            c.execute("INSERT INTO stock_log (date,product_id,product_name,type,qty,note) VALUES(?,?,?,?,?,?)",
                      (today, 0, prod, "IN", qty, f"Return from {cust}"))

        conn.commit(); conn.close()
        messagebox.showinfo("Success", f"{rtype} recorded! Refund: {refund:.2f} Tk")
        self.clear_return_form()
        self.load_returns()
        self.load_products()

    def clear_return_form(self):
        for e in [self.ret_customer, self.ret_product, self.ret_note]:
            e.delete(0, tk.END)
        self.ret_qty.delete(0, tk.END); self.ret_qty.insert(0, "1")
        self.ret_price.delete(0, tk.END)
        self.ret_refund.delete(0, tk.END)

    def load_returns(self):
        for i in self.return_tree.get_children(): self.return_tree.delete(i)
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("SELECT id,date,type,customer_name,product_name,qty,price,refund,reason FROM returns ORDER BY id DESC LIMIT 100")
        for row in c.fetchall():
            tag = ("return",) if "Return" in row[2] else ("exchange",)
            self.return_tree.insert("", "end", values=row, tags=tag)
        conn.close()

    # ======================== USER MANAGEMENT TAB ========================
    def create_user_tab(self):
        left = tk.Frame(self.user_tab, padx=20, pady=20)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="User Management", font=("Arial", 15, "bold")).pack(pady=10)
        tk.Label(left, text="(Admin only)", font=("Arial", 9), fg="gray").pack()

        for lbl, attr, show in [("Username:", "u_name", ""), ("Password:", "u_pass", "*")]:
            tk.Label(left, text=lbl, anchor="w").pack(fill=tk.X, pady=(8,0))
            e = tk.Entry(left, width=25, show=show)
            e.pack(pady=3)
            setattr(self, attr, e)

        tk.Label(left, text="Role:", anchor="w").pack(fill=tk.X, pady=(8,0))
        self.u_role = ttk.Combobox(left, values=["admin", "staff"], width=23, state="readonly")
        self.u_role.set("staff"); self.u_role.pack(pady=3)

        bf = tk.Frame(left); bf.pack(pady=15)
        tk.Button(bf, text="Add User",   command=self.add_user,    bg="#4CAF50", fg="white", width=12).grid(row=0, column=0, padx=4)
        tk.Button(bf, text="Delete",     command=self.delete_user, bg="#f44336", fg="white", width=12).grid(row=0, column=1, padx=4)

        tk.Label(left, text="Change Password", font=("Arial", 11, "bold")).pack(pady=(20,5))
        tk.Label(left, text="New Password:", anchor="w").pack(fill=tk.X)
        self.u_newpass = tk.Entry(left, width=25, show="*"); self.u_newpass.pack(pady=3)
        tk.Button(left, text="Update Password", command=self.change_password,
                  bg="#FF9800", fg="white", width=20).pack(pady=8)

        right = tk.Frame(self.user_tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(right, text="User List", font=("Arial", 13, "bold")).pack()

        cols = ("ID", "Username", "Role")
        self.user_tree = ttk.Treeview(right, columns=cols, show="headings", height=20)
        for col, w in zip(cols, (60, 200, 150)):
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=w)
        self.user_tree.tag_configure("admin", foreground="#1565C0")
        self.user_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.load_users()

    def add_user(self):
        uname = self.u_name.get().strip()
        passw = self.u_pass.get().strip()
        role  = self.u_role.get()
        if not uname or not passw:
            messagebox.showerror("Error", "Username and password required!"); return
        try:
            conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
            c.execute("INSERT INTO users (username,password,role) VALUES(?,?,?)", (uname, passw, role))
            conn.commit(); conn.close()
            messagebox.showinfo("Success", f"User '{uname}' created!")
            self.u_name.delete(0, tk.END); self.u_pass.delete(0, tk.END)
            self.load_users()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")

    def delete_user(self):
        sel = self.user_tree.selection()
        if not sel: return
        uid  = self.user_tree.item(sel[0])['values'][0]
        uname = self.user_tree.item(sel[0])['values'][1]
        if uname == "admin":
            messagebox.showerror("Error", "Cannot delete default admin!"); return
        if uname == self.logged_user:
            messagebox.showerror("Error", "Cannot delete yourself!"); return
        if messagebox.askyesno("Confirm", f"Delete user '{uname}'?"):
            conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
            c.execute("DELETE FROM users WHERE id=?", (uid,))
            conn.commit(); conn.close()
            self.load_users()

    def change_password(self):
        sel = self.user_tree.selection()
        if not sel: messagebox.showwarning("Warning", "Select a user!"); return
        uid   = self.user_tree.item(sel[0])['values'][0]
        uname = self.user_tree.item(sel[0])['values'][1]
        newp  = self.u_newpass.get().strip()
        if not newp or len(newp) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters!"); return
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE id=?", (newp, uid))
        conn.commit(); conn.close()
        messagebox.showinfo("Success", f"Password updated for '{uname}'!")
        self.u_newpass.delete(0, tk.END)

    def load_users(self):
        for i in self.user_tree.get_children(): self.user_tree.delete(i)
        conn = sqlite3.connect('shop_erp.db'); c = conn.cursor()
        c.execute("SELECT id,username,role FROM users ORDER BY id")
        for row in c.fetchall():
            tag = ("admin",) if row[2] == "admin" else ()
            self.user_tree.insert("", "end", values=row, tags=tag)
        conn.close()

# ====================== LOGIN WINDOW ======================
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Shop ERP - Login")
        self.root.geometry("400x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a237e")
        self.success = False

        # Center window
        self.root.eval('tk::PlaceWindow . center')

        tk.Label(root, text="SHOP MANAGEMENT ERP", font=("Arial", 16, "bold"),
                 bg="#1a237e", fg="white").pack(pady=(40, 5))
        tk.Label(root, text="Md. Hasibul Electronics", font=("Arial", 11),
                 bg="#1a237e", fg="#90CAF9").pack(pady=(0, 30))

        card = tk.Frame(root, bg="white", padx=30, pady=30)
        card.pack(padx=40, fill=tk.X)

        tk.Label(card, text="Username", font=("Arial", 10, "bold"), bg="white", anchor="w").pack(fill=tk.X)
        self.username = tk.Entry(card, font=("Arial", 12), width=25)
        self.username.pack(pady=(3, 15), ipady=6, fill=tk.X)
        self.username.insert(0, "admin")

        tk.Label(card, text="Password", font=("Arial", 10, "bold"), bg="white", anchor="w").pack(fill=tk.X)
        self.password = tk.Entry(card, font=("Arial", 12), show="*", width=25)
        self.password.pack(pady=(3, 20), ipady=6, fill=tk.X)
        self.password.bind("<Return>", lambda e: self.login())

        tk.Button(card, text="LOGIN", command=self.login, bg="#1a237e", fg="white",
                  font=("Arial", 12, "bold"), pady=8, relief="flat").pack(fill=tk.X)

        self.msg = tk.Label(root, text="", font=("Arial", 10), bg="#1a237e", fg="#FF8A80")
        self.msg.pack(pady=10)

        tk.Label(root, text="Default: admin / admin123", font=("Arial", 9),
                 bg="#1a237e", fg="#7986CB").pack(pady=5)

        self.username.focus()

    def login(self):
        uname = self.username.get().strip()
        passw = self.password.get().strip()
        if not uname or not passw:
            self.msg.config(text="Username and password required!")
            return
        conn = sqlite3.connect('shop_erp.db')
        c = conn.cursor()
        c.execute("SELECT id, role FROM users WHERE username=? AND password=?", (uname, passw))
        user = c.fetchone()
        conn.close()
        if user:
            self.success = True
            self.logged_user = uname
            self.logged_role = user[1]
            self.root.destroy()
        else:
            self.msg.config(text="Wrong username or password!")
            self.password.delete(0, tk.END)


# ====================== RUN ======================
if __name__ == "__main__":
    init_db()

    # Login first
    login_root = tk.Tk()
    login_app  = LoginWindow(login_root)
    login_root.mainloop()

    if not login_app.success:
        exit()

    # Launch main app
    root = tk.Tk()
    app  = ShopERP(root, login_app.logged_user, login_app.logged_role)
    root.mainloop()