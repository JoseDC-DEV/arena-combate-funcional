# ============================================================
# PROYECTO: ARENA DE COMBATE CON INVENTARIO
# Programación Funcional - Unidades 1 y 2
#CREADO POR JOSE ANDRES DE LA A CEDEÑO
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from dataclasses import dataclass, replace
from typing import Union, List
from functools import reduce

# ============================================================
# CAPA DE DATOS (ESTADO INMUTABLE)
# ============================================================

@dataclass(frozen=True)
class Personaje:
    """Representa un personaje. Es frozen (inmutable)."""
    nombre: str
    hp: int
    hp_max: int
    ataque: int
    defensa: int
    inventario: tuple

@dataclass(frozen=True)
class Objeto:
    """Representa un objeto del inventario."""
    nombre: str
    tipo: str
    valor: int

@dataclass(frozen=True)
class Accion:
    """Representa una acción registrada en el historial."""
    turno: int
    actor: str
    tipo: str
    detalle: str
    danio: int = 0

# ============================================================
# CAPA LÓGICA (FUNCIONES PURAS)
# ============================================================

def calcular_danio(ataque: int, defensa: int, multiplicador: int = 1) -> int:
    """Calcula el daño. No modifica nada externo. Es pura."""
    danio_base = max(1, ataque - defensa)
    return danio_base * multiplicador

def aplicar_danio(personaje: Personaje, danio: int) -> Personaje:
    """Retorna un NUEVO personaje con HP reducido. Inmutable."""
    nuevo_hp = max(0, personaje.hp - danio)
    return replace(personaje, hp=nuevo_hp)

def curar_personaje(personaje: Personaje, cantidad: int) -> Personaje:
    """Retorna un NUEVO personaje con HP aumentado. Inmutable."""
    nuevo_hp = min(personaje.hp_max, personaje.hp + cantidad)
    return replace(personaje, hp=nuevo_hp)

def filtrar_por_tipo(inventario: tuple, tipo: str) -> list:
    """Filtra objetos del inventario por tipo. Usa filter + lambda."""
    return list(filter(lambda obj: obj.tipo == tipo, inventario))

def calcular_poder_total(inventario: tuple) -> int:
    """Suma los valores de todos los objetos. Usa reduce."""
    return reduce(lambda acc, obj: acc + obj.valor, inventario, 0)

def obtener_nombres_objetos(inventario: tuple) -> list:
    """Extrae solo los nombres. Usa map + lambda."""
    return list(map(lambda obj: obj.nombre, inventario))

def procesar_accion(personaje: Personaje, accion: tuple, enemigo: Personaje) -> tuple:
    """
    HOF que procesa una acción usando match/case.
    Retorna (personaje_actualizado, mensaje, danio)
    """
    match accion:
        case ("atacar",):
            danio = calcular_danio(personaje.ataque, enemigo.defensa)
            return (personaje, f"{personaje.nombre} ataca y causa {danio} de daño.", danio)
        
        case ("curar",):
            pociones = filtrar_por_tipo(personaje.inventario, "pocion")
            if not pociones:
                return (personaje, f"{personaje.nombre} no tiene pociones.", 0)
            curado = curar_personaje(personaje, pociones[0].valor)
            return (curado, f"{personaje.nombre} usa {pociones[0].nombre} y recupera {pociones[0].valor} HP.", 0)
        
        case ("defender",):
            return (personaje, f"{personaje.nombre} se defiende. Defensa aumentada temporalmente.", 0)
        
        case ("estado",):
            poder = calcular_poder_total(personaje.inventario)
            return (personaje, f"{personaje.nombre} | HP: {personaje.hp}/{personaje.hp_max} | Poder: {poder}", 0)
        
        case _:
            return (personaje, "Acción no reconocida.", 0)

def crear_multiplicador(factor: int):
    """
    Closure real: retorna una función que multiplica el daño por 'factor'.
    El estado 'factor' queda encapsulado.
    """
    def multiplicar(danio_base: int) -> int:
        return danio_base * factor
    return multiplicar

def transformar_inventario(inventario: tuple, transformacion) -> tuple:
    """HOF que aplica una transformación a cada objeto del inventario."""
    return tuple(map(transformacion, inventario))

