from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import db
from db import Account
from kui.account_editor import AccountEditor


class BalanceSheet(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.account_list = QVBoxLayout(self)
        self.populate()

        db.subscribe_accounts_changes(self.refresh)

    def populate(self) -> None:
        for account_id in sorted(db.ACCOUNTS.keys()):
            account = db.ACCOUNTS[account_id]
            element = AccountElement(account)
            self.account_list.addWidget(element)

        new_account_button = QPushButton("+")
        new_account_button.clicked.connect(self.create_new)
        self.account_list.addWidget(new_account_button)

    def create_new(self) -> None:
        form = AccountEditor(Account(-1, "", "", 0, 0))
        form.exec()

    def refresh(self) -> None:
        for i in range(self.account_list.count()):
            self.account_list.itemAt(i).widget().deleteLater()

        self.populate()


class AccountElement(QWidget):
    def __init__(self, account: Account) -> None:
        super().__init__()

        self.account = account
        self.account_name = QPushButton(account.name)
        self.account_balance = QLabel(str(account.balance))

        layout = QHBoxLayout(self)
        layout.addWidget(self.account_name)
        layout.addWidget(self.account_balance)

        self.account_name.clicked.connect(self.launch_editor)

        account.subscribe_name_changes(
            lambda _, n: self.account_name.setText(n)
        )
        account.subscribe_balance_changes(
            lambda _, n: self.account_balance.setText(str(n))
        )

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def launch_editor(self) -> None:
        form = AccountEditor(self.account)
        form.exec()

    def show_context_menu(self, position) -> None:
        context_menu = QMenu(self)

        edit_event = QAction("Edit Account", self)
        edit_event.triggered.connect(self.launch_editor)
        context_menu.addAction(edit_event)

        delete_event = QAction("Delete Account", self)
        delete_event.triggered.connect(self.delete_account)
        context_menu.addAction(delete_event)

        context_menu.exec(self.mapToGlobal(position))

    def delete_account(self) -> None:
        db.delete_accounts(self.account)
        db.commit_changes()
