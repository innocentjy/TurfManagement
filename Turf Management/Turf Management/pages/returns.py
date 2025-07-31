import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_cursor, get_connection
import csv
from datetime import datetime

class ReturnsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.selected_return_id = None
        self.client_map = {}

        filter_frame = ttk.LabelFrame(self, text="退货记录筛选")
        filter_frame.pack(fill='x', pady=5)

        tk.Label(filter_frame, text="客户名:").pack(side=tk.LEFT, padx=5)
        self.search_client = tk.Entry(filter_frame)
        self.search_client.pack(side=tk.LEFT)

        tk.Label(filter_frame, text="开始日期:").pack(side=tk.LEFT, padx=5)
        self.start_date = tk.Entry(filter_frame)
        self.start_date.pack(side=tk.LEFT)

        tk.Label(filter_frame, text="结束日期:").pack(side=tk.LEFT, padx=5)
        self.end_date = tk.Entry(filter_frame)
        self.end_date.pack(side=tk.LEFT)

        tk.Button(filter_frame, text="搜索", command=self.load_returns).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="导出CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)

        head_form = ttk.LabelFrame(self, text="创建退货单")
        head_form.pack(fill='x', pady=5)

        tk.Label(head_form, text="客户:").grid(row=0, column=0, padx=5)
        self.cmb_client = ttk.Combobox(head_form, state="readonly")
        self.cmb_client.grid(row=0, column=1, padx=5)

        tk.Label(head_form, text="仓库ID:").grid(row=0, column=2, padx=5)
        self.entry_wh = tk.Entry(head_form)
        self.entry_wh.grid(row=0, column=3, padx=5)

        tk.Label(head_form, text="经办人:").grid(row=0, column=4, padx=5)
        self.entry_user = tk.Entry(head_form)
        self.entry_user.grid(row=0, column=5, padx=5)

        tk.Button(head_form, text="创建退货单", command=self.create_return_head).grid(row=0, column=6, padx=5)

        top = ttk.Frame(self)
        top.pack(fill='x', pady=5)

        tk.Label(top, text="退货ID:").pack(side=tk.LEFT, padx=5)
        self.cmb_returns = ttk.Combobox(top, state="readonly")
        self.cmb_returns.pack(side=tk.LEFT)
        self.cmb_returns.bind("<<ComboboxSelected>>", lambda e: self.load_return_items())
        tk.Button(top, text="删除退货单", command=self.delete_return_head).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="刷新退货列表", command=self.load_returns).pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(self, columns=("退货明细ID", "产品型号", "数量", "单价", "小计"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True, pady=5)
        self.tree.bind("<Double-1>", self.edit_return_item)

        form = ttk.LabelFrame(self, text="添加退货明细")
        form.pack(fill='x', pady=5)

        self.cmb_product = ttk.Combobox(form, state="readonly")
        self.ent_qty = tk.Entry(form)
        self.ent_price = tk.Entry(form)

        ttk.Label(form, text="产品型号").grid(row=0, column=0, padx=5)
        self.cmb_product.grid(row=0, column=1, padx=5)
        ttk.Label(form, text="数量").grid(row=0, column=2, padx=5)
        self.ent_qty.grid(row=0, column=3, padx=5)
        ttk.Label(form, text="单价").grid(row=0, column=4, padx=5)
        self.ent_price.grid(row=0, column=5, padx=5)
        tk.Button(form, text="添加明细", command=self.add_return_item).grid(row=0, column=6, padx=10)
        tk.Button(form, text="删除选中明细", command=self.delete_return_item).grid(row=0, column=7, padx=5)

        self.load_clients()
        self.load_products()
        self.load_returns()

    def load_clients(self):
        cursor = get_cursor()
        cursor.execute("SELECT client_id, client_name FROM clients")
        self.client_map = {name: cid for cid, name in cursor.fetchall()}
        self.cmb_client['values'] = list(self.client_map.keys())

    def load_returns(self):
        self.tree.delete(*self.tree.get_children())
        cursor = get_cursor()
        query = "SELECT return_id FROM returns r JOIN clients c ON r.client_id = c.client_id WHERE 1=1"
        params = []
        if self.search_client.get():
            query += " AND c.client_name LIKE ?"
            params.append(f"%{self.search_client.get()}%")
        if self.start_date.get():
            query += " AND r.return_date >= ?"
            params.append(self.start_date.get())
        if self.end_date.get():
            query += " AND r.return_date <= ?"
            params.append(self.end_date.get())
        cursor.execute(query, params)
        ids = [str(r[0]) for r in cursor.fetchall()]
        self.cmb_returns['values'] = ids
        if ids:
            self.cmb_returns.set(ids[0])
            self.load_return_items()

    def load_products(self):
        cursor = get_cursor()
        cursor.execute("SELECT product_model FROM products_common")
        self.cmb_product['values'] = [r[0] for r in cursor.fetchall()]

    def create_return_head(self):
        client_name = self.cmb_client.get()
        if client_name not in self.client_map:
            messagebox.showwarning("错误", "请选择有效客户")
            return
        try:
            cursor = get_cursor()
            conn = get_connection()
            cursor.execute("""
                INSERT INTO returns (client_id, warehouse_id, return_date, reason, handled_by)
                VALUES (?, ?, GETDATE(), '', ?)
            """, (self.client_map[client_name], self.entry_wh.get(), self.entry_user.get()))
            conn.commit()
            self.load_returns()
            messagebox.showinfo("成功", "退货单已创建")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def load_return_items(self):
        self.tree.delete(*self.tree.get_children())
        if not self.cmb_returns.get():
            return
        return_id = int(self.cmb_returns.get())
        self.selected_return_id = return_id
        cursor = get_cursor()
        cursor.execute("""
            SELECT ri.return_item_id, p.product_model, ri.quantity, ri.unit_return_price, ri.total_return_price
            FROM return_items ri
            JOIN products_common p ON ri.product_id = p.product_id
            WHERE ri.return_id = ?
        """, return_id)
        for row in cursor.fetchall():
            self.tree.insert('', tk.END, values=row)

    def add_return_item(self):
        if not self.selected_return_id:
            messagebox.showwarning("提示", "请先选择退货记录")
            return
        try:
            product_model = self.cmb_product.get()
            cursor = get_cursor()
            cursor.execute("SELECT product_id FROM products_common WHERE product_model = ?", product_model)
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("错误", "未找到产品")
                return
            product_id = row[0]
            qty = int(self.ent_qty.get())
            price = float(self.ent_price.get())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO return_items (return_id, order_item_id, product_id, quantity, unit_return_price)
                VALUES (?, NULL, ?, ?, ?)
            """, (self.selected_return_id, product_id, qty, price))
            conn.commit()
            self.load_return_items()
            messagebox.showinfo("成功", "退货明细添加成功")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def edit_return_item(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])['values']
        item_id = values[0]

        win = tk.Toplevel(self)
        win.title("编辑退货明细")

        tk.Label(win, text="数量:").grid(row=0, column=0, padx=5, pady=5)
        ent_qty = tk.Entry(win)
        ent_qty.insert(0, values[2])
        ent_qty.grid(row=0, column=1)

        tk.Label(win, text="单价:").grid(row=1, column=0, padx=5, pady=5)
        ent_price = tk.Entry(win)
        ent_price.insert(0, values[3])
        ent_price.grid(row=1, column=1)

        def save():
            try:
                qty = int(ent_qty.get())
                price = float(ent_price.get())
                cursor = get_cursor()
                cursor.execute("UPDATE return_items SET quantity = ?, unit_return_price = ? WHERE return_item_id = ?",
                               (qty, price, item_id))
                cursor.connection.commit()
                win.destroy()
                self.load_return_items()
                messagebox.showinfo("成功", "已更新退货明细")
            except Exception as e:
                messagebox.showerror("错误", str(e))

        tk.Button(win, text="保存修改", command=save).grid(row=2, column=0, columnspan=2, pady=10)

    def delete_return_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的明细")
            return
        item_id = self.tree.item(selected[0])['values'][0]
        try:
            cursor = get_cursor()
            cursor.execute("DELETE FROM return_items WHERE return_item_id = ?", item_id)
            cursor.connection.commit()
            self.load_return_items()
            messagebox.showinfo("成功", "已删除退货明细")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_return_head(self):
        if not self.cmb_returns.get():
            messagebox.showwarning("提示", "请先选择退货单")
            return
        if not messagebox.askyesno("确认", "确定要删除该退货单及所有明细吗？"):
            return
        try:
            return_id = int(self.cmb_returns.get())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM return_items WHERE return_id = ?", (return_id,))
            cursor.execute("DELETE FROM returns WHERE return_id = ?", (return_id,))
            conn.commit()
            self.selected_return_id = None
            self.cmb_returns.set('')
            self.load_returns()
            self.tree.delete(*self.tree.get_children())
            messagebox.showinfo("成功", "退货单及明细已删除")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if not file:
            return
        with open(file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["退货明细ID", "产品型号", "数量", "单价", "小计"])
            for row_id in self.tree.get_children():
                writer.writerow(self.tree.item(row_id)['values'])
        messagebox.showinfo("成功", f"退货明细已导出到 {file}")
