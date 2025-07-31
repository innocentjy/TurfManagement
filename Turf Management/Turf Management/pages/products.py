import tkinter as tk
from tkinter import ttk
from .products_turf import ProductsTurfTab
from .products_sand import ProductsSandTab
from .products_accessory import ProductsAccessoryTab

class ProductsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        turf_tab = ProductsTurfTab(notebook)
        sand_tab = ProductsSandTab(notebook)
        golf_tab = ProductsAccessoryTab(notebook)

        notebook.add(turf_tab, text="草坪产品")
        notebook.add(sand_tab, text="填充砂产品")
        notebook.add(golf_tab, text="高尔夫配件")