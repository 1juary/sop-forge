#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高亮框选组件：HighlightItem
"""

from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QColor, QPen, QBrush, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF

from src.items.base_item import SmartGraphicItemMixin
from src.items.icon_item import IconItem


class HighlightItem(SmartGraphicItemMixin, QGraphicsRectItem):
    HIGHLIGHT_COLORS = IconItem.STANDARD_COLORS

    def __init__(self, x=0, y=0, width=100, height=60):
        super().__init__(x, y, width, height)
        self._border_color = QColor("#f43f5e")
        self._fill_color = QColor(244, 63, 94, 30)
        self._border_width = 2
        self._dashed = False
        self.setAcceptHoverEvents(True)
        self._is_resizing = False
        self._apply_style()

    def _apply_style(self):
        pen = QPen(self._border_color, self._border_width)
        pen.setStyle(Qt.DashLine if self._dashed else Qt.SolidLine)
        self.setPen(pen)
        self.setBrush(QBrush(self._fill_color))

    def set_border_color(self, color_hex: str):
        self._border_color = QColor(color_hex)
        self._fill_color = QColor(color_hex)
        self._fill_color.setAlpha(30)
        self._apply_style()

    def set_border_color_by_name(self, name: str):
        if name in self.HIGHLIGHT_COLORS:
            self.set_border_color(self.HIGHLIGHT_COLORS[name])

    def set_border_width(self, width: int):
        self._border_width = max(1, min(10, width))
        self._apply_style()

    def set_dashed(self, dashed: bool):
        self._dashed = dashed
        self._apply_style()

    def _handle_rect(self):
        return QRectF(self.rect().right() - 10, self.rect().bottom() - 10, 15, 15)

    def hoverMoveEvent(self, event):
        if self._handle_rect().contains(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.OpenHandCursor if not self.isSelected() else Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._handle_rect().contains(event.pos()):
            self._is_resizing = True
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_is_resizing', False):
            self.prepareGeometryChange()
            self.setRect(0, 0, max(20.0, event.pos().x()), max(20.0, event.pos().y()))
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_is_resizing', False):
            self._is_resizing = False
            if self.scene():
                self.scene().selectionChanged.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#0ea5e9"), 2))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(self.rect().right(), self.rect().bottom()), 6, 6)

    def to_dict(self) -> dict:
        return {
            "type": "highlight", "x": self.scenePos().x(), "y": self.scenePos().y(),
            "width": self.rect().width(), "height": self.rect().height(),
            "border_color": self._border_color.name(),
            "border_width": self._border_width, "dashed": self._dashed,
            "_is_frozen": getattr(self, '_is_frozen', False),
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        item = cls(x=data.get("x", 0), y=data.get("y", 0), width=data.get("width", 100), height=data.get("height", 60))
        if "border_color" in data:
            item.set_border_color(data["border_color"])
        if "border_width" in data:
            item.set_border_width(data["border_width"])
        if "dashed" in data:
            item.set_dashed(data["dashed"])
        if data.get("_is_frozen", False):
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item._is_frozen = True
        return item
