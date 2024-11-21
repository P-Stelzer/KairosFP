import sys
from PySide6.QtWidgets import QApplication

from kui.calendar import InfiniteScrollArea

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = InfiniteScrollArea()
    window.show()

    app.exec()
