import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import Database
from login import UserManagement
from inventory_management import ProductManagement
from reports import Reports
import json
from datetime import datetime

class POSMain:
    def __init__(self, user):
        self.user = user
        self.db = Database()
        self.cart = []
        self.setup_ui()
        self.load_products()
        self.setup_keyboard_shortcuts()
    
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title(f"Sistema POS - Usuario: {self.user['nombre']}")
        self.root.state('zoomed')  # Maximizar ventana
        self.root.configure(bg='#ecf0f1')
        
        # Configurar grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Crear menú
        self.create_menu()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Panel izquierdo - Productos
        self.create_products_panel(main_frame)
        
        # Panel derecho - Carrito y facturación
        self.create_cart_panel(main_frame)
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nueva Venta", command=self.new_sale, accelerator="Ctrl+N")
        file_menu.add_command(label="Imprimir Factura", command=self.print_invoice, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Menú Productos
        products_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Productos", menu=products_menu)
        products_menu.add_command(label="Gestión de Productos", command=self.manage_products, accelerator="F2")
        products_menu.add_command(label="Gestión de Inventario", command=self.manage_inventory, accelerator="F3")
        
        # Menú Usuarios (solo para admin)
        if self.user['rol'] == 'admin':
            users_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Usuarios", menu=users_menu)
            users_menu.add_command(label="Gestión de Usuarios", command=self.manage_users, accelerator="F4")
        
        # Menú Reportes
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reportes", menu=reports_menu)
        reports_menu.add_command(label="Ventas del Día", command=self.daily_sales_report, accelerator="F5")
        reports_menu.add_command(label="Inventario Bajo", command=self.low_stock_report, accelerator="F6")
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Atajos de Teclado", command=self.show_shortcuts)
        help_menu.add_command(label="Acerca de", command=self.show_about)
    
    def create_products_panel(self, parent):
        # Frame de productos
        products_frame = tk.LabelFrame(parent, text="Productos", font=('Arial', 12, 'bold'),
                                      bg='#ecf0f1', fg='#2c3e50', padx=10, pady=10)
        products_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        products_frame.grid_rowconfigure(1, weight=1)
        products_frame.grid_columnconfigure(0, weight=1)
        
        # Barra de búsqueda
        search_frame = tk.Frame(products_frame, bg='#ecf0f1')
        search_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(search_frame, text="Buscar:", font=('Arial', 10, 'bold'),
                bg='#ecf0f1').grid(row=0, column=0, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                    font=('Arial', 10), relief='solid', bd=1)
        self.search_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        self.search_var.trace('w', self.on_search_change)
        
        tk.Button(search_frame, text="Buscar", command=self.search_products,
                 bg='#3498db', fg='white', relief='flat', padx=15).grid(row=0, column=2)
        
        # Lista de productos
        columns = ('Código', 'Nombre', 'Precio', 'Stock')
        self.products_tree = ttk.Treeview(products_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.products_tree.heading(col, text=col)
            if col == 'Nombre':
                self.products_tree.column(col, width=200)
            else:
                self.products_tree.column(col, width=100)
        
        # Scrollbar para productos
        products_scrollbar = ttk.Scrollbar(products_frame, orient='vertical', 
                                          command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        self.products_tree.grid(row=1, column=0, sticky='nsew')
        products_scrollbar.grid(row=1, column=1, sticky='ns')
        
        # Bind doble click para agregar al carrito
        self.products_tree.bind('<Double-1>', self.add_to_cart_from_list)
        self.products_tree.bind('<Return>', self.add_to_cart_from_list)
    
    def create_cart_panel(self, parent):
        # Frame del carrito
        cart_frame = tk.LabelFrame(parent, text="Carrito de Compras", font=('Arial', 12, 'bold'),
                                  bg='#ecf0f1', fg='#2c3e50', padx=10, pady=10)
        cart_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        cart_frame.grid_rowconfigure(1, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)
        
        # Búsqueda rápida por código
        quick_search_frame = tk.Frame(cart_frame, bg='#ecf0f1')
        quick_search_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        quick_search_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(quick_search_frame, text="Código:", font=('Arial', 10, 'bold'),
                bg='#ecf0f1').grid(row=0, column=0, padx=(0, 10))
        
        self.quick_code_var = tk.StringVar()
        self.quick_code_entry = tk.Entry(quick_search_frame, textvariable=self.quick_code_var,
                                        font=('Arial', 10), relief='solid', bd=1)
        self.quick_code_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        self.quick_code_entry.bind('<Return>', self.quick_add_product)
        
        tk.Button(quick_search_frame, text="Agregar", command=self.quick_add_product,
                 bg='#27ae60', fg='white', relief='flat', padx=15).grid(row=0, column=2)
        
        # Lista del carrito
        cart_columns = ('Producto', 'Cantidad', 'Precio', 'Subtotal')
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show='headings', height=15)
        
        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            if col == 'Producto':
                self.cart_tree.column(col, width=150)
            else:
                self.cart_tree.column(col, width=80)
        
        # Scrollbar para carrito
        cart_scrollbar = ttk.Scrollbar(cart_frame, orient='vertical', 
                                      command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        self.cart_tree.grid(row=1, column=0, sticky='nsew')
        cart_scrollbar.grid(row=1, column=1, sticky='ns')
        
        # Frame de totales
        totals_frame = tk.Frame(cart_frame, bg='#ecf0f1')
        totals_frame.grid(row=2, column=0, sticky='ew', pady=10)
        totals_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(totals_frame, text="Subtotal:", font=('Arial', 10, 'bold'),
                bg='#ecf0f1').grid(row=0, column=0, sticky='w')
        self.subtotal_label = tk.Label(totals_frame, text="$0.00", font=('Arial', 10),
                                      bg='#ecf0f1', fg='#2c3e50')
        self.subtotal_label.grid(row=0, column=1, sticky='e')
        
        tk.Label(totals_frame, text="Descuento:", font=('Arial', 10, 'bold'),
                bg='#ecf0f1').grid(row=1, column=0, sticky='w')
        self.discount_label = tk.Label(totals_frame, text="$0.00", font=('Arial', 10),
                                      bg='#ecf0f1', fg='#e74c3c')
        self.discount_label.grid(row=1, column=1, sticky='e')
        
        tk.Label(totals_frame, text="Total:", font=('Arial', 12, 'bold'),
                bg='#ecf0f1').grid(row=2, column=0, sticky='w')
        self.total_label = tk.Label(totals_frame, text="$0.00", font=('Arial', 12, 'bold'),
                                   bg='#ecf0f1', fg='#27ae60')
        self.total_label.grid(row=2, column=1, sticky='e')
        
        # Botones de acción
        buttons_frame = tk.Frame(cart_frame, bg='#ecf0f1')
        buttons_frame.grid(row=3, column=0, sticky='ew', pady=10)
        
        tk.Button(buttons_frame, text="Eliminar Item", command=self.remove_from_cart,
                 bg='#e74c3c', fg='white', relief='flat', padx=10).pack(side='left', padx=(0, 5))
        
        tk.Button(buttons_frame, text="Limpiar Carrito", command=self.clear_cart,
                 bg='#f39c12', fg='white', relief='flat', padx=10).pack(side='left', padx=5)
        
        tk.Button(buttons_frame, text="Aplicar Descuento", command=self.apply_discount,
                 bg='#9b59b6', fg='white', relief='flat', padx=10).pack(side='left', padx=5)
        
        tk.Button(buttons_frame, text="FACTURAR", command=self.process_sale,
                 bg='#27ae60', fg='white', relief='flat', padx=20, font=('Arial', 10, 'bold')).pack(side='right')
        
        # Bind eventos del carrito
        self.cart_tree.bind('<Delete>', lambda e: self.remove_from_cart())
        self.cart_tree.bind('<Button-3>', self.show_cart_context_menu)
    
    def setup_keyboard_shortcuts(self):
        # Atajos globales
        self.root.bind('<Control-n>', lambda e: self.new_sale())
        self.root.bind('<Control-p>', lambda e: self.print_invoice())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F2>', lambda e: self.manage_products())
        self.root.bind('<F3>', lambda e: self.manage_inventory())
        if self.user['rol'] == 'admin':
            self.root.bind('<F4>', lambda e: self.manage_users())
        self.root.bind('<F5>', lambda e: self.daily_sales_report())
        self.root.bind('<F6>', lambda e: self.low_stock_report())
        self.root.bind('<F1>', lambda e: self.show_shortcuts())
        
        # Atajos específicos del POS
        self.root.bind('<F9>', lambda e: self.quick_code_entry.focus())
        self.root.bind('<F10>', lambda e: self.process_sale())
        self.root.bind('<F11>', lambda e: self.clear_cart())
        self.root.bind('<F12>', lambda e: self.apply_discount())
    
    def load_products(self):
        # Limpiar lista
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Cargar productos
        products = self.db.get_products()
        for product in products:
            self.products_tree.insert('', 'end', values=(
                product[1],  # código
                product[2],  # nombre
                f"${product[5]:.2f}",  # precio
                product[6]   # stock
            ), tags=(product[0],))  # ID como tag
    
    def on_search_change(self, *args):
        # Búsqueda en tiempo real
        search_term = self.search_var.get()
        if len(search_term) >= 2:
            self.search_products()
    
    def search_products(self):
        search_term = self.search_var.get().strip()
        
        # Limpiar lista
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Buscar productos
        products = self.db.get_products(search_term)
        for product in products:
            self.products_tree.insert('', 'end', values=(
                product[1],  # código
                product[2],  # nombre
                f"${product[5]:.2f}",  # precio
                product[6]   # stock
            ), tags=(product[0],))  # ID como tag
    
    def quick_add_product(self, event=None):
        code = self.quick_code_var.get().strip()
        if not code:
            return
        
        product = self.db.get_product_by_code(code)
        if product:
            if product[6] > 0:  # Verificar stock
                self.add_to_cart(product[0], product[2], product[5], 1)
                self.quick_code_var.set("")
                self.quick_code_entry.focus()
            else:
                messagebox.showwarning("Sin Stock", f"El producto {product[2]} no tiene stock disponible")
        else:
            messagebox.showerror("Error", f"Producto con código {code} no encontrado")
    
    def add_to_cart_from_list(self, event=None):
        selection = self.products_tree.selection()
        if not selection:
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item['tags'][0]
        product_name = item['values'][1]
        price = float(item['values'][2].replace('$', ''))
        stock = int(item['values'][3])
        
        if stock > 0:
            # Pedir cantidad
            quantity = simpledialog.askinteger("Cantidad", 
                                             f"Ingrese la cantidad para {product_name}:",
                                             minvalue=1, maxvalue=stock)
            if quantity:
                self.add_to_cart(product_id, product_name, price, quantity)
        else:
            messagebox.showwarning("Sin Stock", f"El producto {product_name} no tiene stock disponible")
    
    def add_to_cart(self, product_id, product_name, price, quantity):
        # Verificar si el producto ya está en el carrito
        for i, item in enumerate(self.cart):
            if item['producto_id'] == product_id:
                # Actualizar cantidad
                new_quantity = item['cantidad'] + quantity
                # Verificar stock disponible
                product = self.db.get_product_by_code(self.get_product_code_by_id(product_id))
                if new_quantity <= product[6]:
                    self.cart[i]['cantidad'] = new_quantity
                    self.cart[i]['subtotal'] = new_quantity * price
                    self.update_cart_display()
                    return
                else:
                    messagebox.showwarning("Stock Insuficiente", 
                                         f"Stock disponible: {product[6]}, solicitado: {new_quantity}")
                    return
        
        # Agregar nuevo item al carrito
        self.cart.append({
            'producto_id': product_id,
            'nombre': product_name,
            'precio': price,
            'cantidad': quantity,
            'subtotal': price * quantity
        })
        
        self.update_cart_display()
    
    def get_product_code_by_id(self, product_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo FROM productos WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def update_cart_display(self):
        # Limpiar lista
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Agregar items
        for item in self.cart:
            self.cart_tree.insert('', 'end', values=(
                item['nombre'],
                item['cantidad'],
                f"${item['precio']:.2f}",
                f"${item['subtotal']:.2f}"
            ))
        
        # Actualizar totales
        subtotal = sum(item['subtotal'] for item in self.cart)
        discount = getattr(self, 'discount_amount', 0)
        total = subtotal - discount
        
        self.subtotal_label.config(text=f"${subtotal:.2f}")
        self.discount_label.config(text=f"${discount:.2f}")
        self.total_label.config(text=f"${total:.2f}")
    
    def remove_from_cart(self):
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un item para eliminar")
            return
        
        index = self.cart_tree.index(selection[0])
        del self.cart[index]
        self.update_cart_display()
    
    def clear_cart(self):
        if self.cart and messagebox.askyesno("Confirmar", "¿Está seguro de limpiar el carrito?"):
            self.cart = []
            self.discount_amount = 0
            self.update_cart_display()
    
    def apply_discount(self):
        if not self.cart:
            messagebox.showwarning("Advertencia", "El carrito está vacío")
            return
        
        subtotal = sum(item['subtotal'] for item in self.cart)
        discount = simpledialog.askfloat("Descuento", 
                                       f"Subtotal: ${subtotal:.2f}\nIngrese el descuento:",
                                       minvalue=0, maxvalue=subtotal)
        
        if discount is not None:
            self.discount_amount = discount
            self.update_cart_display()
    
    def process_sale(self):
        if not self.cart:
            messagebox.showwarning("Advertencia", "El carrito está vacío")
            return
        
        # Confirmar venta
        subtotal = sum(item['subtotal'] for item in self.cart)
        discount = getattr(self, 'discount_amount', 0)
        total = subtotal - discount
        
        if messagebox.askyesno("Confirmar Venta", 
                              f"Subtotal: ${subtotal:.2f}\nDescuento: ${discount:.2f}\nTotal: ${total:.2f}\n\n¿Procesar la venta?"):
            try:
                # Procesar venta en la base de datos
                numero_factura, total_final = self.db.create_sale(
                    self.user['id'], 
                    self.cart, 
                    discount, 
                    0  # impuesto
                )
                
                # Mostrar factura
                self.show_invoice(numero_factura, total_final)
                
                # Limpiar carrito
                self.cart = []
                self.discount_amount = 0
                self.update_cart_display()
                
                messagebox.showinfo("Éxito", f"Venta procesada correctamente\nFactura: {numero_factura}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la venta: {str(e)}")
    
    def show_invoice(self, numero_factura, total):
        invoice_window = tk.Toplevel(self.root)
        invoice_window.title(f"Factura {numero_factura}")
        invoice_window.geometry("500x600")
        invoice_window.configure(bg='white')
        
        # Contenido de la factura
        invoice_frame = tk.Frame(invoice_window, bg='white', padx=20, pady=20)
        invoice_frame.pack(expand=True, fill='both')
        
        # Encabezado
        tk.Label(invoice_frame, text="FACTURA DE VENTA", 
                font=('Arial', 16, 'bold'), bg='white').pack(pady=(0, 10))
        
        tk.Label(invoice_frame, text=f"Número: {numero_factura}", 
                font=('Arial', 10), bg='white').pack(anchor='w')
        
        tk.Label(invoice_frame, text=f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                font=('Arial', 10), bg='white').pack(anchor='w')
        
        tk.Label(invoice_frame, text=f"Vendedor: {self.user['nombre']}", 
                font=('Arial', 10), bg='white').pack(anchor='w')
        
        tk.Label(invoice_frame, text="-" * 50, bg='white').pack(pady=10)
        
        # Detalles de productos
        for item in self.cart:
            item_text = f"{item['nombre']} x{item['cantidad']} = ${item['subtotal']:.2f}"
            tk.Label(invoice_frame, text=item_text, 
                    font=('Arial', 9), bg='white').pack(anchor='w')
        
        tk.Label(invoice_frame, text="-" * 50, bg='white').pack(pady=10)
        
        # Totales
        subtotal = sum(item['subtotal'] for item in self.cart)
        discount = getattr(self, 'discount_amount', 0)
        
        tk.Label(invoice_frame, text=f"Subtotal: ${subtotal:.2f}", 
                font=('Arial', 10), bg='white').pack(anchor='e')
        
        if discount > 0:
            tk.Label(invoice_frame, text=f"Descuento: ${discount:.2f}", 
                    font=('Arial', 10), bg='white').pack(anchor='e')
        
        tk.Label(invoice_frame, text=f"TOTAL: ${total:.2f}", 
                font=('Arial', 12, 'bold'), bg='white').pack(anchor='e', pady=(10, 0))
        
        # Botones
        button_frame = tk.Frame(invoice_frame, bg='white')
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Imprimir", command=lambda: self.print_invoice_window(invoice_window),
                 bg='#3498db', fg='white', relief='flat', padx=20).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Cerrar", command=invoice_window.destroy,
                 bg='#95a5a6', fg='white', relief='flat', padx=20).pack(side='left')
    
    def show_cart_context_menu(self, event):
        # Menú contextual para el carrito
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Eliminar Item", command=self.remove_from_cart)
        context_menu.add_command(label="Limpiar Carrito", command=self.clear_cart)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    # Métodos de menú
    def new_sale(self):
        self.clear_cart()
        self.search_var.set("")
        self.load_products()
        self.quick_code_entry.focus()
    
    def print_invoice(self):
        if not self.cart:
            messagebox.showwarning("Advertencia", "No hay venta para imprimir")
            return
        messagebox.showinfo("Imprimir", "Funcionalidad de impresión en desarrollo")
    
    def print_invoice_window(self, window):
        messagebox.showinfo("Imprimir", "Funcionalidad de impresión en desarrollo")
    
    def manage_products(self):
        ProductManagement(self.root, self.db, self.user)
    
    def manage_inventory(self):
        ProductManagement(self.root, self.db, self.user)
    
    def manage_users(self):
        if self.user['rol'] == 'admin':
            UserManagement(self.root, self.db)
        else:
            messagebox.showwarning("Acceso Denegado", "Solo los administradores pueden gestionar usuarios")
    
    def daily_sales_report(self):
        Reports(self.root, self.db, self.user)
    
    def low_stock_report(self):
        Reports(self.root, self.db, self.user)
    
    def show_shortcuts(self):
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Atajos de Teclado")
        shortcuts_window.geometry("500x400")
        shortcuts_window.configure(bg='#f0f0f0')
        
        shortcuts_frame = tk.Frame(shortcuts_window, bg='#f0f0f0', padx=20, pady=20)
        shortcuts_frame.pack(expand=True, fill='both')
        
        tk.Label(shortcuts_frame, text="Atajos de Teclado", 
                font=('Arial', 16, 'bold'), bg='#f0f0f0').pack(pady=(0, 20))
        
        shortcuts = [
            ("Ctrl+N", "Nueva Venta"),
            ("Ctrl+P", "Imprimir Factura"),
            ("Ctrl+Q", "Salir"),
            ("F1", "Mostrar Atajos"),
            ("F2", "Gestión de Productos"),
            ("F3", "Gestión de Inventario"),
            ("F4", "Gestión de Usuarios (Admin)"),
            ("F5", "Reporte Ventas del Día"),
            ("F6", "Reporte Inventario Bajo"),
            ("F9", "Buscar por Código"),
            ("F10", "Procesar Venta"),
            ("F11", "Limpiar Carrito"),
            ("F12", "Aplicar Descuento"),
            ("Enter", "Agregar Producto al Carrito"),
            ("Delete", "Eliminar Item del Carrito")
        ]
        
        for shortcut, description in shortcuts:
            frame = tk.Frame(shortcuts_frame, bg='#f0f0f0')
            frame.pack(fill='x', pady=2)
            
            tk.Label(frame, text=shortcut, font=('Arial', 10, 'bold'), 
                    bg='#f0f0f0', width=15, anchor='w').pack(side='left')
            tk.Label(frame, text=description, font=('Arial', 10), 
                    bg='#f0f0f0').pack(side='left', padx=(10, 0))
    
    def show_about(self):
        messagebox.showinfo("Acerca de", 
                           "Sistema de Punto de Venta v1.0\n\n"
                           "Desarrollado con Python y Tkinter\n"
                           "Base de datos: SQLite\n\n"
                           "Funcionalidades:\n"
                           "• Gestión de productos e inventario\n"
                           "• Facturación y ventas\n"
                           "• Gestión de usuarios\n"
                           "• Reportes básicos\n"
                           "• Atajos de teclado")
    
    def run(self):
        self.root.mainloop()
