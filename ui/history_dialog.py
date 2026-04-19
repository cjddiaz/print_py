"""
ui/history_dialog.py
Print history viewer.
Shows all past print jobs from the SQLite DB and lets the user re-print.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
import data_utils.db as db


class HistoryDialog(QDialog):
    reprint_requested = pyqtSignal(dict)   # emits PrintJob dict

    COLS = ["ID", "Fecha/Hora", "Plantilla", "Impresora", "Filas", "Estado"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Impresiones")
        self.setMinimumSize(760, 420)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.refresh_btn  = QPushButton("🔄 Actualizar")
        self.reprint_btn  = QPushButton("🖨️ Re-imprimir")
        self.reprint_btn.setStyleSheet("background:#27ae60; color:white; font-weight:bold; padding:6px;")
        self.close_btn    = QPushButton("Cerrar")

        self.refresh_btn.clicked.connect(self._load)
        self.reprint_btn.clicked.connect(self._on_reprint)
        self.close_btn.clicked.connect(self.accept)

        for b in [self.refresh_btn, self.reprint_btn, self.close_btn]:
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self._jobs: list[dict] = []
        self._load()

    def _load(self):
        self._jobs = db.list_print_jobs()
        self.table.setRowCount(len(self._jobs))
        status_colors = {"ok": "#2ecc71", "error": "#e74c3c", "partial": "#f39c12"}
        for r, j in enumerate(self._jobs):
            vals = [j["id"], j["timestamp"], j["template_name"],
                    j["printer_name"], j["rows_printed"], j["status"]]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c == 5:  # status column
                    item.setForeground(
                        Qt.GlobalColor.white
                        if j["status"] == "error"
                        else Qt.GlobalColor.black
                    )
                self.table.setItem(r, c, item)

    def _on_reprint(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Info", "Selecciona un trabajo de la lista.")
            return
        job = self._jobs[rows[0].row()]
        self.reprint_requested.emit(job)
        self.accept()
