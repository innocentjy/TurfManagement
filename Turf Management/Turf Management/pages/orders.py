import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_cursor, get_connection
import csv

class OrdersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.selected_order_id = None
        self.search_var = tk.StringVar()
        self.status_filter = tk.StringVar(value="全部")
        self.client_filter = tk.StringVar()
        self.warehouse_filter = tk.StringVar()

        # 搜索与导出区域
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', pady=5)

        tk.Label(search_frame, text="订单日期包含:").pack(side=tk.LEFT, padx=5)
        tk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="客户:").pack(side=tk.LEFT, padx=5)
        self.cmb_client = ttk.Combobox(search_frame, textvariable=self.client_filter, state="readonly")
        self.cmb_client.pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="仓库:").pack(side=tk.LEFT, padx=5)
        self.cmb_warehouse = ttk.Combobox(search_frame, textvariable=self.warehouse_filter, state="readonly")
        self.cmb_warehouse.pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="订单状态:").pack(side=tk.LEFT, padx=5)
        self.cmb_status = ttk.Combobox(search_frame, textvariable=self.status_filter, state="readonly",
                                        values=["全部", "Preparing", "Delivering", "Delivered", "Paid"])
        self.cmb_status.pack(side=tk.LEFT, padx=5)

        ttk.Button(search_frame, text="搜索", command=self.load_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="导出Excel", command=self.export_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="添加订单", command=self.add_order_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="修改订单", command=self.edit_order_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="删除订单", command=self.delete_order).pack(side=tk.LEFT, padx=5)

        # 订单列表
        self.tree_orders = ttk.Treeview(self, columns=(
            "订单编号", "客户名称", "仓库名称", "订单日期", "状态",
            "计划送达", "实际送达", "送货方式", "地址", "距离"
        ), show='headings')
        for col in self.tree_orders["columns"]:
            self.tree_orders.heading(col, text=col)
        self.tree_orders.pack(fill='both', expand=True, padx=10, pady=5)
        self.tree_orders.bind("<<TreeviewSelect>>", self.on_order_select)

        # 订单明细
        self.tree_items = ttk.Treeview(self, columns=(
            "产品ID", "产品型号", "宽度(ft)", "长度(ft)", "数量", "单价", "总价"
        ), show='headings')
        for col in self.tree_items["columns"]:
            self.tree_items.heading(col, text=col)
        self.tree_items.pack(fill='both', expand=True, padx=10, pady=5)
        self.load_filters()
        self.tree_items.bind("<Delete>", self.delete_order_item)

        self.load_orders()


    def load_filters(self):
        cursor = get_cursor()

        cursor.execute("SELECT DISTINCT client_name FROM clients ORDER BY client_name")
        clients = [row[0] for row in cursor.fetchall()]
        self.cmb_client['values'] = ["全部"] + clients
        self.cmb_client.set("全部")

        cursor.execute("SELECT DISTINCT warehouse_name FROM warehouses ORDER BY warehouse_name")
        warehouses = [row[0] for row in cursor.fetchall()]
        self.cmb_warehouse['values'] = ["全部"] + warehouses
        self.cmb_warehouse.set("全部")

    def load_orders(self):
        self.tree_orders.delete(*self.tree_orders.get_children())
        keyword = self.search_var.get().strip()
        status = self.status_filter.get()
        client = self.client_filter.get()
        warehouse = self.warehouse_filter.get()

        query = """
            SELECT o.order_id, o.order_number, c.client_name, w.warehouse_name, o.order_date,
                   o.order_status, o.original_delivery_date, o.actual_delivery_date,
                   o.delivery_type, o.delivery_address, o.distance_from_warehouse
            FROM orders o
            JOIN clients c ON o.client_id = c.client_id
            JOIN warehouses w ON o.warehouse_id = w.warehouse_id
            WHERE 1=1
        """
        params = []
        if keyword:
            query += " AND o.order_date LIKE ?"
            params.append(f"%{keyword}%")
        if client and client != "全部":
            query += " AND c.client_name = ?"
            params.append(client)
        if warehouse and warehouse != "全部":
            query += " AND w.warehouse_name = ?"
            params.append(warehouse)
        if status and status != "全部":
            query += " AND o.order_status = ?"
            params.append(status)

        cursor = get_cursor()
        cursor.execute(query, params)
        for row in cursor.fetchall():
            clean_row = [str(r) if r is not None else '' for r in row[1:]]  # skip order_id
            self.tree_orders.insert('', tk.END, values=clean_row, tags=(str(row[0]),))

    def on_order_select(self, event):
        selected = self.tree_orders.selection()
        if not selected:
            return
        self.selected_order_id = int(self.tree_orders.item(selected[0])['tags'][0])

        self.tree_items.delete(*self.tree_items.get_children())
        cursor = get_cursor()
        cursor.execute("""
            SELECT i.product_id, p.product_model, i.feet_width, i.feet_length,
                   i.quantity, i.unit_sale_price, i.total_sale_price
            FROM order_items i
            JOIN products_common p ON i.product_id = p.product_id
            WHERE i.order_id = ?
        """, (self.selected_order_id,))
        for row in cursor.fetchall():
            clean_row = [str(r) if r is not None else '' for r in row]
            self.tree_items.insert('', tk.END, values=clean_row)

    def export_orders(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if not file:
            return
        with open(file, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["订单编号", "客户名称", "仓库名称", "订单日期", "状态",
                             "计划送达", "实际送达", "送货方式", "地址", "距离"])
            for child in self.tree_orders.get_children():
                writer.writerow(self.tree_orders.item(child)['values'])
        messagebox.showinfo("导出成功", f"已导出到 {file}")

    def delete_order(self):
        selected = self.tree_orders.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的订单")
            return

        order_id = int(self.tree_orders.item(selected[0])['tags'][0])
        values = self.tree_orders.item(selected[0])['values']
        if not messagebox.askyesno("确认删除", f"是否删除订单: {values[0]}, 客户: {values[1]}, 状态: {values[4]}？"):
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
            conn.commit()
            self.load_orders()
            self.tree_items.delete(*self.tree_items.get_children())
            messagebox.showinfo("成功", "订单已删除")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_order_item(self, event):
        selected = self.tree_items.selection()
        if not selected:
            return
        values = self.tree_items.item(selected[0])['values']
        if not messagebox.askyesno("确认删除", f"是否删除该订单明细（产品: {values[1]}, 数量: {values[4]}）？"):
            return
        try:
            cursor = get_cursor()
            cursor.execute("""
                DELETE FROM order_items
                WHERE order_id = ? AND product_id = ?
            """, (self.selected_order_id, values[0]))
            cursor.connection.commit()
            self.on_order_select(None)
            messagebox.showinfo("成功", "订单明细已删除")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def add_order_dialog(self):
        from .order_dialog import show_order_dialog
        show_order_dialog(self, mode="add")

    def edit_order_dialog(self):
        selected = self.tree_orders.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的订单")
            return
        order_id = int(self.tree_orders.item(selected[0])['tags'][0])
        from .order_dialog import show_order_dialog
        show_order_dialog(self, mode="edit", order_id=order_id)
