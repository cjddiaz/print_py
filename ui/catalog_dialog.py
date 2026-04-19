"""
ui/catalog_dialog.py
Internal product catalog CRUD dialog.
Backed by SQLite via data_utils/db.py.
Allows search, add, edit, delete products and "load to canvas" action.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QTableWidget,
                              QTableWidgetItem, QMessageBox, QHeaderView,
                              QDoubleSpinBox, QDialogButtonBox, QFormLayout,
                              QWidget, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
import data_utils.db as db


class _ProductForm(QDialog):
    def __init__(self, parent=None, product: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Producto" if not product else "Editar Producto")
        self.setMinimumWidth(360)
        self._pid = product["id"] if product else None

        layout = QVBoxLayout(self)
        form   = QFormLayout()

        self.name     = QLineEdit(product["name"] if product else "")
        self.barcode  = QLineEdit(product["barcode"] if product else "")
        self.price    = QDoubleSpinBox()
        self.price.setRange(0, 999999); self.price.setDecimals(2)
        if product:
            self.price.setValue(product["price"])
        self.category    = QLineEdit(product.get("category", "") if product else "")
        self.description = QLineEdit(product.get("description", "") if product else "")

        form.addRow("Nombre *",      self.name)
        form.addRow("Código Barras", self.barcode)
        form.addRow("Precio",        self.price)
        form.addRow("Categoría",     self.category)
        form.addRow("Descripción",   self.description)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "id":          self._pid,
            "name":        self.name.text().strip(),
            "barcode":     self.barcode.text().strip(),
            "price":       self.price.value(),
            "category":    self.category.text().strip(),
            "description": self.description.text().strip(),
        }


class CatalogDialog(QDialog):
    """Main catalog dialog. Emits product_selected when user clicks 'Cargar a etiqueta'."""
    product_selected = pyqtSignal(dict)   # dict with product data

    COLS = ["ID", "Nombre", "Código", "Precio", "Categoría"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Catálogo de Productos")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        # Search bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Buscar:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Nombre del producto…")
        self.search.textChanged.connect(self._refresh_table)
        search_row.addWidget(self.search)
        layout.addLayout(search_row)

        # Table
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_use)
        layout.addWidget(self.table)

        # Buttons
        btn_row = QHBoxLayout()
        self.add_btn    = QPushButton("➕ Agregar")
        self.edit_btn   = QPushButton("✏️ Editar")
        self.del_btn    = QPushButton("🗑️ Eliminar")
        self.use_btn    = QPushButton("📋 Cargar a Etiqueta")
        self.use_btn.setStyleSheet("background:#1a73e8; color:white; font-weight:bold; padding:6px;")

        for b in [self.add_btn, self.edit_btn, self.del_btn, self.use_btn]:
            btn_row.addWidget(b)

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.del_btn.clicked.connect(self._on_delete)
        self.use_btn.clicked.connect(self._on_use)
        layout.addLayout(btn_row)

        self._products: list[dict] = []
        self._refresh_table()

    def _refresh_table(self):
        search = self.search.text().strip()
        self._products = db.list_products(search)
        self.table.setRowCount(len(self._products))
        for r, p in enumerate(self._products):
            for c, val in enumerate([p["id"], p["name"], p["barcode"],
                                      f"${p['price']:.2f}", p["category"]]):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)

    def _selected_product(self) -> dict | None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            return self._products[rows[0].row()]
        return None

    def _on_add(self):
        dlg = _ProductForm(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.add_product(d["name"], d["barcode"], d["price"], d["category"], d["description"])
            self._refresh_table()

    def _on_edit(self):
        p = self._selected_product()
        if not p:
            QMessageBox.information(self, "Info", "Selecciona un producto primero.")
            return
        dlg = _ProductForm(self, p)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.update_product(p["id"], name=d["name"], barcode=d["barcode"],
                               price=d["price"], category=d["category"],
                               description=d["description"])
            self._refresh_table()

    def _on_delete(self):
        p = self._selected_product()
        if not p:
            return
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar '{p['name']}'?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                 ) == QMessageBox.StandardButton.Yes:
            db.delete_product(p["id"])
            self._refresh_table()

    def _on_use(self):
        p = self._selected_product()
        if p:
            self.product_selected.emit(p)
            self.accept()
