#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
箭头组件：ArrowItem
"""

import math

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import (
    QColor, QPen, QBrush, QPainter, QPainterPath, QPainterPathStroker,
)
from PySide6.QtCore import Qt, QRectF, QPointF

from src.items.base_item import SmartGraphicItemMixin
from src.items.icon_item import IconItem


class ArrowItem(SmartGraphicItemMixin, QGraphicsItem):
    ARROW_COLORS = IconItem.STANDARD_COLORS

    def __init__(self, angle=0, length=120):
        super().__init__()
        self._angle = angle
        self._length = length
        self._color = QColor("#0ea5e9")
        self._line_width = 2
        self._arrow_size = 12
        self.setAcceptHoverEvents(True)
        self._is_resizing_tip = False
        self._is_resizing_base = False

    def set_angle(self, angle: int):
        self.prepareGeometryChange()
        self._angle = angle
        self.update()

    def set_length(self, length: int):
        self.prepareGeometryChange()
        self._length = max(20, min(800, length))
        self.update()

    def set_color(self, color_hex: str):
        self._color = QColor(color_hex)
        self.update()

    def set_color_by_name(self, name: str):
        if name in self.ARROW_COLORS:
            self.set_color(self.ARROW_COLORS[name])

    def set_line_width(self, width: int):
        self.prepareGeometryChange()
        self._line_width = max(1, min(8, width))
        self.update()

    def boundingRect(self):
        r = self._length + self._arrow_size + self._line_width + 10
        return QRectF(-r, -r, r * 2, r * 2)

    def _tip_rect(self):
        return QRectF(self._length * math.cos(math.radians(self._angle)) - 15, self._length * math.sin(math.radians(self._angle)) - 15, 30, 30)

    def _base_rect(self):
        return QRectF(-15, -15, 30, 30)

    def shape(self):
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(self._length * math.cos(math.radians(self._angle)), self._length * math.sin(math.radians(self._angle)))
        stroker = QPainterPathStroker()
        stroker.setWidth(15)
        return stroker.createStroke(path)

    def hoverMoveEvent(self, event):
        if self._tip_rect().contains(event.pos()) or self._base_rect().contains(event.pos()):
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.OpenHandCursor if not self.isSelected() else Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._tip_rect().contains(event.pos()):
                self._is_resizing_tip = True
                event.accept()
                return
            elif self._base_rect().contains(event.pos()):
                self._is_resizing_base = True
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_is_resizing_tip', False):
            self.prepareGeometryChange()
            self._length = max(20, math.hypot(event.pos().x(), event.pos().y()))
            self._angle = math.degrees(math.atan2(event.pos().y(), event.pos().x()))
            self.update()
            event.accept()
        elif getattr(self, '_is_resizing_base', False):
            old_tip = self.mapToScene(QPointF(self._length * math.cos(math.radians(self._angle)), self._length * math.sin(math.radians(self._angle))))
            self.setPos(event.scenePos())
            new_tip = self.mapFromScene(old_tip)
            self.prepareGeometryChange()
            self._length = max(20, math.hypot(new_tip.x(), new_tip.y()))
            self._angle = math.degrees(math.atan2(new_tip.y(), new_tip.x()))
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_is_resizing_tip', False) or getattr(self, '_is_resizing_base', False):
            self._is_resizing_tip = False
            self._is_resizing_base = False
            if self.scene():
                self.scene().selectionChanged.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.save()
        painter.rotate(self._angle)
        painter.setPen(QPen(self._color, self._line_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(0, 0, self._length, 0)
        p1 = QPointF(self._length - self._arrow_size * math.cos(math.radians(25)), - self._arrow_size * math.sin(math.radians(25)))
        p2 = QPointF(self._length - self._arrow_size * math.cos(math.radians(25)), + self._arrow_size * math.sin(math.radians(25)))
        ap = QPainterPath()
        ap.moveTo(self._length, 0)
        ap.lineTo(p1)
        ap.lineTo(p2)
        ap.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self._color))
        painter.drawPath(ap)
        painter.restore()

        if self.isSelected():
            painter.setPen(QPen(QColor("#0ea5e9"), 2))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(self._length * math.cos(math.radians(self._angle)), self._length * math.sin(math.radians(self._angle))), 6, 6)
            painter.drawEllipse(QPointF(0, 0), 6, 6)

    def to_dict(self) -> dict:
        return {
            "type": "arrow", "angle": self._angle, "x": self.scenePos().x(),
            "y": self.scenePos().y(), "length": self._length,
            "color": self._color.name(), "line_width": self._line_width,
            "_is_frozen": getattr(self, '_is_frozen', False),
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        angle = data.get("angle", {"top_left": 225, "top_right": 315, "bottom_left": 135, "bottom_right": 45}.get(data.get("direction", ""), 0))
        item = cls(angle=angle, length=data.get("length", 120))
        item.setPos(data.get("x", 0), data.get("y", 0))
        if "color" in data:
            item.set_color(data["color"])
        if "line_width" in data:
            item.set_line_width(data["line_width"])
        if data.get("_is_frozen", False):
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item._is_frozen = True
        return item
