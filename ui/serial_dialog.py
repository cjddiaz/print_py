"""
ui/serial_dialog.py
Dialog to configure the serial/auto-increment counter.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                              QLineEdit, QSpinBox, QDialogButtonBox, QLabel)
from core.counters import SerialCounter


class SerialDialog(QDialog):
    def __init__(self, counter: SerialCounter = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contador Serial Automático")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Inserta la variable <b>{SERIAL}</b> en cualquier texto\n"
            "y se reemplazará automáticamente al imprimir."
        ))

        form = QFormLayout()
        self.prefix  = QLineEdit(counter.prefix  if counter else "")
        self.suffix  = QLineEdit(counter.suffix  if counter else "")
        self.start   = QSpinBox(); self.start.setRange(0, 9999999)
        self.step    = QSpinBox(); self.step.setRange(1, 10000)
        self.padding = QSpinBox(); self.padding.setRange(1, 10)

        if counter:
            self.start.setValue(counter.current)
            self.step.setValue(counter.step)
            self.padding.setValue(counter.padding)
        else:
            self.start.setValue(1)
            self.step.setValue(1)
            self.padding.setValue(4)

        form.addRow("Prefijo (ej: LOTE-)",  self.prefix)
        form.addRow("Sufijo",              self.suffix)
        form.addRow("Número Inicial",      self.start)
        form.addRow("Incremento",          self.step)
        form.addRow("Dígitos (padding)",   self.padding)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_counter(self) -> SerialCounter:
        return SerialCounter(
            prefix  = self.prefix.text(),
            start   = self.start.value(),
            step    = self.step.value(),
            padding = self.padding.value(),
            suffix  = self.suffix.text(),
        )
