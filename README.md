<div align="center">

# 🏷️ AgisLabels Pro

**El software de escritorio definitivo para la creación y impresión de etiquetas térmicas.**
Compatible con impresoras Agis, Zebra, TSC, y cualquier impresora del sistema.

[![Release](https://img.shields.io/github/v/release/cjddiaz/print_py?style=for-the-badge&logo=github)](https://github.com/cjddiaz/print_py/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=for-the-badge)](https://github.com/cjddiaz/print_py/releases)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=for-the-badge&logo=python)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

---

<img src="https://raw.githubusercontent.com/cjddiaz/print_py/main/docs/screenshot.png" alt="AgisLabels Pro Screenshot" width="800"/>

</div>

---

## ✨ Características

| Funcionalidad | Descripción |
|---|---|
| 🎨 **Editor WYSIWYG** | Lienzo interactivo con arrastrar y soltar. Lo que ves es lo que se imprime. |
| 📊 **Multi-código** | Code128, QR, EAN13, EAN8, UPC-A, Code39 en el mismo diseño. |
| 🔤 **Variables dinámicas** | Escribe `{nombre}`, `{precio}` en cualquier texto y se auto-rellena desde Excel. |
| 🔢 **Contador serial** | Genera `LOTE-0001`, `LOTE-0002`… automáticamente en cada impresión. |
| 📂 **Impresión masiva** | Carga un `.xlsx` con miles de filas e imprime un lote completo en un clic. |
| 💾 **Proyectos `.agisproj`** | Guarda y comparte tus diseños como archivo portátil. |
| 🗄️ **Catálogo SQLite** | Base de datos interna de productos con búsqueda y carga directa al lienzo. |
| 📜 **Historial de impresiones** | Registro completo de cada trabajo enviado a la impresora, con re-imprimir. |
| 🖥️ **Multiplataforma** | Un solo instalador nativo para Windows, macOS y Linux. |
| 🌙 **Dark Mode** | Interfaz oscura profesional con paleta Fusion. |

---

## 🚀 Descarga e Instalación (Sin Python)

👉 **[Ir a la última versión →](https://github.com/cjddiaz/print_py/releases/latest)**

| Sistema Operativo | Archivo |
|---|---|
| 🪟 **Windows (64-bit)** | `AgisLabels-Pro-Windows.zip` → ejecuta `AgisLabels Pro.exe` |
| 🍎 **macOS (Universal)** | `AgisLabels-Pro-macOS.dmg` → arrastra a Aplicaciones |
| 🐧 **Linux (x64)** | `AgisLabels-Pro-Linux.tar.gz` → ejecuta `./AgisLabels Pro` |

> **No se requiere instalar Python.** Los executables incluyen todo lo necesario.

---

## 🛠️ Instalación desde el Código Fuente

```bash
# 1. Clonar el repositorio
git clone https://github.com/cjddiaz/print_py.git
cd print_py

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

### Requisitos del Sistema
- Python **3.10** o superior
- PyQt6 6.4+
- Pillow 10+

---

## 📐 Uso Rápido

### 1. Diseñar una Etiqueta
1. Ajusta el **Ancho** y **Alto** en la barra superior (ej. 40mm × 25mm)
2. Usa la barra de herramientas para añadir elementos:
   - **✏️ Texto** → haz clic en el lienzo donde quieres colocarlo
   - **📊 Código** → para Code128, QR, EAN13, etc.
   - **🖼️ Logo** → sube una imagen PNG/JPG
   - **▭ Rectángulo** → para bordes decorativos
3. Selecciona cada elemento y ajusta sus propiedades en el **panel derecho**
4. Arrastra los elementos con el mouse hasta posicionarlos perfectamente

### 2. Imprimir una Sola Etiqueta
Haz clic en **🖨️ Imprimir** en la barra superior → selecciona tu impresora → listo.

### 3. Impresión Masiva desde Excel
1. En la pestaña **Impresión Masiva (Excel)**, carga tu archivo `.xlsx`
2. En tus textos/barcodes usa `{Nombre_Columna}` para vincular datos
3. Selecciona las filas y presiona **Imprimir filas seleccionadas**

**Ejemplo de Excel:**
| Descripcion | Codigo | Precio |
|---|---|---|
| Coca Cola 500ml | 7501055301485 | 1.50 |
| Pepsi 355ml | 7501030400157 | 1.25 |

**En el diseño:** `{Descripcion}` → `{Codigo}` (barcode) → `${Precio}`

### 4. Guardar tu Diseño
**Archivo → Guardar** (Ctrl+S) guarda como `.agisproj`. Puedes enviarlo por correo a otras computadoras con AgisLabels Pro.

---

## 🏗️ Arquitectura del Proyecto

```
print_py/
├── main.py                    # Punto de entrada (dark mode + PyQt6)
├── requirements.txt           # Dependencias Python
├── core/
│   ├── elements.py            # Modelo de datos de capas (TextElement, BarcodeElement…)
│   ├── engine.py              # Motor de renderizado PIL multi-código con interpolación
│   ├── counters.py            # Contador serial autónomo ({SERIAL})
│   └── serializer.py          # Guardar/cargar proyectos (.agisproj)
├── ui/
│   ├── main_window.py         # Ventana principal WYSIWYG
│   ├── canvas.py              # Lienzo interactivo QGraphicsScene (Drag & Drop)
│   ├── properties_panel.py    # Panel de propiedades contextual
│   ├── catalog_dialog.py      # CRUD catálogo de productos SQLite
│   ├── history_dialog.py      # Historial de impresiones
│   └── serial_dialog.py       # Configurar contador serial
└── data_utils/
    ├── db.py                   # ORM SQLAlchemy (Product + PrintJob)
    └── excel_reader.py         # Lector de .xlsx con pandas
```

---

## 🧩 Tipos de Código de Barras Soportados

| Tipo | Uso Típico |
|---|---|
| **Code128** | Logística, inventario general |
| **QR** | URLs, fichas de productos, trazabilidad |
| **EAN13** | Productos de consumo masivo (13 dígitos) |
| **EAN8** | Productos pequeños (8 dígitos) |
| **UPC-A** | Mercado norteamericano |
| **Code39** | Industrial, automotriz |

---

## 🔧 Compilar desde el Código (Desarrolladores)

```bash
pip install pyinstaller
pyinstaller AgisLabels.spec
```

El ejecutable se generará en `dist/`. Los builds automáticos para las 3 plataformas se ejecutan vía **GitHub Actions** al crear un tag:

```bash
git tag v2.0.0
git push origin v2.0.0
```

---

## 📋 Roadmap

- [ ] Editor WYSIWYG drag-to-resize (tiradores en esquinas)
- [ ] Soporte DataMatrix (`pylibdmtx`)
- [ ] Conexión directa a base de datos ODBC / PostgreSQL / MySQL
- [ ] Exportar etiqueta como PDF o PNG
- [ ] Historial de impresiones con vista previa de la etiqueta
- [ ] Plantillas prediseñadas incluídas

---

## 📄 Licencia

MIT © 2024 [cjddiaz](https://github.com/cjddiaz)
