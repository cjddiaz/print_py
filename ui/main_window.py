"""
ui/main_window.py
Main application window — full redesign with WYSIWYG canvas, properties panel,
batch printing, serial counter, catalog, and print history.
"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QLabel, QLineEdit, QPushButton, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QFileDialog,
    QComboBox, QHeaderView, QDoubleSpinBox, QSpinBox, QStatusBar,
    QDockWidget, QMenuBar, QMenu, QApplication,
)
from PyQt6.QtGui import QAction, QImage, QPainter, QIcon, QPixmap, QColor, QKeySequence
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from core.elements import (TextElement, BarcodeElement, ImageElement, RectElement,
                            ELEMENT_TEXT, ELEMENT_BARCODE, ELEMENT_IMAGE, ELEMENT_RECT)
from core.engine import LabelEngine
from core.counters import SerialCounter
from core import serializer
from data_utils.excel_reader import ExcelReader
import data_utils.db as db
from ui.canvas import LabelCanvas
from ui.properties_panel import PropertiesPanel
from ui.catalog_dialog import CatalogDialog
from ui.history_dialog import HistoryDialog
from ui.serial_dialog import SerialDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgisLabels Pro — Software Profesional de Etiquetas")
        self.setMinimumSize(1100, 700)

        self.engine   = LabelEngine()
        self.counter: SerialCounter | None = None
        self._project_path: str | None = None
        self._excel_data:   list[dict] = []
        self._excel_cols:   list[str]  = []

        # Ensure DB is initialized
        db.get_engine()

        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

        # Preview timer (debounced)
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._refresh_preview)
        self.canvas.canvas_changed.connect(lambda: self._preview_timer.start(250))

        self._refresh_preview()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        # Archivo
        file_menu = mb.addMenu("Archivo")
        self._act(file_menu, "Nuevo",     self._new_project,  "Ctrl+N")
        self._act(file_menu, "Abrir…",    self._open_project, "Ctrl+O")
        file_menu.addSeparator()
        self._act(file_menu, "Guardar",   self._save_project, "Ctrl+S")
        self._act(file_menu, "Guardar como…", lambda: self._save_project(force_dialog=True), "Ctrl+Shift+S")
        file_menu.addSeparator()
        self._act(file_menu, "Salir",     self.close,         "Ctrl+Q")

        # Editar
        edit_menu = mb.addMenu("Editar")
        self._act(edit_menu, "Eliminar elemento seleccionado", self._delete_selected, "Delete")

        # Herramientas
        tools_menu = mb.addMenu("Herramientas")
        self._act(tools_menu, "Catálogo de Productos…", self._open_catalog)
        self._act(tools_menu, "Historial de Impresiones…", self._open_history)
        self._act(tools_menu, "Configurar Contador Serial…", self._open_serial_dialog)

        # Ayuda
        help_menu = mb.addMenu("Ayuda")
        self._act(help_menu, "Acerca de AgisLabels", self._about)

    def _act(self, menu: QMenu, label: str, slot, shortcut: str = ""):
        action = QAction(label, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        tb = QToolBar("Herramientas de diseño")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Label size
        tb.addWidget(QLabel("  Ancho: "))
        self.val_width = QDoubleSpinBox()
        self.val_width.setRange(5, 500); self.val_width.setValue(40); self.val_width.setSuffix(" mm")
        self.val_width.valueChanged.connect(self._on_size_change)
        tb.addWidget(self.val_width)

        tb.addWidget(QLabel("  Alto: "))
        self.val_height = QDoubleSpinBox()
        self.val_height.setRange(5, 500); self.val_height.setValue(25); self.val_height.setSuffix(" mm")
        self.val_height.valueChanged.connect(self._on_size_change)
        tb.addWidget(self.val_height)

        tb.addSeparator()

        # Insert buttons
        for label, etype, tip in [
            ("✏️ Texto",      ELEMENT_TEXT,    "Añadir texto"),
            ("📊 Código128",  ELEMENT_BARCODE, "Añadir código de barras o QR"),
            ("🖼️ Logo",       ELEMENT_IMAGE,   "Añadir imagen/logo"),
            ("▭ Rectángulo", ELEMENT_RECT,    "Añadir rectángulo"),
        ]:
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda checked, t=etype: self.canvas.set_insert_mode(t))
            tb.addWidget(btn)

        tb.addSeparator()

        del_btn = QPushButton("🗑️ Eliminar")
        del_btn.setToolTip("Eliminar elemento seleccionado")
        del_btn.clicked.connect(self._delete_selected)
        tb.addWidget(del_btn)

        tb.addSeparator()

        print_btn = QPushButton("🖨️ Imprimir")
        print_btn.setStyleSheet("background:#27ae60; color:white; font-weight:bold; padding:4px 12px;")
        print_btn.clicked.connect(self._print_single)
        tb.addWidget(print_btn)

    # ── Central widget ────────────────────────────────────────────────────────

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_h = QHBoxLayout(central)
        main_h.setContentsMargins(4, 4, 4, 4)

        # Left: canvas + tabs
        left_splitter = QSplitter(Qt.Orientation.Vertical)

        # Canvas
        self.canvas = LabelCanvas(40, 25)
        self.canvas.item_clicked.connect(self._on_item_selected)
        left_splitter.addWidget(self.canvas)

        # Tabs: batch print, variables
        self.tabs = QTabWidget()
        self._build_batch_tab()
        self._build_variables_tab()
        left_splitter.addWidget(self.tabs)
        left_splitter.setSizes([500, 200])

        main_h.addWidget(left_splitter, stretch=3)

        # Right: properties + preview
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        self.props = PropertiesPanel()
        self.props.element_changed.connect(self._on_element_changed)
        right_splitter.addWidget(self.props)

        # Preview
        preview_w = QWidget()
        preview_layout = QVBoxLayout(preview_w)
        preview_layout.addWidget(QLabel("Vista Previa de Impresión"))
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(120)
        self.preview_label.setStyleSheet("background:white; border:1px solid #ccc;")
        preview_layout.addWidget(self.preview_label)
        right_splitter.addWidget(preview_w)
        right_splitter.setSizes([400, 200])

        main_h.addWidget(right_splitter, stretch=1)

    def _build_batch_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        top = QHBoxLayout()
        self.load_excel_btn = QPushButton("📂 Cargar Excel (.xlsx)")
        self.load_excel_btn.clicked.connect(self._load_excel)
        self.file_label = QLabel("Sin archivo cargado")
        top.addWidget(self.load_excel_btn)
        top.addWidget(self.file_label)
        top.addStretch()
        layout.addLayout(top)

        self.batch_table = QTableWidget()
        self.batch_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.batch_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.batch_table)

        self.print_batch_btn = QPushButton("🖨️ Imprimir filas seleccionadas")
        self.print_batch_btn.setStyleSheet("background:#2980b9; color:white; font-weight:bold; padding:6px;")
        self.print_batch_btn.clicked.connect(self._print_batch)
        layout.addWidget(self.print_batch_btn)

        self.tabs.addTab(tab, "Impresión Masiva (Excel)")

    def _build_variables_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel(
            "Variables disponibles del Excel cargado.\n"
            "Úsalas en textos como: {nombre_columna}\n"
            "También puedes usar {SERIAL} para el contador automático."
        ))
        self.vars_list = QLabel("(Carga un Excel para ver las columnas)")
        self.vars_list.setWordWrap(True)
        layout.addWidget(self.vars_list)
        layout.addStretch()

        serial_btn = QPushButton("⚙️ Configurar Contador Serial ({SERIAL})")
        serial_btn.clicked.connect(self._open_serial_dialog)
        layout.addWidget(serial_btn)

        self.tabs.addTab(tab, "Variables")

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_lbl = QLabel("Listo")
        sb.addWidget(self._status_lbl)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_size_change(self):
        w = self.val_width.value()
        h = self.val_height.value()
        self.canvas.set_dimensions(w, h)
        self._refresh_preview()

    def _on_item_selected(self, element):
        """Handles both element selection and deselection (element=None)."""
        self.props.load_element(element)

    def _on_element_changed(self, element):
        self.canvas.refresh_item(element)

    def _delete_selected(self):
        self.canvas.remove_selected()

    # ── Preview ───────────────────────────────────────────────────────────────

    def _refresh_preview(self):
        elements = self.canvas.get_elements()
        w = self.val_width.value()
        h = self.val_height.value()
        pil_img = self.engine.render(elements, width_mm=w, height_mm=h)

        data = pil_img.tobytes("raw", "RGB")
        qim  = QImage(data, pil_img.width, pil_img.height,
                      pil_img.width * 3, QImage.Format.Format_RGB888)
        px = QPixmap.fromImage(qim)
        self.preview_label.setPixmap(px.scaled(
            self.preview_label.width() - 4, self.preview_label.height() - 4,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))

    def _pil_to_qimage(self, pil_img) -> QImage:
        data = pil_img.tobytes("raw", "RGB")
        return QImage(data, pil_img.width, pil_img.height,
                      pil_img.width * 3, QImage.Format.Format_RGB888)

    # ── Print single ──────────────────────────────────────────────────────────

    def _print_single(self):
        elements = self.canvas.get_elements()
        if not elements:
            QMessageBox.warning(self, "Aviso", "No hay elementos en el lienzo.")
            return

        data_row = {}
        if self.counter:
            data_row["SERIAL"] = self.counter.next()

        pil_img = self.engine.render(elements, self.val_width.value(),
                                     self.val_height.value(), data_row)
        qim = self._pil_to_qimage(pil_img)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter()
            try:
                painter.begin(printer)
                painter.drawImage(painter.viewport(), qim)
                painter.end()
                db.log_print_job(
                    template_name = os.path.basename(self._project_path) if self._project_path else "Sin guardar",
                    printer_name  = printer.printerName(),
                    rows          = 1,
                )
                self._status_lbl.setText("✅ Etiqueta enviada a la impresora")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ── Excel ─────────────────────────────────────────────────────────────────

    def _load_excel(self):
        f, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel", "",
                                            "Excel (*.xlsx *.xls)")
        if not f:
            return
        try:
            records, cols = ExcelReader.load_excel(f)
            self._excel_data = records
            self._excel_cols = cols
            self.file_label.setText(os.path.basename(f))

            self.batch_table.setRowCount(len(records))
            self.batch_table.setColumnCount(len(cols))
            self.batch_table.setHorizontalHeaderLabels(cols)
            self.batch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            for ri, row in enumerate(records):
                for ci, col in enumerate(cols):
                    self.batch_table.setItem(ri, ci, QTableWidgetItem(str(row.get(col, ""))))

            self.vars_list.setText("Columnas disponibles:\n• " + "\n• ".join(cols))
            self._status_lbl.setText(f"✅ {len(records)} filas cargadas desde {os.path.basename(f)}")
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar Excel", str(e))

    def _print_batch(self):
        if not self._excel_data:
            QMessageBox.warning(self, "Aviso", "Carga un archivo Excel primero.")
            return

        selected = sorted(set(i.row() for i in self.batch_table.selectedItems()))
        if not selected:
            QMessageBox.information(self, "Aviso", "Selecciona las filas a imprimir.")
            return

        elements = self.canvas.get_elements()
        if not elements:
            QMessageBox.warning(self, "Aviso", "El lienzo está vacío. Diseña una etiqueta primero.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        # Reset counter at batch start
        counter_snapshot = self.counter.current if self.counter else None

        painter = QPainter()
        try:
            painter.begin(printer)
            for i, ridx in enumerate(selected):
                data_row = dict(self._excel_data[ridx])
                if self.counter:
                    data_row["SERIAL"] = self.counter.next()

                pil_img = self.engine.render(elements, self.val_width.value(),
                                              self.val_height.value(), data_row)
                qim = self._pil_to_qimage(pil_img)
                painter.drawImage(painter.viewport(), qim)
                if i < len(selected) - 1:
                    printer.newPage()

            painter.end()
            db.log_print_job(
                template_name = os.path.basename(self._project_path) if self._project_path else "Sin guardar",
                printer_name  = printer.printerName(),
                rows          = len(selected),
            )
            self._status_lbl.setText(f"✅ {len(selected)} etiquetas enviadas")
            QMessageBox.information(self, "Éxito", f"Se imprimieron {len(selected)} etiquetas.")
        except Exception as e:
            painter.end()
            QMessageBox.critical(self, "Error en impresión masiva", str(e))

    # ── Project save/load ─────────────────────────────────────────────────────

    def _new_project(self):
        if QMessageBox.question(self, "Nuevo proyecto",
                                "¿Descartar cambios y crear un proyecto nuevo?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                ) == QMessageBox.StandardButton.Yes:
            self.canvas.clear_all()
            self.props.load_element(None)
            self._project_path = None
            self.counter = None
            self.setWindowTitle("AgisLabels Pro — Nuevo Proyecto")
            self._status_lbl.setText("Nuevo proyecto creado")

    def _open_project(self):
        f, _ = QFileDialog.getOpenFileName(self, "Abrir Proyecto", "",
                                            "AgisLabels Project (*.agisproj)")
        if not f:
            return
        try:
            proj = serializer.load_project(f)
            self.canvas.clear_all()
            cfg = proj.get("config", {})
            self.val_width.setValue(cfg.get("width_mm", 40))
            self.val_height.setValue(cfg.get("height_mm", 25))
            for el in proj["elements"]:
                self.canvas.add_element(el)
            self.counter = proj.get("counter")
            self._project_path = f
            self.setWindowTitle(f"AgisLabels Pro — {os.path.basename(f)}")
            self._status_lbl.setText(f"Proyecto abierto: {os.path.basename(f)}")
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))

    def _save_project(self, force_dialog: bool = False):
        if force_dialog or not self._project_path:
            f, _ = QFileDialog.getSaveFileName(self, "Guardar Proyecto", "",
                                                "AgisLabels Project (*.agisproj)")
            if not f:
                return
            if not f.endswith(".agisproj"):
                f += ".agisproj"
            self._project_path = f

        config = {
            "width_mm":    self.val_width.value(),
            "height_mm":   self.val_height.value(),
        }
        try:
            serializer.save_project(self._project_path,
                                    self.canvas.get_elements(),
                                    config, self.counter)
            self.setWindowTitle(f"AgisLabels Pro — {os.path.basename(self._project_path)}")
            self._status_lbl.setText(f"Guardado: {self._project_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def _open_catalog(self):
        dlg = CatalogDialog(self)
        dlg.product_selected.connect(self._load_product_to_canvas)
        dlg.exec()

    def _load_product_to_canvas(self, product: dict):
        # Add a text element for the name and a barcode for the code
        el_text = TextElement(x=2, y=2, width=36, height=6,
                               text=product["name"], font_size=14)
        el_bc   = BarcodeElement(x=2, y=10, width=36, height=13,
                                  code=product["barcode"] or "0000000000",
                                  barcode_type="code128")
        self.canvas.add_element(el_text)
        self.canvas.add_element(el_bc)
        self._status_lbl.setText(f"Producto cargado: {product['name']}")

    def _open_history(self):
        dlg = HistoryDialog(self)
        dlg.exec()

    def _open_serial_dialog(self):
        dlg = SerialDialog(self.counter, self)
        if dlg.exec() == SerialDialog.DialogCode.Accepted:
            self.counter = dlg.get_counter()
            self._status_lbl.setText(
                f"Contador configurado: {self.counter.peek()} → +{self.counter.step}"
            )

    def _about(self):
        QMessageBox.about(self, "AgisLabels Pro",
                          "<b>AgisLabels Pro v2.0</b><br>"
                          "Software profesional de creación e impresión de etiquetas.<br>"
                          "Compatible con Mac, Windows y Linux.<br><br>"
                          "Funcionalidades: WYSIWYG · Drag & Drop · QR · EAN13 · "
                          "Code128 · Impresión masiva · Variables · Contadores · "
                          "Catálogo SQLite · Historial")
