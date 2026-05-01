#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP Forge - SOP排版设计软件 (单文件版)
========================================
UI风格: 明亮科技风 + 多巴胺配色 (Dopamine Tech Light)
功能包含: 多页连排、持久化记忆、Drag&Drop、可视化双向调节
"""

import math
import re
import json
import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QPushButton, QToolButton,
    QFrame, QScrollArea, QGroupBox, QSizePolicy,
    QComboBox, QSpinBox, QDoubleSpinBox, QColorDialog, QCheckBox,
    QFormLayout, QSlider, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsScene,
    QGraphicsView, QGraphicsItemGroup,
)
from PySide6.QtGui import (
    QFont, QColor, QPen, QBrush, QPainter, QPainterPath,
    QPixmap, QAction, QKeySequence, QDrag, QTransform,
    QTextOption, QPolygonF, QPageSize, QFontDatabase,
    QTextCursor, QClipboard, QCursor, QActionGroup,
    QPainterPathStroker, QImage, QPalette
)
from PySide6.QtCore import (
    Qt, Signal, QRectF, QPointF, QPoint, QLineF, QSize, QMimeData,
    QByteArray, QDataStream, QIODevice, QRect, QUrl, QSettings
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# =============================================================================
# 全局多巴胺 QSS 样式定义
# =============================================================================
GLOBAL_QSS = """
/* 全局基础 */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}
QMainWindow {
    background-color: #f1f5f9;
}

/* 顶部菜单与工具栏 */
QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}
QMenuBar::item {
    padding: 6px 12px;
    background: transparent;
    color: #1e293b;
}
QMenuBar::item:selected {
    background: #f0fdf4;
    color: #16a34a;
    border-radius: 4px;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 2px solid #e2e8f0;
    padding: 6px;
    spacing: 8px;
}

/* 面板背景与滚动条 */
QSplitter::handle {
    background-color: #cbd5e1;
    width: 2px;
}
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

/* 分组框 (多巴胺描边) */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 16px;
    font-weight: bold;
    color: #334155;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #0ea5e9;
}

/* 表单组件 */
QLineEdit, QComboBox, QSpinBox {
    background-color: #f8fafc;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    color: #0f172a;
    selection-background-color: #38bdf8;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #06b6d4;
    background-color: #ffffff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    border: 1px solid #06b6d4;
    border-radius: 4px;
    background-color: #ffffff;
    selection-background-color: #cffafe;
    selection-color: #0891b2;
}

/* 滑块 */
QSlider::groove:horizontal {
    border-radius: 4px;
    height: 8px;
    background: #e2e8f0;
}
QSlider::handle:horizontal {
    background: #ec4899;
    width: 16px;
    height: 16px;
    margin: -4px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #f472b6;
    border-radius: 4px;
}

/* 复选框 */
QCheckBox {
    spacing: 8px;
    font-size: 12px;
    color: #1e293b;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #cbd5e1;
    background: #f8fafc;
}
QCheckBox::indicator:checked {
    background: #8b5cf6;
    border: 2px solid #8b5cf6;
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>);
}

