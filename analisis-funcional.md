# Análisis Funcional - Arena de Combate con Inventario

## 1. Problema que resuelve la aplicación

La aplicación es un simulador de combate por turnos donde un héroe se enfrenta a un enemigo. El héroe puede realizar acciones como atacar, curarse usando pociones de su inventario, defenderse o consultar su estado. El sistema calcula el daño aplicado, gestiona las curaciones, actualiza los HP de ambos combatientes y registra un historial completo de todas las acciones realizadas. El objetivo es demostrar cómo se pueden modelar sistemas de estado complejos usando programación funcional en lugar de programación orientada a objetos.

## 2. Estructuras de datos utilizadas

Se utilizaron dataclasses frozen (inmutables) para modelar las entidades del dominio:

- Personaje (dataclass frozen): Representa a un combatiente con nombre, hp, hp_max, ataque, defensa e inventario. Al ser frozen, no puede modificarse después de crearse.
- Objeto (dataclass frozen): Representa un ítem del inventario con nombre, tipo ("pocion", "arma", "armadura") y valor.
- Accion (dataclass frozen): Representa una acción registrada en el historial con turno, actor, tipo, detalle y daño.

Además:
- Tuplas: Usadas para el inventario (inventario: tuple) y para las acciones entrantes (("atacar",)).
- Diccionario: Usado dentro del closure crear_gestor_partida para encapsular el estado de la partida (jugador, enemigo, turno, historial, terminado).
- Listas: Usadas internamente en el historial antes de convertirse en tupla.

## 3. Dónde se aplicó la Unidad 1

### Funciones de Orden Superior (HOF)
- procesar_accion(personaje, accion, enemigo): Recibe una acción y decide qué hacer según su estructura. Es una HOF porque se le puede pasar cualquier acción como tupla y delega el comportamiento.
- transformar_inventario(inventario, transformacion): Recibe una función de transformación como parámetro y la aplica a cada objeto del inventario usando map.

### Pattern Matching (match/case)
En procesar_accion() se usa match accion: con casos para:
- case ("atacar",): Calcula daño y lo aplica.
- case ("curar",): Busca pociones y cura al personaje.
- case ("defender",): Aumenta la defensa temporalmente.
- case ("estado",): Muestra el estado actual.
- case _: Caso por defecto para acciones no reconocidas.

Esto demuestra que la estructura del dato (la tupla) determina el camino a seguir, en lugar de encadenar if/elif.

### Modelado de datos
Se usaron dataclasses frozen (Personaje, Objeto, Accion) para garantizar la inmutabilidad. El uso de frozen=True obliga a que cualquier cambio genere un nuevo objeto.

### Comparación funcional vs imperativo

Enfoque imperativo (NO usado):
pociones = []
for obj in inventario:
    if obj.tipo == "pocion":
        pociones.append(obj)

Enfoque funcional (SÍ usado):
pociones = list(filter(lambda obj: obj.tipo == "pocion", inventario))

Justificación: El enfoque funcional es más declarativo. Le decimos a Python "filtra los que sean pociones" en lugar de "recorre uno por uno y decide". Menos código, menos errores, más claro.

## 4. Dónde se aplicó la Unidad 2

### Lambda
Usadas en tres contextos específicos:
- filter: filter(lambda obj: obj.tipo == "pocion", inventario) — filtra objetos por tipo.
- map: map(lambda obj: obj.nombre, inventario) — extrae solo los nombres.
- reduce: reduce(lambda acc, obj: acc + obj.valor, inventario, 0) — suma los valores.

### Closure
La función crear_gestor_partida(jugador, enemigo) retorna un closure ejecutar_turno que encapsula el estado de la partida usando nonlocal. Este closure:
- Mantiene el turno actual.
- Acumula el historial de acciones.
- Verifica si la partida terminó.
- Modifica el estado sin usar variables globales ni clases.

### Inmutabilidad
- Todas las dataclasses son frozen=True.
- Cuando se aplica daño, se usa replace(personaje, hp=nuevo_hp) en lugar de personaje.hp -= danio.
- El inventario es una tupla, no una lista.
- El historial se actualiza creando una nueva lista con + en lugar de append.

