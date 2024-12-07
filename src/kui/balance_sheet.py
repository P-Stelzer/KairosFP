from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
import db
from db import Account
from kui.account_editor import AccountEditor


class BalanceSheet(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.lay = QVBoxLayout()
        self.setLayout(self.lay)

        header = QLabel("Accounts")
        header.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
            )
        )
        self.lay.addWidget(header)

        self.account_list = QVBoxLayout()
        self.populate()
        self.lay.addLayout(self.account_list)

        self.lay.addItem(
            QSpacerItem(
                0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
            )
        )

        new_account_button = QPushButton("+")
        new_account_button.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
            )
        )
        new_account_button.clicked.connect(self.create_new)
        self.lay.addWidget(new_account_button)

        db.subscribe_accounts_changes(self.refresh)

    def populate(self) -> None:
        for account_id in sorted(db.ACCOUNTS.keys()):
            account = db.ACCOUNTS[account_id]
            element = AccountElement(account)
            self.account_list.addLayout(element)

    def create_new(self) -> None:
        form = AccountEditor(Account(-1, "", "", 0, 0))
        form.exec()

    def refresh(self) -> None:
        for _ in range(self.account_list.count()):
            self.account_list.takeAt(0).layout().deleteLater()

        self.populate()


class AccountElement(QHBoxLayout):
    def __init__(self, account: Account) -> None:
        super().__init__()

        self.account = account
        self.account_name = QPushButton(account.name)
        self.spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.account_balance = QLabel(
            f"$ {account.balance//100}.{account.balance%100}"
        )

        self.addWidget(self.account_name)
        self.addSpacerItem(self.spacer)
        self.addWidget(self.account_balance)

        self.account_name.clicked.connect(self.launch_editor)

        self.name_listener = account.subscribe_name_changes(
            lambda _, n: self.account_name.setText(n)
        )
        self.balance_listener = account.subscribe_balance_changes(
            lambda _, n: self.account_balance.setText(str(n))
        )

        self.account_name.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.account_name.customContextMenuRequested.connect(
            self.show_context_menu
        )

    def deleteLater(self) -> None:
        self.account_name.deleteLater()
        self.account_balance.deleteLater()
        self.account.unsubscribe_name_changes(self.name_listener)
        self.account.unsubscribe_balance_changes(self.balance_listener)
        return super().deleteLater()

    def launch_editor(self) -> None:
        form = AccountEditor(self.account)
        form.exec()

    def show_context_menu(self, position) -> None:
        context_menu = QMenu(self.account_name)

        edit_event = QAction("Edit Account", self.account_name)
        edit_event.triggered.connect(self.launch_editor)
        context_menu.addAction(edit_event)

        delete_event = QAction("Delete Account", self.account_name)
        delete_event.triggered.connect(self.delete_account)
        context_menu.addAction(delete_event)

        context_menu.exec(self.account_name.mapToGlobal(position))

    def delete_account(self) -> None:
        db.delete_accounts(self.account)
        db.commit_changes()
