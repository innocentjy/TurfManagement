import tkinter as tk
from tkinter import ttk, messagebox
from database import get_cursor, get_connection
from datetime import datetime

class PurchasesPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.selected_purchase_id = None
        self.supplier_map = {}

        # 采购单创建
        form = ttk.LabelFrame(self, text="创建采购单")
        form.pack(fill='x', pady=5)

        tk.Label(form, text="供应商:").grid(row=0, column=0, padx=5)
        self.cmb_supplier = ttk.Combobox(form, state="readonly")
        self.cmb_supplier.grid(row=0, column=1, padx=5)

        tk.Label(form, text="经办人:").grid(row=0, column=2, padx=5)
        self.ent_user = tk.Entry(form)
        self.ent_user.grid(row=0, column=3, padx=5)

        tk.Button(form, text="创建采购单", command=self.create_purchase).grid(row=0, column=4, padx=10)

        # 采购单选择
        control = ttk.Frame(self)
        control.pack(fill='x', pady=5)

        tk.Label(control, text="采购单ID:").pack(side=tk.LEFT, padx=5)
        self.cmb_purchases = ttk.Combobox(control, state="readonly")
        self.cmb_purchases.pack(side=tk.LEFT)
        self.cmb_purchases.bind("<<ComboboxSelected>>", lambda e: self.load_items())

        tk.Button(control, text="刷新采购列表", command=self.load_purchases).pack(side=tk.LEFT, padx=5)

        # 明细表格
        self.tree = ttk.Treeview(self, columns=("明细ID", "产品", "数量", "单价", "小计"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True)

        # 添加明细
        detail = ttk.LabelFrame(self, text="添加采购明细")
        detail.pack(fill='x', pady=5)

        tk.Label(detail, text="产品型号").grid(row=0, column=0, padx=5)
        self.cmb_product = ttk.Combobox(detail, state="readonly")
        self.cmb_product.grid(row=0, column=1, padx=5)

        tk.Label(detail, text="数量").grid(row=0, column=2, padx=5)
        self.ent_qty = tk.Entry(detail)
        self.ent_qty.grid(row=0, column=3, padx=5)

        tk.Label(detail, text="单价").grid(row=0, column=4, padx=5)
        self.ent_price = tk.Entry(detail)
        self.ent_price.grid(row=0, column=5, padx=5)

        tk.Button(detail, text="添加明细", command=self.add_item).grid(row=0, column=6, padx=5)

        self.load_suppliers()
        self.load_products()
        self.load_purchases()

    def load_suppliers(self):
        cursor = get_cursor()
        cursor.execute("SELECT supplier_id, supplier_name FROM suppliers")
        self.supplier_map = {name: sid for sid, name in cursor.fetchall()}
        self.cmb_supplier['values'] = list(self.supplier_map.keys())

    def load_products(self):
        cursor = get_cursor()
        cursor.execute("SELECT product_model FROM products_common")
        self.cmb_product['values'] = [r[0] for r in cursor.fetchall()]

    def create_purchase(self):
        name = self.cmb_supplier.get()
        if name not in self.supplier_map:
            messagebox.showwarning("错误", "请选择供应商")
            return
        try:
            cursor = get_cursor()
            conn = get_connection()
            cursor.execute("""
                INSERT INTO purchases (supplier_id, purchase_date, status, handled_by)
                VALUES (?, GETDATE(), 'Pending', ?)
            """, (self.supplier_map[name], self.ent_user.get()))
            conn.commit()
            self.load_purchases()
            messagebox.showinfo("成功", "已创建采购单")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def load_purchases(self):
        cursor = get_cursor()
        cursor.execute("SELECT purchase_id FROM purchases ORDER BY purchase_id DESC")
        ids = [str(r[0]) for r in cursor.fetchall()]
        self.cmb_purchases['values'] = ids
        if ids:
            self.cmb_purchases.set(ids[0])
            self.load_items()

    def load_items(self):
        self.tree.delete(*self.tree.get_children())
        if not self.cmb_purchases.get():
            return
        self.selected_purchase_id = int(self.cmb_purchases.get())
        cursor = get_cursor()
        cursor.execute("""
            SELECT pi.purchase_item_id, p.product_model, pi.quantity, pi.unit_purchase_price, pi.total_purchase_price
            FROM purchase_items pi
            JOIN products_common p ON pi.product_id = p.product_id
            WHERE pi.purchase_id = ?
        """, self.selected_purchase_id)
        for row in cursor.fetchall():
            self.tree.insert('', tk.END, values=row)

    def add_item(self):
        if not self.selected_purchase_id:
            messagebox.showwarning("提示", "请先选择采购单")
            return
        try:
            model = self.cmb_product.get()
            cursor = get_cursor()
            cursor.execute("SELECT product_id FROM products_common WHERE product_model = ?", model)
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("错误", "产品不存在")
                return
            product_id = row[0]
            qty = int(self.ent_qty.get())
            price = float(self.ent_price.get())
            cursor.execute("""
                INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_purchase_price)
                VALUES (?, ?, ?, ?)
            """, (self.selected_purchase_id, product_id, qty, price))
            cursor.connection.commit()
            self.load_items()
            messagebox.showinfo("成功", "已添加采购明细")
        except Exception as e:
            messagebox.showerror("错误", str(e))
