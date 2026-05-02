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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # 添加当前目录到 sys.path，确保 src 模块可被导入。—__file__ 是当前脚本的路径，os.path.dirname 获取目录部分，os.path.abspath 获取绝对路径。这样无论从哪里运行脚本，都能正确找到 src 模块。

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt

from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv) # sys.argv(Argument Vector（参数向量）) 允许从命令行传递参数给应用程序，虽然目前我们没有使用任何参数，但这是一个良好的习惯，可以为未来的功能扩展做好准备。
    app.setStyle("Fusion") # 设置应用程序的样式为 Fusion，这是一种跨平台的现代风格。

    # --- 强制明亮色板，彻底阻断系统暗黑模式的污染 ---
    palette = app.palette() # 获取当前应用程序的调色板对象，准备修改颜色以实现明亮科技风的视觉效果。
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
    app.setPalette(palette) # 将修改后的调色板应用到整个应用程序，确保所有窗口和控件都使用新的明亮色彩方案。

    app.setFont(QFont("Microsoft YaHei", 9)) # 设置全局字体为微软雅黑，大小为9pt，这是一种适合中文显示的清晰字体，能够提升用户界面的可读性和美观度。
    window = MainWindow() # 创建主窗口实例，MainWindow 类定义了应用程序的主要界面和功能逻辑。
    window.show()
    sys.exit(app.exec()) #execute,执行一个底层的五险循环，监听用户操作，把动作打包成event，发给windows 界面控件


if __name__ == "__main__":
    main()
