# main.py
import tkinter as tk
from tkinter import ttk
from pages.products import ProductsPage
from pages.orders import OrdersPage
from pages.inventory import InventoryPage
from pages.returns import ReturnsPage
from pages.purchases import PurchasesPage


root = tk.Tk()

root.title("TurfManagement 管理系统")
root.geometry("800x600")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

products_tab = ProductsPage(notebook)
orders_tab = OrdersPage(notebook)
inventory_tab = InventoryPage(notebook)
returns_tab = ReturnsPage(notebook)
purchases_tab = PurchasesPage(notebook)

notebook.add(products_tab, text='产品查询')
notebook.add(orders_tab, text='订单管理')
notebook.add(inventory_tab, text='库存管理')
notebook.add(returns_tab, text='退货管理')
notebook.add(purchases_tab, text="采购管理")

root.mainloop()