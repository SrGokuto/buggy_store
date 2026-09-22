# Bug 06 — Compra de producto inexistente lanza `KeyError`

**Rama:** `fix/bug06`
**Archivo:** `main.py`
**Ubicación exacta:** línea 26 original — `producto = self.inventario[id_prod]`, dentro de `procesar_pedido`
*(tras el fix, la validación previa vive en las líneas 31-39 y el acceso original quedó protegido en la línea 45)*
**Severidad:** Media-Alta (pérdida del pedido + inventario corrupto a mitad de operación)
**Categoría:** #5/#6 — inventario

---

## 1. Código con el bug

```python
def procesar_pedido(self, carrito, cupon_descuento=None):
    total_pedido = 0.0

    for item in carrito:
        id_prod = item['id_producto']
        cant_comprada = item['cantidad']

        producto = self.inventario[id_prod]   # ← LÍNEA 26: KeyError si el id no existe

        # Actualizamos inventario y sumamos al total
        producto['cantidad'] -= cant_comprada
        total_pedido += producto['precio'] * cant_comprada
    ...
```

## 2. ¿Qué está pasando?

`self.inventario[id_prod]` es una indexación directa de diccionario. Si
`id_prod` no está, Python lanza un **`KeyError` sin control en pleno recorrido
del carrito**. Dos problemas se combinan:

1. **Error incontrolado:** el llamador recibe un `KeyError` crudo que no
   explica qué pasó ni qué producto faltaba.
2. **Se pierde el pedido (atomicidad rota):** como la validación no es previa,
   todos los ítems procesados **ANTES** del faltante **ya descontaron stock**.

```
carrito = [ P01 (existe), ZZZ (no existe) ]
                │                │
                ▼                ▼
        descuenta 2 unidades   💥 KeyError  ──▶  P01 ya quedó descontado
        suma al total                        inventario CORRUPTO y
                                             pedido perdido a medias
```

Ejemplo real:

```python
tienda.procesar_pedido([
    {'id_producto': 'P01', 'cantidad': 2},   # ✅ se descuenta
    {'id_producto': 'ZZZ', 'cantidad': 1},   # ❌ KeyError → todo se pierde
])
# KeyError: 'ZZZ'   (y P01 ya perdió 2 unidades para siempre)
```

## 3. Fix aplicado (bug principal)

**Validar TODO el carrito ANTES de tocar el inventario** y lanzar un error
controlado (`ValueError` con el id del producto):

```python
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
    ...  # segunda pasada: aquí ya sabemos que todos los productos existen
```

Propiedades del fix:

| Propiedad | Antes | Después |
|---|---|---|
| Tipo de error | `KeyError` crudo | `ValueError` controlado y capturable |
| Mensaje | Solo el id (`'ZZZ'`) | Explica qué pasa y **qué producto falta** |
| Cuándo falla | A mitad del recorrido | **Antes** de la primera mutación |
| Inventario al fallar | Descuentos parciales (corrupto) | **Intacto** (todo o nada) |
| Varios faltantes | KeyError silencioso del primero en ejecutarse | Reporta el primero del carrito, sin efectos secundarios |

Uso desde el llamador:

```python
try:
    total = tienda.procesar_pedido(carrito)
except ValueError as e:
    print(f"Pedido rechazado: {e}")   # se puede corregir el carrito y reintentar
```

## 4. Fix aplicado (bonus — bugs menores de la descripción)

### Bonus A — `agregar_producto` no actualizaba nombre/precio (líneas 8-22)

```python
if id_producto in self.inventario:
    producto = self.inventario[id_producto]
    producto['nombre'] = nombre   # actualizar nombre...
    producto['precio'] = precio   # ...y precio si el producto ya existe
    producto['cantidad'] += cantidad   # la cantidad sigue SUMÁNDOSE
```

Antes solo hacía `cantidad += ...`, dejando nombre y precio desactualizados.

### Bonus B — sin validación de precios/cantidades negativos (líneas 10-14)

```python
if precio < 0:
    raise ValueError(f"El precio de '{id_producto}' no puede ser negativo: {precio}")
if cantidad < 0:
    raise ValueError(f"La cantidad de '{id_producto}' no puede ser negativa: {cantidad}")
```

La validación va **antes** de cualquier modificación: si el dato es inválido,
no se crea ni se altera nada en el inventario.

## 5. Test funcional que lo comprueba

**Archivo:** `tests/test_bug06_producto_inexistente.py` (7 tests)

| Test | Qué verifica |
|---|---|
| `test_producto_inexistente_lanza_error_controlado` | `ValueError` (no `KeyError`) e indica el id `ZZZ` |
| `test_pedido_fallido_no_modifica_el_inventario` | Ítem válido ANTES del faltante **no** se descuenta |
| `test_reporta_el_primer_producto_faltante` | Con varios faltantes: mensaje claro e inventario intacto |
| `test_actualiza_nombre_y_precio_si_el_producto_ya_existe` | Bonus A: nombre/precio nuevos + cantidad suma 5+2=7 |
| `test_precio_negativo_lanza_error_controlado` | Bonus B: rechaza y **no** registra el producto |
| `test_cantidad_negativa_lanza_error_controlado` | Bonus B: rechaza y **no** registra el producto |
| `test_precio_negativo_no_altera_un_producto_existente` | La validación ocurre antes de mutar |

### Ejecución

```bash
python3 -m unittest discover -s tests -v
```

### Resultado de la verificación

| Momento | Resultado |
|---|---|
| Antes del fix (código original) | `FAILED (failures=4, errors=3)` — 3 errores son los `KeyError` crudos |
| Después del fix | `Ran 7 tests ... OK` ✅ |

## 6. Notas de alcance

* **Otros bugs NO tocados** (pertenecen a sus propias ramas): typo
  `ventas_totaIes` (hoy `main.py:56`), descuento que multiplica por `1.20`
  (`main.py:53`) y el Bug 01 del diccionario compartido (`main.py:4`).
* Debido al typo `ventas_totaIes`, el **camino feliz** de `procesar_pedido`
  (carrito 100% válido) todavía revienta con `AttributeError` por ese otro
  bug; por eso estos tests se enfocan en el camino de error del Bug 06 y las
  tiendas se construyen con `inventario_inicial` explícito para aislarse del
  Bug 01 (que sigue abierto en esta rama).
