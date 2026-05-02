#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心场景：SOPCanvasScene (多页连排)
"""

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF

from src.items.magnifier import MagnifierConeItem


class SOPCanvasScene(QGraphicsScene):
    A4_WIDTH, A4_HEIGHT = 794, 1123
    SAFE_MARGIN = 50
    PAGE_SPACING = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self._show_grid = True
        self._show_safe_margin = True
        self._grid_size = 20
        self._snap_threshold = 6.0
        self.snap_lines = []
        self.num_pages = 1
        self.setBackgroundBrush(QBrush(QColor("#cbd5e1")))
        self._update_scene_rect()

    def _update_scene_rect(self):
        self.setSceneRect(0, 0, self.A4_WIDTH, self.num_pages * self.A4_HEIGHT + (self.num_pages - 1) * self.PAGE_SPACING)
        self.update()

    def add_page(self):
        self.num_pages += 1
        self._update_scene_rect()

    def set_num_pages(self, num):
        self.num_pages = max(1, num)
        self._update_scene_rect()

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        for i in range(self.num_pages):
            page_rect = QRectF(0, i * (self.A4_HEIGHT + self.PAGE_SPACING), self.A4_WIDTH, self.A4_HEIGHT)
            if not rect.intersects(page_rect):
                continue
            painter.fillRect(page_rect.translated(8, 8), QColor(0, 0, 0, 15))
            painter.fillRect(page_rect, Qt.white)
            if self._show_grid:
                pen = QPen(QColor("#f1f5f9"), 1)
                painter.setPen(pen)
                for x in range(int(page_rect.left()), int(page_rect.right()), self._grid_size):
                    painter.drawLine(x, int(page_rect.top()), x, int(page_rect.bottom()))
                for y in range(int(page_rect.top()), int(page_rect.bottom()), self._grid_size):
                    painter.drawLine(int(page_rect.left()), y, int(page_rect.right()), y)

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if self._show_safe_margin:
            pen = QPen(QColor("#f43f5e"), 1, Qt.DashLine)
            painter.setPen(pen)
            for i in range(self.num_pages):
                m_rect = QRectF(self.SAFE_MARGIN, i * (self.A4_HEIGHT + self.PAGE_SPACING) + self.SAFE_MARGIN, self.A4_WIDTH - 2*self.SAFE_MARGIN, self.A4_HEIGHT - 2*self.SAFE_MARGIN)
                if rect.intersects(m_rect):
                    painter.drawRect(m_rect)
        if self.snap_lines:
            pen = QPen(QColor("#0ea5e9"), 1, Qt.DashLine)
            painter.setPen(pen)
            for line in self.snap_lines:
                painter.drawLine(line)

        # 大头针视觉反馈：在冻结组件右上角绘制 📌
        pin_font = QFont("Segoe UI Emoji", 14)
        painter.setFont(pin_font)
        for item in self.items():
            if getattr(item, '_is_frozen', False):
                br = item.sceneBoundingRect()
                painter.drawText(br.right() - 10, br.top() + 10, "📌")

    def set_show_grid(self, show: bool):
        self._show_grid = show
        self.update()

    def set_show_safe_margin(self, show: bool):
        self._show_safe_margin = show
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.snap_lines:
            self.snap_lines.clear()
            self.update()

    def calculate_snap(self, item, new_pos):
        threshold = self._snap_threshold
        item_center = new_pos + item.boundingRect().center()
        best_x, best_y = new_pos.x(), new_pos.y()

        snap_lines_x = [0, self.A4_WIDTH / 2, self.A4_WIDTH]
        snap_lines_y = []
        for i in range(self.num_pages):
            py = i * (self.A4_HEIGHT + self.PAGE_SPACING)
            snap_lines_y.extend([py, py + self.A4_HEIGHT / 2, py + self.A4_HEIGHT])

        for other in self.items():
            if other == item or not isinstance(other, QGraphicsItem) or not other.isVisible():
                continue
            # 忽略光锥、取景框和放大镜，它们不应作为其他组件对齐的参考线
            if type(other).__name__ in ["MagnifierConeItem", "DraggableNode", "LensItem"]:
                continue
            orect = other.sceneBoundingRect()
            snap_lines_x.extend([orect.left(), orect.center().x(), orect.right()])
            snap_lines_y.extend([orect.top(), orect.center().y(), orect.bottom()])

        self.snap_lines.clear()

        for ref_x in snap_lines_x:
            for anchor_x in [item_center.x(), new_pos.x(), new_pos.x() + item.boundingRect().width()]:
                if abs(ref_x - anchor_x) < threshold:
                    best_x = new_pos.x() + (ref_x - anchor_x)
                    self.snap_lines.append(QLineF(ref_x, 0, ref_x, self.sceneRect().height()))
                    break
            if self.snap_lines:
                break

        for ref_y in snap_lines_y:
            for anchor_y in [item_center.y(), new_pos.y(), new_pos.y() + item.boundingRect().height()]:
                if abs(ref_y - anchor_y) < threshold:
                    best_y = new_pos.y() + (ref_y - anchor_y)
                    self.snap_lines.append(QLineF(0, ref_y, self.A4_WIDTH, ref_y))
                    break
            if len(self.snap_lines) > (1 if best_x != new_pos.x() else 0):
                break

        return QPointF(best_x, best_y)
