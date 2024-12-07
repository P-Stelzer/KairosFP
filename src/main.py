import sys
from PySide6.QtWidgets import QApplication

from kui.calendar import InfiniteScrollArea
from kui.balance_sheet import BalanceSheet

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BalanceSheet()
    window.show()

    app.exec()
