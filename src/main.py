import sys
from PySide6.QtWidgets import QApplication

from kui.calendar import InfiniteScrollArea
from kui.balance_sheet import BalanceSheet
# from kui.account_editor import AccountEditor
# from db import Account

if __name__ == "__main__":
    app = QApplication(sys.argv)

    calendar = InfiniteScrollArea()
    calendar.show()

    balance_sheet = BalanceSheet()
    balance_sheet.show()

    app.exec()
