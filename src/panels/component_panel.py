#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组件面板：DraggableComponentButton, ComponentPanel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QGroupBox, QApplication,
)
from PySide6.QtGui import QFont, QDrag
from PySide6.QtCore import Qt, QMimeData, QPoint, Signal


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
