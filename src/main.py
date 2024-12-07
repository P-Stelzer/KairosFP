import sys
from PySide6.QtWidgets import QApplication

from kui.calendar import InfiniteScrollArea
from kui.balance_sheet import BalanceSheet
# from kui.account_editor import AccountEditor
# from db import Account

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BalanceSheet()
    window.show()

    # acc_edit = AccountEditor(
    #     Account(-1, "", "", 0, 0)
    # )

    # acc_edit.show()

    app.exec()
