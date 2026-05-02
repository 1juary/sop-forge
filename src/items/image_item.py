#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片组件：ImageItem
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import (
    QPixmap, QPainter, QPen, QBrush, QColor, QFont,
)
from PySide6.QtCore import Qt, QRectF, QPointF, QByteArray, QBuffer, QIODevice

from src.items.base_item import SmartGraphicItemMixin
from src.items.text_item import ImageCaptionItem


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
        self._update_caption_text(caption_text if caption_text else f"图 {self._image_number}: 图片")

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
        self._caption.setPlainText(text)
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
        return self._caption.toPlainText()

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
            buffer = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            self._pixmap.save(buffer, "PNG")
            pixmap_base64 = ba.toBase64().data().decode("ascii")
        return {
            "type": "image", "x": pos.x(), "y": pos.y(),
            "width": self._image_width, "height": self._image_height,
            "caption": self.get_caption(), "image_number": self._image_number,
            "show_caption": self._show_caption,
            "pixmap_base64": pixmap_base64,
            "_is_frozen": getattr(self, '_is_frozen', False),
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
        if data.get("_is_frozen", False):
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item._is_frozen = True
        return item
