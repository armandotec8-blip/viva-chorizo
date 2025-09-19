#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Punto de Venta (POS)
Archivo principal de ejecución
"""

import sys
import os
from login import LoginWindow
from pos_main import POSMain

def main():
    """Función principal del sistema POS"""
    try:
        # Mostrar ventana de login
        login_window = LoginWindow()
        user = login_window.run()
        
        # Si el usuario se autenticó correctamente, abrir el sistema principal
        if user:
            print(f"Usuario autenticado: {user['nombre']} ({user['rol']})")
            pos_system = POSMain(user)
            pos_system.run()
        else:
            print("Sesión cancelada por el usuario")
            
    except Exception as e:
        print(f"Error al ejecutar el sistema: {str(e)}")
        input("Presione Enter para salir...")
        sys.exit(1)

if __name__ == "__main__":
    main()


