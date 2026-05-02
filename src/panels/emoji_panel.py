#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emoji 词典面板：EmojiPanel
"""

import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QSettings


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
        return {"警告": "⚠️", "注意": "💡", "检查": "✅", "危险": "🚫", "提示": "💡", "重要": "❗", "完成": "✅", "待办": "📝"}

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
