import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from datetime import datetime, timedelta
import sqlite3

class Reports:
    def __init__(self, parent, db, current_user):
        self.parent = parent
        self.db = db
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Reportes del Sistema")
        self.window.geometry("1000x700")
        self.window.configure(bg='#f0f0f0')
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Título
        title_label = tk.Label(main_frame, text="Reportes del Sistema", 
                              font=('Arial', 18, 'bold'), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Frame de botones de reportes
        reports_frame = tk.Frame(main_frame, bg='#f0f0f0')
        reports_frame.pack(fill='x', pady=(0, 20))
        
        # Botones de reportes
        tk.Button(reports_frame, text="Ventas del Día", 
                 command=self.daily_sales_report, bg='#3498db', fg='white',
                 relief='flat', padx=20, pady=10, font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        tk.Button(reports_frame, text="Ventas por Período", 
                 command=self.period_sales_report, bg='#9b59b6', fg='white',
                 relief='flat', padx=20, pady=10, font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        tk.Button(reports_frame, text="Productos Más Vendidos", 
                 command=self.top_products_report, bg='#e67e22', fg='white',
                 relief='flat', padx=20, pady=10, font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        tk.Button(reports_frame, text="Inventario Bajo", 
                 command=self.low_stock_report, bg='#e74c3c', fg='white',
                 relief='flat', padx=20, pady=10, font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        tk.Button(reports_frame, text="Movimientos de Inventario", 
                 command=self.inventory_movements_report, bg='#34495e', fg='white',
                 relief='flat', padx=20, pady=10, font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        # Frame de filtros
        self.filters_frame = tk.Frame(main_frame, bg='#f0f0f0')
        self.filters_frame.pack(fill='x', pady=(0, 10))
        
        # Frame de resultados
        results_frame = tk.Frame(main_frame, bg='#f0f0f0')
        results_frame.pack(expand=True, fill='both')
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview para mostrar resultados
        self.results_tree = ttk.Treeview(results_frame, show='headings', height=20)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient='horizontal', command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Frame de resumen
        self.summary_frame = tk.Frame(main_frame, bg='#ecf0f1', relief='solid', bd=1)
        self.summary_frame.pack(fill='x', pady=(10, 0))
    
    def clear_filters(self):
        for widget in self.filters_frame.winfo_children():
            widget.destroy()
    
    def clear_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Limpiar columnas
        for col in self.results_tree['columns']:
            self.results_tree.heading(col, text="")
            self.results_tree.column(col, width=0)
    
    def clear_summary(self):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
    
    def daily_sales_report(self):
        self.clear_filters()
        self.clear_results()
        self.clear_summary()
        
        # Configurar columnas
        columns = ('Hora', 'Factura', 'Vendedor', 'Total', 'Descuento', 'Neto')
        self.results_tree['columns'] = columns
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        
        # Obtener fecha actual
        today = datetime.now().date()
        
        # Consultar ventas del día
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.fecha, v.numero_factura, u.nombre, v.total, v.descuento, (v.total - v.descuento) as neto
            FROM ventas v
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE DATE(v.fecha) = ?
            ORDER BY v.fecha DESC
        ''', (today,))
        
        total_sales = 0
        total_discount = 0
        total_net = 0
        sales_count = 0
        
        for sale in cursor.fetchall():
            hora = datetime.strptime(sale[0], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
            self.results_tree.insert('', 'end', values=(
                hora, sale[1], sale[2], f"${sale[3]:.2f}", 
                f"${sale[4]:.2f}", f"${sale[5]:.2f}"
            ))
            total_sales += sale[3]
            total_discount += sale[4]
            total_net += sale[5]
            sales_count += 1
        
        conn.close()
        
        # Mostrar resumen
        self.show_summary([
            f"Fecha: {today.strftime('%d/%m/%Y')}",
            f"Total de Ventas: {sales_count}",
            f"Total Bruto: ${total_sales:.2f}",
            f"Total Descuentos: ${total_discount:.2f}",
            f"Total Neto: ${total_net:.2f}"
        ])
    
    def period_sales_report(self):
        self.clear_filters()
        self.clear_results()
        self.clear_summary()
        
        # Crear filtros de fecha
        filters_frame = tk.Frame(self.filters_frame, bg='#f0f0f0')
        filters_frame.pack()
        
        tk.Label(filters_frame, text="Fecha Inicio:", bg='#f0f0f0').grid(row=0, column=0, padx=(0, 10))
        start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        tk.Entry(filters_frame, textvariable=start_date_var, width=12).grid(row=0, column=1, padx=(0, 20))
        
        tk.Label(filters_frame, text="Fecha Fin:", bg='#f0f0f0').grid(row=0, column=2, padx=(0, 10))
        end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        tk.Entry(filters_frame, textvariable=end_date_var, width=12).grid(row=0, column=3, padx=(0, 20))
        
        def generate_report():
            try:
                start_date = datetime.strptime(start_date_var.get(), '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_var.get(), '%Y-%m-%d').date()
                
                if start_date > end_date:
                    messagebox.showerror("Error", "La fecha de inicio no puede ser mayor a la fecha fin")
                    return
                
                self.generate_period_report(start_date, end_date)
                
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
        
        tk.Button(filters_frame, text="Generar Reporte", command=generate_report,
                 bg='#3498db', fg='white', relief='flat', padx=15).grid(row=0, column=4)
        
        # Generar reporte por defecto (últimos 7 días)
        self.generate_period_report(
            (datetime.now() - timedelta(days=7)).date(),
            datetime.now().date()
        )
    
    def generate_period_report(self, start_date, end_date):
        self.clear_results()
        self.clear_summary()
        
        # Configurar columnas
        columns = ('Fecha', 'Factura', 'Vendedor', 'Total', 'Descuento', 'Neto')
        self.results_tree['columns'] = columns
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        
        # Consultar ventas del período
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.fecha, v.numero_factura, u.nombre, v.total, v.descuento, (v.total - v.descuento) as neto
            FROM ventas v
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE DATE(v.fecha) BETWEEN ? AND ?
            ORDER BY v.fecha DESC
        ''', (start_date, end_date))
        
        total_sales = 0
        total_discount = 0
        total_net = 0
        sales_count = 0
        
        for sale in cursor.fetchall():
            fecha = datetime.strptime(sale[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            self.results_tree.insert('', 'end', values=(
                fecha, sale[1], sale[2], f"${sale[3]:.2f}", 
                f"${sale[4]:.2f}", f"${sale[5]:.2f}"
            ))
            total_sales += sale[3]
            total_discount += sale[4]
            total_net += sale[5]
            sales_count += 1
        
        conn.close()
        
        # Mostrar resumen
        self.show_summary([
            f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            f"Total de Ventas: {sales_count}",
            f"Total Bruto: ${total_sales:.2f}",
            f"Total Descuentos: ${total_discount:.2f}",
            f"Total Neto: ${total_net:.2f}",
            f"Promedio por Venta: ${total_net/sales_count:.2f}" if sales_count > 0 else "Promedio por Venta: $0.00"
        ])
    
    def top_products_report(self):
        self.clear_filters()
        self.clear_results()
        self.clear_summary()
        
        # Crear filtro de cantidad
        filters_frame = tk.Frame(self.filters_frame, bg='#f0f0f0')
        filters_frame.pack()
        
        tk.Label(filters_frame, text="Mostrar Top:", bg='#f0f0f0').grid(row=0, column=0, padx=(0, 10))
        top_count_var = tk.StringVar(value="10")
        tk.Entry(filters_frame, textvariable=top_count_var, width=8).grid(row=0, column=1, padx=(0, 20))
        
        def generate_report():
            try:
                top_count = int(top_count_var.get())
                if top_count <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                    return
                self.generate_top_products_report(top_count)
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido")
        
        tk.Button(filters_frame, text="Generar Reporte", command=generate_report,
                 bg='#e67e22', fg='white', relief='flat', padx=15).grid(row=0, column=2)
        
        # Generar reporte por defecto (top 10)
        self.generate_top_products_report(10)
    
    def generate_top_products_report(self, top_count):
        self.clear_results()
        self.clear_summary()
        
        # Configurar columnas
        columns = ('Producto', 'Código', 'Cantidad Vendida', 'Total Vendido', 'Precio Promedio')
        self.results_tree['columns'] = columns
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == 'Producto':
                self.results_tree.column(col, width=200)
            else:
                self.results_tree.column(col, width=120)
        
        # Consultar productos más vendidos
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.nombre, p.codigo, SUM(dv.cantidad) as total_cantidad,
                   SUM(dv.subtotal) as total_vendido,
                   AVG(dv.precio_unitario) as precio_promedio
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            JOIN ventas v ON dv.venta_id = v.id
            GROUP BY p.id, p.nombre, p.codigo
            ORDER BY total_cantidad DESC
            LIMIT ?
        ''', (top_count,))
        
        total_quantity = 0
        total_sales = 0
        
        for product in cursor.fetchall():
            self.results_tree.insert('', 'end', values=(
                product[0],  # nombre
                product[1],  # código
                int(product[2]),  # cantidad
                f"${product[3]:.2f}",  # total vendido
                f"${product[4]:.2f}"   # precio promedio
            ))
            total_quantity += product[2]
            total_sales += product[3]
        
        conn.close()
        
        # Mostrar resumen
        self.show_summary([
            f"Top {top_count} Productos Más Vendidos",
            f"Total de Unidades Vendidas: {total_quantity}",
            f"Total en Ventas: ${total_sales:.2f}"
        ])
    
    def low_stock_report(self):
        self.clear_filters()
        self.clear_results()
        self.clear_summary()
        
        # Configurar columnas
        columns = ('Código', 'Producto', 'Stock Actual', 'Stock Mínimo', 'Diferencia', 'Estado')
        self.results_tree['columns'] = columns
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == 'Producto':
                self.results_tree.column(col, width=200)
            else:
                self.results_tree.column(col, width=100)
        
        # Consultar productos con stock bajo
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT codigo, nombre, stock, stock_minimo, (stock - stock_minimo) as diferencia
            FROM productos
            WHERE activo = 1 AND stock <= stock_minimo
            ORDER BY diferencia ASC
        ''')
        
        low_stock_count = 0
        out_of_stock_count = 0
        
        for product in cursor.fetchall():
            estado = "Sin Stock" if product[2] == 0 else "Stock Bajo"
            if product[2] == 0:
                out_of_stock_count += 1
            else:
                low_stock_count += 1
            
            self.results_tree.insert('', 'end', values=(
                product[0],  # código
                product[1],  # nombre
                product[2],  # stock actual
                product[3],  # stock mínimo
                product[4],  # diferencia
                estado
            ))
        
        conn.close()
        
        # Mostrar resumen
        self.show_summary([
            f"Productos con Stock Bajo: {low_stock_count}",
            f"Productos Sin Stock: {out_of_stock_count}",
            f"Total de Productos a Reabastecer: {low_stock_count + out_of_stock_count}"
        ])
    
    def inventory_movements_report(self):
        self.clear_filters()
        self.clear_results()
        self.clear_summary()
        
        # Crear filtros
        filters_frame = tk.Frame(self.filters_frame, bg='#f0f0f0')
        filters_frame.pack()
        
        tk.Label(filters_frame, text="Fecha Inicio:", bg='#f0f0f0').grid(row=0, column=0, padx=(0, 10))
        start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        tk.Entry(filters_frame, textvariable=start_date_var, width=12).grid(row=0, column=1, padx=(0, 20))
        
        tk.Label(filters_frame, text="Fecha Fin:", bg='#f0f0f0').grid(row=0, column=2, padx=(0, 10))
        end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        tk.Entry(filters_frame, textvariable=end_date_var, width=12).grid(row=0, column=3, padx=(0, 20))
        
        tk.Label(filters_frame, text="Tipo:", bg='#f0f0f0').grid(row=0, column=4, padx=(0, 10))
        type_var = tk.StringVar(value="todos")
        type_combo = ttk.Combobox(filters_frame, textvariable=type_var, 
                                 values=["todos", "entrada", "salida"], width=10)
        type_combo.grid(row=0, column=5, padx=(0, 20))
        
        def generate_report():
            try:
                start_date = datetime.strptime(start_date_var.get(), '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_var.get(), '%Y-%m-%d').date()
                movement_type = type_var.get()
                
                if start_date > end_date:
                    messagebox.showerror("Error", "La fecha de inicio no puede ser mayor a la fecha fin")
                    return
                
                self.generate_movements_report(start_date, end_date, movement_type)
                
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
        
        tk.Button(filters_frame, text="Generar Reporte", command=generate_report,
                 bg='#34495e', fg='white', relief='flat', padx=15).grid(row=0, column=6)
        
        # Generar reporte por defecto
        self.generate_movements_report(
            (datetime.now() - timedelta(days=7)).date(),
            datetime.now().date(),
            "todos"
        )
    
    def generate_movements_report(self, start_date, end_date, movement_type):
        self.clear_results()
        self.clear_summary()
        
        # Configurar columnas
        columns = ('Fecha', 'Producto', 'Tipo', 'Cantidad', 'Motivo', 'Usuario')
        self.results_tree['columns'] = columns
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == 'Producto':
                self.results_tree.column(col, width=200)
            elif col == 'Motivo':
                self.results_tree.column(col, width=150)
            else:
                self.results_tree.column(col, width=100)
        
        # Construir consulta
        query = '''
            SELECT mi.fecha, p.nombre, mi.tipo_movimiento, mi.cantidad, mi.motivo, u.nombre
            FROM movimientos_inventario mi
            JOIN productos p ON mi.producto_id = p.id
            LEFT JOIN usuarios u ON mi.usuario_id = u.id
            WHERE DATE(mi.fecha) BETWEEN ? AND ?
        '''
        params = [start_date, end_date]
        
        if movement_type != "todos":
            query += " AND mi.tipo_movimiento = ?"
            params.append(movement_type)
        
        query += " ORDER BY mi.fecha DESC"
        
        # Consultar movimientos
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        total_entries = 0
        total_exits = 0
        
        for movement in cursor.fetchall():
            fecha = datetime.strptime(movement[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            tipo = "Entrada" if movement[2] == "entrada" else "Salida"
            
            self.results_tree.insert('', 'end', values=(
                fecha,
                movement[1],  # producto
                tipo,
                movement[3],  # cantidad
                movement[4] or "N/A",  # motivo
                movement[5] or "Sistema"  # usuario
            ))
            
            if movement[2] == "entrada":
                total_entries += movement[3]
            else:
                total_exits += movement[3]
        
        conn.close()
        
        # Mostrar resumen
        self.show_summary([
            f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            f"Tipo: {movement_type.title()}",
            f"Total Entradas: {total_entries}",
            f"Total Salidas: {total_exits}",
            f"Balance: {total_entries - total_exits}"
        ])
    
    def show_summary(self, summary_items):
        for i, item in enumerate(summary_items):
            label = tk.Label(self.summary_frame, text=item, 
                           font=('Arial', 10, 'bold' if i == 0 else 'normal'),
                           bg='#ecf0f1', fg='#2c3e50')
            label.pack(side='left', padx=10, pady=5)

