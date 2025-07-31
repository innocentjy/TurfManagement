import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection, get_cursor

class InventoryPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.product_map = {}  # 型号 -> (product_id, product_type)
        self.warehouse_map = {}  # 名称 -> warehouse_id

        # 搜索栏
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(search_frame, text="仓库筛选:").pack(side=tk.LEFT)
        self.cmb_warehouse_filter = ttk.Combobox(search_frame, state="readonly")
        self.cmb_warehouse_filter.pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="产品筛选:").pack(side=tk.LEFT)
        self.cmb_product_filter = ttk.Combobox(search_frame)
        self.cmb_product_filter.pack(side=tk.LEFT, padx=5)
        self.cmb_product_filter.bind("<KeyRelease>", self.filter_product_options)

        self.var_non_standard = tk.IntVar()
        tk.Checkbutton(search_frame, text="仅显示非标准件", variable=self.var_non_standard).pack(side=tk.LEFT, padx=5)

        tk.Button(search_frame, text="筛选", command=self.load_inventory).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="删除选中", command=self.delete_selected).pack(side=tk.LEFT, padx=5)

        # 表格
        self.tree = ttk.Treeview(self, columns=("产品型号", "仓库", "幅宽", "长度", "库存(卷)", "是否标准件", "面积"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self.on_double_click)

        # 添加表单
        form = ttk.LabelFrame(self, text="新增库存记录")
        form.pack(fill='x', padx=10, pady=5)

        tk.Label(form, text="产品型号:").grid(row=0, column=0, padx=5, pady=2)
        self.cmb_product = ttk.Combobox(form)
        self.cmb_product.grid(row=0, column=1, padx=5, pady=2)
        self.cmb_product.bind("<KeyRelease>", self.filter_product_entry)

        tk.Label(form, text="仓库:").grid(row=0, column=2, padx=5, pady=2)
        self.cmb_warehouse = ttk.Combobox(form, state="readonly")
        self.cmb_warehouse.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(form, text="幅宽(ft):").grid(row=1, column=0, padx=5, pady=2)
        self.ent_width = tk.Entry(form)
        self.ent_width.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form, text="长度(ft):").grid(row=1, column=2, padx=5, pady=2)
        self.ent_length = tk.Entry(form)
        self.ent_length.grid(row=1, column=3, padx=5, pady=2)

        tk.Label(form, text="库存数量").grid(row=2, column=0, padx=5, pady=2)
        self.ent_stock = tk.Entry(form)
        self.ent_stock.grid(row=2, column=1, padx=5, pady=2)

        self.var_standard = tk.IntVar(value=1)
        self.chk_standard = tk.Checkbutton(form, text="是否标准件", variable=self.var_standard)
        self.chk_standard.grid(row=2, column=2, padx=5, pady=2)

        tk.Button(form, text="添加库存", command=self.add_inventory).grid(row=3, column=1, columnspan=2, pady=5)

        self.load_products()
        self.load_warehouses()
        self.load_inventory()

    def filter_product_options(self, event=None):
        input_text = self.cmb_product_filter.get()
        filtered = [k for k in self.product_map.keys() if input_text.lower() in k.lower()]
        self.cmb_product_filter['values'] = filtered

    def filter_product_entry(self, event=None):
        input_text = self.cmb_product.get()
        filtered = [k for k in self.product_map.keys() if input_text.lower() in k.lower()]
        self.cmb_product['values'] = filtered

    def on_product_select(self, event=None):
        model = self.cmb_product.get()
        if model not in self.product_map:
            return
        _, ptype = self.product_map[model]
        show = (ptype == 'Turf')
        state = 'normal' if show else 'disabled'
        self.ent_width.configure(state=state)
        self.ent_length.configure(state=state)
        self.chk_standard.configure(state=state)

    def load_products(self):
        cursor = get_cursor()
        cursor.execute("SELECT product_id, product_model, product_type FROM products_common")
        rows = cursor.fetchall()
        self.product_map = {name: (pid, ptype) for pid, name, ptype in rows}
        product_names = list(self.product_map.keys())
        self.cmb_product_filter['values'] = ["全部"] + product_names
        self.cmb_product_filter.set("全部")
        self.cmb_product['values'] = product_names

    def load_warehouses(self):
        cursor = get_cursor()
        cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses")
        rows = cursor.fetchall()
        self.warehouse_map = {name: wid for wid, name in rows}
        names = list(self.warehouse_map.keys())
        self.cmb_warehouse['values'] = names
        self.cmb_warehouse_filter['values'] = ["全部"] + names
        self.cmb_warehouse_filter.set("全部")

    def load_inventory(self):
        self.tree.delete(*self.tree.get_children())
        filter_wh_name = self.cmb_warehouse_filter.get()
        filter_product = self.cmb_product_filter.get()
        only_non_standard = self.var_non_standard.get()

        query = """
            SELECT i.inventory_id, p.product_model, w.warehouse_name, i.feet_width, i.feet_length, i.stock_level, i.is_standard, ROUND(i.area, 0)
            FROM inventory i
            JOIN products_common p ON i.product_id = p.product_id
            JOIN warehouses w ON i.warehouse_id = w.warehouse_id
            WHERE 1=1
        """
        params = []

        if filter_wh_name and filter_wh_name != "全部":
            query += " AND w.warehouse_name = ?"
            params.append(filter_wh_name)

        if filter_product and filter_product != "全部":
            query += " AND p.product_model = ?"
            params.append(filter_product)

        if only_non_standard:
            query += " AND i.is_standard = 0"

        cursor = get_cursor()
        cursor.execute(query, params)
        for row in cursor.fetchall():
            _, model, warehouse, width, length, stock, is_std, area = row
            self.tree.insert('', tk.END, values=(model, warehouse, width, length, stock, "是" if is_std else "否", int(area) if area else 0))

    def add_inventory(self):
        try:
            model = self.cmb_product.get()
            warehouse_name = self.cmb_warehouse.get()
            stock = int(self.ent_stock.get())

            if model not in self.product_map or warehouse_name not in self.warehouse_map:
                raise ValueError("产品或仓库选择无效")

            product_id, ptype = self.product_map[model]
            warehouse_id = self.warehouse_map[warehouse_name]

            width = length = is_std = None
            if ptype == 'Turf':
                width = float(self.ent_width.get())
                length = float(self.ent_length.get())
                is_std = self.var_standard.get()

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inventory (product_id, warehouse_id, feet_width, feet_length, stock_level, is_standard)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, warehouse_id, width, length, stock, is_std))
            conn.commit()
            self.load_inventory()
            messagebox.showinfo("成功", "库存记录已添加")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的记录")
            return
        item = self.tree.item(selected[0])
        model = item['values'][0]
        warehouse = item['values'][1]
        if not messagebox.askyesno("确认删除", f"确定删除 {model} @ {warehouse} 这条库存记录？"):
            return
        try:
            cursor = get_cursor()
            cursor.execute("""
                DELETE FROM inventory WHERE inventory_id = (
                    SELECT TOP 1 inventory_id FROM inventory i
                    JOIN products_common p ON i.product_id = p.product_id
                    JOIN warehouses w ON i.warehouse_id = w.warehouse_id
                    WHERE p.product_model = ? AND w.warehouse_name = ?
                )
            """, (model, warehouse))
            cursor.connection.commit()
            self.load_inventory()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])['values']
        model = values[0]
        warehouse = values[1]

        cursor = get_cursor()
        cursor.execute("SELECT product_type FROM products_common WHERE product_model = ?", (model,))
        row = cursor.fetchone()
        if not row:
            return
        product_type = row[0]

        edit_win = tk.Toplevel(self)
        edit_win.title("编辑库存")

        tk.Label(edit_win, text="库存数量").grid(row=0, column=0, padx=5, pady=5)
        ent_stock = tk.Entry(edit_win)
        ent_stock.insert(0, values[4])
        ent_stock.grid(row=0, column=1)

        if product_type == 'Turf':
            tk.Label(edit_win, text="幅宽(ft)").grid(row=1, column=0, padx=5, pady=5)
            ent_width = tk.Entry(edit_win)
            ent_width.insert(0, values[2])
            ent_width.grid(row=1, column=1)

            tk.Label(edit_win, text="长度(ft)").grid(row=2, column=0, padx=5, pady=5)
            ent_length = tk.Entry(edit_win)
            ent_length.insert(0, values[3])
            ent_length.grid(row=2, column=1)

            var_std = tk.IntVar(value=1 if values[5] == "是" else 0)
            tk.Checkbutton(edit_win, text="标准件", variable=var_std).grid(row=3, column=0, columnspan=2)

        def save():
            try:
                stock = int(ent_stock.get())
                width = length = is_std = None
                change_info = f"库存: {stock}"
                if product_type == 'Turf':
                    width = float(ent_width.get())
                    length = float(ent_length.get())
                    is_std = var_std.get()
                    change_info = f"幅宽: {width}, 长度: {length}, 库存: {stock}, 是否标准件: {'是' if is_std else '否'}"
                if not messagebox.askyesno("确认修改", f"以下内容将被保存：\n{change_info}\n是否确认？"):
                    return

                cursor.execute("""
                    UPDATE inventory
                    SET feet_width = ?, feet_length = ?, stock_level = ?, is_standard = ?, last_updated = GETDATE()
                    WHERE inventory_id = (
                        SELECT TOP 1 inventory_id FROM inventory i
                        JOIN products_common p ON i.product_id = p.product_id
                        JOIN warehouses w ON i.warehouse_id = w.warehouse_id
                        WHERE p.product_model = ? AND w.warehouse_name = ?
                    )
                """, (width, length, stock, is_std, model, warehouse))
                cursor.connection.commit()
                edit_win.destroy()
                self.load_inventory()
                messagebox.showinfo("成功", "库存记录已更新")
            except Exception as e:
                messagebox.showerror("错误", str(e))

        tk.Button(edit_win, text="保存", command=save).grid(row=4, column=0, columnspan=2, pady=10)

