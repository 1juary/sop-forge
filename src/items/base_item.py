#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用混入类 (Mixin) 与基础数据结构
"""

from PySide6.QtWidgets import QGraphicsItem


class SmartGraphicItemMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

    def is_frozen(self):
        """向上追溯：只要自己或任何父级组合被冻结，即视为冻结"""
        if getattr(self, '_is_frozen', False):
            return True
        p = self.parentItem()
        while p:
            if getattr(p, '_is_frozen', False):
                return True
            p = p.parentItem()
        return False

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # 绝对坐标锁：一旦判定为冻结，强行返回当前坐标，忽略鼠标拖拽！
            if self.is_frozen():
                return self.pos()

            # 1. 如果组件明确排除了磁吸，直接返回
            if getattr(self, '_disable_snap', False):
                return value

            # 2. 专业级交互：按住 Alt 键可临时屏蔽一切磁吸
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            if QApplication.keyboardModifiers() & Qt.AltModifier:
                return value

            if hasattr(self.scene(), "calculate_snap"):
                value = self.scene().calculate_snap(self, value)
            return value
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.scene().update()
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)
