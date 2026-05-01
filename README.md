# SOP Forge - SOP排版设计软件

一款专用于工程团队、质量团队的标准化作业程序(SOP)排版软件。
有别于 Word 或 InDesign，本软件将《排版排雷手册》中的专业设计规范"硬编码"到软件底层，通过防呆机制、自动化约束和高级标注工具，让非设计专业的工程师也能轻松、快速地输出高可读性、高标准、图文并茂的 PDF 规范文档。

## 核心特性

### 📐 专业排版规范硬编码
- **阅读优先级 (Hierarchy)**：大标题 > 正文 > 说明注脚，系统默认绑定不同层级的字号与字重
- **字体限制 (Typography)**：正文禁止使用花体或手写体，提供"现代黑体"和"标准宋体"
- **对齐防雷 (Alignment)**：长段落正文禁止居中/右对齐，内置 UI 警告系统
- **页面安全区 (Safe Margin)**：A4 画布永久显示红色安全边距线

### 🎨 基础画布与组件系统
- **无限/A4 画布**：白底 + 网格背景，支持缩放和平移
- **智能对齐布线 (Smart Guides)**：元素拖拽时自动吸附（6px 阈值）
- **组件类型**：大标题(Title)、正文(Body)、注脚(Caption)、图片(Image)、图标(Icon)

### 🎯 高级标注系统
- **重点框选 (Highlight)**：支持实线/虚线、颜色切换、粗细调整的矩形透明框
- **指向箭头 (Arrow)**：矢量绘制，支持四象限起始指向切换

### 🔍 真·局部放大系统
- **双圆联动**：Source（目标源）+ Lens（放大镜）+ 公切线光锥投影
- **实时克隆与光学变焦**：1.1x - 4.0x 放大倍率
- **完美公切线光锥投影**：使用反余弦三角函数计算外公切线
- **遮罩防穿透 (Masking)**：ClipPath 将 Source 圆内部从光锥区域中挖空

### 😀 智能 Emoji 词典
- 键值对映射面板，支持添加/修改/删除自定义词条
- 正则负向先行断言自动补全

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言与框架 | Python 3.10+ + PySide6 (6.5.x) |
| 渲染核心 | QGraphicsScene / QGraphicsView |
| 序列化 | JSON 导入/导出 |
| PDF 导出 | QPrinter 300 DPI 高保真渲染 |

## 快速开始

### 环境要求
- Python 3.10 或更高版本
- pip 包管理器

### 安装与运行

```bash
# 1. 克隆项目
git clone https://github.com/1juary/sop-forge.git
cd sop-forge

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动软件
python main.py
```

## 项目结构

```
sop-forge/
├── main.py                          # 入口文件
├── requirements.txt                 # 依赖清单 (PySide6>=6.5.0)
├── README.md                        # 项目说明文档
├── src/
│   ├── __init__.py
│   ├── app.py                       # QApplication 启动 + SOPApplication 类
│   ├── main_window.py               # 主窗口（菜单/工具栏/面板布局/组件添加）
│   ├── scene.py                     # SOPCanvasScene（A4画布/网格/安全边距/Smart Guides）
│   ├── view.py                      # SOPCanvasView（缩放/平移/鼠标交互）
│   ├── serialization.py             # JSON 序列化/反序列化
│   ├── pdf_export.py                # PDF 导出（QPrinter 300 DPI）
│   ├── items/                       # 组件系统
│   │   ├── __init__.py
│   │   ├── base_item.py             # SmartGraphicItemMixin + SOPBaseItem
│   │   ├── text_item.py             # SOPTextItem（Title/Body/Caption + Emoji + 防呆）
│   │   ├── image_item.py            # ImageItem（图片+注脚+自动编号）
│   │   ├── icon_item.py             # IconItem（8种图标+8种标准色）
│   │   ├── highlight_item.py        # HighlightItem（框选标注+虚线/颜色/粗细）
│   │   ├── arrow_item.py            # ArrowItem（四象限指向箭头）
│   │   └── magnifier.py             # 局部放大（Source/Lens/公切线光锥）
│   └── panels/                      # 面板系统
│       ├── __init__.py
│       ├── component_panel.py       # 组件工具箱（点击/拖拽添加）
│       ├── property_panel.py        # 动态属性面板（按组件类型切换 UI）
│       └── emoji_panel.py           # Emoji 词典配置面板
└── resources/
    ├── icons/                       # SVG 图标资源目录
    └── fonts/                       # 字体文件目录
```

## 使用指南

### 添加组件
1. **左侧面板**：点击组件按钮在画布中心添加，或拖拽到指定位置
2. **工具栏**：快速添加常用组件（文本、框选、箭头、放大镜）

### 编辑属性
1. 选中画布上的组件
2. 右侧属性面板自动切换为对应组件的编辑 UI
3. 修改属性后实时生效

### 排版规范检查
- 长段落（>20字）禁止居中/右对齐，系统自动弹出警告并恢复左对齐
- 文本层级绑定固定字号：大标题 20pt、正文 12pt、注脚 9pt

### 导出
- **保存/打开**：`.sop.json` 格式，完整保留画布数据
- **导出 PDF**：一键导出为 300 DPI 高保真 A4 PDF

## 开发指南

### 添加新的组件类型
1. 在 `src/items/` 下创建新文件，继承 `SmartGraphicItemMixin` + `QGraphicsXxxItem`
2. 实现 `to_dict()` 和 `from_dict()` 方法
3. 在 `src/items/__init__.py` 中导出
4. 在 `src/main_window.py` 中添加添加方法和属性面板处理逻辑
5. 在 `src/panels/property_panel.py` 中添加对应的属性组

### 代码规范
- 遵循 PEP 8 编码规范
- Mixin 类不继承 Qt 类型（避免 C++ 多重继承陷阱）
- 所有组件必须实现 `to_dict` / `from_dict` 序列化接口

## 许可证

MIT License

Copyright (c) 2026 SOP Forge
