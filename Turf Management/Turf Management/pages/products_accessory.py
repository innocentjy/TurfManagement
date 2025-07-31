import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection, get_cursor

class ProductsAccessoryTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.product_type = 'Golf Accessory'

        # 搜索区域
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(search_frame, text="搜索型号:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="搜索", command=self.load_products).pack(side=tk.LEFT)

        # 表单
        form = ttk.LabelFrame(self, text="添加/修改 Golf Accessory 产品")
        form.pack(fill='x', padx=10, pady=5)

        tk.Label(form, text="型号:").grid(row=0, column=0, padx=5, pady=2)
        self.ent_model = tk.Entry(form)
        self.ent_model.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form, text="售价:").grid(row=0, column=2, padx=5, pady=2)
        self.ent_sale = tk.Entry(form)
        self.ent_sale.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(form, text="采购价:").grid(row=1, column=0, padx=5, pady=2)
        self.ent_purchase = tk.Entry(form)
        self.ent_purchase.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form, text="每包数量:").grid(row=1, column=2, padx=5, pady=2)
        self.ent_count = tk.Entry(form)
        self.ent_count.grid(row=1, column=3, padx=5, pady=2)

        tk.Label(form, text="材质:").grid(row=2, column=0, padx=5, pady=2)
        self.ent_material = tk.Entry(form)
        self.ent_material.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form, text="净重 (kg):").grid(row=2, column=2, padx=5, pady=2)
        self.ent_net = tk.Entry(form)
        self.ent_net.grid(row=2, column=3, padx=5, pady=2)

        tk.Label(form, text="毛重 (kg):").grid(row=3, column=0, padx=5, pady=2)
        self.ent_gross = tk.Entry(form)
        self.ent_gross.grid(row=3, column=1, padx=5, pady=2)

        tk.Button(form, text="添加产品", command=self.add_product).grid(row=4, column=1, pady=5)
        tk.Button(form, text="删除选中", command=self.delete_product).grid(row=4, column=2, pady=5)
        tk.Button(form, text="刷新", command=self.load_products).grid(row=4, column=3, pady=5)

        # 表格
        self.tree = ttk.Treeview(
            self,
            columns=("型号", "售价", "采购价", "每包数量", "材质", "净重", "毛重"),
            show='headings'
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self.edit_product)

        self.load_products()

    def load_products(self):
        self.tree.delete(*self.tree.get_children())
        keyword = self.search_var.get().strip()
        cursor = get_cursor()
        if keyword:
            cursor.execute("""
                SELECT pc.product_model, pc.standard_sales_price, pc.default_purchase_price,
                       pg.quantity_per_count, pg.material, pg.net_weight, pg.gross_weight
                FROM products_common pc
                JOIN products_golf_accessory pg ON pc.product_id = pg.product_id
                WHERE pc.product_type = ? AND pc.product_model LIKE ?
            """, (self.product_type, f"%{keyword}%"))
        else:
            cursor.execute("""
                SELECT pc.product_model, pc.standard_sales_price, pc.default_purchase_price,
                       pg.quantity_per_count, pg.material, pg.net_weight, pg.gross_weight
                FROM products_common pc
                JOIN products_golf_accessory pg ON pc.product_id = pg.product_id
                WHERE pc.product_type = ?
            """, (self.product_type,))
        for row in cursor.fetchall():
            self.tree.insert('', tk.END, values=[str(r) if r is not None else '' for r in row])

    def add_product(self):
        try:
            model = self.ent_model.get().strip()
            sale = self.ent_sale.get()
            purchase = self.ent_purchase.get()
            count = self.ent_count.get()
            material = self.ent_material.get().strip() or None
            net = self.ent_net.get()
            gross = self.ent_gross.get()

            if not model:
                raise ValueError("型号不能为空")

            sale = float(sale) if sale else None
            purchase = float(purchase) if purchase else None
            count = int(count) if count else None
            net = float(net) if net else None
            gross = float(gross) if gross else None

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products_common (product_type, product_model, standard_sales_price, default_purchase_price)
                OUTPUT INSERTED.product_id
                VALUES (?, ?, ?, ?)
            """, (self.product_type, model, sale, purchase))
            pid = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO products_golf_accessory (product_id, quantity_per_count, material, net_weight, gross_weight)
                VALUES (?, ?, ?, ?, ?)
            """, (pid, count, material, net, gross))
            conn.commit()
            self.load_products()
            messagebox.showinfo("成功", f"已添加：\n型号：{model}\n每包数量：{count}\n材质：{material or ''}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的产品")
            return
        model = self.tree.item(selected[0])['values'][0]
        if not messagebox.askyesno("确认删除", f"确定删除产品：{model}？"):
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products_golf_accessory WHERE product_id = (SELECT product_id FROM products_common WHERE product_model = ?)", (model,))
            cursor.execute("DELETE FROM products_common WHERE product_model = ?", (model,))
            conn.commit()
            self.load_products()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def edit_product(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])['values']
        model = values[0]

        win = tk.Toplevel(self)
        win.title(f"编辑产品 - {model}")

        tk.Label(win, text="售价:").grid(row=0, column=0, padx=5, pady=5)
        ent_sale = tk.Entry(win)
        ent_sale.insert(0, values[1])
        ent_sale.grid(row=0, column=1)

        tk.Label(win, text="采购价:").grid(row=1, column=0, padx=5, pady=5)
        ent_purchase = tk.Entry(win)
        ent_purchase.insert(0, values[2])
        ent_purchase.grid(row=1, column=1)

        def save():
            try:
                sale = float(ent_sale.get())
                purchase = float(ent_purchase.get())
                cursor = get_cursor()
                cursor.execute("UPDATE products_common SET standard_sales_price = ?, default_purchase_price = ? WHERE product_model = ?",
                               (sale, purchase, model))
                cursor.connection.commit()
                win.destroy()
                self.load_products()
                messagebox.showinfo("成功", "产品已更新")
            except Exception as e:
                messagebox.showerror("错误", str(e))

        tk.Button(win, text="保存修改", command=save).grid(row=2, column=0, columnspan=2, pady=10)
