import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import Database
import sqlite3

class ProductManagement:
    def __init__(self, parent, db, current_user):
        self.parent = parent
        self.db = db
        self.current_user = current_user
        self.setup_ui()
        self.load_products()
        self.load_categories()
    
    def setup_ui(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gestión de Productos")
        self.window.geometry("1000x700")
        self.window.configure(bg='#f0f0f0')
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Título
        title_label = tk.Label(main_frame, text="Gestión de Productos", 
                              font=('Arial', 18, 'bold'), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Frame de búsqueda y filtros
        search_frame = tk.Frame(main_frame, bg='#f0f0f0')
        search_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(search_frame, text="Buscar:", font=('Arial', 10, 'bold'),
                bg='#f0f0f0').grid(row=0, column=0, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                    font=('Arial', 10), relief='solid', bd=1)
        self.search_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        self.search_var.trace('w', self.on_search_change)
        
        tk.Button(search_frame, text="Buscar", command=self.search_products,
                 bg='#3498db', fg='white', relief='flat', padx=15).grid(row=0, column=2)
        
        tk.Button(search_frame, text="Limpiar", command=self.clear_search,
                 bg='#95a5a6', fg='white', relief='flat', padx=15).grid(row=0, column=3, padx=(5, 0))
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.grid(row=2, column=0, sticky='ew', pady=10)
        
        tk.Button(button_frame, text="Nuevo Producto", 
                 command=self.new_product, bg='#27ae60', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Editar", 
                 command=self.edit_product, bg='#f39c12', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Eliminar", 
                 command=self.delete_product, bg='#e74c3c', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Ajustar Stock", 
                 command=self.adjust_stock, bg='#9b59b6', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Categorías", 
                 command=self.manage_categories, bg='#34495e', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left')
        
        # Lista de productos
        columns = ('ID', 'Código', 'Nombre', 'Categoría', 'Precio Venta', 'Precio Compra', 'Stock', 'Stock Mínimo', 'Estado')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col in ['Nombre', 'Categoría']:
                self.tree.column(col, width=150)
            else:
                self.tree.column(col, width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(main_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=3, column=0, sticky='nsew')
        v_scrollbar.grid(row=3, column=1, sticky='ns')
        h_scrollbar.grid(row=4, column=0, sticky='ew')
        
        # Bind eventos
        self.tree.bind('<Double-1>', self.edit_product)
        self.tree.bind('<Return>', self.edit_product)
    
    def load_products(self):
        # Limpiar lista
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Cargar productos
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.codigo, p.nombre, c.nombre as categoria,
                   p.precio_venta, p.precio_compra, p.stock, p.stock_minimo,
                   CASE WHEN p.activo = 1 THEN 'Activo' ELSE 'Inactivo' END as estado
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            ORDER BY p.nombre
        ''')
        
        for product in cursor.fetchall():
            self.tree.insert('', 'end', values=(
                product[0],  # ID
                product[1],  # código
                product[2],  # nombre
                product[3] or 'Sin categoría',  # categoría
                f"${product[4]:.2f}",  # precio_venta
                f"${product[5]:.2f}" if product[5] else "N/A",  # precio_compra
                product[6],  # stock
                product[7],  # stock_minimo
                product[8]   # estado
            ))
        
        conn.close()
    
    def load_categories(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM categorias WHERE activa = 1 ORDER BY nombre")
        self.categories = cursor.fetchall()
        conn.close()
    
    def on_search_change(self, *args):
        search_term = self.search_var.get()
        if len(search_term) >= 2:
            self.search_products()
    
    def search_products(self):
        search_term = self.search_var.get().strip()
        
        # Limpiar lista
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Buscar productos
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.codigo, p.nombre, c.nombre as categoria,
                   p.precio_venta, p.precio_compra, p.stock, p.stock_minimo,
                   CASE WHEN p.activo = 1 THEN 'Activo' ELSE 'Inactivo' END as estado
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.codigo LIKE ? OR p.nombre LIKE ? OR p.descripcion LIKE ?
            ORDER BY p.nombre
        ''', (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        
        for product in cursor.fetchall():
            self.tree.insert('', 'end', values=(
                product[0],  # ID
                product[1],  # código
                product[2],  # nombre
                product[3] or 'Sin categoría',  # categoría
                f"${product[4]:.2f}",  # precio_venta
                f"${product[5]:.2f}" if product[5] else "N/A",  # precio_compra
                product[6],  # stock
                product[7],  # stock_minimo
                product[8]   # estado
            ))
        
        conn.close()
    
    def clear_search(self):
        self.search_var.set("")
        self.load_products()
    
    def new_product(self):
        self.product_form()
    
    def edit_product(self, event=None):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para editar")
            return
        
        item = self.tree.item(selection[0])
        product_id = item['values'][0]
        self.product_form(product_id)
    
    def delete_product(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar")
            return
        
        item = self.tree.item(selection[0])
        product_id = item['values'][0]
        product_name = item['values'][2]
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el producto {product_name}?"):
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE productos SET activo = 0 WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            self.load_products()
            messagebox.showinfo("Éxito", "Producto eliminado correctamente")
    
    def product_form(self, product_id=None):
        form_window = tk.Toplevel(self.window)
        form_window.title("Nuevo Producto" if not product_id else "Editar Producto")
        form_window.geometry("500x600")
        form_window.configure(bg='#f0f0f0')
        
        # Variables
        codigo_var = tk.StringVar()
        nombre_var = tk.StringVar()
        descripcion_var = tk.StringVar()
        categoria_var = tk.StringVar()
        precio_venta_var = tk.StringVar()
        precio_compra_var = tk.StringVar()
        stock_var = tk.StringVar()
        stock_minimo_var = tk.StringVar()
        activo_var = tk.BooleanVar(value=True)
        
        # Cargar datos si es edición
        if product_id:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT codigo, nombre, descripcion, categoria_id, precio_venta, 
                       precio_compra, stock, stock_minimo, activo
                FROM productos WHERE id = ?
            ''', (product_id,))
            product_data = cursor.fetchone()
            conn.close()
            
            if product_data:
                codigo_var.set(product_data[0])
                nombre_var.set(product_data[1])
                descripcion_var.set(product_data[2] or "")
                categoria_var.set(product_data[3] or "")
                precio_venta_var.set(str(product_data[4]))
                precio_compra_var.set(str(product_data[5]) if product_data[5] else "")
                stock_var.set(str(product_data[6]))
                stock_minimo_var.set(str(product_data[7]))
                activo_var.set(bool(product_data[8]))
        
        # Formulario
        main_frame = tk.Frame(form_window, bg='#f0f0f0', padx=30, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        # Campos
        row = 0
        
        tk.Label(main_frame, text="Código:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=codigo_var, width=30).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        tk.Label(main_frame, text="Nombre:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=nombre_var, width=30).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        tk.Label(main_frame, text="Descripción:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        desc_text = tk.Text(main_frame, width=30, height=3)
        desc_text.grid(row=row, column=1, pady=5, padx=(10, 0))
        if product_id and product_data[2]:
            desc_text.insert('1.0', product_data[2])
        row += 1
        
        tk.Label(main_frame, text="Categoría:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        categoria_combo = ttk.Combobox(main_frame, textvariable=categoria_var, width=27)
        categoria_combo['values'] = [cat[1] for cat in self.categories]
        categoria_combo.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        tk.Label(main_frame, text="Precio Venta:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=precio_venta_var, width=30).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        tk.Label(main_frame, text="Precio Compra:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=precio_compra_var, width=30).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        tk.Label(main_frame, text="Stock:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=stock_var, width=30).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        tk.Label(main_frame, text="Stock Mínimo:", bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=stock_minimo_var, width=30).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        tk.Checkbutton(main_frame, text="Activo", variable=activo_var, bg='#f0f0f0').grid(row=row, column=1, sticky='w', pady=5, padx=(10, 0))
        row += 1
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def save_product():
            codigo = codigo_var.get().strip()
            nombre = nombre_var.get().strip()
            descripcion = desc_text.get('1.0', tk.END).strip()
            categoria_nombre = categoria_var.get().strip()
            precio_venta = precio_venta_var.get().strip()
            precio_compra = precio_compra_var.get().strip()
            stock = stock_var.get().strip()
            stock_minimo = stock_minimo_var.get().strip()
            activo = activo_var.get()
            
            # Validaciones
            if not all([codigo, nombre, precio_venta]):
                messagebox.showerror("Error", "Código, nombre y precio de venta son obligatorios")
                return
            
            try:
                precio_venta = float(precio_venta)
                precio_compra = float(precio_compra) if precio_compra else None
                stock = int(stock) if stock else 0
                stock_minimo = int(stock_minimo) if stock_minimo else 0
            except ValueError:
                messagebox.showerror("Error", "Los valores numéricos deben ser válidos")
                return
            
            # Obtener ID de categoría
            categoria_id = None
            if categoria_nombre:
                for cat in self.categories:
                    if cat[1] == categoria_nombre:
                        categoria_id = cat[0]
                        break
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                if product_id:
                    # Actualizar producto
                    cursor.execute('''
                        UPDATE productos SET codigo=?, nombre=?, descripcion=?, categoria_id=?,
                                           precio_venta=?, precio_compra=?, stock=?, stock_minimo=?, activo=?
                        WHERE id=?
                    ''', (codigo, nombre, descripcion, categoria_id, precio_venta, 
                          precio_compra, stock, stock_minimo, activo, product_id))
                else:
                    # Crear nuevo producto
                    cursor.execute('''
                        INSERT INTO productos (codigo, nombre, descripcion, categoria_id,
                                             precio_venta, precio_compra, stock, stock_minimo, activo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo, nombre, descripcion, categoria_id, precio_venta, 
                          precio_compra, stock, stock_minimo, activo))
                
                conn.commit()
                conn.close()
                form_window.destroy()
                self.load_products()
                messagebox.showinfo("Éxito", "Producto guardado correctamente")
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El código del producto ya existe")
                conn.close()
        
        tk.Button(button_frame, text="Guardar", command=save_product, 
                 bg='#27ae60', fg='white', relief='flat', padx=20).pack(side='left', padx=(0, 10))
        tk.Button(button_frame, text="Cancelar", command=form_window.destroy, 
                 bg='#95a5a6', fg='white', relief='flat', padx=20).pack(side='left')
    
    def adjust_stock(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para ajustar stock")
            return
        
        item = self.tree.item(selection[0])
        product_id = item['values'][0]
        product_name = item['values'][2]
        current_stock = int(item['values'][6])
        
        # Ventana de ajuste de stock
        adjust_window = tk.Toplevel(self.window)
        adjust_window.title(f"Ajustar Stock - {product_name}")
        adjust_window.geometry("400x300")
        adjust_window.configure(bg='#f0f0f0')
        
        main_frame = tk.Frame(adjust_window, bg='#f0f0f0', padx=30, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        tk.Label(main_frame, text=f"Producto: {product_name}", 
                font=('Arial', 12, 'bold'), bg='#f0f0f0').pack(pady=(0, 10))
        
        tk.Label(main_frame, text=f"Stock Actual: {current_stock}", 
                font=('Arial', 10), bg='#f0f0f0').pack(pady=(0, 20))
        
        # Tipo de movimiento
        movement_frame = tk.Frame(main_frame, bg='#f0f0f0')
        movement_frame.pack(fill='x', pady=10)
        
        tk.Label(movement_frame, text="Tipo de Movimiento:", bg='#f0f0f0').pack(anchor='w')
        
        movement_var = tk.StringVar(value="entrada")
        tk.Radiobutton(movement_frame, text="Entrada (+)", variable=movement_var, 
                      value="entrada", bg='#f0f0f0').pack(anchor='w')
        tk.Radiobutton(movement_frame, text="Salida (-)", variable=movement_var, 
                      value="salida", bg='#f0f0f0').pack(anchor='w')
        
        # Cantidad
        quantity_frame = tk.Frame(main_frame, bg='#f0f0f0')
        quantity_frame.pack(fill='x', pady=10)
        
        tk.Label(quantity_frame, text="Cantidad:", bg='#f0f0f0').pack(anchor='w')
        quantity_var = tk.StringVar()
        tk.Entry(quantity_frame, textvariable=quantity_var, width=20).pack(anchor='w')
        
        # Motivo
        reason_frame = tk.Frame(main_frame, bg='#f0f0f0')
        reason_frame.pack(fill='x', pady=10)
        
        tk.Label(reason_frame, text="Motivo:", bg='#f0f0f0').pack(anchor='w')
        reason_var = tk.StringVar()
        tk.Entry(reason_frame, textvariable=reason_var, width=30).pack(anchor='w')
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        def apply_adjustment():
            try:
                quantity = int(quantity_var.get())
                if quantity <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                    return
                
                movement_type = movement_var.get()
                reason = reason_var.get().strip() or "Ajuste manual"
                
                # Verificar stock suficiente para salida
                if movement_type == "salida" and quantity > current_stock:
                    messagebox.showerror("Error", f"Stock insuficiente. Disponible: {current_stock}")
                    return
                
                # Aplicar ajuste
                self.db.update_stock(product_id, quantity, movement_type, 
                                   self.current_user['id'], reason)
                
                adjust_window.destroy()
                self.load_products()
                messagebox.showinfo("Éxito", "Stock ajustado correctamente")
                
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número válido")
        
        tk.Button(button_frame, text="Aplicar", command=apply_adjustment, 
                 bg='#27ae60', fg='white', relief='flat', padx=20).pack(side='left', padx=(0, 10))
        tk.Button(button_frame, text="Cancelar", command=adjust_window.destroy, 
                 bg='#95a5a6', fg='white', relief='flat', padx=20).pack(side='left')
    
    def manage_categories(self):
        CategoryManagement(self.window, self.db)

class CategoryManagement:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.setup_ui()
        self.load_categories()
    
    def setup_ui(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gestión de Categorías")
        self.window.geometry("600x400")
        self.window.configure(bg='#f0f0f0')
        
        main_frame = tk.Frame(self.window, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        tk.Label(main_frame, text="Gestión de Categorías", 
                font=('Arial', 16, 'bold'), bg='#f0f0f0').pack(pady=(0, 20))
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(0, 10))
        
        tk.Button(button_frame, text="Nueva Categoría", 
                 command=self.new_category, bg='#27ae60', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Editar", 
                 command=self.edit_category, bg='#f39c12', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Eliminar", 
                 command=self.delete_category, bg='#e74c3c', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left')
        
        # Lista de categorías
        columns = ('ID', 'Nombre', 'Descripción', 'Estado')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.bind('<Double-1>', self.edit_category)
    
    def load_categories(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, nombre, descripcion, 
                   CASE WHEN activa = 1 THEN 'Activa' ELSE 'Inactiva' END as estado
            FROM categorias ORDER BY nombre
        ''')
        
        for category in cursor.fetchall():
            self.tree.insert('', 'end', values=category)
        
        conn.close()
    
    def new_category(self):
        self.category_form()
    
    def edit_category(self, event=None):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una categoría para editar")
            return
        
        item = self.tree.item(selection[0])
        category_id = item['values'][0]
        self.category_form(category_id)
    
    def delete_category(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una categoría para eliminar")
            return
        
        item = self.tree.item(selection[0])
        category_id = item['values'][0]
        category_name = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la categoría {category_name}?"):
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE categorias SET activa = 0 WHERE id = ?", (category_id,))
            conn.commit()
            conn.close()
            self.load_categories()
            messagebox.showinfo("Éxito", "Categoría eliminada correctamente")
    
    def category_form(self, category_id=None):
        form_window = tk.Toplevel(self.window)
        form_window.title("Nueva Categoría" if not category_id else "Editar Categoría")
        form_window.geometry("400x250")
        form_window.configure(bg='#f0f0f0')
        
        # Variables
        nombre_var = tk.StringVar()
        descripcion_var = tk.StringVar()
        activa_var = tk.BooleanVar(value=True)
        
        # Cargar datos si es edición
        if category_id:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, descripcion, activa FROM categorias WHERE id = ?", (category_id,))
            category_data = cursor.fetchone()
            conn.close()
            
            if category_data:
                nombre_var.set(category_data[0])
                descripcion_var.set(category_data[1] or "")
                activa_var.set(bool(category_data[2]))
        
        # Formulario
        main_frame = tk.Frame(form_window, bg='#f0f0f0', padx=30, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        tk.Label(main_frame, text="Nombre:", bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=nombre_var, width=30).grid(row=0, column=1, pady=5, padx=(10, 0))
        
        tk.Label(main_frame, text="Descripción:", bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        desc_text = tk.Text(main_frame, width=30, height=3)
        desc_text.grid(row=1, column=1, pady=5, padx=(10, 0))
        if category_id and category_data[1]:
            desc_text.insert('1.0', category_data[1])
        
        tk.Checkbutton(main_frame, text="Activa", variable=activa_var, bg='#f0f0f0').grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def save_category():
            nombre = nombre_var.get().strip()
            descripcion = desc_text.get('1.0', tk.END).strip()
            activa = activa_var.get()
            
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                if category_id:
                    cursor.execute('''
                        UPDATE categorias SET nombre=?, descripcion=?, activa=?
                        WHERE id=?
                    ''', (nombre, descripcion, activa, category_id))
                else:
                    cursor.execute('''
                        INSERT INTO categorias (nombre, descripcion, activa)
                        VALUES (?, ?, ?)
                    ''', (nombre, descripcion, activa))
                
                conn.commit()
                conn.close()
                form_window.destroy()
                self.load_categories()
                messagebox.showinfo("Éxito", "Categoría guardada correctamente")
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El nombre de la categoría ya existe")
                conn.close()
        
        tk.Button(button_frame, text="Guardar", command=save_category, 
                 bg='#27ae60', fg='white', relief='flat', padx=20).pack(side='left', padx=(0, 10))
        tk.Button(button_frame, text="Cancelar", command=form_window.destroy, 
                 bg='#95a5a6', fg='white', relief='flat', padx=20).pack(side='left')