/* 表格 */
QTableWidget {
    background-color: #ffffff;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    color: #1e293b;
}
QTableWidget::item {
    background-color: #ffffff;
    color: #1e293b;
    padding: 4px;
}
QTableWidget::item:selected {
    background-color: #e0f2fe;
    color: #0369a1;
}
QHeaderView::section {
    background-color: #f8fafc;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    padding: 8px;
    font-weight: bold;
    color: #475569;
}
"""

# =============================================================================
# 第 2 部分：通用混入类 (Mixin) 与基础数据结构
# =============================================================================

class SmartGraphicItemMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            if hasattr(self.scene(), "calculate_snap"):
                value = self.scene().calculate_snap(self, value)
            return value
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.scene().update()
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)


# =============================================================================
# 第 3 部分：所有的画布组件 (Items)
# =============================================================================

class SOPTextItem(SmartGraphicItemMixin, QGraphicsTextItem):
    LEVEL_CONFIG = {
        "title": {"font_size": 20, "bold": True, "color": "#0f172a", "desc": "大标题"},
        "body": {"font_size": 12, "bold": False, "color": "#334155", "desc": "正文"},
        "caption": {"font_size": 9, "bold": False, "color": "#64748b", "desc": "注脚"},
    }
    DEFAULT_EMOJI_DICT = {
        "警告": "⚠️", "注意": "💡", "检查": "✅", "危险": "🚫",
        "提示": "💡", "重要": "❗", "完成": "✅", "待办": "📝",
    }
    textChanged = Signal()

    def __init__(self, text="请输入正文...", level="body"):
        super().__init__(text)
        self._level = level
        self._emoji_dict = dict(self.DEFAULT_EMOJI_DICT)
        self._enable_emoji = True
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self._apply_level_style()
        self.document().contentsChange.connect(self._on_text_changed)

    def _apply_level_style(self):
        config = self.LEVEL_CONFIG.get(self._level, self.LEVEL_CONFIG["body"])
        font = QFont("Microsoft YaHei", config["font_size"])
        font.setBold(config["bold"])
        self.setFont(font)
        self.setDefaultTextColor(QColor(config["color"]))
        option = self.document().defaultTextOption()
        option.setAlignment(Qt.AlignLeft)
        self.document().setDefaultTextOption(option)

    def set_level(self, level: str):
        if level in self.LEVEL_CONFIG:
            self._level = level
            self._apply_level_style()

    def get_level(self) -> str: 
        return self._level

    def mouseDoubleClickEvent(self, event):
        if self.textInteractionFlags() == Qt.NoTextInteraction:
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setFocus()
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.check_alignment()
        super().focusOutEvent(event)

    def _on_text_changed(self, position, charsRemoved, charsAdded):
        if not self._enable_emoji or charsAdded <= 0: 
            return
        doc = self.document()
        text = doc.toPlainText()
        modified = False
        for keyword, emoji in self._emoji_dict.items():
            pattern = re.escape(keyword) + r"(?!\s*" + re.escape(emoji) + r")"
            if re.search(pattern, text):
                text = re.sub(pattern, f"{keyword}{emoji}", text)
                modified = True
        if modified:
            self.document().contentsChange.disconnect(self._on_text_changed)
            cursor = self.textCursor()
            pos = cursor.position()
            self.setPlainText(text)
            new_cursor = self.textCursor()
            new_cursor.setPosition(min(pos + 1, len(self.toPlainText())))
            self.setTextCursor(new_cursor)
            self.document().contentsChange.connect(self._on_text_changed)
            self.textChanged.emit()

    def check_alignment(self):
        doc = self.document()
        alignment = doc.defaultTextOption().alignment()
        if len(self.toPlainText()) > 20 and (alignment & (Qt.AlignCenter | Qt.AlignRight)):
            QMessageBox.warning(None, "排版防雷", "超过20字的长段落禁止『居中』或『右对齐』。\n已自动恢复。")
            option = doc.defaultTextOption()
            option.setAlignment(Qt.AlignLeft)
            doc.setDefaultTextOption(option)

    def set_emoji_dict(self, emoji_dict: dict): 
        self._emoji_dict = emoji_dict.copy()

    def to_dict(self) -> dict:
        pos = self.scenePos() if self.scene() else self.pos()
        return {
            "type": "text", "level": self._level, "text": self.toPlainText(), 
            "x": pos.x(), "y": pos.y(), "font_family": self.font().family(), 
            "font_size": self.font().pointSize(), "bold": self.font().bold()
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        item = cls(text=data.get("text", ""), level=data.get("level", "body"))
        item.setPos(data.get("x", 0), data.get("y", 0))
        if "font_family" in data:
            font = item.font()
            font.setFamily(data["font_family"])
            item.setFont(font)
        return item


class ImageCaptionItem(QGraphicsTextItem):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Microsoft YaHei", 9))
        self.setDefaultTextColor(QColor("#64748b"))
        self.setTextInteractionFlags(Qt.TextEditorInteraction)

class ImageItem(SmartGraphicItemMixin, QGraphicsItem):
    _image_counter = 0

    def __init__(self, pixmap=None, caption_text=""):
        super().__init__()
        ImageItem._image_counter += 1
        self._image_number = ImageItem._image_counter
        self._pixmap = pixmap or QPixmap()
        self._caption = ImageCaptionItem(self)
        self._show_caption = True
        self.setAcceptHoverEvents(True)
        self._is_resizing = False
        self._calc_initial_size()
        self._update_caption_text(caption_text)

    def _calc_initial_size(self):
        if not self._pixmap.isNull():
            orig_w = self._pixmap.width()
            orig_h = self._pixmap.height()
            scale = min(400.0 / max(1, orig_w), 300.0 / max(1, orig_h), 1.0)
            self._image_width = orig_w * scale
            self._image_height = orig_h * scale
        else:
            self._image_width = 200
            self._image_height = 150

    def _update_caption_text(self, text=""):
        self._caption.setPlainText(f"图 {self._image_number}: " + text if text else f"图 {self._image_number}: ")
        self._update_caption_position()

    def _update_caption_position(self):
        self._caption.setPos(QPointF((self._image_width - self._caption.boundingRect().width()) / 2, self._image_height + 4))

    def set_show_caption(self, show: bool):
        self.prepareGeometryChange()
        self._show_caption = show
        self._caption.setVisible(show)
        self.update()

    def set_pixmap(self, pixmap: QPixmap):
        self.prepareGeometryChange()
        self._pixmap = pixmap
        self._calc_initial_size()
        self._update_caption_position()
        self.update()

    def set_caption(self, text: str): 
        self._update_caption_text(text)

    def get_caption(self) -> str: 
        return re.sub(r"^图 \d+: ", "", self._caption.toPlainText())

    def boundingRect(self):
        extra_h = 30 if self._show_caption else 0
        return QRectF(0, 0, self._image_width, self._image_height + extra_h)

    def _handle_rect(self): 
        return QRectF(self._image_width - 10, self._image_height - 10, 15, 15)

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
            new_w = max(30.0, event.pos().x())
            if not self._pixmap.isNull():
                new_h = new_w * (self._pixmap.height() / max(1, self._pixmap.width())) 
            else:
                new_h = max(30.0, event.pos().y())
            self.prepareGeometryChange()
            self._image_width = new_w
            self._image_height = new_h
            self._update_caption_position()
            self.update()
            if self.scene(): 
                self.scene().update()
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
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(int(self._image_width), int(self._image_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(QPointF((self._image_width - scaled.width()) / 2, (self._image_height - scaled.height()) / 2), scaled)
        else:
            painter.setPen(QPen(QColor("#94a3b8"), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor("#f1f5f9")))
            painter.drawRect(QRectF(0, 0, self._image_width, self._image_height))
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(QRectF(0, 0, self._image_width, self._image_height), Qt.AlignCenter, "未加载图片")
            
        if self.isSelected():
            painter.setPen(QPen(QColor("#0ea5e9"), 2))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(self._image_width, self._image_height), 6, 6)

    def to_dict(self) -> dict:
        pos = self.scenePos() if self.scene() else self.pos()
        pixmap_base64 = ""
        if not self._pixmap.isNull():
            ba = QByteArray()
            self._pixmap.save(QDataStream(ba, QIODevice.WriteOnly), "PNG")
            pixmap_base64 = ba.toBase64().data().decode("ascii")
        return {
            "type": "image", "x": pos.x(), "y": pos.y(),
            "width": self._image_width, "height": self._image_height,
            "caption": self.get_caption(), "image_number": self._image_number,
            "show_caption": self._show_caption,
            "pixmap_base64": pixmap_base64,
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        pixmap = QPixmap()
        if pb := data.get("pixmap_base64", ""): 
            pixmap.loadFromData(QByteArray.fromBase64(pb.encode("ascii")), "PNG")
        item = cls(pixmap=pixmap, caption_text=data.get("caption", ""))
        item.setPos(data.get("x", 0), data.get("y", 0))
        item._image_width = data.get("width", 200)
        item._image_height = data.get("height", 150)
        item._image_number = data.get("image_number", cls._image_counter)
        item.set_show_caption(data.get("show_caption", True))
        item._update_caption_position()
        return item


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
            "size": self._size, "color": self._color.name()
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        item = cls(icon_type=data.get("icon_type", "warning"), size=data.get("size", 32))
        item.setPos(data.get("x", 0), data.get("y", 0))
        if "color" in data: 
            item.set_color(data["color"])
        return item


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
            "border_width": self._border_width, "dashed": self._dashed
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
        return item


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
            "color": self._color.name(), "line_width": self._line_width
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
        return item


class DraggableNode(SmartGraphicItemMixin, QGraphicsEllipseItem):
    def __init__(self, x, y, r):
        super().__init__(-r, -r, r * 2, r * 2)
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        self.setPen(QPen(QColor("#0ea5e9"), 2, Qt.DashLine))
        self.setZValue(5)
        self.setAcceptHoverEvents(True)
        self._is_resizing = False

    def _is_on_edge(self, pos): 
        return abs(math.hypot(pos.x(), pos.y()) - self.rect().width() / 2) < 8

    def hoverMoveEvent(self, event):
        if self._is_on_edge(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.OpenHandCursor if not self.isSelected() else Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_on_edge(event.pos()): 
            self._is_resizing = True
            event.accept()
        else: 
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_is_resizing', False):
            r = max(10, min(800, math.hypot(event.pos().x(), event.pos().y())))
            self.prepareGeometryChange()
            self.setRect(-r, -r, r * 2, r * 2)
            self.update()
            if self.scene(): 
                self.scene().update()
            event.accept()
        else: 
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_is_resizing', False): 
            self._is_resizing = False
            event.accept()
        else: 
            super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        if getattr(self, '_is_rendering', False): 
            return
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            painter.setPen(QPen(QColor("#0ea5e9"), 2))
            painter.setBrush(QColor("#ffffff"))
            r = self.rect().width() / 2
            for pt in[QPointF(r, 0), QPointF(0, r), QPointF(-r, 0), QPointF(0, -r)]: 
                painter.drawEllipse(pt, 5, 5)
            painter.restore()


class LensItem(SmartGraphicItemMixin, QGraphicsEllipseItem):
    def __init__(self, source_circle, x, y, r, zoom_factor=2.0, cone_item=None):
        super().__init__(-r, -r, r * 2, r * 2)
        self.setPos(x, y)
        self.source = source_circle
        self.zoom_factor = zoom_factor
        self._cone = cone_item
        self.setZValue(10)
        self.setPen(QPen(QColor("#f43f5e"), 3))
        self.setAcceptHoverEvents(True)
        self._is_resizing = False

    def set_cone(self, cone_item): 
        self._cone = cone_item

    def _is_on_edge(self, pos): 
        return abs(math.hypot(pos.x(), pos.y()) - self.rect().width() / 2) < 8

    def hoverMoveEvent(self, event):
        if self._is_on_edge(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.OpenHandCursor if not self.isSelected() else Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_on_edge(event.pos()): 
            self._is_resizing = True
            event.accept()
        else: 
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_is_resizing', False):
            r = max(20, min(800, math.hypot(event.pos().x(), event.pos().y())))
            self.prepareGeometryChange()
            self.setRect(-r, -r, r * 2, r * 2)
            self.update()
            if self.scene(): 
                self.scene().update()
            event.accept()
        else: 
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_is_resizing', False): 
            self._is_resizing = False
            event.accept()
        else: 
            super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        if getattr(self, '_is_rendering', False): 
            return
        painter.save() 
        path = QPainterPath()
        path.addEllipse(self.rect())
        painter.setClipPath(path)
        if self.scene() and self.source:
            target_rect = QRectF(-self.rect().width() / 2, -self.rect().height() / 2, self.rect().width(), self.rect().height())
            cw = self.rect().width() / self.zoom_factor
            ch = self.rect().height() / self.zoom_factor
            sp = self.source.scenePos()
            source_rect = QRectF(sp.x() - cw / 2, sp.y() - ch / 2, cw, ch)
            
            self._is_rendering = True
            if self.source: 
                self.source._is_rendering = True
            if getattr(self, '_cone', None): 
                self._cone._is_rendering = True
                
            self.scene().render(painter, target_rect, source_rect)
            
            self._is_rendering = False
            if self.source: 
                self.source._is_rendering = False
            if getattr(self, '_cone', None): 
                self._cone._is_rendering = False
        painter.restore()
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            painter.setPen(QPen(QColor("#f43f5e"), 2))
            painter.setBrush(QColor("#ffffff"))
            r = self.rect().width() / 2
            for pt in[QPointF(r, 0), QPointF(0, r), QPointF(-r, 0), QPointF(0, -r)]: 
                painter.drawEllipse(pt, 5, 5)
            painter.restore()

    def to_dict(self) -> dict: 
        return {
            "type": "lens", "x": self.scenePos().x(), "y": self.scenePos().y(), 
            "radius": self.rect().width() / 2, "zoom_factor": self.zoom_factor
        }


class MagnifierConeItem(QGraphicsItem):
    def __init__(self, source_circle, lens_circle):
        super().__init__()
        self.source = source_circle
        self.lens = lens_circle
        self.setZValue(-1)
        self.cone_color = QColor(244, 63, 94, 15) 
        self.line_color = QColor(244, 63, 94, 120)

    def boundingRect(self): 
        return self.source.sceneBoundingRect().united(self.lens.sceneBoundingRect())

    def paint(self, painter, option, widget):
        if getattr(self, '_is_rendering', False): 
            return

        cx1, cy1 = self.source.scenePos().x(), self.source.scenePos().y()
        r1 = self.source.rect().width() / 2
        cx2, cy2 = self.lens.scenePos().x(), self.lens.scenePos().y()
        r2 = self.lens.rect().width() / 2

        d = math.hypot(cx2 - cx1, cy2 - cy1)
        if d <= abs(r1 - r2) or d == 0: 
            return

        cos_a = max(-1, min(1, (r1 - r2) / d))
        theta = math.acos(cos_a)
        gamma = math.atan2(cy2 - cy1, cx2 - cx1)

        a1, a2 = gamma + theta, gamma - theta
        p1x, p1y = cx1 + r1 * math.cos(a1), cy1 + r1 * math.sin(a1)
        p2x, p2y = cx1 + r1 * math.cos(a2), cy1 + r1 * math.sin(a2)
        p3x, p3y = cx2 + r2 * math.cos(a1), cy2 + r2 * math.sin(a1)
        p4x, p4y = cx2 + r2 * math.cos(a2), cy2 + r2 * math.sin(a2)

        clip_path = QPainterPath()
        clip_path.addRect(self.scene().sceneRect())
        source_path = QPainterPath()
        source_path.addEllipse(QPointF(cx1, cy1), r1, r1)
        clip_path = clip_path.subtracted(source_path)
        painter.setClipPath(clip_path)

        cone_path = QPainterPath()
        cone_path.moveTo(p1x, p1y)
        cone_path.lineTo(p3x, p3y)
        cone_path.lineTo(p4x, p4y)
        cone_path.lineTo(p2x, p2y)
        cone_path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.cone_color))
        painter.drawPath(cone_path)
        pen = QPen(self.line_color, 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(p1x, p1y), QPointF(p3x, p3y))
        painter.drawLine(QPointF(p2x, p2y), QPointF(p4x, p4y))


# =============================================================================
# 第 4 部分：核心场景与视图 (多页连排)
# =============================================================================

class SOPCanvasScene(QGraphicsScene):
    A4_WIDTH, A4_HEIGHT = 794, 1123
    SAFE_MARGIN = 50
    PAGE_SPACING = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self._show_grid = True
        self._show_safe_margin = True
        self._grid_size = 20
        self._snap_threshold = 6.0
        self.snap_lines =[]
        self.num_pages = 1
        self.setBackgroundBrush(QBrush(QColor("#cbd5e1"))) 
        self._update_scene_rect()

    def _update_scene_rect(self):
        self.setSceneRect(0, 0, self.A4_WIDTH, self.num_pages * self.A4_HEIGHT + (self.num_pages - 1) * self.PAGE_SPACING)
        self.update()

    def add_page(self): 
        self.num_pages += 1
        self._update_scene_rect()

    def set_num_pages(self, num): 
        self.num_pages = max(1, num)
        self._update_scene_rect()

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        for i in range(self.num_pages):
            page_rect = QRectF(0, i * (self.A4_HEIGHT + self.PAGE_SPACING), self.A4_WIDTH, self.A4_HEIGHT)
            if not rect.intersects(page_rect): 
                continue
            painter.fillRect(page_rect.translated(8, 8), QColor(0, 0, 0, 15))
            painter.fillRect(page_rect, Qt.white)
            if self._show_grid:
                pen = QPen(QColor("#f1f5f9"), 1)
                painter.setPen(pen)
                for x in range(int(page_rect.left()), int(page_rect.right()), self._grid_size): 
                    painter.drawLine(x, int(page_rect.top()), x, int(page_rect.bottom()))
                for y in range(int(page_rect.top()), int(page_rect.bottom()), self._grid_size): 
                    painter.drawLine(int(page_rect.left()), y, int(page_rect.right()), y)

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if self._show_safe_margin:
            pen = QPen(QColor("#f43f5e"), 1, Qt.DashLine)
            painter.setPen(pen)
            for i in range(self.num_pages):
                m_rect = QRectF(self.SAFE_MARGIN, i * (self.A4_HEIGHT + self.PAGE_SPACING) + self.SAFE_MARGIN, self.A4_WIDTH - 2*self.SAFE_MARGIN, self.A4_HEIGHT - 2*self.SAFE_MARGIN)
                if rect.intersects(m_rect): 
                    painter.drawRect(m_rect)
        if self.snap_lines:
            pen = QPen(QColor("#0ea5e9"), 1, Qt.DashLine)
            painter.setPen(pen)
            for line in self.snap_lines: 
                painter.drawLine(line)

    def set_show_grid(self, show: bool): 
        self._show_grid = show
        self.update()

    def set_show_safe_margin(self, show: bool): 
        self._show_safe_margin = show
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.snap_lines: 
            self.snap_lines.clear()
            self.update()

    def calculate_snap(self, item, new_pos):
        threshold = self._snap_threshold
        item_center = new_pos + item.boundingRect().center()
        best_x, best_y = new_pos.x(), new_pos.y()
        
        snap_lines_x =[0, self.A4_WIDTH / 2, self.A4_WIDTH]
        snap_lines_y =[]
        for i in range(self.num_pages):
            py = i * (self.A4_HEIGHT + self.PAGE_SPACING)
            snap_lines_y.extend([py, py + self.A4_HEIGHT / 2, py + self.A4_HEIGHT])

        for other in self.items():
            if other == item or not isinstance(other, QGraphicsItem) or not other.isVisible() or isinstance(other, MagnifierConeItem): 
                continue
            orect = other.sceneBoundingRect()
            snap_lines_x.extend([orect.left(), orect.center().x(), orect.right()])
            snap_lines_y.extend([orect.top(), orect.center().y(), orect.bottom()])

        self.snap_lines.clear()
        
        for ref_x in snap_lines_x:
            for anchor_x in[item_center.x(), new_pos.x(), new_pos.x() + item.boundingRect().width()]:
                if abs(ref_x - anchor_x) < threshold:
                    best_x = new_pos.x() + (ref_x - anchor_x)
                    self.snap_lines.append(QLineF(ref_x, 0, ref_x, self.sceneRect().height()))
                    break
            if self.snap_lines: 
                break

        for ref_y in snap_lines_y:
            for anchor_y in[item_center.y(), new_pos.y(), new_pos.y() + item.boundingRect().height()]:
                if abs(ref_y - anchor_y) < threshold:
                    best_y = new_pos.y() + (ref_y - anchor_y)
                    self.snap_lines.append(QLineF(0, ref_y, self.A4_WIDTH, ref_y))
                    break
            if len(self.snap_lines) > (1 if best_x != new_pos.x() else 0): 
                break

        return QPointF(best_x, best_y)


# =============================================================================
# 第 5 部分：UI 面板 (带 QSettings 持久化)
# =============================================================================

class DraggableComponentButton(QPushButton):
    def __init__(self, text, icon_text, component_type, border_color, parent=None):
        super().__init__(text, parent)
        self._component_type = component_type
        self._icon_text = icon_text
        self.setFixedHeight(48)
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start_pos = None
        self.setStyleSheet(f"""
            QPushButton {{ text-align: left; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff; font-size: 13px; font-weight: bold; color: #334155; border-left: 4px solid {border_color}; }}
            QPushButton:hover {{ background-color: #f8fafc; border-color: {border_color}; }}
            QPushButton:pressed {{ background-color: #e2e8f0; }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: 
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._drag_start_pos: 
            return super().mouseMoveEvent(event)
        if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance(): 
            return super().mouseMoveEvent(event)
        self.setDown(False)
        self.setCursor(Qt.ClosedHandCursor)
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self._component_type)
        drag.setMimeData(mime)
        preview = QLabel(self._icon_text + " " + self.text())
        preview.setStyleSheet("background-color: #0ea5e9; color: white; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: bold;")
        drag.setPixmap(preview.grab())
        drag.setHotSpot(QPoint(drag.pixmap().width() // 2, drag.pixmap().height() // 2))
        drag.exec(Qt.CopyAction)
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start_pos = None
        super().mouseMoveEvent(event)


class ComponentPanel(QWidget):
    componentSelected = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        title = QLabel("🧩 工具箱")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setStyleSheet("color: #0f172a; padding: 4px 0;")
        layout.addWidget(title)
        hint = QLabel("点击或拖拽组件到画布")
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(8)

        tg = self._make_group("📝 文本")
        self._add_btn(tg, "大标题", "H", "title", "#8b5cf6")
        self._add_btn(tg, "正文", "T", "body", "#8b5cf6")
        self._add_btn(tg, "注脚", "C", "caption", "#8b5cf6")
        scroll_layout.addWidget(tg)
        
        mg = self._make_group("🎯 标注")
        self._add_btn(mg, "框选", "□", "highlight", "#22c55e")
        self._add_btn(mg, "箭头", "→", "arrow", "#22c55e")
        scroll_layout.addWidget(mg)
        
        vg = self._make_group("🖼 视觉")
        self._add_btn(vg, "图片", "🖼", "image", "#eab308")
        self._add_btn(vg, "图标", "🔣", "icon", "#eab308")
        self._add_btn(vg, "局部放大", "🔍", "magnifier", "#eab308")
        scroll_layout.addWidget(vg)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _make_group(self, title_text):
        group = QGroupBox(title_text)
        group.setLayout(QVBoxLayout())
        group.layout().setSpacing(6)
        group.layout().setContentsMargins(8, 20, 8, 8)
        return group
        
    def _add_btn(self, group, text, icon, ctype, color):
        btn = DraggableComponentButton(text, icon, ctype, color)
        btn.clicked.connect(lambda: self.componentSelected.emit(ctype))
        group.layout().addWidget(btn)


class PropertyPanel(QWidget):
    propertyChanged = Signal(str, object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self._current_item = None
        self._setup_ui()

    def _setup_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 12, 12, 12)
        self._main_layout.setSpacing(12)
        self._title = QLabel("📐 属性面板")
        self._title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self._title.setStyleSheet("color: #0f172a; padding: 4px 0;")
        self._main_layout.addWidget(self._title)
        self._hint = QLabel("请选中画布上的组件")
        self._hint.setStyleSheet("color: #64748b; font-size: 12px; padding: 40px 0;")
        self._hint.setAlignment(Qt.AlignCenter)
        self._main_layout.addWidget(self._hint)
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._content_widget.hide()
        self._main_layout.addWidget(self._content_widget)
        self._main_layout.addStretch()

    def set_current_item(self, item):
        self._current_item = item
        self._clear_content()
        if item is None: 
            self._hint.show()
            self._content_widget.hide()
            return
        self._hint.hide()
        self._content_widget.show()

        if isinstance(item, SOPTextItem): 
            self._build_text_properties(item)
        elif isinstance(item, HighlightItem): 
            self._build_highlight_properties(item)
        elif isinstance(item, ArrowItem): 
            self._build_arrow_properties(item)
        elif isinstance(item, ImageItem): 
            self._build_image_properties(item)
        elif isinstance(item, IconItem): 
            self._build_icon_properties(item)
        elif isinstance(item, LensItem): 
            self._build_magnifier_properties(item)
        else: 
            self._build_generic_properties(item)

    def _clear_content(self):
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget(): 
                child.widget().deleteLater()

    def _add_property_group(self, title_text):
        group = QGroupBox(title_text)
        form = QFormLayout(group)
        form.setSpacing(8)
        form.setContentsMargins(8, 20, 8, 8)
        self._content_layout.addWidget(group)
        return form

    def _add_combo_row(self, form, label, items, current, prop_name):
        combo = QComboBox()
        combo.addItems(items)
        if current in items: 
            combo.setCurrentText(current)
        combo.currentTextChanged.connect(lambda v: self.propertyChanged.emit(prop_name, v))
        form.addRow(label, combo)
        return combo

    def _add_spin_row(self, form, label, value, min_v, max_v, prop_name):
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(int(value))
        spin.valueChanged.connect(lambda v: self.propertyChanged.emit(prop_name, v))
        form.addRow(label, spin)
        return spin

    def _add_color_row(self, form, label, current_color, prop_name):
        color_btn = QPushButton()
        color_btn.setFixedSize(28, 28)
        color_btn.setStyleSheet(f"QPushButton {{ background-color: {current_color}; border: 2px solid #cbd5e1; border-radius: 6px; }}")
        color_btn.clicked.connect(lambda: self._pick_color(color_btn, prop_name))
        form.addRow(label, color_btn)
        return color_btn

    def _add_check_row(self, form, label, checked, prop_name):
        check = QCheckBox()
        check.setChecked(checked)
        check.stateChanged.connect(lambda v: self.propertyChanged.emit(prop_name, bool(v)))
        form.addRow(label, check)
        return check

    def _pick_color(self, btn, prop_name):
        color = QColorDialog.getColor()
        if color.isValid():
            btn.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; border: 2px solid #cbd5e1; border-radius: 6px; }}")
            self.propertyChanged.emit(prop_name, color.name())

    def _build_text_properties(self, item):
        form = self._add_property_group("文本属性")
        self._add_combo_row(form, "层级", ["大标题", "正文", "注脚"], {"title": "大标题", "body": "正文", "caption": "注脚"}.get(item.get_level(), "正文"), "level")
        self._add_combo_row(form, "对齐",["左对齐", "居中", "右对齐"], "左对齐", "alignment")
        self._add_color_row(form, "文字颜色", item.defaultTextColor().name(), "text_color")

    def _build_highlight_properties(self, item):
        form = self._add_property_group("框选属性")
        self._add_combo_row(form, "颜色", list(HighlightItem.HIGHLIGHT_COLORS.keys()), self._find_key_by_value(HighlightItem.HIGHLIGHT_COLORS, item._border_color.name()), "color")
        self._add_spin_row(form, "线宽", item._border_width, 1, 10, "border_width")
        self._add_check_row(form, "虚线", item._dashed, "dashed")

    def _build_arrow_properties(self, item):
        form = self._add_property_group("箭头属性")
        self._add_spin_row(form, "角度(°)", item._angle, 0, 360, "angle")
        self._add_combo_row(form, "颜色", list(ArrowItem.ARROW_COLORS.keys()), self._find_key_by_value(ArrowItem.ARROW_COLORS, item._color.name()), "arrow_color")
        self._add_spin_row(form, "线宽", item._line_width, 1, 8, "line_width")
        self._add_spin_row(form, "长度", item._length, 20, 800, "length")

    def _build_image_properties(self, item):
        form = self._add_property_group("图片属性")
        self._add_spin_row(form, "宽度", item._image_width, 50, 800, "image_width")
        self._add_spin_row(form, "高度", item._image_height, 50, 800, "image_height")
        self._add_check_row(form, "显示注脚", getattr(item, "_show_caption", True), "show_caption")
        caption_line = QLineEdit(item.get_caption())
        caption_line.textChanged.connect(lambda v: self.propertyChanged.emit("caption", v))
        form.addRow("注脚", caption_line)

    def _build_icon_properties(self, item):
        form = self._add_property_group("图标属性")
        self._add_combo_row(form, "类型",["警告", "提示", "工具", "检查", "错误", "右箭头", "下箭头", "星标"], {"warning": "警告", "info": "提示", "tool": "工具", "check": "检查", "error": "错误", "arrow_right": "右箭头", "arrow_down": "下箭头", "star": "星标"}.get(item._icon_type, "警告"), "icon_type")
        self._add_combo_row(form, "颜色", list(IconItem.STANDARD_COLORS.keys()), self._find_key_by_value(IconItem.STANDARD_COLORS, item._color.name()), "icon_color")
        self._add_spin_row(form, "大小", item._size, 16, 64, "icon_size")

    def _build_magnifier_properties(self, item):
        form = self._add_property_group("放大镜属性")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(11, 40)
        slider.setValue(int(item.zoom_factor * 10))
        slider.valueChanged.connect(lambda v: self.propertyChanged.emit("zoom", v / 10.0))
        form.addRow("放大倍率", slider)
        zoom_label = QLabel(f"{item.zoom_factor:.1f}x")
        zoom_label.setStyleSheet("color: #64748b; font-size: 11px;")
        form.addRow("", zoom_label)
        slider.valueChanged.connect(lambda v: zoom_label.setText(f"{v / 10.0:.1f}x"))

    def _build_generic_properties(self, item):
        form = self._add_property_group("通用属性")
        pos = item.scenePos() if item.scene() else item.pos()
        self._add_spin_row(form, "X", int(pos.x()), -5000, 5000, "x")
        self._add_spin_row(form, "Y", int(pos.y()), -5000, 5000, "y")

    @staticmethod
    def _find_key_by_value(d, value):
        for k, v in d.items():
            if v == value: 
                return k
        return list(d.keys())[0]


class EmojiPanel(QWidget):
    emojiDictChanged = Signal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.settings = QSettings("SOPForge", "SOPDesigner")
        saved_dict = self.settings.value("emoji_dict")
        if saved_dict:
            try: 
                self._emoji_dict = json.loads(saved_dict)
            except: 
                self._emoji_dict = self._get_default_dict()
        else:
            self._emoji_dict = self._get_default_dict()
        self.setup_ui()

    def _get_default_dict(self):
        return { "警告": "⚠️", "注意": "💡", "检查": "✅", "危险": "🚫", "提示": "💡", "重要": "❗", "完成": "✅", "待办": "📝" }
        
    def _save_dict(self):
        self.settings.setValue("emoji_dict", json.dumps(self._emoji_dict))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        title = QLabel("😀 Emoji 词典")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setStyleSheet("color: #0f172a; padding: 4px 0;")
        layout.addWidget(title)
        hint = QLabel("配置映射后，打字时自动补全")
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        add_group = QGroupBox("添加映射")
        add_layout = QVBoxLayout(add_group)
        add_layout.setSpacing(8)
        add_layout.setContentsMargins(8, 20, 8, 8)
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("关键词...")
        add_layout.addWidget(self._keyword_input)
        self._emoji_input = QLineEdit()
        self._emoji_input.setPlaceholderText("Emoji...")
        add_layout.addWidget(self._emoji_input)
        add_btn = QPushButton("➕ 添 加")
        add_btn.setStyleSheet("QPushButton { background-color: #0ea5e9; color: white; border: none; border-radius: 6px; padding: 8px; font-size: 13px; font-weight:bold; } QPushButton:hover { background-color: #0284c7; }")
        add_btn.clicked.connect(self._add_entry)
        add_layout.addWidget(add_btn)
        layout.addWidget(add_group)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["关键词", "Emoji", "操作"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().hide()
        self._table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self._table.cellChanged.connect(self._on_cell_changed)
        self._refresh_table()
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("🔄 恢复默认")
        reset_btn.setStyleSheet("QPushButton { background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; font-size: 12px; } QPushButton:hover { background-color: #e2e8f0; }")
        reset_btn.clicked.connect(self._reset_default)
        btn_layout.addWidget(reset_btn)
        apply_btn = QPushButton("✅ 应用词典")
        apply_btn.setStyleSheet("QPushButton { background-color: #22c55e; color: white; border: none; border-radius: 6px; padding: 8px; font-size: 12px; font-weight:bold; } QPushButton:hover { background-color: #16a34a; }")
        apply_btn.clicked.connect(self._apply_dict)
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)

    def _refresh_table(self):
        try: 
            self._table.cellChanged.disconnect(self._on_cell_changed)
        except: 
            pass
        self._table.setRowCount(len(self._emoji_dict))
        for i, (keyword, emoji) in enumerate(self._emoji_dict.items()):
            kw_item = QTableWidgetItem(keyword)
            kw_item.setFlags(kw_item.flags() | Qt.ItemIsEditable)
            self._table.setItem(i, 0, kw_item)
            emoji_item = QTableWidgetItem(emoji)
            emoji_item.setFlags(emoji_item.flags() | Qt.ItemIsEditable)
            self._table.setItem(i, 1, emoji_item)
            delete_btn = QPushButton("🗑")
            delete_btn.setFixedSize(28, 24)
            delete_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 14px; color:#1e293b; } QPushButton:hover { background-color: #ffe4e6; border-radius: 4px; }")
            delete_btn.clicked.connect(lambda checked, k=keyword: self._delete_entry(k))
            self._table.setCellWidget(i, 2, delete_btn)
        self._table.cellChanged.connect(self._on_cell_changed)

    def _on_cell_changed(self, row, column):
        if column >= 2: 
            return
        kw_item = self._table.item(row, 0)
        emoji_item = self._table.item(row, 1)
        if kw_item is None or emoji_item is None: 
            return
        new_keyword = kw_item.text().strip()
        new_emoji = emoji_item.text().strip()
        if not new_keyword or not new_emoji: 
            return
        old_keywords = list(self._emoji_dict.keys())
        if row < len(old_keywords):
            old_keyword = old_keywords[row]
            if old_keyword != new_keyword or self._emoji_dict[old_keyword] != new_emoji:
                del self._emoji_dict[old_keyword]
                self._emoji_dict[new_keyword] = new_emoji
                self._save_dict()
                self._refresh_table()

    def _add_entry(self):
        keyword = self._keyword_input.text().strip()
        emoji = self._emoji_input.text().strip()
        if not keyword or not emoji: 
            return
        self._emoji_dict[keyword] = emoji
        self._keyword_input.clear()
        self._emoji_input.clear()
        self._save_dict()
        self._refresh_table()

    def _delete_entry(self, keyword):
        if keyword in self._emoji_dict: 
            del self._emoji_dict[keyword]
            self._save_dict()
            self._refresh_table()

    def _reset_default(self):
        self._emoji_dict = self._get_default_dict()
        self._save_dict()
        self._refresh_table()

    def _apply_dict(self): 
        self.emojiDictChanged.emit(self._emoji_dict.copy())


# =============================================================================
# 第 6 部分：序列化与导出逻辑 (多页面)
# =============================================================================

def export_to_json(scene, filepath):
    data = {"num_pages": getattr(scene, 'num_pages', 1), "items":[]}
    for item in scene.items():
        if hasattr(item, "to_dict"):
            try: 
                data["items"].append(item.to_dict())
            except: 
                pass
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def import_from_json(scene, filepath):
    with open(filepath, "r", encoding="utf-8") as f: 
        data = json.load(f)
    scene.clear()
    
    if hasattr(scene, 'set_num_pages'):
        scene.set_num_pages(data.get("num_pages", 1))
        
    TYPE_MAP = { "text": SOPTextItem, "image": ImageItem, "icon": IconItem, "highlight": HighlightItem, "arrow": ArrowItem }
    lens_data_list =[]
    for item_data in data.get("items",[]):
        item_type = item_data.get("type", "")
        if item_type in TYPE_MAP: 
            scene.addItem(TYPE_MAP[item_type].from_dict(item_data, scene))
        elif item_type in ["source", "lens"]: 
            lens_data_list.append(item_data)
    
    source_item = None
    lens_item = None
    for item_data in lens_data_list:
        if item_data.get("type") == "source":
            source_item = DraggableNode(item_data.get("x", 300), item_data.get("y", 300), item_data.get("radius", 30))
            scene.addItem(source_item)
        elif item_data.get("type") == "lens" and source_item:
            lens_item = LensItem(source_item, item_data.get("x", 450), item_data.get("y", 250), item_data.get("radius", 50), item_data.get("zoom_factor", 2.0))
            scene.addItem(lens_item)
    if source_item and lens_item:
        cone = MagnifierConeItem(source_item, lens_item)
        scene.addItem(cone)
        lens_item.set_cone(cone)

def export_to_pdf(scene, filepath):
    show_grid_was = getattr(scene, "_show_grid", True)
    show_margin_was = getattr(scene, "_show_safe_margin", True)
    if hasattr(scene, "set_show_grid"): 
        scene.set_show_grid(False)
    if hasattr(scene, "set_show_safe_margin"): 
        scene.set_show_safe_margin(False)
    scene.clearSelection()

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(filepath)
    printer.setPageSize(QPageSize.A4)
    printer.setResolution(300)
    
    painter = QPainter()
    painter.begin(printer)
    
    pr = printer.pageRect(QPrinter.DevicePixel)
    scale = min(pr.width() / scene.A4_WIDTH, pr.height() / scene.A4_HEIGHT)
    
    num_pages = getattr(scene, 'num_pages', 1)
    for i in range(num_pages):
        if i > 0: 
            printer.newPage()
        page_y = i * (scene.A4_HEIGHT + getattr(scene, 'PAGE_SPACING', 0))
        page_rect_scene = QRectF(0, page_y, scene.A4_WIDTH, scene.A4_HEIGHT)
        
        painter.save()
        painter.scale(scale, scale)
        painter.translate(0, -page_y) 
        scene.render(painter, QRectF(0, page_y, scene.A4_WIDTH, scene.A4_HEIGHT), page_rect_scene)
        painter.restore()
        
    painter.end()

    if hasattr(scene, "set_show_grid"): 
        scene.set_show_grid(show_grid_was)
    if hasattr(scene, "set_show_safe_margin"): 
        scene.set_show_safe_margin(show_margin_was)


# =============================================================================
# 第 7 部分：主窗口与程序入口
# =============================================================================

class SOPCanvasView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QGraphicsView { border: none; background-color: #cbd5e1; }")
        self.setAcceptDrops(True)
        
        self._zoom = 1.0
        self._min_zoom = 0.3
        self._max_zoom = 5.0
        self._is_panning = False
        self._pan_start = None

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87
        new_zoom = self._zoom * factor
        if self._min_zoom <= new_zoom <= self._max_zoom:
            self._zoom = new_zoom
            self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning and self._pan_start:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self._pan_start = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None: 
            return
        self.scene().clearSelection()
        item.setSelected(True)
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: white; border: 1px solid #e2e8f0; border-radius: 6px; } QMenu::item { padding: 6px 24px; color: #1e293b; } QMenu::item:selected { background-color: #f1f5f9; color: #0ea5e9; }")
        
        action_top = menu.addAction("⬆ 置于顶层")
        action_top.triggered.connect(lambda: item.setZValue(max([i.zValue() for i in self.scene().items()]) + 1))
        
        action_bottom = menu.addAction("⬇ 置于底层")
        action_bottom.triggered.connect(lambda: item.setZValue(min([i.zValue() for i in self.scene().items()]) - 1))
        
        menu.addSeparator()
        if not (item.flags() & QGraphicsItem.ItemIsMovable):
            action_unlock = menu.addAction("🔓 解锁位置")
            action_unlock.triggered.connect(lambda:[item.setFlag(QGraphicsItem.ItemIsMovable, True), item.setFlag(QGraphicsItem.ItemIsSelectable, True)])
        else:
            action_lock = menu.addAction("🔒 锁定位置")
            action_lock.triggered.connect(lambda:[item.setFlag(QGraphicsItem.ItemIsMovable, False), item.setFlag(QGraphicsItem.ItemIsSelectable, True)])
            
        menu.addSeparator()
        action_delete = menu.addAction("🗑 删除")
        action_delete.triggered.connect(lambda: self.window()._on_delete())
        
        menu.exec(event.globalPos())

    def zoom_in(self): 
        self.wheelEvent(self._make_wheel_event(120))

    def zoom_out(self): 
        self.wheelEvent(self._make_wheel_event(-120))

    def zoom_fit(self): 
        self._zoom = 1.0
        self.resetTransform()
        self.centerOn(self.sceneRect().center())

    def _make_wheel_event(self, delta):
        pos = self.viewport().mapFromGlobal(QCursor.pos())
        return QWheelEvent(pos, self.mapToScene(pos), QPoint(delta, 0), QPoint(0, 0), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasText() or mime.hasUrls() or mime.hasImage(): 
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        mime = event.mimeData()
        if mime.hasText() or mime.hasUrls() or mime.hasImage(): 
            event.acceptProposedAction()

    def dropEvent(self, event):
        scene_pos = self.mapToScene(event.position().toPoint())
        main_window = self.window()
        mime = event.mimeData()

        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    if hasattr(main_window, "_add_image_from_file"): 
                        main_window._add_image_from_file(url.toLocalFile(), scene_pos)
            event.acceptProposedAction()
            return
            
        if mime.hasImage():
            if hasattr(main_window, "_add_image_from_pixmap"): 
                main_window._add_image_from_pixmap(QPixmap.fromImage(mime.imageData()), scene_pos)
            event.acceptProposedAction()
            return
            
        if mime.hasText():
            if hasattr(main_window, "_add_component_at"): 
                main_window._add_component_at(mime.text(), scene_pos)
            event.acceptProposedAction()

    def keyPressEvent(self, event):
        scene = self.scene()
        focus_item = scene.focusItem() if scene else None
        is_editing_text = isinstance(focus_item, QGraphicsTextItem) and focus_item.textInteractionFlags() == Qt.TextEditorInteraction

        if event.matches(QKeySequence.Paste):
            if is_editing_text: 
                return super().keyPressEvent(event)
            mime = QApplication.clipboard().mimeData()
            scene_pos = self.mapToScene(self.viewport().rect().center())
            if mime.hasImage():
                self.window()._add_image_from_pixmap(QPixmap.fromImage(mime.imageData()), scene_pos)
                event.accept()
                return
            elif mime.hasUrls():
                for url in mime.urls():
                    if url.isLocalFile() and url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        self.window()._add_image_from_file(url.toLocalFile(), scene_pos)
                event.accept()
                return
                
        elif event.matches(QKeySequence.Delete) or event.key() == Qt.Key_Backspace:
            if is_editing_text: 
                return super().keyPressEvent(event)
            self.window()._on_delete()
            event.accept()
            return
            
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOP Forge - 专业排版引擎")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self._current_file = None
        self.setup_scene()
        self.setup_view()
        self.setup_panels()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_connections()
        self.setStyleSheet(GLOBAL_QSS)

    def setup_scene(self): 
        self.scene = SOPCanvasScene(self)
        
    def setup_view(self): 
        self.view = SOPCanvasView(self.scene, self)

    def setup_panels(self):
        self.component_panel = ComponentPanel(self)
        self.property_panel = PropertyPanel(self)
        self.emoji_panel = EmojiPanel(self)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.property_panel)
        right_layout.addWidget(self.emoji_panel)
        right_panel.setLayout(right_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.component_panel)
        splitter.addWidget(self.view)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 800, 260])
        splitter.setHandleWidth(2)
        self.setCentralWidget(splitter)

    def setup_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("文件(&F)")
        
        action_new = fm.addAction("新建(&N)")
        action_new.setShortcut(QKeySequence.New)
        action_new.triggered.connect(self._on_new)
        
        action_open = fm.addAction("打开(&O)...")
        action_open.setShortcut(QKeySequence.Open)
        action_open.triggered.connect(self._on_open)
        
        action_save = fm.addAction("保存(&S)")
        action_save.setShortcut(QKeySequence.Save)
        action_save.triggered.connect(self._on_save)
        
        action_save_as = fm.addAction("另存为(&A)...")
        action_save_as.setShortcut(QKeySequence.SaveAs)
        action_save_as.triggered.connect(self._on_save_as)
        
        fm.addSeparator()
        action_export = fm.addAction("导出 PDF(&P)...")
        action_export.setShortcut(QKeySequence.Print)
        action_export.triggered.connect(self._on_export_pdf)
        
        em = mb.addMenu("编辑(&E)")
        action_delete = em.addAction("删除(&D)")
        action_delete.setShortcut(QKeySequence.Delete)
        action_delete.triggered.connect(self._on_delete)
        
        action_selall = em.addAction("全选(&A)")
        action_selall.setShortcut(QKeySequence.SelectAll)
        action_selall.triggered.connect(self._on_select_all)
        
        vm = mb.addMenu("视图(&V)")
        a1 = vm.addAction("显示/隐藏网格")
        a1.setCheckable(True)
        a1.setChecked(True)
        a1.triggered.connect(self.scene.set_show_grid)
        
        a2 = vm.addAction("显示/隐藏安全边距")
        a2.setCheckable(True)
        a2.setChecked(True)
        a2.triggered.connect(self.scene.set_show_safe_margin)
        
        vm.addSeparator()
        action_zi = vm.addAction("放大")
        action_zi.setShortcut(QKeySequence.ZoomIn)
        action_zi.triggered.connect(self.view.zoom_in)
        
        action_zo = vm.addAction("缩小")
        action_zo.setShortcut(QKeySequence.ZoomOut)
        action_zo.triggered.connect(self.view.zoom_out)
        
        action_zf = vm.addAction("适应窗口")
        action_zf.setShortcut(QKeySequence("Ctrl+0"))
        action_zf.triggered.connect(self.view.zoom_fit)

    def setup_toolbar(self):
        tb = QToolBar("主工具栏")
        self.addToolBar(tb)
        tb.addWidget(self._make_tool_btn("H 大标题", lambda: self._add_component_at("title")))
        tb.addWidget(self._make_tool_btn("T 正文", lambda: self._add_component_at("body")))
        tb.addWidget(self._make_tool_btn("C 注脚", lambda: self._add_component_at("caption")))
        tb.addSeparator()
        tb.addWidget(self._make_tool_btn("□ 框选", lambda: self._add_component_at("highlight")))
        tb.addWidget(self._make_tool_btn("→ 箭头", lambda: self._add_component_at("arrow")))
        tb.addSeparator()
        tb.addWidget(self._make_tool_btn("🔍 放大", lambda: self._add_component_at("magnifier")))
        tb.addSeparator()
        btn_page = self._make_tool_btn("📄 ＋新页面", self._add_page)
        btn_page.setStyleSheet(btn_page.styleSheet().replace("color: #334155;", "color: #16a34a; font-weight: bold;"))
        tb.addWidget(btn_page)

    def _make_tool_btn(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("QPushButton { padding: 6px 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: white; font-size: 12px; color: #334155; } QPushButton:hover { background-color: #f0fdf4; border-color: #22c55e; color:#16a34a; }")
        btn.clicked.connect(callback)
        return btn

    def setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
        lbl = QLabel("SOP Forge 多巴胺版 v2.0")
        lbl.setStyleSheet("color: #64748b; padding: 0 8px; font-weight:bold;")
        self.statusbar.addPermanentWidget(lbl)

    def setup_connections(self):
        self.component_panel.componentSelected.connect(self._add_component_at)
        
        def on_selection_changed():
            items = self.scene.selectedItems()
            self.property_panel.set_current_item(items[0] if items else None)
            
        self.scene.selectionChanged.connect(on_selection_changed)
        self.property_panel.propertyChanged.connect(self._on_property_changed)
        
        def update_emoji(d):
            for i in self.scene.items():
                if hasattr(i, "set_emoji_dict"):
                    i.set_emoji_dict(d)
                    
        self.emoji_panel.emojiDictChanged.connect(update_emoji)

    def _on_property_changed(self, prop, value):
        selected = self.scene.selectedItems()
        if not selected: 
            return
        item = selected[0]
        if prop == "x": 
            item.setPos(value, item.pos().y())
        elif prop == "y": 
            item.setPos(item.pos().x(), value)
        elif prop == "level": 
            item.set_level({"大标题": "title", "正文": "body", "注脚": "caption"}.get(value, "body"))
        elif prop == "alignment":
            option = item.document().defaultTextOption()
            option.setAlignment({"左对齐": Qt.AlignLeft, "居中": Qt.AlignCenter, "右对齐": Qt.AlignRight}.get(value, Qt.AlignLeft))
            item.document().setDefaultTextOption(option)
            item.check_alignment()
        elif prop == "text_color": 
            item.setDefaultTextColor(QColor(value))
        elif prop == "color": 
            item.set_border_color(value)
        elif prop == "border_width": 
            item.set_border_width(value)
        elif prop == "dashed": 
            item.set_dashed(value)
        elif prop == "angle": 
            item.set_angle(value)
        elif prop == "arrow_color": 
            item.set_color(value)
        elif prop == "line_width": 
            item.set_line_width(value)
        elif prop == "length": 
            item.set_length(value)
        elif prop == "image_width": 
            item.prepareGeometryChange()
            item._image_width = value
            item._update_caption_position()
            item.update()
        elif prop == "image_height": 
            item.prepareGeometryChange()
            item._image_height = value
            item._update_caption_position()
            item.update()
        elif prop == "show_caption": 
            item.set_show_caption(value)
        elif prop == "caption": 
            item.set_caption(value)
        elif prop == "icon_type": 
            item.set_icon_type({"警告": "warning", "提示": "info", "工具": "tool", "检查": "check", "错误": "error", "右箭头": "arrow_right", "下箭头": "arrow_down", "星标": "star"}.get(value, "warning"))
        elif prop == "icon_color": 
            item.set_color_by_name(value)
        elif prop == "icon_size": 
            item.set_size(value)
        elif prop == "zoom": 
            item.zoom_factor = value
            item.update()

    def _on_new(self): 
        self.scene.clear()
        self.scene.set_num_pages(1)
        self._current_file = None
        self.statusbar.showMessage("新建文档")
        
    def _on_open(self):
        fp, _ = QFileDialog.getOpenFileName(self, "打开 SOP 文件", "", "SOP 文件 (*.sop.json);;JSON 文件 (*.json)")
        if fp: 
            import_from_json(self.scene, fp)
            self._current_file = fp
            self.statusbar.showMessage(f"已打开: {fp}")
        
    def _on_save(self): 
        if self._current_file:
            export_to_json(self.scene, self._current_file)
        else:
            self._on_save_as()
            
    def _on_save_as(self):
        fp, _ = QFileDialog.getSaveFileName(self, "保存 SOP 文件", "", "SOP 文件 (*.sop.json);;JSON 文件 (*.json)")
        if fp: 
            export_to_json(self.scene, fp)
            self._current_file = fp
            self.statusbar.showMessage(f"已保存: {fp}")
        
    def _on_export_pdf(self):
        fp, _ = QFileDialog.getSaveFileName(self, "导出 PDF", "", "PDF 文件 (*.pdf)")
        if fp: 
            export_to_pdf(self.scene, fp)
            self.statusbar.showMessage(f"PDF 已导出: {fp}")
        
    def _on_delete(self):
        items_to_delete = set(self.scene.selectedItems())
        for item in list(items_to_delete):
            if isinstance(item, DraggableNode):
                for other in self.scene.items():
                    if isinstance(other, LensItem) and getattr(other, 'source', None) == item:
                        items_to_delete.add(other)
                        if getattr(other, '_cone', None): 
                            items_to_delete.add(other._cone)
            elif isinstance(item, LensItem):
                if getattr(item, 'source', None): 
                    items_to_delete.add(item.source)
                if getattr(item, '_cone', None): 
                    items_to_delete.add(item._cone)
        for item in items_to_delete: 
            self.scene.removeItem(item)

    def _on_select_all(self):
        for i in self.scene.items():
            i.setSelected(True)

    def _add_page(self): 
        self.scene.add_page()
        self.statusbar.showMessage(f"已新增页面，当前共 {self.scene.num_pages} 页")

    def _add_image_from_file(self, filepath, pos=None):
        image = QImage(filepath)
        if image.isNull(): 
            QMessageBox.warning(self, "加载失败", f"无法识别或读取图片文件:\n{filepath}")
            return
        self._add_image_from_pixmap(QPixmap.fromImage(image), pos, os.path.basename(filepath))

    def _add_image_from_pixmap(self, pixmap, pos=None, caption="图片"):
        if pos is None: 
            pos = self.view.mapToScene(self.view.viewport().rect().center())
        item = ImageItem(pixmap=pixmap, caption_text=caption)
        item.setPos(pos.x(), pos.y())
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)
        self.statusbar.showMessage("已添加图片")

    def _add_component_at(self, component_type, scene_pos=None):
        if scene_pos is None: 
            scene_pos = self.view.mapToScene(self.view.viewport().rect().center())
            
        item = None
        if component_type in ["title", "body", "caption"]: 
            item = SOPTextItem(text={"title": "大标题", "body": "正文内容...", "caption": "注脚说明"}.get(component_type), level=component_type)
        elif component_type == "highlight": 
            item = HighlightItem(0, 0, 120, 80)
        elif component_type == "arrow": 
            item = ArrowItem(angle=45, length=120)
        elif component_type == "image":
            fp, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)")
            if fp: 
                self._add_image_from_file(fp, scene_pos)
            return
        elif component_type == "icon": 
            item = IconItem("warning", 32)
        elif component_type == "magnifier":
            source = DraggableNode(scene_pos.x(), scene_pos.y(), 30)
            self.scene.addItem(source)
            lens = LensItem(source, scene_pos.x() + 150, scene_pos.y() - 50, 50, zoom_factor=2.0)
            self.scene.addItem(lens)
            cone = MagnifierConeItem(source, lens)
            self.scene.addItem(cone)
            lens.set_cone(cone)
            source.setSelected(True)
            self.statusbar.showMessage("已添加局部放大")
            return
            
        if item:
            item.setPos(scene_pos.x(), scene_pos.y())
            self.scene.addItem(item)
            self.scene.clearSelection()
            item.setSelected(True)
            self.statusbar.showMessage(f"已添加: {component_type}")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # --- 强制明亮色板，彻底阻断系统暗黑模式的污染 ---
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor("#f1f5f9"))
    palette.setColor(QPalette.WindowText, QColor("#1e293b"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#1e293b"))
    palette.setColor(QPalette.Text, QColor("#1e293b"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#1e293b"))
    palette.setColor(QPalette.BrightText, QColor("#f43f5e"))
    palette.setColor(QPalette.Highlight, QColor("#0ea5e9"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    
    app.setFont(QFont("Microsoft YaHei", 9))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__": 
    main()