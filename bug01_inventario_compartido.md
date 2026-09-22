# Bug 01 — Inventario compartido entre instancias

**Rama:** `fix/bug01`
**Archivo:** `main.py`
**Ubicación exacta:** línea 4 (con efecto en la línea 5), método `__init__` de la clase `TiendaOnline`
**Severidad:** Alta (corrupción de datos entre "tiendas")

---

## 1. Código con el bug

```python
class TiendaOnline:
    # Sistema básico de gestión de inventario y ventas

    def __init__(self, inventario_inicial={}):   # ← línea 4
        self.inventario = inventario_inicial      # ← línea 5
        self.ventas_totales = 0.0
```

## 2. ¿Qué está pasando?

En Python, los argumentos por defecto **se evalúan una sola vez, cuando se
define la función** (es decir, al cargar la clase), no cada vez que se llama.
Como `{}` es un objeto **mutable**, ese único diccionario queda "vivo" para
siempre y **todas las instancias de `TiendaOnline` terminan apuntando al mismo
objeto**.

```
TiendaOnline.__init__  ──default──▶  { }   (un único dict creado al importar main.py)
        │                                  ▲            ▲            ▲
        ▼                                  │            │            │
   tienda1.inventario ─────────────────────┘            │            │
   tienda2.inventario ──────────────────────────────────┘            │
   tienda3.inventario ───────────────────────────────────────────────┘
```

Consecuencia: cuando `tienda1.agregar_producto(...)` muta su inventario,
`tienda2`, `tienda3`, ... **"ven" esos mismos productos**, aunque nunca los
hayan agregado.

## 3. ¿Cómo se detecta?

El propio código de pruebas del archivo ya lo delataba (`main.py`, Prueba 1):

```python
tienda1 = TiendaOnline()
tienda1.agregar_producto("P01", "Teclado Mecánico", 150000, 5)

tienda2 = TiendaOnline()
# ¿Qué inventario tiene tienda2?
print(f"Inventario tienda 2: {tienda2.inventario}")
```

* **Antes del fix:** imprime
  `{'P01': {'nombre': 'Teclado Mecánico', 'precio': 150000, 'cantidad': 5}}`
  → tienda2 nace con productos que nunca agregó.
* **Después del fix:** imprime `{}` → tienda2 nace vacía e independiente.

## 4. Impacto

* Fuga de datos entre instancias: cualquier tienda ve el inventario de las demás.
* Imposible crear dos tiendas aisladas (multi-tienda, tests aislados, tenants).
* Los datos "fantasma" persisten entre ejecuciones de la clase dentro del
  mismo proceso (el dict no se reinicia nunca).

## 5. Fix aplicado

```python
def __init__(self, inventario_inicial=None):
    # None por defecto: cada instancia recibe su propio diccionario.
    # (Un {} como default se crea una sola vez y quedaría compartido.)
    self.inventario = inventario_inicial if inventario_inicial is not None else {}
    self.ventas_totales = 0.0
```

Ideas clave:

1. El parámetro pasa a ser `inventario_inicial=None` → **no se crea ningún
   objeto en la definición**; `None` es inmutable y seguro como default.
2. Si el llamador no pasa nada, se construye **un diccionario nuevo** en cada
   llamada (`{}`), por lo que cada instancia queda aislada.
3. Si el llamador **sí** pasa un inventario, se respeta tal cual.

> Nota: esto es equivalente a la alternativa sugerida
> `self.inventario = inventario_inicial or {}`, pero usa `is not None` para no
> rebindear sorpresivamente un dict **vacío pasado explícitamente** a otro
> objeto distinto (se preserva la identidad del argumento del llamador).

## 6. Test funcional que lo comprueba

**Archivo:** `tests/test_bug01_inventario_compartido.py`

Cubre 5 casos:

| Test | Qué verifica |
|---|---|
| `test_dos_instancias_no_comparten_el_mismo_diccionario` | `tienda1.inventario is not tienda2.inventario` |
| `test_producto_agregado_en_tienda1_no_aparece_en_tienda2` | Reproduce la *Prueba 1*: `tienda2` nace vacía |
| `test_mutaciones_de_una_instancia_no_afectan_a_las_demas` | Muta la 1ª de 5 tiendas; las otras 4 quedan `{}` |
| `test_cada_instancia_tiene_un_inventario_vacio_al_nacer` | Ninguna tienda recibe datos "fantasma" |
| `test_inventario_inicial_explicito_se_respeta` | El parámetro opcional sigue funcionando |

### Ejecución

```bash
python3 -m unittest discover -s tests -v
```

### Resultado de la verificación

| Momento | Resultado |
|---|---|
| Antes del fix (código original) | `FAILED (failures=5)` — el bug se reproduce |
| Después del fix | `Ran 5 tests ... OK` ✅ |

---

*Nota: este cambio corresponde **solo al Bug 01**. Los otros bugs del
repositorio (p. ej. el typo `ventas_totaIes` en `main.py:39`) se abordan en sus
respectivas ramas.*
