#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP Forge - SOP排版设计软件 (模块化版)
========================================
UI风格: 明亮科技风 + 多巴胺配色 (Dopamine Tech Light)
功能包含: 多页连排、持久化记忆、Drag&Drop、可视化双向调节
"""

import sys
import os

# 确保 src 模块能被绝对引用
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt

from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # --- 强制明亮色板，彻底阻断系统暗黑模式的污染 ---
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor("#f1f5f9"))
    palette.setColor(QPalette.WindowText, QColor("#1e293b"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#1e293b"))
    palette.setColor(QPalette.Text, QColor("#1e293b"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#1e293b"))
    palette.setColor(QPalette.BrightText, QColor("#f43f5e"))
    palette.setColor(QPalette.Highlight, QColor("#0ea5e9"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    app.setFont(QFont("Microsoft YaHei", 9))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
