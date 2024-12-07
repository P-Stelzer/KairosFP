from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
import db


class BalanceSheet(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.account_list = QVBoxLayout(self)
        for account_id in sorted(db.ACCOUNTS.keys()):
            account_entry = QHBoxLayout()
            account = db.ACCOUNTS[account_id]
            account_entry.addWidget(QLabel(account.name))
