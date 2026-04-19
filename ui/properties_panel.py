"""
ui/properties_panel.py  (v2 — bugs fixed)

Fixes applied:
 1. _loading flag in PropertiesPanel.load_element() — prevents _on_change from
    writing the *old* panel values to the *new* element while load() triggers
    spinbox/lineedit signals.
 2. _GeometryProps.load() now blocks all spinbox signals before calling setValue(),
    exactly as the other sub-panels do. Without this, every setValue fired _emit
    → changed → PropertiesPanel._on_change during the loading sequence.
 3. BarcodeProps.load() also blocks show_text signals.
 4. RectProps.load() blocks border_width signals.
 5. ImageProps.load() blocks keep_aspect signals.
 6. load_element() sets self._current = None FIRST, then loads the panel,
    then sets self._current = element — so any leftover spurious signals
    during loading are completely harmless (the guard `if self._current is None: return`
    absorbs them).
 7. item_clicked(None) from the canvas (deselect) is handled gracefully.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QComboBox, QCheckBox, QPushButton,
                              QSpinBox, QDoubleSpinBox, QColorDialog,
                              QFileDialog, QStackedWidget, QFrame)
from PyQt6.QtGui  import QColor
from PyQt6.QtCore import Qt, pyqtSignal

from core.elements import (BaseElement, TextElement, BarcodeElement,
                            ImageElement, RectElement, BARCODE_TYPES,
                            ELEMENT_TEXT, ELEMENT_BARCODE, ELEMENT_IMAGE, ELEMENT_RECT)


# ── Helpers ────────────────────────────────────────────────────────────────────

class ColorButton(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.setFixedHeight(28)
        self.clicked.connect(self._pick_color)

    def set_color(self, color: str):
        self._color = color
        self._update_style()

    def color(self) -> str:
        return self._color

    def _update_style(self):
        self.setStyleSheet(
            f"background:{self._color}; border:1px solid #888; border-radius:3px;")
        self.setText(self._color)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self)
        if c.isValid():
            self._color = c.name()
            self._update_style()
            self.color_changed.emit(self._color)


def _hrow(label: str, widget: QWidget) -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setMinimumWidth(80)
    row.addWidget(lbl)
    row.addWidget(widget)
    return row


# ── Sub-panels ─────────────────────────────────────────────────────────────────

class _BaseProps(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def load(self, element: BaseElement):
        pass

    def _emit(self, *_):
        self.changed.emit()


class _GeometryProps(_BaseProps):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.x = QDoubleSpinBox(); self.x.setRange(0,   500); self.x.setSuffix(" mm")
        self.y = QDoubleSpinBox(); self.y.setRange(0,   500); self.y.setSuffix(" mm")
        self.w = QDoubleSpinBox(); self.w.setRange(0.5, 500); self.w.setSuffix(" mm")
        self.h = QDoubleSpinBox(); self.h.setRange(0.5, 500); self.h.setSuffix(" mm")

        for sp, lbl in [(self.x, "X"), (self.y, "Y"), (self.w, "Ancho"), (self.h, "Alto")]:
            sp.valueChanged.connect(self._emit)
            layout.addLayout(_hrow(lbl, sp))

    def load(self, element: BaseElement):
        # ── FIX: block ALL spinbox signals before calling setValue().
        for sp in (self.x, self.y, self.w, self.h):
            sp.blockSignals(True)
        self.x.setValue(element.x)
        self.y.setValue(element.y)
        self.w.setValue(element.width)
        self.h.setValue(element.height)
        for sp in (self.x, self.y, self.w, self.h):
            sp.blockSignals(False)

    def apply(self, element: BaseElement):
        element.x      = self.x.value()
        element.y      = self.y.value()
        element.width  = self.w.value()
        element.height = self.h.value()


class TextProps(_BaseProps):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.text   = QLineEdit();         self.text.textChanged.connect(self._emit)
        self.font   = QLineEdit("Arial");  self.font.textChanged.connect(self._emit)
        self.size   = QSpinBox();
        self.size.setRange(4, 200);        self.size.valueChanged.connect(self._emit)
        self.bold   = QCheckBox("Negrita");  self.bold.toggled.connect(self._emit)
        self.italic = QCheckBox("Cursiva");  self.italic.toggled.connect(self._emit)
        self.color  = ColorButton();         self.color.color_changed.connect(self._emit)
        self.align  = QComboBox()
        self.align.addItems(["left", "center", "right"])
        self.align.currentIndexChanged.connect(self._emit)

        layout.addLayout(_hrow("Texto",     self.text))
        layout.addLayout(_hrow("Fuente",    self.font))
        layout.addLayout(_hrow("Tamaño",    self.size))
        cbrow = QHBoxLayout()
        cbrow.addWidget(self.bold)
        cbrow.addWidget(self.italic)
        layout.addLayout(cbrow)
        layout.addLayout(_hrow("Color",     self.color))
        layout.addLayout(_hrow("Alineación", self.align))

    def load(self, el: TextElement):
        # Block all signals during load
        for w in (self.text, self.font, self.size, self.bold, self.italic, self.align):
            w.blockSignals(True)
        self.text.setText(el.text)
        self.font.setText(el.font_family)
        self.size.setValue(el.font_size)
        self.bold.setChecked(el.bold)
        self.italic.setChecked(el.italic)
        self.color.set_color(el.color)
        idx = self.align.findText(el.align)
        self.align.setCurrentIndex(max(0, idx))
        for w in (self.text, self.font, self.size, self.bold, self.italic, self.align):
            w.blockSignals(False)

    def apply(self, el: TextElement):
        el.text        = self.text.text()
        el.font_family = self.font.text()
        el.font_size   = self.size.value()
        el.bold        = self.bold.isChecked()
        el.italic      = self.italic.isChecked()
        el.color       = self.color.color()
        el.align       = self.align.currentText()


class BarcodeProps(_BaseProps):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.code      = QLineEdit();  self.code.textChanged.connect(self._emit)
        self.btype     = QComboBox();  self.btype.addItems(BARCODE_TYPES)
        self.btype.currentIndexChanged.connect(self._emit)
        self.show_text = QCheckBox("Mostrar número")
        self.show_text.toggled.connect(self._emit)

        layout.addLayout(_hrow("Valor", self.code))
        layout.addLayout(_hrow("Tipo",  self.btype))
        layout.addWidget(self.show_text)

    def load(self, el: BarcodeElement):
        # ── FIX: block show_text signal too
        for w in (self.code, self.btype, self.show_text):
            w.blockSignals(True)
        self.code.setText(el.code)
        idx = self.btype.findText(el.barcode_type)
        self.btype.setCurrentIndex(max(0, idx))
        self.show_text.setChecked(el.show_text)
        for w in (self.code, self.btype, self.show_text):
            w.blockSignals(False)

    def apply(self, el: BarcodeElement):
        el.code         = self.code.text()
        el.barcode_type = self.btype.currentText()
        el.show_text    = self.show_text.isChecked()


class ImageProps(_BaseProps):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.path     = QLineEdit(); self.path.setReadOnly(True)
        browse_btn    = QPushButton("Buscar…")
        browse_btn.clicked.connect(self._browse)
        self.keep_aspect = QCheckBox("Mantener proporción")
        self.keep_aspect.setChecked(True)
        self.keep_aspect.toggled.connect(self._emit)

        row_w = QWidget()
        row   = QHBoxLayout(row_w)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.path)
        row.addWidget(browse_btn)
        layout.addLayout(_hrow("Logo", row_w))
        layout.addWidget(self.keep_aspect)

    def _browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "",
                                            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if f:
            self.path.blockSignals(True)
            self.path.setText(f)
            self.path.blockSignals(False)
            self._emit()

    def load(self, el: ImageElement):
        # ── FIX: block keep_aspect signal
        self.keep_aspect.blockSignals(True)
        self.path.setText(el.path)
        self.keep_aspect.setChecked(el.keep_aspect)
        self.keep_aspect.blockSignals(False)

    def apply(self, el: ImageElement):
        el.path        = self.path.text()
        el.keep_aspect = self.keep_aspect.isChecked()


class RectProps(_BaseProps):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.border_color = ColorButton()
        self.fill_color   = ColorButton("#ffffff")
        self.border_width = QDoubleSpinBox(); self.border_width.setRange(0.5, 20)
        self.filled       = QCheckBox("Relleno sólido")

        self.border_color.color_changed.connect(self._emit)
        self.fill_color.color_changed.connect(self._emit)
        self.border_width.valueChanged.connect(self._emit)
        self.filled.toggled.connect(self._emit)

        layout.addLayout(_hrow("Borde",   self.border_color))
        layout.addLayout(_hrow("Relleno", self.fill_color))
        layout.addLayout(_hrow("Grosor",  self.border_width))
        layout.addWidget(self.filled)

    def load(self, el: RectElement):
        # ── FIX: block border_width and filled signals
        self.border_width.blockSignals(True)
        self.filled.blockSignals(True)
        self.border_color.set_color(el.border_color)
        self.fill_color.set_color(el.fill_color)
        self.border_width.setValue(el.border_width)
        self.filled.setChecked(el.filled)
        self.border_width.blockSignals(False)
        self.filled.blockSignals(False)

    def apply(self, el: RectElement):
        el.border_color = self.border_color.color()
        el.fill_color   = self.fill_color.color()
        el.border_width = self.border_width.value()
        el.filled       = self.filled.isChecked()


# ── Main panel ─────────────────────────────────────────────────────────────────

class PropertiesPanel(QWidget):
    element_changed = pyqtSignal(object)  # emits the modified BaseElement

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(300)

        # ── FIX: _current starts as None; set to None BEFORE loading to block
        #   spurious _on_change calls during setValue / setText.
        self._current: BaseElement | None = None
        self._loading: bool = False   # extra guard

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)

        self._title = QLabel("Sin selección")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            "font-weight:bold; padding:4px; background:#1a73e8;"
            "color:white; border-radius:3px;")
        outer.addWidget(self._title)

        self._geo = _GeometryProps()
        self._geo.changed.connect(self._on_change)
        outer.addWidget(self._geo)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(sep)

        self._stack     = QStackedWidget()
        self._text_p    = TextProps();    self._text_p.changed.connect(self._on_change)
        self._barcode_p = BarcodeProps(); self._barcode_p.changed.connect(self._on_change)
        self._image_p   = ImageProps();   self._image_p.changed.connect(self._on_change)
        self._rect_p    = RectProps();    self._rect_p.changed.connect(self._on_change)
        self._empty_p   = QWidget()

        for p in (self._empty_p, self._text_p, self._barcode_p,
                  self._image_p, self._rect_p):
            self._stack.addWidget(p)

        outer.addWidget(self._stack)
        outer.addStretch()

        self._PAGE = {
            ELEMENT_TEXT:    1,
            ELEMENT_BARCODE: 2,
            ELEMENT_IMAGE:   3,
            ELEMENT_RECT:    4,
        }

    # ── Public API ─────────────────────────────────────────────────────────

    def load_element(self, element: BaseElement | None):
        """
        Load an element's data into the panel.

        Key fix: set self._current = None BEFORE touching any widget, so any
        spurious signals emitted during setValue/setText reach _on_change while
        _current is None and are silently ignored.
        """
        # ── FIX ①: detach current element before loading
        self._current = None
        self._loading = True

        if element is None:
            self._title.setText("Sin selección")
            self._stack.setCurrentIndex(0)
            self._geo.setEnabled(False)
            self._loading = False
            return

        self._geo.setEnabled(True)
        self._geo.load(element)

        page = self._PAGE.get(element.type, 0)
        self._stack.setCurrentIndex(page)
        self._title.setText({
            ELEMENT_TEXT:    "✏️  Texto",
            ELEMENT_BARCODE: "📊 Código / QR",
            ELEMENT_IMAGE:   "🖼️  Imagen / Logo",
            ELEMENT_RECT:    "▭  Rectángulo",
        }.get(element.type, "Elemento"))

        if element.type == ELEMENT_TEXT:
            self._text_p.load(element)
        elif element.type == ELEMENT_BARCODE:
            self._barcode_p.load(element)
        elif element.type == ELEMENT_IMAGE:
            self._image_p.load(element)
        elif element.type == ELEMENT_RECT:
            self._rect_p.load(element)

        # ── FIX ②: only NOW attach the element — any changes from here on
        #   are real user edits.
        self._current = element
        self._loading = False

    # ── Internal ───────────────────────────────────────────────────────────

    def _on_change(self):
        # ── FIX: double guard — _loading flag + _current None check
        if self._loading or self._current is None:
            return
        self._geo.apply(self._current)
        if self._current.type == ELEMENT_TEXT:
            self._text_p.apply(self._current)
        elif self._current.type == ELEMENT_BARCODE:
            self._barcode_p.apply(self._current)
        elif self._current.type == ELEMENT_IMAGE:
            self._image_p.apply(self._current)
        elif self._current.type == ELEMENT_RECT:
            self._rect_p.apply(self._current)
        self.element_changed.emit(self._current)
