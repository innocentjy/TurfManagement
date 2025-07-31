import tkinter as tk
from tkinter import ttk, messagebox
from database import get_cursor, get_connection

class OrderDialog(tk.Toplevel):
    def __init__(self, parent, mode="add", order_id=None):
        super().__init__(parent)
        self.title("添加订单" if mode == "add" else "修改订单")
        self.mode = mode
        self.order_id = order_id
        self.items = []  # 暂存订单明细

        self.client_var = tk.StringVar()
        self.warehouse_var = tk.StringVar()
        self.order_date_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.delivery_type_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.distance_var = tk.StringVar()
        self.original_date_var = tk.StringVar()
        self.actual_date_var = tk.StringVar()

        self.setup_ui()
        if mode == "edit":
            self.load_order()

    def setup_ui(self):
        frame = ttk.LabelFrame(self, text="订单头")
        frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(frame, text="客户:").grid(row=0, column=0, padx=5, pady=2)
        self.cmb_client = ttk.Combobox(frame, textvariable=self.client_var, state="readonly")
        self.cmb_client.grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="仓库:").grid(row=0, column=2, padx=5)
        self.cmb_warehouse = ttk.Combobox(frame, textvariable=self.warehouse_var, state="readonly")
        self.cmb_warehouse.grid(row=0, column=3, padx=5)

        ttk.Label(frame, text="订单日期:").grid(row=1, column=0, padx=5)
        ttk.Entry(frame, textvariable=self.order_date_var).grid(row=1, column=1, padx=5)

        ttk.Label(frame, text="状态:").grid(row=1, column=2, padx=5)
        self.cmb_status = ttk.Combobox(frame, textvariable=self.status_var, values=["Preparing", "Delivering", "Delivered", "Paid"], state="readonly")
        self.cmb_status.grid(row=1, column=3, padx=5)

        ttk.Label(frame, text="送货方式:").grid(row=2, column=0, padx=5)
        ttk.Entry(frame, textvariable=self.delivery_type_var).grid(row=2, column=1, padx=5)

        ttk.Label(frame, text="地址:").grid(row=2, column=2, padx=5)
        ttk.Entry(frame, textvariable=self.address_var, width=30).grid(row=2, column=3, padx=5)

        ttk.Label(frame, text="距离:").grid(row=3, column=0, padx=5)
        ttk.Entry(frame, textvariable=self.distance_var).grid(row=3, column=1, padx=5)

        ttk.Label(frame, text="计划送达:").grid(row=3, column=2, padx=5)
        ttk.Entry(frame, textvariable=self.original_date_var).grid(row=3, column=3, padx=5)

        ttk.Label(frame, text="实际送达:").grid(row=4, column=0, padx=5)
        ttk.Entry(frame, textvariable=self.actual_date_var).grid(row=4, column=1, padx=5)

        # 明细部分
        detail_frame = ttk.LabelFrame(self, text="订单明细")
        detail_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(detail_frame, columns=("产品型号", "宽度", "长度", "数量", "单价"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True)

        btns = ttk.Frame(self)
        btns.pack(fill='x', pady=5)
        ttk.Button(btns, text="添加明细", command=self.add_item_dialog).pack(side=tk.LEFT, padx=10)
        ttk.Button(btns, text="保存订单", command=self.save_order).pack(side=tk.RIGHT, padx=10)

        self.load_clients_and_warehouses()

    def load_clients_and_warehouses(self):
        cursor = get_cursor()
        cursor.execute("SELECT client_name FROM clients")
        self.cmb_client['values'] = [r[0] for r in cursor.fetchall()]

        cursor.execute("SELECT warehouse_name FROM warehouses")
        self.cmb_warehouse['values'] = [r[0] for r in cursor.fetchall()]

    def load_order(self):
        cursor = get_cursor()
        cursor.execute("""
            SELECT c.client_name, w.warehouse_name, o.order_date, o.order_status,
                   o.delivery_type, o.delivery_address, o.distance_from_warehouse,
                   o.original_delivery_date, o.actual_delivery_date
            FROM orders o
            JOIN clients c ON o.client_id = c.client_id
            JOIN warehouses w ON o.warehouse_id = w.warehouse_id
            WHERE o.order_id = ?
        """, (self.order_id,))
        row = cursor.fetchone()
        if row:
            self.client_var.set(row[0])
            self.warehouse_var.set(row[1])
            self.order_date_var.set(row[2])
            self.status_var.set(row[3])
            self.delivery_type_var.set(row[4])
            self.address_var.set(row[5])
            self.distance_var.set(row[6])
            self.original_date_var.set(row[7])
            self.actual_date_var.set(row[8])

        cursor.execute("""
            SELECT p.product_model, i.feet_width, i.feet_length,
                   i.quantity, i.unit_sale_price
            FROM order_items i
            JOIN products_common p ON i.product_id = p.product_id
            WHERE i.order_id = ?
        """, (self.order_id,))
        for row in cursor.fetchall():
            self.items.append(row)
            self.tree.insert('', tk.END, values=[str(r) if r is not None else '' for r in row])

    def add_item_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("添加明细")

        model_var = tk.StringVar()
        width_var = tk.StringVar()
        length_var = tk.StringVar()
        qty_var = tk.StringVar()
        price_var = tk.StringVar()

        cursor = get_cursor()
        cursor.execute("SELECT product_model FROM products_common")
        models = [r[0] for r in cursor.fetchall()]

        ttk.Label(dialog, text="产品型号:").grid(row=0, column=0)
        cmb_model = ttk.Combobox(dialog, textvariable=model_var, values=models)
        cmb_model.grid(row=0, column=1)

        ttk.Label(dialog, text="宽度(ft):").grid(row=1, column=0)
        ttk.Entry(dialog, textvariable=width_var).grid(row=1, column=1)

        ttk.Label(dialog, text="长度(ft):").grid(row=2, column=0)
        ttk.Entry(dialog, textvariable=length_var).grid(row=2, column=1)

        ttk.Label(dialog, text="数量:").grid(row=3, column=0)
        ttk.Entry(dialog, textvariable=qty_var).grid(row=3, column=1)

        ttk.Label(dialog, text="单价:").grid(row=4, column=0)
        ttk.Entry(dialog, textvariable=price_var).grid(row=4, column=1)

        def confirm():
            row = (model_var.get(), width_var.get(), length_var.get(), qty_var.get(), price_var.get())
            self.items.append(row)
            self.tree.insert('', tk.END, values=row)
            dialog.destroy()

        ttk.Button(dialog, text="确定", command=confirm).grid(row=5, columnspan=2, pady=5)

    def save_order(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 获取 client_id 和 warehouse_id
            cursor.execute("SELECT client_id FROM clients WHERE client_name = ?", (self.client_var.get(),))
            client_id = cursor.fetchone()[0]
            cursor.execute("SELECT warehouse_id FROM warehouses WHERE warehouse_name = ?", (self.warehouse_var.get(),))
            warehouse_id = cursor.fetchone()[0]

            if self.mode == "add":
                cursor.execute("""
                    INSERT INTO orders (order_number, client_id, warehouse_id, order_date, order_status,
                        delivery_type, delivery_address, distance_from_warehouse,
                        original_delivery_date, actual_delivery_date, updated_date)
                    VALUES (CONVERT(varchar(20), GETDATE(), 112) + RIGHT('000' + CAST(ABS(CHECKSUM(NEWID())) % 1000 AS VARCHAR), 3), ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    client_id, warehouse_id, self.order_date_var.get(), self.status_var.get(),
                    self.delivery_type_var.get(), self.address_var.get(), self.distance_var.get(),
                    self.original_date_var.get(), self.actual_date_var.get()
                ))
                cursor.execute("SELECT SCOPE_IDENTITY()")
                order_id = int(cursor.fetchone()[0])
            else:
                order_id = self.order_id
                cursor.execute("""
                    UPDATE orders SET client_id=?, warehouse_id=?, order_date=?, order_status=?,
                        delivery_type=?, delivery_address=?, distance_from_warehouse=?,
                        original_delivery_date=?, actual_delivery_date=?, updated_date=GETDATE()
                    WHERE order_id=?
                """, (
                    client_id, warehouse_id, self.order_date_var.get(), self.status_var.get(),
                    self.delivery_type_var.get(), self.address_var.get(), self.distance_var.get(),
                    self.original_date_var.get(), self.actual_date_var.get(), order_id
                ))
                cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))

            for item in self.items:
                cursor.execute("SELECT product_id FROM products_common WHERE product_model = ?", (item[0],))
                product_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, feet_width, feet_length,
                                             quantity, unit_sale_price, total_sale_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id, product_id, float(item[1]), float(item[2]), int(item[3]), float(item[4]),
                    float(item[3]) * float(item[4])
                ))

            conn.commit()
            self.destroy()
            messagebox.showinfo("成功", "订单已保存")
            self.master.load_orders()
        except Exception as e:
            messagebox.showerror("错误", str(e))


def show_order_dialog(parent, mode="add", order_id=None):
    OrderDialog(parent, mode=mode, order_id=order_id)
