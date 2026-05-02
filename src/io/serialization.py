#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
序列化与导出逻辑 (多页面)
支持 width/height 序列化，兼容旧版 radius 数据
"""

import json

from PySide6.QtWidgets import QGraphicsItem

from src.items.text_item import SOPTextItem
from src.items.image_item import ImageItem
from src.items.icon_item import IconItem
from src.items.highlight_item import HighlightItem
from src.items.arrow_item import ArrowItem
from src.items.magnifier import DraggableNode, LensItem, MagnifierConeItem
from src.items.group_item import SOPGroupItem


def export_to_json(scene, filepath):
    data = {"num_pages": getattr(scene, 'num_pages', 1), "items": []}
    for item in scene.items():
        # 跳过作为子元素的 item (它们会被 Group 递归导出)
        if item.parentItem() is not None:
            continue

        if hasattr(item, "to_dict"):
            try:
                item_data = item.to_dict()
                item_data["z_value"] = item.zValue()  # 动态注入 z_value
                data["items"].append(item_data)
            except Exception:
                pass
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def import_from_json(scene, filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    scene.clear()

    if hasattr(scene, 'set_num_pages'):
        scene.set_num_pages(data.get("num_pages", 1))

    TYPE_MAP = {"text": SOPTextItem, "image": ImageItem, "icon": IconItem, "highlight": HighlightItem, "arrow": ArrowItem, "group": SOPGroupItem}
    lens_data_list = []
    sources_dict = {}  # 用于存储 uuid -> source 实例的映射

    # Pass 1: 实例化常规组件和 Source
    for item_data in data.get("items", []):
        item_type = item_data.get("type", "")
        if item_type in TYPE_MAP:
            item = TYPE_MAP[item_type].from_dict(item_data, scene)
            item.setZValue(item_data.get("z_value", 0))  # 恢复图层高度
            scene.addItem(item)
        elif item_type == "source":
            w = item_data.get("width", item_data.get("radius", 30) * 2)
            h = item_data.get("height", w)
            source_item = DraggableNode(item_data.get("x", 300), item_data.get("y", 300), w, h)
            if "uuid" in item_data:
                source_item.uuid = item_data["uuid"]
            source_item.setZValue(item_data.get("z_value", 5))  # 恢复
            if item_data.get("_is_frozen", False):
                source_item._is_frozen = True
                source_item.setFlag(QGraphicsItem.ItemIsMovable, False)
            scene.addItem(source_item)
            sources_dict[getattr(source_item, 'uuid', '')] = source_item
        elif item_type == "lens":
            lens_data_list.append(item_data)

    # Pass 2: 实例化 Lens 和 Cone
    for item_data in lens_data_list:
        target_uuid = item_data.get("source_uuid", "")
        # 如果能匹配到 UUID 就用匹配的，否则兼容旧版数据取第一个
        source_item = sources_dict.get(target_uuid)
        if not source_item and sources_dict:
            source_item = list(sources_dict.values())[0]

        if source_item:
            w = item_data.get("width", item_data.get("radius", 50) * 2)
            h = item_data.get("height", w)
            lens_item = LensItem(source_item, item_data.get("x", 450), item_data.get("y", 250), w, h, item_data.get("zoom_factor", 2.0))
            lens_item.setZValue(item_data.get("z_value", 10))  # 恢复
            if item_data.get("_is_frozen", False):
                lens_item._is_frozen = True
                lens_item.setFlag(QGraphicsItem.ItemIsMovable, False)
            scene.addItem(lens_item)
            cone = MagnifierConeItem(source_item, lens_item)
            cone.setZValue(lens_item.zValue() - 0.1)  # 让光锥永远紧贴镜头下层
            scene.addItem(cone)
            lens_item.set_cone(cone)
