#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 导出逻辑
"""

from PySide6.QtGui import QPainter, QPageSize
from PySide6.QtCore import QRectF
from PySide6.QtPrintSupport import QPrinter


def export_to_pdf(scene, filepath):
    # 【新增】导出前，通知所有放大镜生成静态高清快照
    for item in scene.items():
        if hasattr(item, 'prepare_export_cache'):
            item.prepare_export_cache()

    show_grid_was = getattr(scene, "_show_grid", True)
    show_margin_was = getattr(scene, "_show_safe_margin", True)
    if hasattr(scene, "set_show_grid"):
        scene.set_show_grid(False)
    if hasattr(scene, "set_show_safe_margin"):
        scene.set_show_safe_margin(False)
    scene.clearSelection()

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(filepath)
    printer.setPageSize(QPageSize.A4)
    printer.setResolution(300)

    painter = QPainter()
    painter.begin(printer)

    pr = printer.pageRect(QPrinter.DevicePixel)
    scale = min(pr.width() / scene.A4_WIDTH, pr.height() / scene.A4_HEIGHT)

    num_pages = getattr(scene, 'num_pages', 1)
    for i in range(num_pages):
        if i > 0:
            printer.newPage()
        page_y = i * (scene.A4_HEIGHT + getattr(scene, 'PAGE_SPACING', 0))
        page_rect_scene = QRectF(0, page_y, scene.A4_WIDTH, scene.A4_HEIGHT)

        painter.save()
        painter.scale(scale, scale)
        painter.translate(0, -page_y)
        scene.render(painter, QRectF(0, page_y, scene.A4_WIDTH, scene.A4_HEIGHT), page_rect_scene)
        painter.restore()

    painter.end()

    # 【新增】导出结束，清空静态快照，恢复 UI 动态渲染
    for item in scene.items():
        if hasattr(item, 'clear_export_cache'):
            item.clear_export_cache()

    if hasattr(scene, "set_show_grid"):
        scene.set_show_grid(show_grid_was)
    if hasattr(scene, "set_show_safe_margin"):
        scene.set_show_safe_margin(show_margin_was)
