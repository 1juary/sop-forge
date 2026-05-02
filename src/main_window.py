#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口：MainWindow (顶层组装者)
"""

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QLabel, QPushButton, QGraphicsItem,
)
from PySide6.QtGui import (
    QFont, QColor, QPixmap, QImage, QAction, QKeySequence, QPalette,
)
from PySide6.QtCore import Qt, QRectF

from src.theme import GLOBAL_QSS
from src.scene import SOPCanvasScene # 负责管理数据的“幕后数据源”
from src.view import SOPCanvasView # 负责用户交互的“前台窗口”，直接与用户操作绑定
from src.panels.component_panel import ComponentPanel #（组件面板），提供大标题、正文、图片等基础元素的拖拽或点击入口
from src.panels.property_panel import PropertyPanel #属性面板，用于调节大小、颜色等
from src.panels.emoji_panel import EmojiPanel #表情面板
from src.io.serialization import export_to_json, import_from_json
from src.io.pdf_export import export_to_pdf
from src.items.text_item import SOPTextItem
from src.items.highlight_item import HighlightItem
from src.items.arrow_item import ArrowItem
from src.items.image_item import ImageItem
from src.items.icon_item import IconItem
from src.items.magnifier import DraggableNode, LensItem, MagnifierConeItem
from src.items.group_item import SOPGroupItem


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
        self.setup_connections() # 信号与槽链接
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

        em.addSeparator()
        action_group = em.addAction("🔗 组合选区")
        action_group.setShortcut(QKeySequence("Ctrl+G"))
        action_group.triggered.connect(self._on_group)

        action_ungroup = em.addAction("💔 取消组合")
        action_ungroup.setShortcut(QKeySequence("Ctrl+Shift+G"))
        action_ungroup.triggered.connect(self._on_ungroup)

        em.addSeparator()
        action_freeze = em.addAction("📌 冻结元素")
        action_freeze.setShortcut(QKeySequence("Ctrl+L"))
        action_freeze.triggered.connect(self._on_freeze)

        action_unfreeze = em.addAction("📍 解冻元素")
        action_unfreeze.setShortcut(QKeySequence("Ctrl+Shift+L"))
        action_unfreeze.triggered.connect(self._on_unfreeze)

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
        tb.addWidget(self._make_tool_btn("🔗 组合", self._on_group))
        tb.addWidget(self._make_tool_btn("💔 打散", self._on_ungroup))
        tb.addWidget(self._make_tool_btn("📌 冻结", self._on_freeze))
        tb.addWidget(self._make_tool_btn("📍 解冻", self._on_unfreeze))
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
            # 防止窗口关闭后场景已被销毁时仍被信号触发
            try:
                scene = self.scene
                if scene is None:
                    return
                items = scene.selectedItems()
            except RuntimeError:
                return
            self.property_panel.set_current_item(items[0] if items else None)

            # 【恢复组合框的整体状态】
            from src.items.group_item import SOPGroupItem
            try:
                for item in scene.items():
                    if isinstance(item, SOPGroupItem):
                        # 如果组合本身和内部的所有子元素都失去了焦点，重新合体为单一板块
                        is_active = item.isSelected() or any(c.isSelected() for c in item.childItems())
                        if not is_active:
                            item.setHandlesChildEvents(True)
            except RuntimeError:
                pass

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
            # 联动：当 zoom 改变时，同步更新 LensItem 的尺寸
            if hasattr(item, 'source') and item.source:
                sr = item.source.rect()
                sw, sh = sr.width(), sr.height()
                item.prepareGeometryChange()
                item.setRect(-sw * value / 2, -sh * value / 2, sw * value, sh * value)
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

    def _group_items(self):
        selected = self.scene.selectedItems()
        if len(selected) < 2:
            return
        group = SOPGroupItem()
        for item in selected:
            group.addToGroup(item)
        self.scene.addItem(group)
        group.setSelected(True)
        self.statusbar.showMessage(f"已组合 {len(selected)} 个组件")

    def _ungroup_items(self, group_item):
        children = group_item.childItems()[:]
        for child in children:
            group_item.removeFromGroup(child)
        self.scene.removeItem(group_item)
        self.scene.clearSelection()
        for child in children:
            child.setSelected(True)
        self.statusbar.showMessage("已取消组合")

    def _on_freeze(self):
        for item in self.scene.selectedItems():
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            item._is_frozen = True
        self.scene.update()
        self.statusbar.showMessage("已冻结选中元素")

    def _on_unfreeze(self):
        for item in self.scene.selectedItems():
            item.setFlag(QGraphicsItem.ItemIsMovable, True)
            item._is_frozen = False
        self.scene.update()
        self.statusbar.showMessage("已解冻选中元素")

    def _on_group(self):
        if len(self.scene.selectedItems()) > 1:
            self._group_items()

    def _on_ungroup(self):
        for item in self.scene.selectedItems():
            if isinstance(item, SOPGroupItem):
                self._ungroup_items(item)
                break

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

    def _add_component_at(self, component_type, scene_pos=None): #工厂模式函数
        if scene_pos is None:
            scene_pos = self.view.mapToScene(self.view.viewport().rect().center()) # 如果没有指定位置，默认放在视图中心。mapToScene 将视口坐标转换为场景坐标，确保组件出现在用户当前看到的位置。

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
