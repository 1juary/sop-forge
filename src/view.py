#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画布视图：SOPCanvasView
如果我们在之前把 Scene（场景）比作“舞台和演员（数据）”，那么 View（视图）就是**“摄像机和用户的双手”**。舞台上的东西怎么显示、能放多大、怎么用鼠标拖拽、怎么用快捷键，全都是这个类在管。
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
        #将之前创建好的 scene（数据舞台）装载到当前的 view（摄像机）里，同时认领父级窗口（挂载到对象树上防内存泄漏）。
        super().__init__(scene, parent)
        #Antialiasing（抗锯齿）：Qt 默认画斜线或圆圈时，边缘会有马赛克般的“狗牙（锯齿）”。开启这个开关，系统会用边缘半透明像素过滤，让所有矢量图形极其平滑。
        #SmoothPixmapTransform（平滑图像变换）：当你在画布上把一张图片放大或缩小时，开启它会使用“双线性插值算法”，让图片尽量保持柔和，而不是变成粗糙的像素块。
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform) 
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)        #不管哪里动了，直接把整个屏幕画面全部重新算一遍画出来

        self.setDragMode(QGraphicsView.RubberBandDrag)         #设置视图的默认拖拽模式为“橡皮筋模式”（Rubber Band）。就是允许用户在空白处按下鼠标左键并拖动，画出一个半透明的虚线框，用来批量选中框内的多个组件。
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  #当用户用鼠标滚轮缩放画布时，保持鼠标指针所在位置不动，画布以那个点为中心进行放大或缩小。

        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)  #这三行代码强行关闭了水平和垂直的滚动条，并且去掉了边框。没有了丑陋的系统滚动条，用户将完全依赖鼠标中键平移和滚轮缩放来导航画布，沉浸感极强。
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setStyleSheet("QGraphicsView { border: none; background-color: #cbd5e1; }")
        self.setAcceptDrops(True)  #打通与操作系统的桥梁，允许用户从桌面上把文件（图片、文字）直接拖进这个窗口里。

    # 这是在给后面要写的滚轮事件（缩放）和鼠标事件（平移）准备记录本（状态变量）。
        self._zoom = 1.0         # 当前缩放倍率（100%）
        self._min_zoom = 0.3     # 最小只能缩到 30%
        self._max_zoom = 5.0     # 最大只能放大到 500%
        # 平移相关状态记录
        self._is_panning = False # 记录目前是否按下了鼠标中键正在平移
        self._pan_start = None   # 记录平移开始时，鼠标按下的初始坐标

    #鼠标滚轮缩放（Zoom In / Zoom Out）核心逻辑
    def wheelEvent(self, event):    #重写了 Qt 原生的 QWheelEvent（滚轮事件）。只要用户的鼠标在这个画布范围内滚动了滚轮，操作系统就会向软件发送一个信号，这段代码就会立刻拦截并接管这个信号。
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87  #event.angleDelta().y()：获取滚轮滚动的方向和力度。大于 0 代表向前推（向上滚），通常代表“放大”；小于 0 代表向后拉（向下滚），代表“缩小”。
        new_zoom = self._zoom * factor  #self._zoom 是我们在 __init__ 里初始化的变量(1.0)
        if self._min_zoom <= new_zoom <= self._max_zoom:  #预测的 new_zoom 是否落在我们规定的安全范围内
            self._zoom = new_zoom
            self.scale(factor, factor)    #Qt 框架中 QGraphicsView 类原生自带的内置函数。数据与显示的分离

    #“鼠标中键拖拽平移（Panning）”的三部曲中的第一部：按下鼠标（触发状态）。
    #重写并拦截了Qt 的原生鼠标按下事件。只要用户的鼠标指针在画布区域内，并且按下了任何一个鼠标按键（左、中、右），这个函数就会被瞬间唤醒，并把包含按键信息的 event 对象传进来。
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:  #判断是否鼠标中键
            self._is_panning = True  #后续的鼠标移动事件（mouseMoveEvent）看到这个标志位是 True，才会去移动画面。
            self._pan_start = event.pos()  #event.pos() 是鼠标按下那一瞬间，相对于视图窗口的精确 (X, Y) 像素坐标
            self.setCursor(Qt.ClosedHandCursor)  #瞬间把鼠标光标从普通的箭头，变成一个“紧紧攥住的小手”图标
            event.accept()  #事件的“截流”，告诉 Qt 底层系统：“这个中键按下的事件，我已经亲手处理完毕了，不要再把它往上传递给别的组件了。”
            return
        #如果第一步查身份证时，发现按下的不是中键（比如是左键），就会跳过 if 块，来到这里。
        #super() 会把这个左键事件原封不动地还给父类（QGraphicsView）。请父类按照原厂设定处理这个事件！
        super().mousePressEvent(event) 

    #鼠标移动（计算并执行位移）”处理“手在按住不放的情况下，移动了多远，画布就要跟着挪动多远”。
    def mouseMoveEvent(self, event):
        if self._is_panning and self._pan_start:  #只有当 _is_panning 为 True（确实按下了中键），并且 _pan_start 有值（确实记录了起点）时，才执行平移。普通的不按按键的鼠标乱晃，直接无视。
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()  #把 _pan_start 更新为当前的 event.pos()，就像是接力跑：算完这一次 5 像素的位移后，立刻把现在的位置当成下一次计算的起点。这样系统就能保证每次计算出来的 delta 都是细微、平滑的一小段位移。
            #这是 Qt 框架操作画面的底层逻辑。虽然我们之前用代码隐藏了滚动条，但它在内存里依然存在，并且实际控制着摄像机的视野位置。
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)
    #松开鼠标（结束状态与清理现场）”
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self._pan_start = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    #这是重写了 Qt 的右键菜单事件。第一步先去场景（Scene）里问：“现在有哪些组件被选中了？” 如果用户是在一块毫无内容的空白处点的右键（not items），就直接 return 结束，什么都不弹。
    def contextMenuEvent(self, event):
        items = self.scene().selectedItems()
        if not items:
            return
        #实例化一个空的菜单对象，并直接塞入一段 QSS 代码。
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: white; border: 1px solid #e2e8f0; border-radius: 6px; } QMenu::item { padding: 6px 24px; color: #1e293b; } QMenu::item:selected { background-color: #f1f5f9; color: #0ea5e9; }")

        # 【重写】置于顶层逻辑 — 级联提升光锥
        def bring_to_front():
            #这段代码遍历了画布上的所有组件，拿到它们当前的 Z 轴高度（zValue），然后找出最大值。
            max_z = max([i.zValue() for i in self.scene().items()] + [0])  #后面的 + [0] 是个非常精妙的 Python 容错技巧：如果画布上什么都没有，max() 会报错，加了个 [0] 就保证了保底高度是 0。
            for i in items: #选中的元素
                i.setZValue(max_z + 1) # 把当前选中组件的高度，设为“全场最高 + 1”，确保它绝对盖住别人
                # 针对放大镜组件，级联提升光锥
                if hasattr(i, '_cone') and i._cone:
                    i._cone.setZValue(max_z + 0.9)
                elif type(i).__name__ == "DraggableNode":  #放大镜的取景框
                    for other in self.scene().items(): #遍历画布上的所有组件，找到那些以这个取景框为 source 的光锥，把它们的高度也提升到 max_z + 0.9，确保它们永远比取景框略微矮一点，但又高于其他所有组件。
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

        action_top = menu.addAction("⬆ 置于顶层")  #在一张白纸上画了一个按钮，并且给它贴上了文本标签
        action_top.triggered.connect(bring_to_front) #把鼠标给按钮的信号，绑定到函数上

        action_bottom = menu.addAction("⬇ 置于底层")
        action_bottom.triggered.connect(send_to_back)

        #在右键菜单里画一条横向的灰色细线。把“置顶/置底”这类图层操作，与“冻结/解冻”这类状态操作在视觉上隔开，让菜单看起来更专业、更有条理。
        menu.addSeparator() 
        # 冻结/解冻
        all_frozen = all(getattr(i, '_is_frozen', False) for i in items)  #all() 是 Python 的内置函数。它会检查一个列表里的所有元素，只有当里面所有的元素全都是 True 时，它才返回 True。只要混进去哪怕一个 False，它立刻返回 False。
        if all_frozen:
            action_unfreeze = menu.addAction("📍 解冻")  #如果刚才的判定结果是“全都被冻结了”。那么菜单里就只显示“解冻”按钮。
            action_unfreeze.triggered.connect(lambda: self._toggle_freeze(items, False)) #要调用的真实函数是 self._toggle_freeze(items, True)，它需要知道冻结哪些东西（items）和设置成什么状态（True/False）。这里lambda函数是“没有名字、只有一行、用完即抛”的微型函数
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
