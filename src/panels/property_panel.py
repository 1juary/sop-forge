#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
属性面板：PropertyPanel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QFormLayout, QComboBox, QSpinBox, QCheckBox, QSlider, QLineEdit,
    QColorDialog,
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal

from src.items.text_item import SOPTextItem
from src.items.highlight_item import HighlightItem
from src.items.arrow_item import ArrowItem
from src.items.image_item import ImageItem
from src.items.icon_item import IconItem
from src.items.magnifier import LensItem


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
        self._add_combo_row(form, "对齐", ["左对齐", "居中", "右对齐"], "左对齐", "alignment")
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
        self._add_combo_row(form, "类型", ["警告", "提示", "工具", "检查", "错误", "右箭头", "下箭头", "星标"], {"warning": "警告", "info": "提示", "tool": "工具", "check": "检查", "error": "错误", "arrow_right": "右箭头", "arrow_down": "下箭头", "star": "星标"}.get(item._icon_type, "警告"), "icon_type")
        self._add_combo_row(form, "颜色", list(IconItem.STANDARD_COLORS.keys()), self._find_key_by_value(IconItem.STANDARD_COLORS, item._color.name()), "icon_color")
        self._add_spin_row(form, "大小", item._size, 16, 64, "icon_size")

    def _build_magnifier_properties(self, item):
        form = self._add_property_group("放大镜属性")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(11, 50)
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
