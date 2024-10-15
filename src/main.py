import sys
from PySide6.QtWidgets import QApplication
import ui

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ui.InfiniteScrollArea()
    window.show()

    app.exec()
