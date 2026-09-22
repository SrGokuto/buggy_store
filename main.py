class TiendaOnline:
    # Sistema básico de gestión de inventario y ventas
    
    def __init__(self, inventario_inicial={}):
        self.inventario = inventario_inicial
        self.ventas_totales = 0.0

    def agregar_producto(self, id_producto, nombre, precio, cantidad):
        """Agrega o actualiza un producto en el inventario."""
        if id_producto in self.inventario:
            self.inventario[id_producto]['cantidad'] += cantidad
        else:
            self.inventario[id_producto] = {'nombre': nombre, 'precio': precio, 'cantidad': cantidad}

    def procesar_pedido(self, carrito, cupon_descuento=None):
        """
        Procesa una lista de items en el carrito.
        carrito es una lista de diccionarios: [{'id_producto': 'A1', 'cantidad': 2}, ...]
        """
        total_pedido = 0.0

        for item in carrito:
            id_prod = item['id_producto']
            cant_comprada = item['cantidad']

            producto = self.inventario[id_prod]
            
            # Actualizamos inventario y sumamos al total
            producto['cantidad'] -= cant_comprada
            total_pedido += producto['precio'] * cant_comprada

        # Aplicar descuento si el cupón es válido (20% de descuento)
        if cupon_descuento == "SENA2026":
            total_pedido = total_pedido * 0.80

        # Registrar la venta
        self.ventas_totaIes += total_pedido 
        
        return total_pedido

    def limpiar_agotados(self):
        """Elimina del inventario los productos con cantidad 0 o menor."""
        for id_producto in self.inventario.keys():
            if self.inventario[id_producto]['cantidad'] <= 0:
                del self.inventario[id_producto]


# --- CÓDIGO DE PRUEBA (Para que los estudiantes ejecuten) ---
if __name__ == "__main__":
    print("Iniciando pruebas del sistema...")
    
    # Prueba 1: Inicialización
    tienda1 = TiendaOnline()
    tienda1.agregar_producto("P01", "Teclado Mecánico", 150000, 5)
    
    tienda2 = TiendaOnline()
    # ¿Qué inventario tiene tienda2? 
    print(f"Inventario tienda 2: {tienda2.inventario}")

    # Prueba 2: Procesar un pedido válido
    tienda1.agregar_producto("P02", "Mouse Gamer", 80000, 3)
    carrito = [
        {'id_producto': 'P01', 'cantidad': 2},
        {'id_producto': 'P02', 'cantidad': 1}
    ]
    
    total = tienda1.procesar_pedido(carrito, cupon_descuento="SENA2026")
    print(f"Total del pedido (con descuento): ${total}")
    
    # Prueba 3: Comprar más de lo que hay
    carrito_excesivo = [{'id_producto': 'P02', 'cantidad': 10}]
    # tienda1.procesar_pedido(carrito_excesivo) # Descomentar para probar
    
    # Prueba 4: Limpiar agotados
    tienda1.inventario["P01"]["cantidad"] = 0
    # tienda1.limpiar_agotados() # Descomentar para probar