# ============================================================
# CAPA DE ESTADO (Gestor con closure)
# ============================================================

def crear_gestor_partida(jugador: Personaje, enemigo: Personaje):
    """
    Closure que encapsula el estado de la partida.
    Retorna una función que procesa turnos.
    """
    estado = {
        "jugador": jugador,
        "enemigo": enemigo,
        "turno": 0,
        "historial": [],
        "terminado": False
    }
    
    def ejecutar_turno(accion_jugador: tuple):
        nonlocal estado
        
        if estado["terminado"]:
            return "La partida ya terminó."
        
        estado["turno"] += 1
        turno_actual = estado["turno"]
        
        # Turno del jugador
        jugador_actual, mensaje_jugador, danio_jugador = procesar_accion(
            estado["jugador"], accion_jugador, estado["enemigo"]
        )
        
        # Aplicar daño al enemigo (inmutable)
        if danio_jugador > 0:
            enemigo_actualizado = aplicar_danio(estado["enemigo"], danio_jugador)
        else:
            enemigo_actualizado = estado["enemigo"]
        
        # Registrar en historial
        accion_registrada = Accion(
            turno=turno_actual,
            actor=jugador_actual.nombre,
            tipo=accion_jugador[0],
            detalle=mensaje_jugador,
            danio=danio_jugador
        )
        
        # Actualizar estado (inmutable)
        estado["jugador"] = jugador_actual
        estado["enemigo"] = enemigo_actualizado
        estado["historial"] = estado["historial"] + [accion_registrada]
        
        # Verificar si el enemigo murió
        if enemigo_actualizado.hp <= 0:
            estado["terminado"] = True
            return f"{mensaje_jugador}\n\n¡{enemigo_actualizado.nombre} ha sido derrotado! ¡Victoria!"
        
        # Si la acción fue "estado", no hay contraataque
        if accion_jugador[0] == "estado":
            return mensaje_jugador
        
        # Turno del enemigo (contraataque simple)
        danio_enemigo = calcular_danio(estado["enemigo"].ataque, jugador_actual.defensa)
        jugador_actualizado = aplicar_danio(jugador_actual, danio_enemigo)
        
        accion_enemigo = Accion(
            turno=turno_actual,
            actor=enemigo_actualizado.nombre,
            tipo="contraataque",
            detalle=f"{enemigo_actualizado.nombre} contraataca y causa {danio_enemigo} de daño.",
            danio=danio_enemigo
        )
        
        estado["jugador"] = jugador_actualizado
        estado["historial"] = estado["historial"] + [accion_enemigo]
        
        # Verificar si el jugador murió
        if jugador_actualizado.hp <= 0:
            estado["terminado"] = True
            return f"{mensaje_jugador}\n{accion_enemigo.detalle}\n\n¡{jugador_actualizado.nombre} ha sido derrotado! Derrota."
        
        return f"{mensaje_jugador}\n{accion_enemigo.detalle}"
    
    def obtener_estado():
        return estado
    
    return ejecutar_turno, obtener_estado


# ============================================================
# CAPA VISUAL (INTERFAZ GRÁFICA)
# ============================================================

class ArenaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("⚔️ Arena de Combate Funcional")
        self.root.geometry("900x700")
        
        espada = Objeto("Espada de Fuego", "arma", 15)
        pocion = Objeto("Poción Mayor", "pocion", 30)
        armadura = Objeto("Armadura de Dragón", "armadura", 10)
        
        self.jugador = Personaje(
            nombre="Héroe", hp=100, hp_max=100, ataque=25, defensa=10,
            inventario=(espada, pocion, armadura)
        )
        
        self.enemigo = Personaje(
            nombre="Dragón", hp=120, hp_max=120, ataque=20, defensa=8, inventario=()
        )
        
        self.ejecutar_turno, self.obtener_estado = crear_gestor_partida(
            self.jugador, self.enemigo
        )
        
        self._construir_interfaz()
        self._actualizar_vista()
    
    def _construir_interfaz(self):
        titulo = tb.Label(
            self.root, text="⚔️ ARENA DE COMBATE ⚔️",
            font=("Helvetica", 20, "bold"), bootstyle="danger"
        )
        titulo.pack(pady=10)
        
        frame_estado = tb.LabelFrame(self.root, text="Estado de los Combatientes", padding=10)
        frame_estado.pack(fill="x", padx=15, pady=5)
        
        self.lbl_jugador = tb.Label(frame_estado, text="", font=("Helvetica", 12))
        self.lbl_jugador.pack(anchor="w")
        
        self.lbl_enemigo = tb.Label(frame_estado, text="", font=("Helvetica", 12))
        self.lbl_enemigo.pack(anchor="w")
        
        frame_acciones = tb.LabelFrame(self.root, text="Acciones", padding=10)
        frame_acciones.pack(fill="x", padx=15, pady=5)
        
        botones_frame = tb.Frame(frame_acciones)
        botones_frame.pack()
        
        tb.Button(botones_frame, text="🗡️ Atacar", bootstyle="danger",
                  command=lambda: self._accion("atacar")).pack(side="left", padx=5)
        tb.Button(botones_frame, text="🧪 Curar", bootstyle="success",
                  command=lambda: self._accion("curar")).pack(side="left", padx=5)
        tb.Button(botones_frame, text="🛡️ Defender", bootstyle="info",
                  command=lambda: self._accion("defender")).pack(side="left", padx=5)
        tb.Button(botones_frame, text="📊 Estado", bootstyle="secondary",
                  command=lambda: self._accion("estado")).pack(side="left", padx=5)
        
        frame_inv = tb.LabelFrame(self.root, text="Inventario del Héroe", padding=10)
        frame_inv.pack(fill="x", padx=15, pady=5)
        
        self.lbl_inventario = tb.Label(frame_inv, text="", font=("Helvetica", 10))
        self.lbl_inventario.pack(anchor="w")
        
        frame_hist = tb.LabelFrame(self.root, text="Historial de Acciones", padding=10)
        frame_hist.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.txt_historial = tk.Text(frame_hist, height=10, font=("Courier", 10))
        self.txt_historial.pack(fill="both", expand=True)
        
        tb.Button(self.root, text="🔄 Reiniciar Partida", bootstyle="warning",
                  command=self._reiniciar).pack(pady=10)
    
    def _accion(self, tipo):
        """Callback que delega a la lógica. NO contiene lógica de negocio."""
        mensaje = self.ejecutar_turno((tipo,))
        self._actualizar_vista()
        self._agregar_historial(mensaje)
    
    def _actualizar_vista(self):
        """Actualiza la vista desde el estado (efecto secundario justificado)."""
        estado = self.obtener_estado()
        jugador = estado["jugador"]
        enemigo = estado["enemigo"]
        
        self.lbl_jugador.config(
            text=f"🦸 {jugador.nombre}: HP {jugador.hp}/{jugador.hp_max} | ATK {jugador.ataque} | DEF {jugador.defensa}"
        )
        self.lbl_enemigo.config(
            text=f"🐉 {enemigo.nombre}: HP {enemigo.hp}/{enemigo.hp_max} | ATK {enemigo.ataque} | DEF {enemigo.defensa}"
        )
        
        nombres = obtener_nombres_objetos(jugador.inventario)
        self.lbl_inventario.config(text=" | ".join(nombres) if nombres else "Vacío")
    
    def _agregar_historial(self, mensaje):
        """Efecto secundario: escribir en el widget de texto."""
        self.txt_historial.insert("end", f"{mensaje}\n{'─' * 50}\n")
        self.txt_historial.see("end")
    
    def _reiniciar(self):
        """Reinicia la partida creando nuevos personajes."""
        espada = Objeto("Espada de Fuego", "arma", 15)
        pocion = Objeto("Poción Mayor", "pocion", 30)
        armadura = Objeto("Armadura de Dragón", "armadura", 10)
        
        self.jugador = Personaje("Héroe", 100, 100, 25, 10, (espada, pocion, armadura))
        self.enemigo = Personaje("Dragón", 120, 120, 20, 8, ())
        
        self.ejecutar_turno, self.obtener_estado = crear_gestor_partida(
            self.jugador, self.enemigo
        )
        
        self.txt_historial.delete("1.0", "end")
        self._actualizar_vista()


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    app = tb.Window(themename="darkly")
    ArenaApp(app)
    app.mainloop()