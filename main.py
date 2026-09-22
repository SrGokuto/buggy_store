class TiendaOnline:
    # Sistema básico de gestión de inventario y ventas
    
    def __init__(self, inventario_inicial=None):
        # None por defecto: cada instancia recibe su propio diccionario.
        # (Un {} como default se crea una sola vez y quedaría compartido.)
        self.inventario = inventario_inicial if inventario_inicial is not None else {}
        self.ventas_totales = 0.0

    def agregar_producto(self, id_producto, nombre, precio, cantidad):
        """Agrega o actualiza un producto en el inventario."""
        # Validar ANTES de tocar el inventario (nada se registra si el dato es inválido)
        if precio < 0:
            raise ValueError(f"El precio de '{id_producto}' no puede ser negativo: {precio}")
        if cantidad < 0:
            raise ValueError(f"La cantidad de '{id_producto}' no puede ser negativa: {cantidad}")

        if id_producto in self.inventario:
            producto = self.inventario[id_producto]
            producto['nombre'] = nombre   # actualizar nombre...
            producto['precio'] = precio   # ...y precio si el producto ya existe
            producto['cantidad'] += cantidad
        else:
            self.inventario[id_producto] = {'nombre': nombre, 'precio': precio, 'cantidad': cantidad}

    def procesar_pedido(self, carrito, cupon_descuento=None):
        """
        Procesa una lista de items en el carrito.
        carrito es una lista de diccionarios: [{'id_producto': 'A1', 'cantidad': 2}, ...]
        """
        total_pedido = 0.0

        # Validamos TODOS los ítems del carrito ANTES de tocar el inventario.
        # Así, un producto inexistente lanza un ValueError controlado (con el id
        # del producto) y el pedido no queda procesado a medias.
        for item in carrito:
            id_prod = item['id_producto']
            if id_prod not in self.inventario:
                raise ValueError(
                    f"No se puede procesar el pedido: el producto '{id_prod}' no existe en el inventario."
                )

        for item in carrito:
            id_prod = item['id_producto']
            cant_comprada = item['cantidad']

            producto = self.inventario[id_prod]
            
            # Validar stock suficiente antes de descontar (Bug 5)
            if cant_comprada > producto['cantidad']:
                raise ValueError(
                    f"Stock insuficiente para '{id_prod}': "
                    f"disponible {producto['cantidad']}, solicitado {cant_comprada}"
                )

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