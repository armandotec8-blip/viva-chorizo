import tkinter as tk
from tkinter import ttk, messagebox
from database import Database

class LoginWindow:
    def __init__(self):
        self.db = Database()
        self.current_user = None
        self.setup_ui()
    
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Punto de Venta - Inicio de Sesión")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f0f0')
        
        # Centrar ventana
        self.center_window()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0', padx=40, pady=40)
        main_frame.pack(expand=True, fill='both')
        
        # Título
        title_label = tk.Label(main_frame, text="Sistema POS", 
                              font=('Arial', 24, 'bold'), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 30))
        
        # Frame de credenciales
        cred_frame = tk.Frame(main_frame, bg='#f0f0f0')
        cred_frame.pack(fill='x', pady=10)
        
        # Usuario
        tk.Label(cred_frame, text="Usuario:", 
                font=('Arial', 12), bg='#f0f0f0').pack(anchor='w')
        self.username_entry = tk.Entry(cred_frame, font=('Arial', 12), 
                                      width=25, relief='solid', bd=1)
        self.username_entry.pack(pady=(5, 15), fill='x')
        
        # Contraseña
        tk.Label(cred_frame, text="Contraseña:", 
                font=('Arial', 12), bg='#f0f0f0').pack(anchor='w')
        self.password_entry = tk.Entry(cred_frame, font=('Arial', 12), 
                                      width=25, show='*', relief='solid', bd=1)
        self.password_entry.pack(pady=(5, 20), fill='x')
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=10)
        
        self.login_btn = tk.Button(button_frame, text="Iniciar Sesión", 
                                  font=('Arial', 12, 'bold'),
                                  bg='#3498db', fg='white', 
                                  relief='flat', padx=20, pady=10,
                                  command=self.login)
        self.login_btn.pack(side='left', padx=(0, 10))
        
        self.cancel_btn = tk.Button(button_frame, text="Cancelar", 
                                   font=('Arial', 12),
                                   bg='#95a5a6', fg='white', 
                                   relief='flat', padx=20, pady=10,
                                   command=self.root.quit)
        self.cancel_btn.pack(side='left')
        
        # Atajos de teclado
        self.root.bind('<Return>', lambda e: self.login())
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # Focus inicial
        self.username_entry.focus()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Por favor ingrese usuario y contraseña")
            return
        
        user = self.db.authenticate_user(username, password)
        
        if user:
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'nombre': user[2],
                'rol': user[3]
            }
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def run(self):
        self.root.mainloop()
        return self.current_user

class UserManagement:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.setup_ui()
    
    def setup_ui(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gestión de Usuarios")
        self.window.geometry("600x400")
        self.window.configure(bg='#f0f0f0')
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Título
        title_label = tk.Label(main_frame, text="Gestión de Usuarios", 
                              font=('Arial', 18, 'bold'), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(0, 10))
        
        tk.Button(button_frame, text="Nuevo Usuario", 
                 command=self.new_user, bg='#27ae60', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Editar", 
                 command=self.edit_user, bg='#f39c12', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=(0, 10))
        
        tk.Button(button_frame, text="Eliminar", 
                 command=self.delete_user, bg='#e74c3c', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left')
        
        # Lista de usuarios
        columns = ('ID', 'Usuario', 'Nombre', 'Rol', 'Estado')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.load_users()
    
    def load_users(self):
        # Limpiar lista
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Cargar usuarios desde la base de datos
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, nombre, rol, 
                   CASE WHEN activo = 1 THEN 'Activo' ELSE 'Inactivo' END as estado
            FROM usuarios ORDER BY id
        ''')
        
        for user in cursor.fetchall():
            self.tree.insert('', 'end', values=user)
        
        conn.close()
    
    def new_user(self):
        self.user_form()
    
    def edit_user(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un usuario para editar")
            return
        
        item = self.tree.item(selection[0])
        user_id = item['values'][0]
        self.user_form(user_id)
    
    def delete_user(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un usuario para eliminar")
            return
        
        item = self.tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al usuario {username}?"):
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            self.load_users()
            messagebox.showinfo("Éxito", "Usuario eliminado correctamente")
    
    def user_form(self, user_id=None):
        form_window = tk.Toplevel(self.window)
        form_window.title("Nuevo Usuario" if not user_id else "Editar Usuario")
        form_window.geometry("400x300")
        form_window.configure(bg='#f0f0f0')
        
        # Variables
        username_var = tk.StringVar()
        password_var = tk.StringVar()
        nombre_var = tk.StringVar()
        rol_var = tk.StringVar(value="vendedor")
        
        # Cargar datos si es edición
        if user_id:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username, nombre, rol FROM usuarios WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                username_var.set(user_data[0])
                nombre_var.set(user_data[1])
                rol_var.set(user_data[2])
        
        # Formulario
        main_frame = tk.Frame(form_window, bg='#f0f0f0', padx=30, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        # Campos
        tk.Label(main_frame, text="Usuario:", bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=username_var, width=25).grid(row=0, column=1, pady=5, padx=(10, 0))
        
        tk.Label(main_frame, text="Contraseña:", bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=password_var, show='*', width=25).grid(row=1, column=1, pady=5, padx=(10, 0))
        
        tk.Label(main_frame, text="Nombre:", bg='#f0f0f0').grid(row=2, column=0, sticky='w', pady=5)
        tk.Entry(main_frame, textvariable=nombre_var, width=25).grid(row=2, column=1, pady=5, padx=(10, 0))
        
        tk.Label(main_frame, text="Rol:", bg='#f0f0f0').grid(row=3, column=0, sticky='w', pady=5)
        rol_combo = ttk.Combobox(main_frame, textvariable=rol_var, values=['admin', 'vendedor'], width=22)
        rol_combo.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        def save_user():
            username = username_var.get().strip()
            password = password_var.get().strip()
            nombre = nombre_var.get().strip()
            rol = rol_var.get()
            
            if not all([username, nombre, rol]):
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                if user_id:
                    # Actualizar usuario
                    if password:
                        password_hash = self.db.hash_password(password)
                        cursor.execute('''
                            UPDATE usuarios SET username=?, password=?, nombre=?, rol=?
                            WHERE id=?
                        ''', (username, password_hash, nombre, rol, user_id))
                    else:
                        cursor.execute('''
                            UPDATE usuarios SET username=?, nombre=?, rol=?
                            WHERE id=?
                        ''', (username, nombre, rol, user_id))
                else:
                    # Crear nuevo usuario
                    if not password:
                        messagebox.showerror("Error", "La contraseña es obligatoria para nuevos usuarios")
                        return
                    
                    password_hash = self.db.hash_password(password)
                    cursor.execute('''
                        INSERT INTO usuarios (username, password, nombre, rol)
                        VALUES (?, ?, ?, ?)
                    ''', (username, password_hash, nombre, rol))
                
                conn.commit()
                conn.close()
                form_window.destroy()
                self.load_users()
                messagebox.showinfo("Éxito", "Usuario guardado correctamente")
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El nombre de usuario ya existe")
                conn.close()
        
        tk.Button(button_frame, text="Guardar", command=save_user, 
                 bg='#27ae60', fg='white', relief='flat', padx=20).pack(side='left', padx=(0, 10))
        tk.Button(button_frame, text="Cancelar", command=form_window.destroy, 
                 bg='#95a5a6', fg='white', relief='flat', padx=20).pack(side='left')

