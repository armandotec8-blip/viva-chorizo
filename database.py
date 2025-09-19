import sqlite3
import hashlib
from datetime import datetime

class Database:
    def __init__(self, db_name="pos_system.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL,
                rol TEXT NOT NULL,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de categorías
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT,
                activa INTEGER DEFAULT 1
            )
        ''')
        
        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                categoria_id INTEGER,
                precio_venta REAL NOT NULL,
                precio_compra REAL,
                stock INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
        ''')
        
        # Tabla de ventas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT UNIQUE NOT NULL,
                usuario_id INTEGER NOT NULL,
                total REAL NOT NULL,
                descuento REAL DEFAULT 0,
                impuesto REAL DEFAULT 0,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                estado TEXT DEFAULT 'completada',
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabla de detalles de venta
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        # Tabla de movimientos de inventario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                tipo_movimiento TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                motivo TEXT,
                usuario_id INTEGER,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Crear usuario administrador por defecto
        self.create_default_admin()
        self.create_default_categories()
    
    def create_default_admin(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe un admin
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'")
        if cursor.fetchone()[0] == 0:
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO usuarios (username, password, nombre, rol)
                VALUES (?, ?, ?, ?)
            ''', ("admin", password_hash, "Administrador", "admin"))
        
        conn.commit()
        conn.close()
    
    def create_default_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        default_categories = [
            ("General", "Productos generales"),
            ("Electrónicos", "Dispositivos electrónicos"),
            ("Ropa", "Vestimenta y accesorios"),
            ("Alimentos", "Productos alimenticios"),
            ("Hogar", "Artículos para el hogar")
        ]
        
        for nombre, descripcion in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categorias (nombre, descripcion)
                VALUES (?, ?)
            ''', (nombre, descripcion))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, username, nombre, rol FROM usuarios 
            WHERE username = ? AND password = ? AND activo = 1
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_products(self, search_term=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if search_term:
            cursor.execute('''
                SELECT p.id, p.codigo, p.nombre, p.descripcion, c.nombre as categoria,
                       p.precio_venta, p.stock, p.stock_minimo
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.activo = 1 AND (p.codigo LIKE ? OR p.nombre LIKE ? OR p.descripcion LIKE ?)
                ORDER BY p.nombre
            ''', (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            cursor.execute('''
                SELECT p.id, p.codigo, p.nombre, p.descripcion, c.nombre as categoria,
                       p.precio_venta, p.stock, p.stock_minimo
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.activo = 1
                ORDER BY p.nombre
            ''')
        
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_product_by_code(self, codigo):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.codigo, p.nombre, p.descripcion, c.nombre as categoria,
                   p.precio_venta, p.stock, p.stock_minimo
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.codigo = ? AND p.activo = 1
        ''', (codigo,))
        
        product = cursor.fetchone()
        conn.close()
        return product
    
    def update_stock(self, producto_id, cantidad, tipo_movimiento, usuario_id, motivo=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Actualizar stock del producto
        if tipo_movimiento == "entrada":
            cursor.execute('''
                UPDATE productos SET stock = stock + ? WHERE id = ?
            ''', (cantidad, producto_id))
        elif tipo_movimiento == "salida":
            cursor.execute('''
                UPDATE productos SET stock = stock - ? WHERE id = ?
            ''', (cantidad, producto_id))
        
        # Registrar movimiento
        cursor.execute('''
            INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, motivo, usuario_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (producto_id, tipo_movimiento, cantidad, motivo, usuario_id))
        
        conn.commit()
        conn.close()
    
    def create_sale(self, usuario_id, items, descuento=0, impuesto=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generar número de factura
        numero_factura = f"FAC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calcular total
        total = sum(item['subtotal'] for item in items)
        total_final = total - descuento + impuesto
        
        # Crear venta
        cursor.execute('''
            INSERT INTO ventas (numero_factura, usuario_id, total, descuento, impuesto)
            VALUES (?, ?, ?, ?, ?)
        ''', (numero_factura, usuario_id, total_final, descuento, impuesto))
        
        venta_id = cursor.lastrowid
        
        # Crear detalles de venta y actualizar stock
        for item in items:
            cursor.execute('''
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            ''', (venta_id, item['producto_id'], item['cantidad'], item['precio'], item['subtotal']))
            
            # Actualizar stock
            self.update_stock(item['producto_id'], item['cantidad'], "salida", usuario_id, f"Venta {numero_factura}")
        
        conn.commit()
        conn.close()
        
        return numero_factura, total_final

