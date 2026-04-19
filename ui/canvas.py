"""
ui/canvas.py  (v2 — bugs fixed)

Fixes applied:
 1. RubberBandDrag → NoDrag: items now move freely in X and Y simultaneously.
 2. _initializing flag in ElementItem prevents itemChange from firing during __init__.
 3. mouseReleaseEvent only emits item_clicked when the mouse didn't travel (no false
    triggers at the end of a drag).
 4. _draw_background now removes only items whose zValue < 0, so ElementItem child
    labels (QGraphicsTextItem) are never accidentally removed.
 5. element_added signal: after inserting via toolbar the new item gets auto-selected
    and its properties shown immediately.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsItem,
                              QGraphicsRectItem, QGraphicsTextItem)
from PyQt6.QtGui  import (QPen, QBrush, QColor, QPainter)
from PyQt6.QtCore import Qt, QPointF, pyqtSignal

from core.elements import (BaseElement, TextElement, BarcodeElement,
                            ImageElement, RectElement,
                            ELEMENT_TEXT, ELEMENT_BARCODE, ELEMENT_IMAGE, ELEMENT_RECT)

SCREEN_SCALE = 3.0   # screen pixels per engine-pixel (8 px/mm at 203 DPI)


def _mm_to_screen(mm: float) -> float:
    return mm * 8.0 * SCREEN_SCALE


class ElementItem(QGraphicsRectItem):
    """
    Visual proxy for a BaseElement on the QGraphicsScene.
    Moving the item on screen keeps element.x / element.y in sync.
    """

    def __init__(self, element: BaseElement, canvas: "LabelCanvas"):
        w = _mm_to_screen(element.width)
        h = _mm_to_screen(element.height)
        super().__init__(0, 0, w, h)

        # Prevent itemChange from firing while we set the initial position
        self._initializing = True

        self.element = element
        self.canvas  = canvas

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        # Visual style — blue dashed outline
        self.setPen(QPen(QColor("#1a73e8"), 1, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(Qt.GlobalColor.transparent))

        # Content label (child item)
        self._label = QGraphicsTextItem(self)
        self._label.setDefaultTextColor(QColor("#1a73e8"))
        self._label.setPos(2, 2)
        font = self._label.font()
        font.setPointSize(7)
        self._label.setFont(font)
        self._update_label()

        # Set position last so itemChange sees _initializing = True
        self.setPos(_mm_to_screen(element.x), _mm_to_screen(element.y))
        self._initializing = False

        # Track mouse-press position to distinguish click from drag
        self._press_pos: QPointF | None = None

    # ── Label ──────────────────────────────────────────────────────────────

    def _update_label(self):
        el = self.element
        if el.type == ELEMENT_TEXT:
            self._label.setPlainText(f"[T] {el.text[:22]}")
        elif el.type == ELEMENT_BARCODE:
            self._label.setPlainText(f"[{el.barcode_type.upper()}] {el.code[:15]}")
        elif el.type == ELEMENT_IMAGE:
            import os
            name = os.path.basename(el.path) if el.path else "(sin imagen)"
            self._label.setPlainText(f"[IMG] {name}")
        elif el.type == ELEMENT_RECT:
            self._label.setPlainText("[RECT]")

    def refresh(self):
        """Call when element data changed externally (properties panel)."""
        self._update_label()
        self._initializing = True
        self.setRect(0, 0, _mm_to_screen(self.element.width),
                           _mm_to_screen(self.element.height))
        self.setPos(_mm_to_screen(self.element.x),
                    _mm_to_screen(self.element.y))
        self._initializing = False

    # ── Qt overrides ───────────────────────────────────────────────────────

    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
                and not self._initializing):
            # Sync screen position → data model
            pos = value  # QPointF
            self.element.x = round(pos.x() / (8.0 * SCREEN_SCALE), 2)
            self.element.y = round(pos.y() / (8.0 * SCREEN_SCALE), 2)
            if self.canvas:
                self.canvas.request_preview_refresh()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self._press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Only emit item_clicked when the user did NOT drag (displacement < 3 px)
        if self.canvas and self._press_pos is not None:
            delta = event.pos() - self._press_pos
            if abs(delta.x()) < 3 and abs(delta.y()) < 3:
                self.canvas.item_clicked.emit(self.element)
        self._press_pos = None

    def mouseDoubleClickEvent(self, event):
        """Double-click always shows properties."""
        super().mouseDoubleClickEvent(event)
        if self.canvas:
            self.canvas.item_clicked.emit(self.element)


class LabelCanvas(QGraphicsView):
    # Emitted with the BaseElement the user clicked/selected
    item_clicked   = pyqtSignal(object)
    # Emitted whenever the layout changes (triggers preview refresh)
    canvas_changed = pyqtSignal()

    def __init__(self, width_mm: float = 40, height_mm: float = 25, parent=None):
        super().__init__(parent)
        self.width_mm  = width_mm
        self.height_mm = height_mm
        self._items: list[ElementItem] = []
        self._pending_insert_type: str | None = None

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ── FIX: NoDrag lets QGraphicsItem.ItemIsMovable work freely in X+Y.
        #   RubberBandDrag mode conflicts with ItemIsMovable and restricts
        #   movement to a single axis.
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # Emit canvas_changed when scene selection changes (e.g. delete key)
        self.scene.selectionChanged.connect(self._on_selection_changed)

        self._draw_background()

    # ── Public API ─────────────────────────────────────────────────────────

    def set_dimensions(self, width_mm: float, height_mm: float):
        self.width_mm  = width_mm
        self.height_mm = height_mm
        self._draw_background()
        self.request_preview_refresh()

    def add_element(self, element: BaseElement) -> ElementItem:
        item = ElementItem(element, self)
        self.scene.addItem(item)
        self._items.append(item)
        # Auto-select the newly added item
        self.scene.clearSelection()
        item.setSelected(True)
        self.request_preview_refresh()
        return item

    def remove_selected(self) -> list[BaseElement]:
        removed = []
        for item in list(self.scene.selectedItems()):
            if isinstance(item, ElementItem):
                removed.append(item.element)
                self.scene.removeItem(item)
                self._items.remove(item)
        self.request_preview_refresh()
        return removed

    def get_elements(self) -> list[BaseElement]:
        return [i.element for i in self._items]

    def clear_all(self):
        for item in list(self._items):
            self.scene.removeItem(item)
        self._items.clear()
        self._draw_background()

    def refresh_item(self, element: BaseElement):
        for item in self._items:
            if item.element is element:
                item.refresh()
        self.request_preview_refresh()

    def set_insert_mode(self, element_type: str | None):
        self._pending_insert_type = element_type
        if element_type:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def request_preview_refresh(self):
        self.canvas_changed.emit()

    # ── Mouse handling ─────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if self._pending_insert_type and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            x_mm = round(scene_pos.x() / (8.0 * SCREEN_SCALE), 1)
            y_mm = round(scene_pos.y() / (8.0 * SCREEN_SCALE), 1)
            # Clamp to label area
            x_mm = max(0.0, min(x_mm, self.width_mm - 5))
            y_mm = max(0.0, min(y_mm, self.height_mm - 5))
            el = self._insert_element_at(self._pending_insert_type, x_mm, y_mm)
            self.set_insert_mode(None)
            if el:
                self.item_clicked.emit(el)
            return
        super().mousePressEvent(event)

    def _insert_element_at(self, etype: str, x: float, y: float) -> BaseElement | None:
        if etype == ELEMENT_TEXT:
            el = TextElement(x=x, y=y, width=30, height=6, text="Nuevo texto")
        elif etype == ELEMENT_BARCODE:
            el = BarcodeElement(x=x, y=y, width=35, height=15,
                                code="0000000000000", barcode_type="code128")
        elif etype == ELEMENT_IMAGE:
            el = ImageElement(x=x, y=y, width=15, height=15)
        elif etype == ELEMENT_RECT:
            el = RectElement(x=x, y=y, width=20, height=10)
        else:
            return None
        self.add_element(el)
        return el

    # ── Background / safety guides ─────────────────────────────────────────

    def _draw_background(self):
        # ── FIX: only remove items whose zValue < 0 (background/guide items).
        #   Previously ALL non-ElementItem items were removed, which could also
        #   delete QGraphicsTextItem children of ElementItems.
        for item in list(self.scene.items()):
            if item.zValue() < 0:
                self.scene.removeItem(item)

        W = _mm_to_screen(self.width_mm)
        H = _mm_to_screen(self.height_mm)
        margin_px = _mm_to_screen(2)

        self.scene.setSceneRect(-20, -20, W + 40, H + 40)

        # White label background with drop shadow effect
        shadow = self.scene.addRect(3, 3, W, H,
                                     QPen(Qt.PenStyle.NoPen),
                                     QBrush(QColor("#00000030")))
        shadow.setZValue(-11)

        bg = self.scene.addRect(0, 0, W, H,
                                 QPen(QColor("#aaaaaa"), 1),
                                 QBrush(QColor("#ffffff")))
        bg.setZValue(-10)

        # Safety margin guides (red dashed lines)
        pen = QPen(QColor("#e03030"), 1, Qt.PenStyle.DashLine)
        for coords in [
            (margin_px, 0,         margin_px, H),
            (W - margin_px, 0,     W - margin_px, H),
            (0,         margin_px, W, margin_px),
            (0, H - margin_px,     W, H - margin_px),
        ]:
            gl = self.scene.addLine(*coords, pen)
            gl.setZValue(-9)

    # ── Internal signals ───────────────────────────────────────────────────

    def _on_selection_changed(self):
        """When Esc or click-on-empty deselects, clear the properties panel."""
        selected = [i for i in self.scene.selectedItems() if isinstance(i, ElementItem)]
        if not selected:
            self.item_clicked.emit(None)
