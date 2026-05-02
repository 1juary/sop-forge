#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本组件：SOPTextItem, ImageCaptionItem
"""

import re

from PySide6.QtWidgets import (
    QGraphicsTextItem, QGraphicsItem, QMessageBox,
)
from PySide6.QtGui import QFont, QColor, QTextOption
from PySide6.QtCore import Qt, Signal

from src.items.base_item import SmartGraphicItemMixin


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
            "font_size": self.font().pointSize(), "bold": self.font().bold(),
            "_is_frozen": getattr(self, '_is_frozen', False),
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        item = cls(text=data.get("text", ""), level=data.get("level", "body"))
        item.setPos(data.get("x", 0), data.get("y", 0))
        if "font_family" in data:
            font = item.font()
            font.setFamily(data["font_family"])
            item.setFont(font)
        if data.get("_is_frozen", False):
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item._is_frozen = True
        return item


class ImageCaptionItem(QGraphicsTextItem):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Microsoft YaHei", 9))
        self.setDefaultTextColor(QColor("#64748b"))
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
