#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局多巴胺 Qt Style Sheets（Qt 样式表） 样式定义
键值对格式
"""

GLOBAL_QSS = """
/* 全局基础 */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}
QMainWindow {
    background-color: #f1f5f9;
}

/* 顶部菜单与工具栏 */
QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}
QMenuBar::item {
    padding: 6px 12px;
    background: transparent;
    color: #1e293b;
}
QMenuBar::item:selected {
    background: #f0fdf4;
    color: #16a34a;
    border-radius: 4px;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 2px solid #e2e8f0;
    padding: 6px;
    spacing: 8px;
}

/* 面板背景与滚动条 */
QSplitter::handle {
    background-color: #cbd5e1;
    width: 2px;
}
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

/* 分组框 (多巴胺描边) */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 16px;
    font-weight: bold;
    color: #334155;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #0ea5e9;
}

/* 表单组件 */
QLineEdit, QComboBox, QSpinBox {
    background-color: #f8fafc;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    color: #0f172a;
    selection-background-color: #38bdf8;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #06b6d4;
    background-color: #ffffff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    border: 1px solid #06b6d4;
    border-radius: 4px;
    background-color: #ffffff;
    selection-background-color: #cffafe;
    selection-color: #0891b2;
}

/* 滑块 */
QSlider::groove:horizontal {
    border-radius: 4px;
    height: 8px;
    background: #e2e8f0;
}
QSlider::handle:horizontal {
    background: #ec4899;
    width: 16px;
    height: 16px;
    margin: -4px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #f472b6;
    border-radius: 4px;
}

/* 复选框 */
QCheckBox {
    spacing: 8px;
    font-size: 12px;
    color: #1e293b;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #cbd5e1;
    background: #f8fafc;
}
QCheckBox::indicator:checked {
    background: #8b5cf6;
    border: 2px solid #8b5cf6;
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>);
}

/* 表格 */
QTableWidget {
    background-color: #ffffff;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    color: #1e293b;
}
QTableWidget::item {
    background-color: #ffffff;
    color: #1e293b;
    padding: 4px;
}
QTableWidget::item:selected {
    background-color: #e0f2fe;
    color: #0369a1;
}
QHeaderView::section {
    background-color: #f8fafc;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    padding: 8px;
    font-weight: bold;
    color: #475569;
}
"""
