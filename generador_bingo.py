import csv
import random
import os
import hashlib

# --- LIBRERÍA PARA PDF PREMIUM ---
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from PIL import Image
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ ADVERTENCIA: ReportLab no está instalado. Solo se generará CSV.")

# Paleta Aesthetic del Coro
C_AZUL = colors.HexColor("#091433")
C_VERDE = colors.HexColor("#394f3d")
C_BEIGE = colors.HexColor("#ebd6b4")
C_ROJO = colors.HexColor("#561118")

class GeneradorBingo:
    def __init__(self):
        self.cartones_unicos = set()
        self.total_generados = 0

    def generar_distribucion_conteos(self):
        """Calcula cuántos números irán en cada columna para 6 cartones."""
        col_totals = [9, 10, 10, 10, 10, 10, 10, 10, 11]
        while True:
            # Base: Cada cartón recibe al menos 1 número de cada columna
            matrix = [[1]*9 for _ in range(6)]
            rem_cols = [c - 6 for c in col_totals]
            rem_cards = [6]*6 # Faltan 6 números por cartón para llegar a 15

            valid = True
            for c in range(9):
                available_cards = [i for i in range(6) if rem_cards[i] > 0]
                if len(available_cards) < rem_cols[c]:
                    valid = False
                    break
                picked = random.sample(available_cards, rem_cols[c])
                for p in picked:
                    matrix[p][c] += 1
                    rem_cards[p] -= 1
                    
            if valid and all(rc == 0 for rc in rem_cards):
                return matrix

    def ubicar_en_filas(self, carton_nums):
        """Distribuye los 15 números del cartón en 3 filas de exactamente 5 números."""
        while True:
            filas = [[0]*9 for _ in range(3)]
            cols_con_2 = [c for c in range(9) if len(carton_nums[c]) == 2]
            cols_con_1 = [c for c in range(9) if len(carton_nums[c]) == 1]
            
            random.shuffle(cols_con_2)
            random.shuffle(cols_con_1)
            
            exito = True
            conteos_filas = [0, 0, 0]
            
            # Ubicar columnas con 2 números
            for c in cols_con_2:
                opciones = [r for r in range(3) if conteos_filas[r] < 5]
                if len(opciones) < 2:
                    exito = False
                    break
                rows = random.sample(opciones, 2)
                rows.sort()
                filas[rows[0]][c] = carton_nums[c][0]
                filas[rows[1]][c] = carton_nums[c][1]
                conteos_filas[rows[0]] += 1
                conteos_filas[rows[1]] += 1
                
            if not exito: continue
            
            # Ubicar columnas con 1 número
            for c in cols_con_1:
                opciones = [r for r in range(3) if conteos_filas[r] < 5]
                if not opciones:
                    exito = False
                    break
                r = random.choice(opciones)
                filas[r][c] = carton_nums[c][0]
                conteos_filas[r] += 1
                
            if exito and all(cnt == 5 for cnt in conteos_filas):
                return filas

    def generar_serie(self, start_id):
        """Genera 1 Serie perfecta = 6 cartones (contienen los 90 números exactos)"""
        conteos = self.generar_distribucion_conteos()
        
        # Crear bolillero mezclado por columna
        cols = []
        for i in range(9):
            start = 1 if i == 0 else i * 10
            end = 9 if i == 0 else (90 if i == 8 else i * 10 + 9)
            col_nums = list(range(start, end + 1))
            random.shuffle(col_nums)
            cols.append(col_nums)
            
        serie_actual = []
        for i in range(6):
            carton_nums = [[] for _ in range(9)]
            for c in range(9):
                for _ in range(conteos[i][c]):
                    carton_nums[c].append(cols[c].pop())
                    
            for c in range(9):
                carton_nums[c].sort()
                
            matriz_3x9 = self.ubicar_en_filas(carton_nums)
            
            # Huella digital (Hashing) para garantizar Unicidad
            numeros_planos = sorted([num for fila in matriz_3x9 for num in fila if num != 0])
            huella = hashlib.md5(str(numeros_planos).encode()).hexdigest()
            
            # Si el cartón ya existe (extremadamente raro), abortamos esta serie y generamos otra
            if huella in self.cartones_unicos:
                return None 
                
            self.cartones_unicos.add(huella)
            
            # Formato Aplanado
            lista_aplanada = [num for fila in matriz_3x9 for num in fila]
            serie_actual.append((start_id + i, lista_aplanada, matriz_3x9))
            
        return serie_actual

    def exportar_csv(self, ruta, todos_los_cartones):
        with open(ruta, mode="w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            for carton in todos_los_cartones:
                id_carton = carton[0]
                lista_aplanada = carton[1]
                
                # Extraemos solo los números descartando los ceros (huecos)
                numeros_reales = [num for num in lista_aplanada if num != 0]
                
                # Escribimos la fila: [ID, num1, num2, ..., num15]
                escritor.writerow([id_carton] + numeros_reales)

    def exportar_pdf(self, ruta, todos_los_cartones, nombre_ronda):
        if not PDF_AVAILABLE: return
        
        c = canvas.Canvas(ruta, pagesize=A4)
        ancho_a4, alto_a4 = A4
        
        cartones_por_pagina = 6
        margen_x = 15 * mm
        margen_y = 12 * mm
        espacio_entre_cartones = 4 * mm
        
        alto_disponible = alto_a4 - (2 * margen_y) - (espacio_entre_cartones * (cartones_por_pagina - 1))
        alto_carton = alto_disponible / cartones_por_pagina
        ancho_carton = ancho_a4 - (2 * margen_x)
        
        logo_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logo.png")
        has_logo = os.path.exists(logo_path)
        
        for idx, carton in enumerate(todos_los_cartones):
            if idx > 0 and idx % cartones_por_pagina == 0:
                c.showPage() 
                
            pos_y = alto_a4 - margen_y - ((idx % cartones_por_pagina) + 1) * alto_carton - ((idx % cartones_por_pagina) * espacio_entre_cartones)
            alto_header = 14 * mm 
            y_header = pos_y + alto_carton - alto_header
            
            # --- 1. FONDOS (Efecto Dual-Tone) ---
            # 1A. Fondo base (Pinta todo de Beige, creando el color de la cabecera)
            c.setFillColor(C_BEIGE)
            c.roundRect(margen_x, pos_y, ancho_carton, alto_carton, 4*mm, stroke=0, fill=1)
            
            # 1B. Fondo de la sección del cartón (Pinta de Blanco la zona de abajo)
            c.setFillColor(colors.white)
            c.roundRect(margen_x, pos_y, ancho_carton, alto_carton - alto_header, 4*mm, stroke=0, fill=1)
            # Parche para que encastre recto con la línea de la cabecera
            c.rect(margen_x, pos_y + 4*mm, ancho_carton, alto_carton - alto_header - 4*mm, stroke=0, fill=1)
            
            # 1C. Borde exterior principal (Para contener todo)
            c.setStrokeColor(C_AZUL)
            c.setLineWidth(1.5)
            c.roundRect(margen_x, pos_y, ancho_carton, alto_carton, 4*mm, stroke=1, fill=0)
            
            # --- 2. CABECERA ---
            c.setStrokeColor(C_AZUL)
            c.setLineWidth(1)
            c.line(margen_x, y_header, margen_x + ancho_carton, y_header)
            
            x_texto = margen_x + 4*mm
            if has_logo:
                tam_logo = 10 * mm
                try:
                    c.drawImage(logo_path, margen_x + 4*mm, y_header + 2*mm, width=tam_logo, height=tam_logo, mask='auto')
                    x_texto = margen_x + 16*mm 
                except: pass
                
            # Títulos
            c.setFillColor(C_AZUL)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_texto, y_header + 7.5*mm, nombre_ronda.upper())
            
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(C_VERDE) 
            c.drawString(x_texto, y_header + 2.5*mm, "BIN CAPU PEÑA")
            
            # Número de cartón
            c.setFillColor(C_ROJO)
            c.setFont("Helvetica-Bold", 14)
            texto_id = f"N° {carton[0]:04d}"
            ancho_id = c.stringWidth(texto_id, "Helvetica-Bold", 14)
            c.drawString(margen_x + ancho_carton - ancho_id - 4*mm, y_header + 4.5*mm, texto_id)
            
            # --- 3. GRILLA DE NÚMEROS (Cuadrada y con colores invertidos) ---
            pad_x = 3 * mm
            pad_y = 3 * mm
            ancho_grilla = ancho_carton - (2 * pad_x)
            alto_grilla = alto_carton - alto_header - (2 * pad_y)
            
            ancho_celda = ancho_grilla / 9
            alto_celda = alto_grilla / 3
            matriz = carton[2]
            
            for fila in range(3):
                for col in range(9):
                    x_celda = margen_x + pad_x + (col * ancho_celda)
                    y_celda = pos_y + pad_y + ((2 - fila) * alto_celda)
                    
                    valor = matriz[fila][col]
                    
                    # 💥 ACÁ ESTÁ LA MAGIA: Beige para números, Blanco para espacios vacíos
                    if valor != 0:
                        c.setFillColor(C_BEIGE)
                    else:
                        c.setFillColor(colors.white)
                        
                    c.setStrokeColor(C_AZUL)
                    c.setLineWidth(0.5) 
                    c.rect(x_celda, y_celda, ancho_celda, alto_celda, stroke=1, fill=1)
                    
                    # Escribir el número
                    if valor != 0:
                        c.setFillColor(C_AZUL)
                        c.setFont("Helvetica-Bold", 16)
                        c.drawCentredString(x_celda + (ancho_celda/2), y_celda + (alto_celda/2) - 2*mm, str(valor))
                        
        c.save()

    def procesar(self, cantidad_cartones, nombre_archivo):
        os.makedirs("rondas", exist_ok=True)
        nombre_base = nombre_archivo.replace(".csv", "")
        ruta_csv = os.path.join("rondas", f"{nombre_base}.csv")
        ruta_pdf = os.path.join("rondas", f"{nombre_base}.pdf")
        
        todos_los_cartones = []
        id_actual = 1
        
        print(f"Generando {cantidad_cartones} cartones (en series de 6)...")
        while len(todos_los_cartones) < cantidad_cartones:
            serie = self.generar_serie(id_actual)
            if serie: # Si la serie no tiene colisiones de huella
                for carton in serie:
                    if len(todos_los_cartones) < cantidad_cartones:
                        todos_los_cartones.append(carton)
                        id_actual += 1
                        
        # Exportaciones
        self.exportar_csv(ruta_csv, todos_los_cartones)
        print(f"✅ CSV Creado: {ruta_csv}")
        
        if PDF_AVAILABLE:
            print("🎨 Diseñando PDFs para imprenta...")
            self.exportar_pdf(ruta_pdf, todos_los_cartones, nombre_base.replace("_", " "))
            print(f"✅ PDF Creado: {ruta_pdf}")

if __name__ == "__main__":
    app = GeneradorBingo()
    ronda = input("Introduce el nombre de la ronda (ej: Ronda_1_Navidad): ")
    try:
        cant = int(input("¿Cuántos cartones deseas generar?: "))
        # Ajustamos al múltiplo de 6 más cercano
        cant_ajustada = cant + (6 - cant % 6) if cant % 6 != 0 else cant
        if cant_ajustada != cant:
            print(f"⚠️ Ajustando cantidad a {cant_ajustada} para respetar las series perfectas.")
            
        app.procesar(cant_ajustada, ronda)
    except ValueError:
        print("Por favor ingresa un número válido.")