### Pureza
Funciones puras (no modifican nada externo, siempre retornan lo mismo con las mismas entradas):
- calcular_danio
- aplicar_danio
- curar_personaje
- filtrar_por_tipo
- calcular_poder_total
- obtener_nombres_objetos
- procesar_accion

### map / filter / reduce
- filter: En filtrar_por_tipo() para obtener pociones.
- map: En obtener_nombres_objetos() y transformar_inventario().
- reduce: En calcular_poder_total() para sumar valores del inventario.

## 5. Partes puras e impuras

### Funciones puras
- calcular_danio: No modifica nada externo. Solo calcula y retorna.
- aplicar_danio: Retorna un nuevo Personaje usando replace().
- curar_personaje: Retorna un nuevo Personaje.
- filtrar_por_tipo: Solo retorna una lista filtrada.
- calcular_poder_total: Solo suma valores.
- obtener_nombres_objetos: Solo mapea nombres.
- procesar_accion: Retorna una tupla sin modificar las entradas.

### Funciones impuras
- _actualizar_vista: Modifica los widgets de Tkinter.
- _agregar_historial: Escribe en un widget de texto.
- _accion: Llama al closure y actualiza la UI.
- _reiniciar: Reinicia el estado y borra el widget.

## 6. Efectos secundarios

Los efectos secundarios están aislados en la capa visual:
- Modificar los widgets (config, insert, delete).
- Escribir en el historial de la interfaz.
- Reiniciar la partida (borrar el widget y crear nuevo estado).

El closure ejecutar_turno modifica el diccionario estado internamente, pero ese efecto está encapsulado y no afecta al resto del programa.

## 7. Inmutabilidad

- Las dataclasses Personaje, Objeto y Accion son frozen=True, lo que significa que sus atributos no pueden modificarse después de creadas.
- Cuando se aplica daño, se usa replace(personaje, hp=nuevo_hp) en lugar de mutar el objeto original.
- El inventario es una tupla (inmutable).
- El historial se actualiza con + en lugar de append.
- Cada turno genera nuevos objetos en lugar de modificar los existentes.

## 8. Closure implementado

Closure: crear_gestor_partida(jugador, enemigo) retorna la función ejecutar_turno.

Para qué sirve: Encapsula el estado de la partida (turno, historial, terminado) sin usar variables globales ni clases. Cada partida creada con esta función tiene su propio estado aislado.

Cómo funciona:
def crear_gestor_partida(jugador, enemigo):
    estado = {"jugador": jugador, "enemigo": enemigo, "turno": 0, "historial": [], "terminado": False}
    def ejecutar_turno(accion_jugador):
        nonlocal estado
        estado["turno"] = estado["turno"] + 1
        # procesar la accion, actualizar jugador, enemigo e historial
        return estado
    return ejecutar_turno

## 9. Qué partes sugirió la IA

- La estructura general en 3 capas (visual, lógica, estado).
- El uso de dataclass frozen para inmutabilidad.
- La idea de usar reduce para calcular el poder total.
- La sugerencia de usar un diccionario dentro del closure.
- El uso de filter/map/reduce en lugar de bucles.

## 10. Qué corregí o rechacé de la IA

- Rechacé: Una versión que usaba variables globales para el estado.
- Corregí: La IA sugirió usar for para filtrar el inventario. Lo cambié por filter con lambda.
- Corregí: La IA no usaba match/case. Lo agregué en procesar_accion.
- Corregí: La IA proponía clases para la lógica. Las reemplacé por funciones puras.
- Corregí: La IA no usaba frozen=True en las dataclasses. Lo agregué yo para garantizar inmutabilidad.

## 11. Qué aprendí técnicamente

- Cómo usar dataclass(frozen=True) para garantizar inmutabilidad real.
- Cómo un closure puede encapsular el estado de una partida sin variables globales.
- Cómo separar la lógica de la interfaz gráfica (callbacks delgados).
- Cómo usar match/case para procesar datos estructurados (tuplas).
- Cómo filter, map y reduce reemplazan bucles imperativos.
- La diferencia entre funciones puras (sin efectos secundarios) e impuras (con efectos).
- Cómo modelar un sistema de combate sin usar POO.