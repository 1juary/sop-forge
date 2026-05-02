#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画布视图：SOPCanvasView
"""

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsItem, QGraphicsTextItem, QMenu, QApplication,
)
from PySide6.QtGui import (
    QPainter, QPixmap, QImage, QKeySequence, QClipboard, QCursor,
    QWheelEvent,
)
from PySide6.QtCore import Qt, QPoint, QPointF

from src.items.group_item import SOPGroupItem


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
        items = self.scene().selectedItems()
        if not items:
            return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: white; border: 1px solid #e2e8f0; border-radius: 6px; } QMenu::item { padding: 6px 24px; color: #1e293b; } QMenu::item:selected { background-color: #f1f5f9; color: #0ea5e9; }")

        # 【重写】置于顶层逻辑 — 级联提升光锥
        def bring_to_front():
            max_z = max([i.zValue() for i in self.scene().items()] + [0])
            for i in items:
                i.setZValue(max_z + 1)
                # 级联提升光锥
                if hasattr(i, '_cone') and i._cone:
                    i._cone.setZValue(max_z + 0.9)
                elif type(i).__name__ == "DraggableNode":
                    for other in self.scene().items():
                        if getattr(other, 'source', None) == i and getattr(other, '_cone', None):
                            other._cone.setZValue(max_z + 0.9)

        # 【重写】置于底层逻辑 — 级联降低光锥
        def send_to_back():
            min_z = min([i.zValue() for i in self.scene().items()] + [0])
            for i in items:
                i.setZValue(min_z - 1)
                # 级联降低光锥
                if hasattr(i, '_cone') and i._cone:
                    i._cone.setZValue(min_z - 1.1)
                elif type(i).__name__ == "DraggableNode":
                    for other in self.scene().items():
                        if getattr(other, 'source', None) == i and getattr(other, '_cone', None):
                            other._cone.setZValue(min_z - 1.1)

        action_top = menu.addAction("⬆ 置于顶层")
        action_top.triggered.connect(bring_to_front)

        action_bottom = menu.addAction("⬇ 置于底层")
        action_bottom.triggered.connect(send_to_back)

        menu.addSeparator()
        # 冻结/解冻
        all_frozen = all(getattr(i, '_is_frozen', False) for i in items)
        if all_frozen:
            action_unfreeze = menu.addAction("📍 解冻")
            action_unfreeze.triggered.connect(lambda: self._toggle_freeze(items, False))
        else:
            action_freeze = menu.addAction("📌 冻结")
            action_freeze.triggered.connect(lambda: self._toggle_freeze(items, True))

        menu.addSeparator()
        # 组合/取消组合
        if len(items) > 1:
            action_group = menu.addAction("🔗 组合选区")
            action_group.triggered.connect(lambda: self.window()._group_items())
        elif len(items) == 1 and isinstance(items[0], SOPGroupItem):
            action_ungroup = menu.addAction("💔 取消组合")
            action_ungroup.triggered.connect(lambda: self.window()._ungroup_items(items[0]))

        menu.addSeparator()
        action_delete = menu.addAction("🗑 删除")
        action_delete.triggered.connect(lambda: self.window()._on_delete())

        menu.exec(event.globalPos())

    def _set_top_z(self, items):
        max_z = max([i.zValue() for i in self.scene().items()]) + 1
        for i in items:
            i.setZValue(max_z)

    def _set_bottom_z(self, items):
        min_z = min([i.zValue() for i in self.scene().items()]) - 1
        for i in items:
            i.setZValue(min_z)

    def _toggle_freeze(self, items, freeze):
        for i in items:
            i.setFlag(QGraphicsItem.ItemIsMovable, not freeze)
            i._is_frozen = freeze
        self.scene().update()

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
