import tkinter as tk
from tkinter import ttk, messagebox
from database import get_cursor, get_connection

class ProductsTurfTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.product_type = 'Turf'

        # 搜索区域
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(search_frame, text="搜索型号:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="搜索", command=self.load_products).pack(side=tk.LEFT)

        # 表单
        form = ttk.LabelFrame(self, text="添加/修改 Turf 产品")
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

        tk.Label(form, text="FOB:").grid(row=1, column=2, padx=5, pady=2)
        self.ent_fob = tk.Entry(form)
        self.ent_fob.grid(row=1, column=3, padx=5, pady=2)

        tk.Label(form, text="草高:").grid(row=2, column=0, padx=5, pady=2)
        self.ent_pile = tk.Entry(form)
        self.ent_pile.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form, text="针数:").grid(row=2, column=2, padx=5, pady=2)
        self.ent_stitch = tk.Entry(form)
        self.ent_stitch.grid(row=2, column=3, padx=5, pady=2)

        tk.Label(form, text="行距:").grid(row=3, column=0, padx=5, pady=2)
        self.ent_gauge = tk.Entry(form)
        self.ent_gauge.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(form, text="行距分数:").grid(row=3, column=2, padx=5, pady=2)
        self.ent_gauge_frac = tk.Entry(form)
        self.ent_gauge_frac.grid(row=3, column=3, padx=5, pady=2)

        tk.Label(form, text="标准分特数:").grid(row=4, column=0, padx=5, pady=2)
        self.ent_sdtex = tk.Entry(form)
        self.ent_sdtex.grid(row=4, column=1, padx=5, pady=2)

        tk.Label(form, text="实际分特数:").grid(row=4, column=2, padx=5, pady=2)
        self.ent_dtex = tk.Entry(form)
        self.ent_dtex.grid(row=4, column=3, padx=5, pady=2)

        tk.Button(form, text="添加产品", command=self.add_product).grid(row=5, column=1, pady=5)
        tk.Button(form, text="删除选中", command=self.delete_product).grid(row=5, column=2, pady=5)
        tk.Button(form, text="刷新", command=self.load_products).grid(row=5, column=3, pady=5)

        # 表格
        self.tree = ttk.Treeview(
            self,
            columns=("型号", "售价", "采购价", "草高", "针数", "分特数", "Face Weight"),
            show='headings'
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.fill_form)
        self.tree.bind("<Double-1>", self.edit_product)

        self.load_products()

    def load_products(self):
        self.tree.delete(*self.tree.get_children())
        keyword = self.search_var.get().strip()
        cursor = get_cursor()
        if keyword:
            cursor.execute("""
                SELECT pc.product_model, pc.standard_sales_price, pc.default_purchase_price,
                       pt.pile_height, pt.stitch_rate, pt.dtex, pt.label_face_weight
                FROM products_common pc
                JOIN products_turf pt ON pc.product_id = pt.product_id
                WHERE pc.product_type = ? AND pc.product_model LIKE ?
            """, (self.product_type, f"%{keyword}%"))
        else:
            cursor.execute("""
                SELECT pc.product_model, pc.standard_sales_price, pc.default_purchase_price,
                       pt.pile_height, pt.stitch_rate, pt.dtex, pt.label_face_weight
                FROM products_common pc
                JOIN products_turf pt ON pc.product_id = pt.product_id
                WHERE pc.product_type = ?
            """, (self.product_type,))
        for row in cursor.fetchall():
            self.tree.insert('', tk.END, values=[str(r) if r is not None else '' for r in row])

    def add_product(self):
        try:
            required_fields = [
                (self.ent_model.get(), "型号"),
                # (self.ent_sale.get(), "售价"),
                (self.ent_purchase.get(), "采购价"),
                (self.ent_fob.get(), "FOB 价格"),
                (self.ent_pile.get(), "草高"),
                (self.ent_stitch.get(), "针数"),
                (self.ent_gauge.get(), "行距"),
                (self.ent_gauge_frac.get(), "行距分数"),
                (self.ent_sdtex.get(), "标准分特数"),
                (self.ent_dtex.get(), "实际分特数")
            ]
            for val, name in required_fields:
                if not val.strip():
                    messagebox.showwarning("必填项", f"请填写 {name}")
                    return

            model = self.ent_model.get().strip()
            sale = self.ent_sale.get()
            purchase = self.ent_purchase.get()
            fob = self.ent_fob.get()
            pile = self.ent_pile.get()
            stitch = self.ent_stitch.get()
            gauge = self.ent_gauge.get()
            gauge_frac = self.ent_gauge_frac.get().strip() or None
            sdtex = self.ent_sdtex.get()
            dtex = self.ent_dtex.get()

            if not model:
                raise ValueError("型号不能为空")

            sale = float(sale) if sale else None
            purchase = float(purchase) if purchase else None
            fob = float(fob) if fob else None
            pile = float(pile) if pile else None
            stitch = float(stitch) if stitch else None
            gauge = float(gauge) if gauge else None
            sdtex = int(sdtex) if sdtex else None
            dtex = int(dtex) if dtex else None

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products_common (product_type, product_model, standard_sales_price, default_purchase_price)
                OUTPUT INSERTED.product_id
                VALUES ('Turf', ?, ?, ?)
            """, (model, sale, purchase))
            row = cursor.fetchone()
            if not row:
                raise Exception("插入失败，未返回ID")
            pid = row[0]

            cursor.execute("""
                INSERT INTO products_turf (
                    product_id, fob_price, pile_height, stitch_rate, machine_gauge, machine_gauge_fraction, standard_dtex, dtex)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, fob, pile, stitch, gauge, gauge_frac, sdtex, dtex))
            conn.commit()
            self.load_products()
            messagebox.showinfo("成功", f"添加成功：\n型号：{model}\n售价：{sale}\n采购价：{purchase}\nFOB：{fob}\n草高：{pile}\n针数：{stitch}\n行距：{gauge}\n行距分数：{gauge_frac}\n标准分特数：{sdtex}\n实际分特数：{dtex}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def fill_form(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])['values']
        self.ent_model.delete(0, tk.END)
        self.ent_model.insert(0, values[0])
        self.ent_sale.delete(0, tk.END)
        self.ent_sale.insert(0, values[1])
        self.ent_purchase.delete(0, tk.END)
        self.ent_purchase.insert(0, values[2])
        self.ent_pile.delete(0, tk.END)
        self.ent_pile.insert(0, values[3])

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
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE products_common SET standard_sales_price=?, default_purchase_price=? WHERE product_model=?",
                               (sale, purchase, model))
                conn.commit()
                self.load_products()
                win.destroy()
                messagebox.showinfo("成功", "产品已更新")
            except Exception as e:
                messagebox.showerror("错误", str(e))

        tk.Button(win, text="保存修改", command=save).grid(row=2, column=0, columnspan=2, pady=10)

    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的产品")
            return

        model = self.tree.item(selected[0])['values'][0]
        if not messagebox.askyesno("确认删除", f"是否确认删除产品：{model}？"):
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products_turf WHERE product_id = (SELECT product_id FROM products_common WHERE product_model = ?)", (model,))
            cursor.execute("DELETE FROM products_common WHERE product_model = ?", (model,))
            conn.commit()
            self.load_products()
        except Exception as e:
            messagebox.showerror("错误", str(e))
