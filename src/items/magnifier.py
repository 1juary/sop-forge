#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
放大镜组件：DraggableNode, LensItem, MagnifierConeItem
支持椭圆缩放、双向等比同步、5倍缩放
"""

import math
import uuid

from PySide6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PySide6.QtGui import (
    QColor, QPen, QBrush, QPainter, QPainterPath, QImage,
)
from PySide6.QtCore import Qt, QRectF, QPointF

from src.items.base_item import SmartGraphicItemMixin


class DraggableNode(SmartGraphicItemMixin, QGraphicsEllipseItem):
    def __init__(self, x, y, w, h=None):
        if h is None:
            h = w
        super().__init__(-w / 2, -h / 2, w, h)
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        self.setPen(QPen(QColor("#0ea5e9"), 2, Qt.DashLine))
        self.setZValue(5)
        self.setAcceptHoverEvents(True)
        self._resize_mode = None
        self._aspect_ratio = 1.0
        self.uuid = str(uuid.uuid4())
        # 彻底关闭该取景框的移动磁吸功能，保证丝滑取景
        self._disable_snap = True

    def boundingRect(self):
        # 扩展 10 像素的包围盒，确保外围控制柄不会被裁剪
        return self.rect().adjusted(-10, -10, 10, 10)

    def shape(self):
        # 核心修复：用整体矩形替代默认的椭圆判定，防止角落把手点击穿透
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def _get_handles(self):
        """返回 5 个控制点的矩形热区字典 (扩大判定区)"""
        hw = self.rect().width() / 2
        hh = self.rect().height() / 2
        return {
            "corner": QRectF(hw - 10, hh - 10, 20, 20),
            "right": QRectF(hw - 10, -10, 20, 20),
            "bottom": QRectF(-10, hh - 10, 20, 20),
            "left": QRectF(-hw - 10, -10, 20, 20),
            "top": QRectF(-10, -hh - 10, 20, 20)
        }

    def hoverMoveEvent(self, event):
        handles = self._get_handles()
        pos = event.pos()
        if handles["corner"].contains(pos):
            self.setCursor(Qt.SizeFDiagCursor)
        elif handles["right"].contains(pos) or handles["left"].contains(pos):
            self.setCursor(Qt.SizeHorCursor)
        elif handles["bottom"].contains(pos) or handles["top"].contains(pos):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.OpenHandCursor if not self.isSelected() else Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'is_frozen') and self.is_frozen():
                event.accept()
                return
            # 判断点击了哪个控制点
            self._resize_mode = None
            for key, h_rect in self._get_handles().items():
                if h_rect.contains(event.pos()):
                    self._resize_mode = key
                    self._aspect_ratio = self.rect().height() / max(1.0, self.rect().width())
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_resize_mode', None):
            pos = event.pos()
            hw = self.rect().width() / 2
            hh = self.rect().height() / 2
            
            if self._resize_mode == "corner":
                hw = max(15.0, abs(pos.x()))
                hh = hw * getattr(self, '_aspect_ratio', 1.0)
            elif self._resize_mode == "right": hw = max(15.0, abs(pos.x()))
            elif self._resize_mode == "bottom": hh = max(15.0, abs(pos.y()))
            elif self._resize_mode == "left": hw = max(15.0, abs(pos.x()))
            elif self._resize_mode == "top": hh = max(15.0, abs(pos.y()))

            self.prepareGeometryChange()
            self.setRect(-hw, -hh, hw * 2, hh * 2)
            
            # 【同步给 LensItem】
            for other in self.scene().items():
                if type(other).__name__ == "LensItem" and getattr(other, 'source', None) == self:
                    zoom = other.zoom_factor
                    other.prepareGeometryChange()
                    other.setRect(-hw * zoom, -hh * zoom, hw * 2 * zoom, hh * 2 * zoom)
                    other.update()
                    
            self.update()
            if self.scene(): self.scene().update()
            event.accept()
        else: 
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_resize_mode', None):
            self._resize_mode = None
            if self.scene():
                self.scene().selectionChanged.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        if getattr(self, '_is_rendering', False):
            return
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            hw, hh = self.rect().width() / 2, self.rect().height() / 2
            theme_color = QColor("#0ea5e9")

            # 画方形虚线包围盒
            painter.setPen(QPen(QColor("#94a3b8"), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(-hw, -hh, hw * 2, hh * 2)

            # 画4个边缘单向调整控制圆点
            painter.setPen(QPen(theme_color, 2))
            painter.setBrush(QColor("#ffffff"))
            for pt in [QPointF(hw, 0), QPointF(0, hh), QPointF(-hw, 0), QPointF(0, -hh)]:
                painter.drawEllipse(pt, 4, 4)

            # 画右下角等比缩放控制方块
            painter.drawRect(hw - 5, hh - 5, 10, 10)
            painter.restore()

    def to_dict(self) -> dict:
        return {
            "type": "source", "x": self.scenePos().x(), "y": self.scenePos().y(),
            "width": self.rect().width(), "height": self.rect().height(),
            "_is_frozen": getattr(self, '_is_frozen', False),
            "uuid": self.uuid,
        }


class LensItem(SmartGraphicItemMixin, QGraphicsEllipseItem):
    def __init__(self, source_circle, x, y, w, h=None, zoom_factor=2.0, cone_item=None):
        if h is None:
            h = w
        super().__init__(-w / 2, -h / 2, w, h)
        self.setPos(x, y)
        self.source = source_circle
        self.zoom_factor = zoom_factor
        self._cone = cone_item
        self.setZValue(10)
        self.setPen(QPen(QColor("#f43f5e"), 3))
        self.setAcceptHoverEvents(True)
        self._resize_mode = None
        self._aspect_ratio = 1.0

    def set_cone(self, cone_item):
        self._cone = cone_item

    def boundingRect(self):
        # 扩展 10 像素的包围盒，确保外围控制柄不会被裁剪
        return self.rect().adjusted(-10, -10, 10, 10)

    def shape(self):
        # 核心修复：用整体矩形替代默认的椭圆判定，防止角落把手点击穿透
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def _get_handles(self):
        """返回 5 个控制点的矩形热区字典 (扩大判定区)"""
        hw = self.rect().width() / 2
        hh = self.rect().height() / 2
        return {
            "corner": QRectF(hw - 10, hh - 10, 20, 20),
            "right": QRectF(hw - 10, -10, 20, 20),
            "bottom": QRectF(-10, hh - 10, 20, 20),
            "left": QRectF(-hw - 10, -10, 20, 20),
            "top": QRectF(-10, -hh - 10, 20, 20)
        }

    def hoverMoveEvent(self, event):
        handles = self._get_handles()
        pos = event.pos()
        if handles["corner"].contains(pos):
            self.setCursor(Qt.SizeFDiagCursor)
        elif handles["right"].contains(pos) or handles["left"].contains(pos):
            self.setCursor(Qt.SizeHorCursor)
        elif handles["bottom"].contains(pos) or handles["top"].contains(pos):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.OpenHandCursor if not self.isSelected() else Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'is_frozen') and self.is_frozen():
                event.accept()
                return
            # 判断点击了哪个控制点
            self._resize_mode = None
            for key, h_rect in self._get_handles().items():
                if h_rect.contains(event.pos()):
                    self._resize_mode = key
                    self._aspect_ratio = self.rect().height() / max(1.0, self.rect().width())
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_resize_mode', None):
            pos = event.pos()
            hw = self.rect().width() / 2
            hh = self.rect().height() / 2
            
            if self._resize_mode == "corner":
                hw = max(15.0, abs(pos.x()))
                hh = hw * getattr(self, '_aspect_ratio', 1.0)
            elif self._resize_mode == "right": hw = max(15.0, abs(pos.x()))
            elif self._resize_mode == "bottom": hh = max(15.0, abs(pos.y()))
            elif self._resize_mode == "left": hw = max(15.0, abs(pos.x()))
            elif self._resize_mode == "top": hh = max(15.0, abs(pos.y()))

            self.prepareGeometryChange()
            self.setRect(-hw, -hh, hw * 2, hh * 2)
            
            # 【同步给 DraggableNode (Source)】
            if self.source:
                zoom = self.zoom_factor
                self.source.prepareGeometryChange()
                self.source.setRect(-hw / zoom, -hh / zoom, (hw * 2) / zoom, (hh * 2) / zoom)
                self.source.update()
                
            self.update()
            if self.scene(): self.scene().update()
            event.accept()
        else: 
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_resize_mode', None):
            self._resize_mode = None
            if self.scene():
                self.scene().selectionChanged.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def prepare_export_cache(self):
        """在 PDF 导出前预渲染 4x 高清快照，避开 QPrinter 的嵌套渲染限制"""
        if not self.scene() or not self.source:
            return
        target_rect = QRectF(-self.rect().width() / 2, -self.rect().height() / 2, self.rect().width(), self.rect().height())
        cw, ch = self.rect().width() / self.zoom_factor, self.rect().height() / self.zoom_factor
        sp = self.source.scenePos()
        source_rect = QRectF(sp.x() - cw / 2, sp.y() - ch / 2, cw, ch)

        img_w, img_h = int(math.ceil(target_rect.width() * 4.0)), int(math.ceil(target_rect.height() * 4.0))
        if img_w > 0 and img_h > 0:
            img = QImage(img_w, img_h, QImage.Format_ARGB32_Premultiplied)
            img.fill(Qt.transparent)
            img_painter = QPainter(img)
            img_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

            self._is_rendering = True
            if self.source:
                self.source._is_rendering = True
            if getattr(self, '_cone', None):
                self._cone._is_rendering = True

            self.scene().render(img_painter, QRectF(0, 0, img_w, img_h), source_rect)
            img_painter.end()

            self._is_rendering = False
            if self.source:
                self.source._is_rendering = False
            if getattr(self, '_cone', None):
                self._cone._is_rendering = False
            self._export_cache = img

    def clear_export_cache(self):
        self._export_cache = None

    def paint(self, painter, option, widget):
        if getattr(self, '_is_rendering', False):
            return
        painter.save()
        path = QPainterPath()
        path.addEllipse(self.rect())
        painter.setClipPath(path)

        target_rect = QRectF(-self.rect().width() / 2, -self.rect().height() / 2, self.rect().width(), self.rect().height())

        # 如果存在导出快照，直接绘制快照（避开嵌套 render）
        if getattr(self, '_export_cache', None):
            painter.drawImage(target_rect, self._export_cache)
        elif self.scene() and self.source:
            cw = self.rect().width() / self.zoom_factor
            ch = self.rect().height() / self.zoom_factor
            sp = self.source.scenePos()
            source_rect = QRectF(sp.x() - cw / 2, sp.y() - ch / 2, cw, ch)

            # 使用高分辨率 QImage 中间层修复 PDF 导出时的矩阵崩溃
            img_w = int(math.ceil(target_rect.width() * 2.0))
            img_h = int(math.ceil(target_rect.height() * 2.0))

            if img_w > 0 and img_h > 0:
                img = QImage(img_w, img_h, QImage.Format_ARGB32_Premultiplied)
                img.fill(Qt.transparent)
                img_painter = QPainter(img)
                img_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

                self._is_rendering = True
                if self.source:
                    self.source._is_rendering = True
                if getattr(self, '_cone', None):
                    self._cone._is_rendering = True

                self.scene().render(img_painter, QRectF(0, 0, img_w, img_h), source_rect)
                img_painter.end()

                self._is_rendering = False
                if self.source:
                    self.source._is_rendering = False
                if getattr(self, '_cone', None):
                    self._cone._is_rendering = False

                painter.drawImage(target_rect, img)
        painter.restore()
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            hw, hh = self.rect().width() / 2, self.rect().height() / 2
            theme_color = QColor("#f43f5e")

            # 画方形虚线包围盒
            painter.setPen(QPen(QColor("#94a3b8"), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(-hw, -hh, hw * 2, hh * 2)

            # 画4个边缘单向调整控制圆点
            painter.setPen(QPen(theme_color, 2))
            painter.setBrush(QColor("#ffffff"))
            for pt in [QPointF(hw, 0), QPointF(0, hh), QPointF(-hw, 0), QPointF(0, -hh)]:
                painter.drawEllipse(pt, 4, 4)

            # 画右下角等比缩放控制方块
            painter.drawRect(hw - 5, hh - 5, 10, 10)
            painter.restore()

    def to_dict(self) -> dict:
        return {
            "type": "lens", "x": self.scenePos().x(), "y": self.scenePos().y(),
            "width": self.rect().width(), "height": self.rect().height(),
            "zoom_factor": self.zoom_factor,
            "_is_frozen": getattr(self, '_is_frozen', False),
            "source_uuid": self.source.uuid if self.source else None,
        }


class MagnifierConeItem(QGraphicsItem):
    def __init__(self, source_circle, lens_circle):
        super().__init__()
        self.source = source_circle
        self.lens = lens_circle
        self.setZValue(-1)
        self.cone_color = QColor(244, 63, 94, 15)
        self.line_color = QColor(244, 63, 94, 120)

    def boundingRect(self):
        return self.source.sceneBoundingRect().united(self.lens.sceneBoundingRect())

    def _ellipse_point(self, cx, cy, rx, ry, angle):
        """椭圆极坐标上的点: (cx,cy) 为中心, rx/ry 为半轴, angle 为弧度"""
        return QPointF(cx + rx * math.cos(angle), cy + ry * math.sin(angle))

    def paint(self, painter, option, widget):
        if getattr(self, '_is_rendering', False):
            return

        cx1, cy1 = self.source.scenePos().x(), self.source.scenePos().y()
        sr = self.source.rect()
        rx1, ry1 = sr.width() / 2, sr.height() / 2

        cx2, cy2 = self.lens.scenePos().x(), self.lens.scenePos().y()
        lr = self.lens.rect()
        rx2, ry2 = lr.width() / 2, lr.height() / 2

        # 近似光锥：通过圆心连线角度计算垂直方向，用椭圆极坐标求4个近似切点
        angle = math.atan2(cy2 - cy1, cx2 - cx1)
        perp1 = angle + math.pi / 2
        perp2 = angle - math.pi / 2

        p1 = self._ellipse_point(cx1, cy1, rx1, ry1, perp1)
        p2 = self._ellipse_point(cx1, cy1, rx1, ry1, perp2)
        p3 = self._ellipse_point(cx2, cy2, rx2, ry2, perp1)
        p4 = self._ellipse_point(cx2, cy2, rx2, ry2, perp2)

        clip_path = QPainterPath()
        clip_path.addRect(self.scene().sceneRect())
        source_path = QPainterPath()
        source_path.addEllipse(sr.translated(cx1, cy1))
        clip_path = clip_path.subtracted(source_path)
        painter.setClipPath(clip_path)

        cone_path = QPainterPath()
        cone_path.moveTo(p1)
        cone_path.lineTo(p3)
        cone_path.lineTo(p4)
        cone_path.lineTo(p2)
        cone_path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.cone_color))
        painter.drawPath(cone_path)
        pen = QPen(self.line_color, 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(p1, p3)
        painter.drawLine(p2, p4)
