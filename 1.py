import sys
from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow

app = QApplication(sys.argv)

# 强制将全局风格设置为 Fusion
app.setStyle('macintosh')  # 这行代码设置了应用程序的风格为 macOS 风格，确保在 macOS 系统上也能保持一致的外观。对于其他系统，Fusion 风格仍然会被应用。

window = QMainWindow()
button = QPushButton("我是一个 Fusion 风格的按钮", window)
button.resize(200, 50)
button.move(50, 50)

window.resize(300, 150)
window.show()

# 启动事件循环
sys.exit(app.exec())