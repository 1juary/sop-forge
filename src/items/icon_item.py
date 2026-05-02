#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标组件：IconItem
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QColor, QPen, QBrush, QPainter, QFont
from PySide6.QtCore import Qt, QRectF

from src.items.base_item import SmartGraphicItemMixin


class IconItem(SmartGraphicItemMixin, QGraphicsItem):
    ICON_TYPES = {
        "warning": {"symbol": "⚠", "default_color": "#eab308"},
        "info": {"symbol": "ℹ", "default_color": "#0ea5e9"},
        "tool": {"symbol": "🔧", "default_color": "#64748b"},
        "check": {"symbol": "✓", "default_color": "#22c55e"},
        "error": {"symbol": "✕", "default_color": "#f43f5e"},
        "arrow_right": {"symbol": "→", "default_color": "#8b5cf6"},
        "arrow_down": {"symbol": "↓", "default_color": "#8b5cf6"},
        "star": {"symbol": "★", "default_color": "#eab308"},
    }
    STANDARD_COLORS = {
        "多巴胺黄": "#eab308", "赛博青": "#0ea5e9", "石板灰": "#64748b",
        "生命绿": "#22c55e", "霓虹粉": "#f43f5e", "电竞紫": "#8b5cf6",
        "元气橙": "#f97316", "冰晶蓝": "#06b6d4",
    }

    def __init__(self, icon_type="warning", size=32):
        super().__init__()
        self._icon_type = icon_type
        self._size = size
        self._color = QColor(self.ICON_TYPES[icon_type]["default_color"])
        self._show_bg = True

    def set_icon_type(self, icon_type: str):
        if icon_type in self.ICON_TYPES:
            self._icon_type = icon_type
            self._color = QColor(self.ICON_TYPES[icon_type]["default_color"])
            self.update()

    def set_color(self, color_hex: str):
        self._color = QColor(color_hex)
        self.update()

    def set_color_by_name(self, color_name: str):
        if color_name in self.STANDARD_COLORS:
            self.set_color(self.STANDARD_COLORS[color_name])

    def set_size(self, size: int):
        self.prepareGeometryChange()
        self._size = max(16, min(64, size))
        self.update()

    def boundingRect(self):
        return QRectF(0, 0, self._size + 8, self._size + 8)

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        if self._show_bg:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f8fafc")))
            painter.drawEllipse(rect.center(), self._size / 2 + 2, self._size / 2 + 2)
        painter.setPen(self._color)
        painter.setFont(QFont("Segoe UI Emoji", int(self._size * 0.6)))
        painter.drawText(rect, Qt.AlignCenter, self.ICON_TYPES.get(self._icon_type, self.ICON_TYPES["warning"])["symbol"])

    def to_dict(self) -> dict:
        return {
            "type": "icon", "icon_type": self._icon_type,
            "x": self.scenePos().x(), "y": self.scenePos().y(),
            "size": self._size, "color": self._color.name(),
            "_is_frozen": getattr(self, '_is_frozen', False),
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        item = cls(icon_type=data.get("icon_type", "warning"), size=data.get("size", 32))
        item.setPos(data.get("x", 0), data.get("y", 0))
        if "color" in data:
            item.set_color(data["color"])
        if data.get("_is_frozen", False):
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item._is_frozen = True
        return item
