import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import random
import math
import os

# --- IMPORTAR PILLOW ---
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ ADVERTENCIA: Pillow no está instalado. Usando texto de emergencia.")

class JuegoBingoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel del Administrador - Control de Bingo")
        #self.root.geometry("500x750")
        # Forzar centrado estricto en el monitor principal
        self.root.update_idletasks()
        w_pantalla = self.root.winfo_screenwidth()
        h_pantalla = self.root.winfo_screenheight()
        x_admin = (w_pantalla // 2) - (500 // 2)
        y_admin = (h_pantalla // 2) - (750 // 2)
        self.root.geometry(f"500x750+{x_admin}+{y_admin}")
        
        # Paleta de colores - Light Premium Theme
        self.c_azul = "#091433"    
        self.c_verde = "#394f3d"   
        self.c_beige = "#ebd6b4"   
        self.c_naranja = "#9c451b" 
        self.c_rojo = "#561118"    
        self.c_sombra_oscura = "#03081a" 
        self.c_sombra_clara = "#cfb894"  
        
        self.root.configure(bg=self.c_beige)
        
        # Variables de estado
        self.cartones = {}
        self.bolas_sacadas = []
        self.bolas_disponibles = list(range(1, 91))
        
        self.linea_cantada = False
        self.bingo_cantado = False
        self.ruleta_girando = False
        self.angulo_actual_ruleta = 0.0
        self.bola_en_espera = None
        
        self.ganadores_teoricos_linea = []
        self.ganadores_teoricos_bingo = []
        
        self.crear_interfaz_admin()
        self.ventana_publico = None
        
        # --- CARGA Y CACHÉ DEL LOGO ---
        self.logo_pil_base = None   
        self.logo_publico_tk = None 
        self.last_r_in = 0  

        if PIL_AVAILABLE:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            logo_path = os.path.join(script_dir, "logo.png")
            
            if os.path.exists(logo_path):
                try:
                    self.logo_pil_base = Image.open(logo_path)
                except Exception:
                    self.logo_pil_base = None

        self.abrir_pantalla_publico()

    # ==========================================
    # INTERFAZ ADMINISTRADOR
    # ==========================================
    def crear_interfaz_admin(self):
        def crear_titulo(padre, texto):
            tk.Label(padre, text=texto.upper(), font=("Helvetica", 10, "bold"), fg=self.c_azul, bg=self.c_beige, anchor="w").pack(fill="x", pady=(20, 5))

        main_frame = tk.Frame(self.root, bg=self.c_beige, padx=25, pady=10)
        main_frame.pack(fill="both", expand=True)

        crear_titulo(main_frame, "Configuración de Ronda")
        f_arch = tk.Frame(main_frame, bg=self.c_beige)
        f_arch.pack(fill="x")
        tk.Button(f_arch, text="Cargar CSV", command=self.cargar_csv, bg=self.c_azul, fg=self.c_beige, font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", padx=15, pady=5).pack(side="left")
        self.lbl_status = tk.Label(f_arch, text="Esperando archivo...", fg=self.c_rojo, bg=self.c_beige, font=("Helvetica", 10))
        self.lbl_status.pack(side="left", padx=15)

        crear_titulo(main_frame, "Extracción")
        self.btn_sacar = tk.Button(main_frame, text="SACAR BOLILLA", font=("Helvetica", 16, "bold"), command=self.iniciar_extraccion, state="disabled", bg=self.c_naranja, fg=self.c_beige, relief="flat", height=2, cursor="hand2")
        self.btn_sacar.pack(fill="x", pady=10)
        
        self.lbl_admin_bola = tk.Label(main_frame, text="--", font=("Helvetica", 36, "bold"), bg=self.c_beige, fg=self.c_rojo)
        self.lbl_admin_bola.pack(pady=5)

        # --- SECCIÓN MODIFICADA: SOLO CONSULTA ---
        crear_titulo(main_frame, "Consulta Rápida")
        f_val = tk.Frame(main_frame, bg=self.c_beige)
        f_val.pack(fill="x")
        
        tk.Label(f_val, text="N°:", bg=self.c_beige, fg=self.c_azul, font=("Helvetica", 12)).pack(side="left")
        self.entry_carton_val = tk.Entry(f_val, width=6, font=("Helvetica", 14), justify="center", bg="white", fg=self.c_azul, relief="flat")
        self.entry_carton_val.pack(side="left", padx=10)
        
        self.btn_val_linea = tk.Button(f_val, text="Consultar Línea", bg=self.c_verde, fg=self.c_beige, font=("Helvetica", 10, "bold"), relief="flat", command=lambda: self.validar_premio("linea"), padx=10)
        self.btn_val_linea.pack(side="left", padx=5)
        
        self.btn_val_bingo = tk.Button(f_val, text="Consultar Bingo", bg=self.c_rojo, fg=self.c_beige, font=("Helvetica", 10, "bold"), relief="flat", command=lambda: self.validar_premio("bingo"), padx=10)
        self.btn_val_bingo.pack(side="left", padx=5)

        # --- SECCIÓN NUEVA: CIERRE DE ETAPAS ---
        crear_titulo(main_frame, "Control de Juego (Cerrar)")
        f_cierre = tk.Frame(main_frame, bg=self.c_beige)
        f_cierre.pack(fill="x")
        
        self.btn_cerrar_linea = tk.Button(f_cierre, text="Cerrar Línea", bg=self.c_azul, fg=self.c_beige, font=("Helvetica", 10, "bold"), relief="flat", command=self.cerrar_linea, padx=10, width=15)
        self.btn_cerrar_linea.pack(side="left", padx=(0, 10))
        
        self.btn_cerrar_bingo = tk.Button(f_cierre, text="Cerrar Bingo", bg=self.c_sombra_oscura, fg=self.c_beige, font=("Helvetica", 10, "bold"), relief="flat", command=self.cerrar_bingo, padx=10, width=15)
        self.btn_cerrar_bingo.pack(side="left")

        crear_titulo(main_frame, "Monitoreo en Vivo")
        self.txt_proyecciones = tk.Text(main_frame, wrap="word", font=("Courier", 11), bg=self.c_azul, fg=self.c_beige, padx=15, pady=15, relief="flat", borderwidth=0)
        self.txt_proyecciones.pack(fill="both", expand=True, pady=5)

    # ==========================================
    # INTERFAZ PÚBLICO
    # ==========================================
    def abrir_pantalla_publico(self):
        self.ventana_publico = tk.Toplevel(self.root)
        self.ventana_publico.title("BINGO - Pantalla Principal")
        #self.ventana_publico.geometry("1600x900") 
        # Forzar centrado estricto en el monitor principal
        self.ventana_publico.update_idletasks()
        w_pantalla = self.root.winfo_screenwidth()
        h_pantalla = self.root.winfo_screenheight()
        # La hacemos un poco más chica de arranque para que no te tape toda la pantalla
        # y la desfasamos un poco para que no tape al panel de control
        w_pub, h_pub = 1280, 720 
        x_pub = (w_pantalla // 2) - (w_pub // 2) + 50
        y_pub = (h_pantalla // 2) - (h_pub // 2) + 50
        self.ventana_publico.geometry(f"{w_pub}x{h_pub}+{x_pub}+{y_pub}")
        self.ventana_publico.configure(bg=self.c_beige)
        
        # Grid optimizado para maximizar el área de juego
        self.ventana_publico.rowconfigure(0, weight=0) # Cabecera fija y pequeña
        self.ventana_publico.rowconfigure(1, weight=1) # Juego expandible
        self.ventana_publico.columnconfigure(0, weight=65)
        self.ventana_publico.columnconfigure(1, weight=35)

        # --- HEADER COMPACTO ---
        frame_header = tk.Frame(self.ventana_publico, bg=self.c_beige)
        frame_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(15, 5))
        
        # Título más pequeño y elegante
        tk.Label(frame_header, text="B I N   C A P U   P E Ñ A", font=("Helvetica", 22, "bold"), fg=self.c_azul, bg=self.c_beige).pack()
        
        # Subtítulo más discreto
        self.lbl_ronda_publico = tk.Label(frame_header, text="ESPERANDO RONDA...", font=("Helvetica", 10, "bold"), fg=self.c_naranja, bg=self.c_beige)
        self.lbl_ronda_publico.pack(pady=(2, 8))
        
        # Línea separadora más sutil
        linea = tk.Frame(frame_header, bg=self.c_sombra_clara, height=1)
        linea.pack(fill="x", padx=100)

        # --- ÁREA DE JUEGO REPOTENCIADA ---
        frame_izquierdo = tk.Frame(self.ventana_publico, bg=self.c_beige)
        frame_izquierdo.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.canvas_ruleta = tk.Canvas(frame_izquierdo, bg=self.c_beige, highlightthickness=0)
        self.canvas_ruleta.pack(fill="both", expand=True)
        self.canvas_ruleta.bind("<Configure>", lambda e: self.dibujar_ruleta_estatica(self.angulo_actual_ruleta))

        frame_derecho = tk.Frame(self.ventana_publico, bg=self.c_beige)
        frame_derecho.grid(row=1, column=1, sticky="nsew", padx=20, pady=10)
        
        frame_bola_actual = tk.Frame(frame_derecho, bg=self.c_beige)
        frame_bola_actual.pack(fill="x", pady=(0, 10))
        
        tk.Label(frame_bola_actual, text="Ú L T I M O   N Ú M E R O", font=("Helvetica", 12, "bold"), fg=self.c_azul, bg=self.c_beige).pack()
        self.lbl_bola_publico = tk.Label(frame_bola_actual, text="--", font=("Helvetica", 140, "bold"), fg=self.c_rojo, bg=self.c_beige)
        self.lbl_bola_publico.pack()
        
        tk.Label(frame_derecho, text="N Ú M E R O S   S O R T E A D O S", font=("Helvetica", 9, "bold"), fg=self.c_azul, bg=self.c_beige).pack(pady=(0, 5))
        
        self.canvas_tablero = tk.Canvas(frame_derecho, bg=self.c_beige, highlightthickness=0)
        self.canvas_tablero.pack(fill="both", expand=True)
        self.canvas_tablero.bind("<Configure>", lambda e: self.dibujar_tablero_responsive())
        
        self.circulos_tablero = {} 

    def dibujar_tablero_responsive(self):
        if not hasattr(self, 'canvas_tablero') or not self.canvas_tablero.winfo_exists(): return
        self.canvas_tablero.delete("all")
        self.circulos_tablero.clear()
        w, h = self.canvas_tablero.winfo_width(), self.canvas_tablero.winfo_height()
        if w <= 1 or h <= 1: return 
        
        cols, filas = 10, 9
        pad_x, pad_y = w * 0.05, h * 0.05
        w_util, h_util = w - (pad_x * 2), h - (pad_y * 2)
        espacio_x, espacio_y = w_util / cols, h_util / filas
        radio = min(espacio_x, espacio_y) * 0.42
        offset_x, offset_y = pad_x + (espacio_x / 2), pad_y + (espacio_y / 2)
        font_size = max(8, int(radio * 0.8)) 
        
        for idx in range(1, 91):
            r, c = (idx - 1) // cols, (idx - 1) % cols
            cx, cy = offset_x + (c * espacio_x), offset_y + (r * espacio_y)
            if idx in self.bolas_sacadas:
                self.canvas_tablero.create_oval(cx-radio+1, cy-radio+2, cx+radio+1, cy+radio+2, outline="", fill=self.c_sombra_clara)
                self.canvas_tablero.create_oval(cx-radio, cy-radio, cx+radio, cy+radio, outline="", fill=self.c_rojo)
                self.canvas_tablero.create_text(cx+1, cy+1, text=f"{idx}", font=("Helvetica", font_size, "bold"), fill=self.c_sombra_oscura)
                self.canvas_tablero.create_text(cx, cy, text=f"{idx}", font=("Helvetica", font_size, "bold"), fill=self.c_beige)
            else:
                self.canvas_tablero.create_oval(cx-radio, cy-radio, cx+radio, cy+radio, outline=self.c_azul, width=1, fill="")
                self.canvas_tablero.create_text(cx, cy, text=f"{idx}", font=("Helvetica", font_size), fill=self.c_azul)

    def dibujar_ruleta_estatica(self, angulo_offset=0, bola_ganadora_iluminada=None):
        if not self.ventana_publico or not self.canvas_ruleta.winfo_exists(): return
        self.canvas_ruleta.delete("ruleta")
        lista_dibujo = list(self.bolas_disponibles)
        if self.bola_en_espera and self.bola_en_espera not in lista_dibujo:
            lista_dibujo.insert(self.indice_espera, self.bola_en_espera)

        n = len(lista_dibujo)
        if n == 0: return
        w, h = self.canvas_ruleta.winfo_width(), self.canvas_ruleta.winfo_height()
        cx, cy = w / 2, h / 2
        if w <= 1 or h <= 1: return
            
        r_out = min(w, h) * 0.485 
        r_in = r_out * 0.22 
        angulo_porcion = 360 / n
        self.canvas_ruleta.create_oval(cx-r_out+1, cy-r_out+2, cx+r_out+1, cy+r_out+2, fill=self.c_sombra_clara, outline="", tags="ruleta")
        
        colores_porciones = [self.c_azul, self.c_verde, self.c_naranja]
        for i, bola in enumerate(lista_dibujo):
            ang_inicio = angulo_offset + (i * angulo_porcion)
            color_fondo = self.c_rojo if bola_ganadora_iluminada == bola else colores_porciones[i % 3]
            self.canvas_ruleta.create_arc(cx-r_out, cy-r_out, cx+r_out, cy+r_out, start=ang_inicio, extent=angulo_porcion, fill=color_fondo, tags="ruleta", outline="", width=0)
            
            ang_centro = ang_inicio + (angulo_porcion / 2)
            rad = math.radians(ang_centro)
            tx, ty = cx + (r_out * 0.83) * math.cos(rad), cy - (r_out * 0.83) * math.sin(rad)
            font_size = max(8, int((r_out * 3.14 / n) * 0.65))
            if n < 30: font_size = min(28, font_size)
            
            self.canvas_ruleta.create_text(tx+1, ty+1, text=str(bola), font=("Helvetica", font_size), fill=self.c_sombra_oscura, angle=ang_centro % 360, tags="ruleta")
            self.canvas_ruleta.create_text(tx, ty, text=str(bola), font=("Helvetica", font_size), fill=self.c_beige, angle=ang_centro % 360, tags="ruleta")
        
        self.canvas_ruleta.create_oval(cx-r_in+1, cy-r_in+2, cx+r_in+1, cy+r_in+2, fill=self.c_sombra_oscura, outline="", tags="ruleta")
        self.canvas_ruleta.create_oval(cx-r_in, cy-r_in, cx+r_in, cy+r_in, fill=self.c_beige, outline="", tags="ruleta")
        
        if self.logo_pil_base:
            target_diametro = r_in * 2 * 0.82 
            if target_diametro > 5:
                if abs(self.last_r_in - r_in) > 1:
                    self.last_r_in = r_in
                    w_o, h_o = self.logo_pil_base.size
                    ratio = w_o / h_o
                    tw = int(target_diametro) if ratio > 1 else int(target_diametro * ratio)
                    th = int(target_diametro / ratio) if ratio > 1 else int(target_diametro)
                    logo_scaled = self.logo_pil_base.resize((tw, th), Image.Resampling.LANCZOS).convert("RGBA")
                    mask = Image.new('L', (tw, th), 0)
                    ImageDraw.Draw(mask).ellipse((-2, -2, tw + 1, th + 1), fill=255)
                    logo_scaled.putalpha(mask)
                    self.logo_publico_tk = ImageTk.PhotoImage(logo_scaled)
                self.canvas_ruleta.create_image(cx, cy, image=self.logo_publico_tk, anchor="center", tags="ruleta")
        else:
            fs = max(8, int(r_in * 0.22))
            self.canvas_ruleta.create_text(cx+1, cy+1, text="BIN\nCAPU\nPEÑA", font=("Georgia", fs, "bold"), fill=self.c_sombra_clara, justify="center", tags="ruleta")
            self.canvas_ruleta.create_text(cx, cy, text="BIN\nCAPU\nPEÑA", font=("Georgia", fs, "bold"), fill=self.c_azul, justify="center", tags="ruleta")

        poly_shadow = [cx-12+1, cy-r_out-25+1, cx+12+1, cy-r_out-25+1, cx+1, cy-r_out+5+1]
        self.canvas_ruleta.create_polygon(poly_shadow, fill=self.c_sombra_clara, outline="", tags="ruleta")
        poly = [cx-12, cy-r_out-25, cx+12, cy-r_out-25, cx, cy-r_out+5]
        self.canvas_ruleta.create_polygon(poly, fill=self.c_rojo, outline="", tags="ruleta")

    def cargar_csv(self):
        ruta = filedialog.askopenfilename(initialdir="./rondas", title="Seleccionar Ronda", filetypes=[("Archivos CSV", "*.csv")])
        if not ruta: return
        try:
            cartones_nuevos = {}
            ids_vistos = set()
            errores = []
            total_errores = 0

            def registrar_error(mensaje):
                nonlocal total_errores
                total_errores += 1
                if len(errores) < 8:
                    errores.append(mensaje)

            with open(ruta, mode="r", encoding="utf-8") as f:
                for numero_fila, fila in enumerate(csv.reader(f), start=1):
                    fila = [celda.strip() for celda in fila]
                    if not fila or all(celda == "" for celda in fila):
                        continue

                    # Ahora esperamos 16 columnas: 1 ID + 15 números reales
                    if len(fila) != 16:
                        registrar_error(f"Fila {numero_fila}: se esperaban 16 columnas, pero hay {len(fila)}.")
                        continue

                    try:
                        id_c = int(fila[0])
                    except ValueError:
                        registrar_error(f"Fila {numero_fila}: el ID del cartón no es un número entero.")
                        continue

                    if id_c <= 0:
                        registrar_error(f"Fila {numero_fila}: el ID del cartón debe ser positivo.")
                        continue

                    if id_c in ids_vistos:
                        registrar_error(f"Fila {numero_fila}: el cartón {id_c} está repetido.")
                        continue

                    try:
                        # Tomamos los 15 números
                        nums = [int(x) for x in fila[1:16]]
                    except ValueError:
                        registrar_error(f"Fila {numero_fila}: todos los números del cartón deben ser enteros.")
                        continue

                    fuera_de_rango = sorted({n for n in nums if n < 1 or n > 90})
                    if fuera_de_rango:
                        registrar_error(f"Fila {numero_fila}: hay números fuera de 1-90: {fuera_de_rango}.")
                        continue

                    repetidos = sorted({n for n in nums if nums.count(n) > 1})
                    if repetidos:
                        registrar_error(f"Fila {numero_fila}: hay números repetidos en el cartón: {repetidos}.")
                        continue

                    ids_vistos.add(id_c)

                    # Reconstruimos las 3 filas (5 números por fila)
                    # Esto es vital para que la validación de Línea funcione perfecto
                    cartones_nuevos[id_c] = [nums[0:5], nums[5:10], nums[10:15]]

            if total_errores:
                detalle = "\n".join(errores)
                if total_errores > len(errores):
                    detalle += f"\n... y {total_errores - len(errores)} error/es más."
                messagebox.showerror("CSV inválido", f"No se cargó la ronda. Corregí el archivo y volvé a intentar.\n\n{detalle}")
                return

            if not cartones_nuevos:
                messagebox.showerror("CSV inválido", "No se encontró ningún cartón válido. La ronda actual se mantiene sin cambios.")
                return

            self.cartones = cartones_nuevos
            self.lbl_status.config(text=f"{len(cartones_nuevos)} Cartones", fg=self.c_verde)
            self.btn_sacar.config(state="normal")
            nombre = os.path.splitext(os.path.basename(ruta))[0].replace("_", " ").upper()
            self.lbl_ronda_publico.config(text=f"JUGANDO: {nombre}")
            self.reiniciar_juego()
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al cargar: {str(e)}")

    def reiniciar_juego(self):
        self.bolas_sacadas.clear()
        self.bolas_disponibles = list(range(1, 91))
        self.linea_cantada = self.bingo_cantado = self.ruleta_girando = False
        
        # Volvemos a encender los botones de cierre
        self.btn_cerrar_linea.config(state="normal", bg=self.c_azul)
        self.btn_cerrar_bingo.config(state="normal", bg=self.c_sombra_oscura)
        
        self.angulo_actual_ruleta = 0.0
        self.bola_en_espera = None
        self.ganadores_teoricos_linea.clear()
        self.ganadores_teoricos_bingo.clear()
        self.lbl_admin_bola.config(text="--")
        self.lbl_bola_publico.config(text="--")
        if not self.cartones: self.lbl_ronda_publico.config(text="ESPERANDO RONDA...")
        self.dibujar_tablero_responsive()
        self.dibujar_ruleta_estatica()
        self.analizar_estado_cartones()

    def iniciar_extraccion(self):
        if not self.bolas_disponibles or self.ruleta_girando or self.bingo_cantado: return
        self.ruleta_girando = True
        self.btn_sacar.config(state="disabled", bg="#d4be9c")
        if self.bola_en_espera:
            if self.bola_en_espera in self.bolas_disponibles: self.bolas_disponibles.remove(self.bola_en_espera)
            self.bola_en_espera = None
        bola = random.choice(self.bolas_disponibles)
        idx = self.bolas_disponibles.index(bola)
        ap = 360 / len(self.bolas_disponibles)
        af = (90 - (idx * ap) - (ap/2)) % 360
        dist = (af - (self.angulo_actual_ruleta % 360)) % 360
        self.giro_total, self.giro_in, self.frame_anim, self.total_frames = dist + (360*4), self.angulo_actual_ruleta, 0, 150
        self.animar_giro(bola, idx)

    def animar_giro(self, bola, idx):
        self.frame_anim += 1
        t = self.frame_anim / self.total_frames
        self.angulo_actual_ruleta = self.giro_in + (self.giro_total * (1 - pow(1 - t, 4)))
        self.dibujar_ruleta_estatica(self.angulo_actual_ruleta)
        if self.frame_anim < self.total_frames: self.root.after(16, self.animar_giro, bola, idx)
        else: self.procesar_bola(bola, idx)

    def procesar_bola(self, bola, idx):
        self.ruleta_girando = False
        self.btn_sacar.config(state="normal", bg=self.c_naranja)
        self.bolas_sacadas.append(bola)
        self.bola_en_espera, self.indice_espera = bola, idx
        self.lbl_admin_bola.config(text=f"{bola}")
        self.lbl_bola_publico.config(text=str(bola))
        self.dibujar_tablero_responsive()
        self.dibujar_ruleta_estatica(self.angulo_actual_ruleta, bola)
        self.analizar_estado_cartones()

    def validar_premio(self, tipo):
        txt = self.entry_carton_val.get()
        if not txt.isdigit(): return
        idc = int(txt)
        if idc not in self.cartones: 
            messagebox.showwarning("Atención", f"El cartón {idc} no existe en esta ronda.")
            return
            
        set_s = set(self.bolas_sacadas)
        if tipo == "linea":
            if min([len([n for n in f if n != 0 and n not in set_s]) for f in self.cartones[idc]]) == 0:
                messagebox.showinfo("✅ LÍNEA VÁLIDA", f"¡Todo en orden!\nEl Cartón {idc} completó al menos una Línea.")
            else:
                messagebox.showerror("❌ FALSA ALARMA", f"Al Cartón {idc} todavía le faltan números para sacar Línea.")
        else:
            todos = [n for f in self.cartones[idc] for n in f if n != 0]
            if len([n for n in todos if n not in set_s]) == 0:
                messagebox.showinfo("✅ BINGO VÁLIDO", f"¡Cantalo, cantalo!\nEl Cartón {idc} completó el Bingo.")
            else:
                messagebox.showerror("❌ FALSA ALARMA", f"Al Cartón {idc} todavía le faltan números para el Bingo.")

    def cerrar_linea(self):
        if not self.cartones or self.linea_cantada: return
        
        # Escaneo rápido para ver si alguien ya completó la Línea (faltan 0 números)
        set_s = set(self.bolas_sacadas)
        min_faltan = min(min([len([n for n in f if n != 0 and n not in set_s]) for f in m]) for m in self.cartones.values())
        
        # Armamos el mensaje dependiendo de si hay ganador o no
        if min_faltan > 0:
            mensaje = f"⚠️ ATENCIÓN: Matemáticamente nadie sacó Línea todavía (al mejor cartón le faltan {min_faltan} número/s).\n\n¿Estás completamente seguro de que querés cerrar la etapa de Línea sin ganadores?"
        else:
            mensaje = "¿Estás seguro de que querés dar por cerrada la etapa de Línea?"
            
        # Doble confirmación
        confirmacion = messagebox.askyesno("Confirmar Cierre de Línea", mensaje)
        
        if confirmacion:
            self.linea_cantada = True
            self.btn_cerrar_linea.config(state="disabled", bg="#d4be9c") 
            self.analizar_estado_cartones() # Actualiza el monitor para borrar la info de Línea
            messagebox.showinfo("Etapa Cerrada", "Se cerró el juego de Línea. El monitoreo ahora se enfoca solo en el Bingo.")

    def cerrar_bingo(self):
        if not self.cartones or self.bingo_cantado: return
        
        # Escaneo rápido para ver si alguien ya completó el Bingo (faltan 0 números)
        set_s = set(self.bolas_sacadas)
        min_faltan = min(len([n for f in m for n in f if n != 0 and n not in set_s]) for m in self.cartones.values())
        
        # Armamos el mensaje dependiendo de si hay ganador o no
        if min_faltan > 0:
            mensaje = f"⚠️ ATENCIÓN: Matemáticamente nadie llenó el cartón todavía (al mejor cartón le faltan {min_faltan} número/s).\n\n¿Estás completamente seguro de que querés finalizar el Bingo sin ganadores?"
        else:
            mensaje = "¿Estás seguro de que querés dar por finalizado el Bingo?"
            
        # Doble confirmación
        confirmacion = messagebox.askyesno("Confirmar Cierre de Bingo", mensaje)
        
        if confirmacion:
            self.bingo_cantado = True
            self.btn_cerrar_bingo.config(state="disabled", bg="#d4be9c")
            self.btn_sacar.config(state="disabled", bg="#d4be9c") # Frena la ruleta
            self.txt_proyecciones.insert(tk.END, "\n🎉 ¡BINGO FINALIZADO! 🎉\n")
            messagebox.showinfo("Juego Finalizado", "Se cerró el Bingo. Ya no se pueden extraer más bolillas.")

    def analizar_estado_cartones(self):
        if not self.cartones or self.bingo_cantado: return
        set_s = set(self.bolas_sacadas)
        
        l_info, b_info = [], []
        posibles_linea = []
        posibles_bingo = []

        for idc, m in self.cartones.items():
            if not self.linea_cantada:
                # Calculamos cuántos números faltan por cada fila individualmente
                faltantes_filas = [len([n for n in f if n != 0 and n not in set_s]) for f in m]
                
                # Buscamos la fila a la que menos le falta
                mf = min(faltantes_filas)
                
                # Identificamos qué fila (o filas) tienen ese mínimo 
                # (sumamos 1 al índice para que lo muestre como Fila 1, 2 o 3)
                mejores_filas = [i + 1 for i, faltan in enumerate(faltantes_filas) if faltan == mf]
                
                l_info.append((idc, mf, mejores_filas))
                
                # Si a la fila le faltan 0 números, es ganadora
                if mf == 0: 
                    for fila in mejores_filas:
                        posibles_linea.append(f"#{idc:03d} (Fila {fila})")

            # --- Lógica de Bingo (se mantiene igual) ---
            tb = len([n for f in m for n in f if n != 0 and n not in set_s])
            b_info.append((idc, tb))
            if tb == 0: 
                posibles_bingo.append(f"#{idc:03d}")

        # Ordenamos de menor a mayor cantidad de números faltantes
        b_info.sort(key=lambda x: x[1])
        
        self.txt_proyecciones.delete("1.0", tk.END)
        
        if not self.linea_cantada:
            l_info.sort(key=lambda x: x[1])
            self.txt_proyecciones.insert(tk.END, ">>> LINEA <<<\n")
            
            if posibles_linea: 
                self.txt_proyecciones.insert(tk.END, f"👑 POSIBLES: {', '.join(posibles_linea)}\n")
                
            # Mostramos el top 3 de los que están a punto de sacar línea, indicando la fila
            for idc, faltan, filas in [x for x in l_info if x[1] > 0][:3]:
                filas_str = " o ".join([str(f) for f in filas])
                self.txt_proyecciones.insert(tk.END, f"#{idc:03d} - Falta {faltan} en Fila {filas_str}\n")
                
        self.txt_proyecciones.insert(tk.END, "\n>>> BINGO <<<\n")
        if posibles_bingo: 
            self.txt_proyecciones.insert(tk.END, f"🏆 POSIBLES: {', '.join(posibles_bingo)}\n")
            
        for idc, faltan in [x for x in b_info if x[1] > 0][:3]:
            self.txt_proyecciones.insert(tk.END, f"#{idc:03d} - Faltan {faltan}\n")

if __name__ == "__main__":
    if os.name == 'nt':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception: pass
    root = tk.Tk()
    app = JuegoBingoGUI(root)
    root.mainloop()
