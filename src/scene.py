#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心场景：SOPCanvasScene (多页连排)
“高内聚”是好代码的标志，意思是“把属于同一个任务的所有细节都集中在自己身上”。
在 SOPCanvasScene 中：
它自己知道 A4 纸有多大（A4_WIDTH, A4_HEIGHT）。
它自己知道怎么算网格线（drawBackground）。
它自己掌握了极其复杂的磁吸对齐算法（calculate_snap）。
这些逻辑没有外溢到程序的其他地方。如果有任何关于“画布背景怎么画”的 Bug，你只需要来这个文件里找，绝对不用去翻 MainWindow 的代码。
它给外部（比如主窗口）留下了几个极其简单的“遥控器按钮”：
add_page()：主窗口只要调用这个，它内部就会自动算好新的高度并更新边界。
set_show_grid(True)：主窗口一按，它自己就会重绘背景加上网格。
被动等待调用的“零件”属性
注意看这个文件的最底部，它没有写 if __name__ == "__main__": 然后弹出一个窗口。
这就说明，它生来就不是为了单独运行的。它就是一个“零件供应商”
"""

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF

from src.items.magnifier import MagnifierConeItem


class SOPCanvasScene(QGraphicsScene):
    A4_WIDTH, A4_HEIGHT = 794, 1123
    SAFE_MARGIN = 50
    PAGE_SPACING = 60

    def __init__(self, parent=None): #默认情况下是none，这里是MainWindow，这里被MainWindow调用了
        super().__init__(parent) #调用父类的构造函数，初始化场景
        self._show_grid = True
        self._show_safe_margin = True
        self._grid_size = 20
        self._snap_threshold = 6.0
        self.snap_lines = []
        self.num_pages = 1
        self.setBackgroundBrush(QBrush(QColor("#cbd5e1"))) #不是 A4 纸的颜色，而是纸张外面那一整片巨大空间的“桌面颜色”（一种偏灰蓝的石板色）。这样才能衬托出 A4 纸是白色的。
        self._update_scene_rect()

    def _update_scene_rect(self):
        self.setSceneRect(0, 0, self.A4_WIDTH, self.num_pages * self.A4_HEIGHT + (self.num_pages - 1) * self.PAGE_SPACING)
        self.update() #重绘

    def add_page(self):
        self.num_pages += 1
        self._update_scene_rect()

    def set_num_pages(self, num):
        self.num_pages = max(1, num)
        self._update_scene_rect()

    def drawBackground(self, painter, rect): #rectangle，表示需要重绘的区域
        super().drawBackground(painter, rect)
        for i in range(self.num_pages):
            # 计算第 i 页纸的绝对坐标和大小
            page_rect = QRectF(0, i * (self.A4_HEIGHT + self.PAGE_SPACING), self.A4_WIDTH, self.A4_HEIGHT)
            # 【极其关键的性能优化：视椎体裁剪】这里是在做判断：“我要画的这页纸（page_rect），和屏幕当前需要刷新的区域（rect）有重叠吗？”
            if not rect.intersects(page_rect):
                continue
            # 画阴影,效果：先在右下角偏移的位置涂上一层半透明的灰黑底色，然后再把纯白色的 A4 纸 Qt.white 盖在正中间。利用视觉错觉，一张拥有完美悬浮立体阴影的 A4 纸就跃然纸上了。
            painter.fillRect(page_rect.translated(8, 8), QColor(0, 0, 0, 15))
            # 画白纸本体
            painter.fillRect(page_rect, Qt.white)

            if self._show_grid: #__init__里设定的网格开关
                ## 准备一支浅灰蓝色的细笔
                pen = QPen(QColor("#f1f5f9"), 1)
                painter.setPen(pen)
                # 画纵向的竖线 (X 轴移动，从上画到下)
                for x in range(int(page_rect.left()), int(page_rect.right()), self._grid_size):
                    painter.drawLine(x, int(page_rect.top()), x, int(page_rect.bottom()))
                # 画横向的横线 (Y 轴移动，从左画到右)
                for y in range(int(page_rect.top()), int(page_rect.bottom()), self._grid_size):
                    painter.drawLine(int(page_rect.left()), y, int(page_rect.right()), y)

    def drawForeground(self, painter, rect): #绘制在最顶层的“辅助UI”
        super().drawForeground(painter, rect) #惯例调用父类方法。确保 Qt 底层如果有一些默认的前景绘制逻辑，依然能够正常运行。如果不调用，是不是会导致某些默认的前景元素（比如选中框、拖动时的线条等）无法显示？需要测试一下。
        if self._show_safe_margin: #__init__里设定的安全边距开关
            pen = QPen(QColor("#f43f5e"), 1, Qt.DashLine) ## 设置画笔：玫瑰红 (#f43f5e)，粗细为 1，线条样式为虚线 (DashLine)
            painter.setPen(pen)
            # 核心数学计算：精准算出每一页内部那个安全框的坐标和大小
            for i in range(self.num_pages):
                m_rect = QRectF(
                    self.SAFE_MARGIN, # X起点：向右缩进安全距离
                    i * (self.A4_HEIGHT + self.PAGE_SPACING) + self.SAFE_MARGIN, # Y起点：算出当前页的顶部在哪，再向下缩进安全距离
                    self.A4_WIDTH - 2*self.SAFE_MARGIN, # 框的宽度：总宽度减去左右两边的安全距离
                    self.A4_HEIGHT - 2*self.SAFE_MARGIN # 框的高度：总高度减去上下两边的安全距离
                    )
                if rect.intersects(m_rect): #先判断这个红框在不在当前用户的视野（rect）里，如果在，才调用 drawRect 画出来。
                    painter.drawRect(m_rect)
        if self.snap_lines:
            pen = QPen(QColor("#0ea5e9"), 1, Qt.DashLine) ## 设置画笔：天蓝色 (#0ea5e9)，粗细为 1，线条样式为虚线 (DashLine)
            painter.setPen(pen) #把画笔交给画家
            # 遍历列表里所有的线条数据，直接画出来
            for line in self.snap_lines:
                painter.drawLine(line)

        # 大头针视觉反馈：在冻结组件右上角绘制 📌
        pin_font = QFont("Segoe UI Emoji", 14) # 准备字体：使用系统自带的 Emoji 字体，字号 14
        painter.setFont(pin_font)
        # 遍历当前画布上的【所有】组件
        for item in self.items():
            if getattr(item, '_is_frozen', False): #getattr 保证了如果没有这个属性，就默认返回 False
                br = item.sceneBoundingRect()
                painter.drawText(br.right() - 10, br.top() + 10, "📌") #算出组件的绝对边界后，走到最右边向左退 10 像素，走到最上边向下退 10 像素。
    
    #经典的 setter 方法，设置完属性后调用 update() 触发重绘，确保界面及时反映出最新的状态。
    def set_show_grid(self, show: bool):
        self._show_grid = show
        self.update() # 是 Qt 中极其高频的函数，它告诉系统“我的数据变了，请尽快帮我重画一下屏幕”。

    def set_show_safe_margin(self, show: bool):
        self._show_safe_margin = show
        self.update() # 同上，触发重新绘制（触发 drawForeground）

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.snap_lines:
            self.snap_lines.clear()
            self.update()

    def calculate_snap(self, item, new_pos):
        threshold = self._snap_threshold # 提取触发吸附的临界距离（之前设置的 6 个像素）
        item_center = new_pos + item.boundingRect().center() # 算出被拖动组件当前的【绝对中心坐标】
        best_x, best_y = new_pos.x(), new_pos.y() # new_pos 是组件即将要移动到的新位置。
        # 先把整个场景扫了一遍，建立了一个包含所有边缘和中心点的巨大数字池（snap_lines_x 和 snap_lines_y）
        snap_lines_x = [0, self.A4_WIDTH / 2, self.A4_WIDTH] # 默认把纸张的最左边、最中间、最右边作为X轴参考线
        snap_lines_y = []
        for i in range(self.num_pages):
            py = i * (self.A4_HEIGHT + self.PAGE_SPACING) # 循环遍历每一页纸，把它们的顶部、中间、底部加入到 Y 轴参考线中
            snap_lines_y.extend([py, py + self.A4_HEIGHT / 2, py + self.A4_HEIGHT])

        for other in self.items():
            # 遍历画布上的所有其他东西。跳过自己、非图形组件、和被隐藏的组件，这是一个“卫语句（Guard Clause）”
            if other == item or not isinstance(other, QGraphicsItem) or not other.isVisible():
                continue #continue 触发，直接放弃这个 other，去检查画布上的下一个东西。
            # 业务逻辑：排除掉这些特殊的标记物，它们不能作为排版对齐的标准
            if type(other).__name__ in ["MagnifierConeItem", "DraggableNode", "LensItem"]:
                continue
            orect = other.sceneBoundingRect() # 获取这个其他组件的绝对边界
            # 将其他组件的 左、中、右 加入 X 轴参考池
            snap_lines_x.extend([orect.left(), orect.center().x(), orect.right()])
            # 将其他组件的 上、中、下 加入 Y 轴参考池
            snap_lines_y.extend([orect.top(), orect.center().y(), orect.bottom()])

        self.snap_lines.clear()# 清空上一帧画的旧辅助线

        for ref_x in snap_lines_x: # 遍历所有的 X 轴参考线
            # 拿当前拖动物体的【中心、左侧、右侧】去分别做比较
            for anchor_x in [item_center.x(), new_pos.x(), new_pos.x() + item.boundingRect().width()]:
                if abs(ref_x - anchor_x) < threshold: # 如果距离小于 6 像素
                    # 发生吸附！修正 best_x，强行把组件挪到参考线上
                    best_x = new_pos.x() + (ref_x - anchor_x) 
                    # 记录一根贯穿上下的线，准备在屏幕上画出来给用户看
                    self.snap_lines.append(QLineF(ref_x, 0, ref_x, self.sceneRect().height()))
                    break # X轴只要吸附到了一根线，就不再寻找了
            if self.snap_lines:
                break

        # Y 轴的逻辑与 X 轴完全一致
        for ref_y in snap_lines_y:
            for anchor_y in [item_center.y(), new_pos.y(), new_pos.y() + item.boundingRect().height()]:
                if abs(ref_y - anchor_y) < threshold:
                    best_y = new_pos.y() + (ref_y - anchor_y)
                    self.snap_lines.append(QLineF(0, ref_y, self.A4_WIDTH, ref_y))
                    break
            # 这里有个小细节：如果前面 X 轴吸附了，这里 Y 轴也吸附了，没关系，两个轴可以同时触发对齐
            if len(self.snap_lines) > (1 if best_x != new_pos.x() else 0):
                break

        return QPointF(best_x, best_y) # 最终返回系统修正过的完美坐标，交还给拖拽事件执行移动