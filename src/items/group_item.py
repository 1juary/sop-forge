#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组合组件：SOPGroupItem
支持组合/取消组合、递归序列化
PPT 式交互：首次点击选中组，再次点击选中子元素
"""

from PySide6.QtWidgets import QGraphicsItem, QGraphicsItemGroup
from PySide6.QtCore import Qt

from src.items.base_item import SmartGraphicItemMixin
from src.items.text_item import SOPTextItem
from src.items.image_item import ImageItem
from src.items.icon_item import IconItem
from src.items.highlight_item import HighlightItem
from src.items.arrow_item import ArrowItem
from src.items.magnifier import DraggableNode, LensItem


class SOPGroupItem(SmartGraphicItemMixin, QGraphicsItemGroup):
    """
    组合组件：将多个 Item 组合为一个整体。
    PPT 式交互：首次点击选中组，再次点击穿透选中子元素。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 默认：将组合视为一个整体
        self.setHandlesChildEvents(True)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self._is_frozen = False

    def mousePressEvent(self, event):
        if self.is_frozen():
            event.accept()
            return

        # 【PPT 交互核心】
        # 如果组合已经被选中，再次点击时，放开事件拦截，允许用户单选里面的子元素
        if self.isSelected():
            self.setHandlesChildEvents(False)
            self.setSelected(False)
            # 获取鼠标下方的子元素并主动选中
            child = self.scene().itemAt(event.scenePos(), self.scene().views()[0].transform())
            if child and child in self.childItems():
                child.setSelected(True)
            event.accept()
            return

        super().mousePressEvent(event)

    def to_dict(self) -> dict:
        children = []
        for child in self.childItems():
            if hasattr(child, "to_dict"):
                try:
                    d = child.to_dict()
                    d["_group_child"] = True
                    d["z_value"] = child.zValue()  # 保存子元素层级
                    children.append(d)
                except:
                    pass
        return {
            "type": "group",
            "x": self.scenePos().x(),
            "y": self.scenePos().y(),
            "children": children,
        }

    @classmethod
    def from_dict(cls, data: dict, scene=None):
        group = cls()
        group.setPos(data.get("x", 0), data.get("y", 0))
        # 先创建所有子元素并添加到 scene，再 addToGroup
        child_items = []
        for child_data in data.get("children", []):
            item_type = child_data.get("type", "")
            item = None
            if item_type == "text":
                item = SOPTextItem.from_dict(child_data, scene)
            elif item_type == "image":
                item = ImageItem.from_dict(child_data, scene)
            elif item_type == "icon":
                item = IconItem.from_dict(child_data, scene)
            elif item_type == "highlight":
                item = HighlightItem.from_dict(child_data, scene)
            elif item_type == "arrow":
                item = ArrowItem.from_dict(child_data, scene)
            elif item_type == "source":
                w = child_data.get("width", child_data.get("radius", 30) * 2)
                h = child_data.get("height", w)
                item = DraggableNode(child_data.get("x", 0), child_data.get("y", 0), w, h)
            elif item_type == "lens":
                w = child_data.get("width", child_data.get("radius", 50) * 2)
                h = child_data.get("height", w)
                # lens 需要 source，但组内重建时先创建占位
                item = LensItem(None, child_data.get("x", 0), child_data.get("y", 0), w, h, child_data.get("zoom_factor", 2.0))
            if item:
                if scene:
                    scene.addItem(item)
                child_items.append((item, child_data))
        # 将所有子元素加入组，并恢复子元素层级
        for item, child_data in child_items:
            item.setZValue(child_data.get("z_value", 0))  # 恢复子元素层级
            group.addToGroup(item)
        group.setZValue(data.get("z_value", 0))  # 恢复 group 自身层级
        return group
