from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QLineEdit,
    QDialog,
    QWidget,
)
import db
from db import Account
import kui.calendar as calendar

class AccountEditor(QDialog):
    def __init__(self, acc: Account) -> None:
        super().__init__()

        self.target_acc = acc

        # container (box)
        self.box = QVBoxLayout(self)

        # account name label (label)
        self.account_name_text_box = QLineEdit()
        self.account_name_text_box.setPlaceholderText("Account name...")
        self.account_name_text_box.setText(acc.name)
        self.box.addWidget(self.account_name_text_box)

        # memo (text box)
        self.account_memo_text_box = QLineEdit()
        self.account_memo_text_box.setPlaceholderText("Enter description...")
        self.account_memo_text_box.setText(acc.description)
        self.box.addWidget(self.account_memo_text_box)

        # min and max balances (text box)
        self.balance_layer = QHBoxLayout()

        # MIN balance
        self.min_balance = QLineEdit()
        self.min_balance.setPlaceholderText("Enter minimum balance...")
        self.amount_validator = QDoubleValidator(0, 999999999.99, 2, self)
        self.amount_validator.setNotation(
            QDoubleValidator.Notation.StandardNotation
        )
        self.min_balance.setValidator(self.amount_validator)
        if acc.min_balance >= 0:
            self.min_balance.setText(
                f"{acc.min_balance//100}.{acc.min_balance%100}"
            )
        self.balance_layer.addWidget(self.min_balance)

        # MAX balance
        self.max_balance = QLineEdit()
        self.max_balance.setPlaceholderText("Enter maximum balance...")
        self.amount_validator = QDoubleValidator(0, 999999999.99, 2, self)
        self.amount_validator.setNotation(
            QDoubleValidator.Notation.StandardNotation
        )
        self.max_balance.setValidator(self.amount_validator)
        if acc.max_balance >= 0:
            self.max_balance.setText(
                f"{acc.max_balance//100}.{acc.max_balance%100}"
            )
        self.balance_layer.addWidget(self.max_balance)
        
        self.box.addLayout(self.balance_layer)
        
        # confirm button (button)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.attempt_confirm)
        self.box.addWidget(self.confirm_button)

        self.setLayout(self.box)

    def attempt_confirm(self):
        # read values from text boxes
        name = self.account_name_text_box.text()
        desc = self.account_memo_text_box.text()
        min = self.min_balance.text()
        max = self.max_balance.text()
        

        # input validation
        if len(min) == 0:
            print("Invlaid input amount")
            return

        # write MIN as an integer
        split_min = min.split(".")
        dollar_min = int(split_min[0])
        cent_min = int(split_min[1]) if len(split_min) > 1 else 0
        serialized_min = (dollar_min * 100) + cent_min

        # write MAX as an integer
        split_max = max.split(".")
        dollar_max = int(split_max[0])
        cent_max = int(split_max[1]) if len(split_max) > 1 else 0
        serialized_max = (dollar_max * 100) + cent_max

        # set values to the stored account
        self.target_acc.name = name
        self.target_acc.description = desc
        self.target_acc.min_balance = serialized_min
        self.target_acc.max_balance = serialized_max

        if self.target_acc.id < 0:
            new_acc = db.register_account(
                self.target_acc.name,
                self.target_acc.description,
                self.target_acc.min_balance,
                self.target_acc.max_balance,
            )
            # calendar.insert_new_event(new_acc) REVISIT THIS TO CONNECT THE ACCOUNT EDITOR TO THE CALENDAR

        else:
            db.alter_accounts(self.target_acc)

        db.commit_changes()
        self.close()