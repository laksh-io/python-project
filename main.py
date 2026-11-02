import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).with_name("expenses.db")
BG = "#F3F6FB"
NAVY = "#172554"
BLUE = "#2563EB"
GREEN = "#059669"
RED = "#DC2626"
TEXT = "#1E293B"
MUTED = "#64748B"
WHITE = "#FFFFFF"

CATEGORIES = ["Food", "Travel", "Shopping", "Education", "Bills", "Health",
              "Entertainment", "Rent", "Salary", "Other"]


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Expense Tracker")
        self.root.geometry("1120x720")
        self.root.minsize(940, 620)
        self.root.configure(bg=BG)
        self.selected_id = None

        self.setup_database()
        self.setup_style()
        self.build_ui()
        self.refresh_data()

    def setup_database(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    txn_date TEXT NOT NULL,
                    txn_type TEXT NOT NULL CHECK(txn_type IN ('Income', 'Expense')),
                    category TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    description TEXT
                )
            """)

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10),
                        background=WHITE, fieldbackground=WHITE, foreground=TEXT)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#E8EEF8", foreground=NAVY, padding=8)
        style.map("Treeview", background=[("selected", "#DBEAFE")],
                  foreground=[("selected", NAVY)])
        style.configure("TCombobox", padding=6)
        style.configure("TEntry", padding=7)

    def card(self, parent, title, value, color):
        frame = tk.Frame(parent, bg=WHITE, highlightbackground="#E2E8F0",
                         highlightthickness=1)
        tk.Label(frame, text=title, bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(13, 4))
        label = tk.Label(frame, text=value, bg=WHITE, fg=color,
                         font=("Segoe UI", 21, "bold"))
        label.pack(anchor="w", padx=16, pady=(0, 13))
        return frame, label

    def build_ui(self):
        header = tk.Frame(self.root, bg=NAVY, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="SMART EXPENSE TRACKER", bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 19, "bold")).pack(side="left", padx=24, pady=18)
        tk.Label(header, text="Manage your money • Track your habits",
                 bg=NAVY, fg="#CBD5E1", font=("Segoe UI", 10)).pack(
                     side="right", padx=24)

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=22, pady=18)

        cards = tk.Frame(content, bg=BG)
        cards.pack(fill="x", pady=(0, 16))
        self.balance_card, self.balance_value = self.card(cards, "CURRENT BALANCE", "₹0.00", BLUE)
        self.income_card, self.income_value = self.card(cards, "TOTAL INCOME", "₹0.00", GREEN)
        self.expense_card, self.expense_value = self.card(cards, "TOTAL EXPENSES", "₹0.00", RED)
        for c in (self.balance_card, self.income_card, self.expense_card):
            c.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.expense_card.pack_configure(padx=0)

        body = tk.Frame(content, bg=BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=WHITE, width=300, highlightbackground="#E2E8F0",
                        highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)
        tk.Label(left, text="ADD TRANSACTION", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=17, pady=(17, 12))

        self.type_var = tk.StringVar(value="Expense")
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.category_var = tk.StringVar(value="Food")
        self.amount_var = tk.StringVar()
        self.description_var = tk.StringVar()

        self.add_field(left, "Transaction type")
        ttk.Combobox(left, textvariable=self.type_var, values=["Expense", "Income"],
                     state="readonly").pack(fill="x", padx=17, pady=(0, 10))
        self.add_field(left, "Date (YYYY-MM-DD)")
        ttk.Entry(left, textvariable=self.date_var).pack(fill="x", padx=17, pady=(0, 10))
        self.add_field(left, "Category")
        self.category_box = ttk.Combobox(left, textvariable=self.category_var,
                                         values=CATEGORIES, state="readonly")
        self.category_box.pack(fill="x", padx=17, pady=(0, 10))
        self.add_field(left, "Amount (₹)")
        ttk.Entry(left, textvariable=self.amount_var).pack(fill="x", padx=17, pady=(0, 10))
        self.add_field(left, "Description")
        ttk.Entry(left, textvariable=self.description_var).pack(fill="x", padx=17, pady=(0, 14))

        self.save_button = tk.Button(left, text="＋  Add Transaction", command=self.save_transaction,
                                     bg=BLUE, fg=WHITE, activebackground="#1D4ED8",
                                     activeforeground=WHITE, relief="flat",
                                     font=("Segoe UI", 10, "bold"), cursor="hand2", pady=10)
        self.save_button.pack(fill="x", padx=17)
        tk.Button(left, text="Clear Form", command=self.clear_form, bg="#E2E8F0",
                  fg=TEXT, relief="flat", font=("Segoe UI", 9, "bold"),
                  cursor="hand2", pady=8).pack(fill="x", padx=17, pady=8)
        tk.Label(left, text="Tip: Select a row to edit or delete it.",
                 bg=WHITE, fg=MUTED, font=("Segoe UI", 8), wraplength=250,
                 justify="left").pack(anchor="w", padx=17, pady=(8, 0))

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        top = tk.Frame(right, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="TRANSACTION HISTORY", bg=BG, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(top, textvariable=self.filter_var,
                     values=["All", "Income", "Expense"], state="readonly",
                     width=11).pack(side="right")
        self.filter_var.trace_add("write", lambda *_: self.refresh_data())
        self.search_var = tk.StringVar()
        search = ttk.Entry(top, textvariable=self.search_var, width=24)
        search.pack(side="right", padx=8)
        search.insert(0, "")
        self.search_var.trace_add("write", lambda *_: self.refresh_data())

        table_frame = tk.Frame(right, bg=WHITE, highlightbackground="#E2E8F0",
                               highlightthickness=1)
        table_frame.pack(fill="both", expand=True)
        cols = ("date", "type", "category", "amount", "description")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        headings = {"date": "DATE", "type": "TYPE", "category": "CATEGORY",
                    "amount": "AMOUNT (₹)", "description": "DESCRIPTION"}
        widths = {"date": 100, "type": 85, "category": 110, "amount": 110, "description": 180}
        for col in cols:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.column("amount", anchor="e")
        self.tree.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.tag_configure("Income", foreground=GREEN)
        self.tree.tag_configure("Expense", foreground=RED)

        actions = tk.Frame(right, bg=BG)
        actions.pack(fill="x", pady=10)
        tk.Button(actions, text="Edit Selected", command=self.prepare_edit,
                  bg="#DBEAFE", fg=NAVY, relief="flat", padx=15, pady=8,
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left")
        tk.Button(actions, text="Delete Selected", command=self.delete_transaction,
                  bg="#FEE2E2", fg=RED, relief="flat", padx=15, pady=8,
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left", padx=8)
        tk.Button(actions, text="Monthly Summary", command=self.show_monthly_summary,
                  bg="#D1FAE5", fg="#065F46", relief="flat", padx=15, pady=8,
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="right")

        footer = tk.Label(content, text="Data is saved locally on this computer in expenses.db",
                          bg=BG, fg=MUTED, font=("Segoe UI", 8))
        footer.pack(anchor="w", pady=(8, 0))

    def add_field(self, parent, label):
        tk.Label(parent, text=label, bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=17, pady=(0, 4))

    def save_transaction(self):
        txn_type = self.type_var.get()
        txn_date = self.date_var.get().strip()
        category = self.category_var.get()
        description = self.description_var.get().strip()
        try:
            datetime.strptime(txn_date, "%Y-%m-%d")
            amount = float(self.amount_var.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Enter a valid date (YYYY-MM-DD) and an amount greater than zero.")
            return

        with sqlite3.connect(DB_PATH) as conn:
            if self.selected_id is None:
                conn.execute("""INSERT INTO transactions
                    (txn_date, txn_type, category, amount, description)
                    VALUES (?, ?, ?, ?, ?)""",
                    (txn_date, txn_type, category, amount, description))
                messagebox.showinfo("Saved", "Transaction added successfully.")
            else:
                conn.execute("""UPDATE transactions SET txn_date=?, txn_type=?,
                    category=?, amount=?, description=? WHERE id=?""",
                    (txn_date, txn_type, category, amount, description, self.selected_id))
                messagebox.showinfo("Updated", "Transaction updated successfully.")
        self.clear_form()
        self.refresh_data()

    def clear_form(self):
        self.selected_id = None
        self.type_var.set("Expense")
        self.date_var.set(date.today().isoformat())
        self.category_var.set("Food")
        self.amount_var.set("")
        self.description_var.set("")
        self.save_button.config(text="＋  Add Transaction")

    def on_select(self, _event=None):
        pass

    def prepare_edit(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select transaction", "Please select a transaction first.")
            return
        txn_id = int(selection[0])
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("""SELECT txn_date, txn_type, category, amount, description
                                  FROM transactions WHERE id=?""", (txn_id,)).fetchone()
        if row:
            self.selected_id = txn_id
            self.date_var.set(row[0])
            self.type_var.set(row[1])
            self.category_var.set(row[2])
            self.amount_var.set(str(row[3]))
            self.description_var.set(row[4] or "")
            self.save_button.config(text="Save Changes")

    def delete_transaction(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select transaction", "Please select a transaction first.")
            return
        if not messagebox.askyesno("Confirm delete", "Delete the selected transaction permanently?"):
            return
        txn_id = int(selection[0])
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
        self.clear_form()
        self.refresh_data()

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        filter_type = self.filter_var.get()
        search = self.search_var.get().strip()
        query = "SELECT id, txn_date, txn_type, category, amount, description FROM transactions WHERE 1=1"
        params = []
        if filter_type in ("Income", "Expense"):
            query += " AND txn_type=?"
            params.append(filter_type)
        if search:
            query += " AND (category LIKE ? OR description LIKE ? OR txn_date LIKE ?)"
            params.extend([f"%{search}%"] * 3)
        query += " ORDER BY txn_date DESC, id DESC"
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(query, params).fetchall()
            income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE txn_type='Income'").fetchone()[0]
            expenses = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE txn_type='Expense'").fetchone()[0]
        for row in rows:
            txn_id, txn_date, txn_type, category, amount, description = row
            self.tree.insert("", "end", iid=str(txn_id),
                             values=(txn_date, txn_type, category, f"{amount:,.2f}", description or "—"),
                             tags=(txn_type,))
        self.balance_value.config(text=f"₹{income-expenses:,.2f}")
        self.income_value.config(text=f"₹{income:,.2f}")
        self.expense_value.config(text=f"₹{expenses:,.2f}")

    def show_monthly_summary(self):
        month = date.today().strftime("%Y-%m")
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("""SELECT txn_type, category, SUM(amount)
                FROM transactions WHERE substr(txn_date,1,7)=?
                GROUP BY txn_type, category ORDER BY txn_type, SUM(amount) DESC""",
                (month,)).fetchall()
        win = tk.Toplevel(self.root)
        win.title("Monthly Summary")
        win.geometry("440x420")
        win.configure(bg=BG)
        tk.Label(win, text=f"SUMMARY — {date.today().strftime('%B %Y')}",
                 bg=NAVY, fg=WHITE, font=("Segoe UI", 13, "bold"),
                 pady=15).pack(fill="x")
        if not rows:
            tk.Label(win, text="No transactions recorded this month.",
                     bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(pady=35)
            return
        totals = {"Income": 0, "Expense": 0}
        for kind, category, amount in rows:
            totals[kind] += amount
        summary = tk.Frame(win, bg=WHITE)
        summary.pack(fill="x", padx=18, pady=18)
        tk.Label(summary, text=f"Income: ₹{totals['Income']:,.2f}",
                 bg=WHITE, fg=GREEN, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=8)
        tk.Label(summary, text=f"Expenses: ₹{totals['Expense']:,.2f}",
                 bg=WHITE, fg=RED, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=8)
        tk.Label(summary, text=f"Net: ₹{totals['Income']-totals['Expense']:,.2f}",
                 bg=WHITE, fg=BLUE, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=8)
        tk.Label(win, text="CATEGORY BREAKDOWN", bg=BG, fg=NAVY,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20)
        for kind, category, amount in rows:
            tk.Label(win, text=f"{kind:8}  {category:18}  ₹{amount:,.2f}",
                     bg=BG, fg=TEXT, font=("Consolas", 9)).pack(anchor="w", padx=22, pady=3)


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
