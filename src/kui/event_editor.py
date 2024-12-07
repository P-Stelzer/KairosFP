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
from db import Account, Event, Tag
import kui.calendar as calendar


class EventEditor(QDialog):
    def __init__(self, event: Event) -> None:
        super().__init__()

        self.target_event = event

        self.added_tags: list[int] = list()
        self.removed_tags: list[int] = list()
        self.tag_editor_form = TagSelector(self)

        self.account_selector = AccountSelector(self)
        self.account_changes: dict[int, int] = dict()
        # None - no change
        # 0 - flip cr/dr
        # 1 - add as debit
        # 2 - add as credit
        # -1 - remove credit account
        # -2 - remove debit account

        # container (box)
        self.box = QVBoxLayout(self)
        self.top_layer = QHBoxLayout()

        # WRAPPER: TOP_LAYER {

        # event name label (label)
        self.event_name_text_box = QLineEdit()
        self.event_name_text_box.setPlaceholderText("Event name...")
        self.event_name_text_box.setText(event.name)
        self.top_layer.addWidget(self.event_name_text_box)

        # tag edit (button)
        self.add_tag_button = QPushButton("Edit Tags")
        self.add_tag_button.clicked.connect(self.launch_tag_editor_form)
        self.top_layer.addWidget(self.add_tag_button)

        # event color (button)
        self.event_color_button = QPushButton("Select Event Color")
        self.top_layer.addWidget(self.event_color_button)

        self.box.addLayout(self.top_layer)
        # }

        # amount (text box)
        self.event_amount_text_box = QLineEdit()
        self.event_amount_text_box.setPlaceholderText("Enter amount...")
        self.amount_validator = QDoubleValidator(0, 999999999.99, 2, self)
        self.amount_validator.setNotation(
            QDoubleValidator.Notation.StandardNotation
        )
        self.event_amount_text_box.setValidator(self.amount_validator)
        if event.amount >= 0:
            self.event_amount_text_box.setText(
                f"{event.amount//100}.{event.amount%100}"
            )
        self.box.addWidget(self.event_amount_text_box)

        # memo (text box)
        self.event_memo_text_box = QLineEdit()
        self.event_memo_text_box.setPlaceholderText("Enter memo...")
        self.event_memo_text_box.setText(event.memo)
        self.box.addWidget(self.event_memo_text_box)

        # associated account (list of accounts)
        self.box.addWidget(QLabel("Accounts"))
        self.account_list = QVBoxLayout()
        self.account_list.setSpacing(0)
        self.box.addLayout(self.account_list)
        for account_id, is_credit in self.target_event.accounts:
            self.account_list.addWidget(
                AccountEventItem(self, db.ACCOUNTS[account_id], is_credit)
            )
        add_account_button = QPushButton("+")
        add_account_button.clicked.connect(self.account_selector.exec)
        self.box.addWidget(add_account_button)

        # add account (button)

        # confirm button (button)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.attempt_confirm)
        self.box.addWidget(self.confirm_button)

        self.setLayout(self.box)

    def launch_tag_editor_form(self):
        self.tag_editor_form.exec()

    def attempt_confirm(self):
        for key, value in self.account_changes.items():
            print(db.ACCOUNTS[key].name, value)
        name = self.event_name_text_box.text()
        amount = self.event_amount_text_box.text()
        memo = self.event_memo_text_box.text()
        if len(amount) == 0:
            print("Invlaid input amount")
            return

        split_amount = amount.split(".")
        dollar_amount = int(split_amount[0])
        cent_amount = int(split_amount[1]) if len(split_amount) > 1 else 0
        serialized_amount = (dollar_amount * 100) + cent_amount

        self.target_event.name = name
        self.target_event.memo = memo
        self.target_event.amount = serialized_amount

        for tag_id in self.removed_tags:
            self.target_event.tag_ids.remove(tag_id)
        for tag_id in self.added_tags:
            self.target_event.tag_ids.append(tag_id)

        altered_accounts: list[int] = list()
        removed_accounts: list[int] = list()
        added_accounts: list[tuple[int, bool]] = list()
        for i, (account_id, is_credit) in enumerate(self.target_event.accounts):
            match self.account_changes.get(account_id):
                case None:
                    continue
                case 0:
                    self.target_event.accounts[i] = (account_id, not is_credit)
                    altered_accounts.append(account_id)
                case -1 | -2:
                    self.target_event.accounts.pop(i)
                    removed_accounts.append(account_id)
                    
        for account_id, change in self.account_changes.items():
            if change > 0:
                self.target_event.accounts.append((account_id, change == 2))
                added_accounts.append((account_id, change == 2))

        if self.target_event.id < 0:
            new_event = db.insert_event(
                self.target_event.date,
                self.target_event.amount,
                self.target_event.name,
                self.target_event.memo,
                self.target_event.accounts,
                self.target_event.tag_ids,
            )
            calendar.insert_new_event(new_event)

        else:
            db.alter_events(self.target_event)
            db.remove_tags_from_event(self.target_event.id, self.removed_tags)
            db.add_tags_to_event(self.target_event.id, self.added_tags)
            db.toggle_account_type_for_event(
                self.target_event.id, altered_accounts
            )
            db.remove_accounts_from_event(
                self.target_event.id, removed_accounts
            )
            db.add_accounts_to_event(self.target_event.id, added_accounts)
            calendar.refresh_day(self.target_event.date)

        db.commit_changes()
        self.close()

    def add_account(self, account: Account) -> None:
        self.account_list.addWidget(AccountEventItem(self, account, True))

        match self.account_changes.get(account.id):
            case None:
                self.account_changes[account.id] = 2
            case -1:
                self.account_changes.pop(account.id)
            case -2:
                self.account_changes[account.id] = 0

    def remove_account(self, account_item: "AccountEventItem") -> None:
        self.account_list.removeWidget(account_item)
        account_item.deleteLater()

        match self.account_changes.get(account_item.account.id):
            # If not in changes: mark for deletion and save type
            case None:
                self.account_changes[account_item.account.id] = (
                    account_item.crdr_button.is_credit - 2
                )
            # If added: remove from changes
            case 1 | 2:
                self.account_changes.pop(account_item.account.id)
            # If type changed: mark for deletion and save original type
            case 0:
                self.account_changes[account_item.account.id] = (
                    not account_item.crdr_button.is_credit
                ) - 2

    def flip_account(self, account: Account) -> None:
        match self.account_changes.get(account.id):
            case None:
                self.account_changes[account.id] = 0
            case 1:
                self.account_changes[account.id] = 2
            case 2:
                self.account_changes[account.id] = 1
            case 0:
                self.account_changes.pop(account.id)

    def close(self) -> bool:
        for key, value in self.account_changes.items():
            print(db.ACCOUNTS[key].name, value)
        return super().close()


class TagSelector(QDialog):
    def __init__(self, event_editor: EventEditor) -> None:
        super().__init__()

        self.event_editor = event_editor

        self.tags_layout = QVBoxLayout(self)

        # clicking tag from list adds it to that specific event
        for tag in db.fetch_all_registered_tags():
            tag_button = TagSelectorButton(
                self, tag, tag.id in self.event_editor.target_event.tag_ids
            )
            self.tags_layout.addWidget(tag_button)


class TagSelectorButton(QPushButton):
    def __init__(
        self, tag_editor: TagSelector, tag: Tag, is_event_member: bool
    ):
        super().__init__()

        self.tag_editor = tag_editor
        self.tag = tag
        self.is_event_member = is_event_member
        self.is_activated = is_event_member

        self.update_text()

        self.clicked.connect(self.toggle_tag)

    def update_text(self):
        if self.is_activated:
            self.setText(f"Remove {self.tag.name}")
        else:
            self.setText(f"Add {self.tag.name}")

    def toggle_tag(self):
        self.is_activated = not self.is_activated
        self.update_text()

        match (self.is_event_member, self.is_activated):
            case (True, True):
                self.tag_editor.event_editor.removed_tags.remove(self.tag.id)
            case (True, False):
                self.tag_editor.event_editor.removed_tags.append(self.tag.id)
            case (False, True):
                self.tag_editor.event_editor.added_tags.append(self.tag.id)
            case (False, False):
                self.tag_editor.event_editor.added_tags.remove(self.tag.id)


class AccountSelector(QDialog):
    def __init__(self, event_editor: EventEditor) -> None:
        super().__init__()

        self.event_editor = event_editor

        layout = QVBoxLayout(self)
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        self.account_buttons: list[AccountSelectorButton] = list()
        for account in db.fetch_all_registered_accounts():
            button = AccountSelectorButton(
                self,
                account,
                any(
                    t[0] == account.id
                    for t in event_editor.target_event.accounts
                ),
            )
            self.account_buttons.append(button)

    def add_account(self, account: Account):
        self.close()
        self.event_editor.add_account(account)

    def exec(self) -> int:
        self.rebuild()
        return super().exec()

    def rebuild(self):
        for button in self.account_buttons:
            self.grid.removeWidget(button)

        num_columns = (len(self.account_buttons) + 7) // 8
        num_rows = (len(self.account_buttons) // num_columns) + (
            1 if len(self.account_buttons) % num_columns else 0
        )

        next_button = iter(self.account_buttons)
        for col in range(num_columns):
            for row in range(num_rows):
                button = next(next_button)

                if button is None:
                    break

                if button.is_active():
                    self.grid.addWidget(button, row, col)
                    button.setVisible(True)
                else:
                    button.hide()


class AccountSelectorButton(QPushButton):
    def __init__(
        self,
        account_selector: AccountSelector,
        account: Account,
        is_member: bool,
    ) -> None:
        super().__init__()

        self.account_selector = account_selector
        self.is_member = is_member
        self.account = account
        self.setText(account.name)
        self.clicked.connect(self.add_account)

    def add_account(self):
        self.account_selector.add_account(self.account)

    def is_active(self) -> bool:
        changes = self.account_selector.event_editor.account_changes.get(
            self.account.id
        )
        return (changes is not None and changes < 0) or (
            changes is None and not self.is_member
        )


class AccountEventItem(QWidget):
    def __init__(
        self, event_editor: EventEditor, account: Account, is_credit: bool
    ) -> None:
        super().__init__()

        self.event_editor = event_editor
        self.account = account

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(account.name))
        self.crdr_button = CrDrToggleButton(self, is_credit)
        layout.addWidget(self.crdr_button)
        remove_button = QPushButton("-")
        remove_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        remove_button.clicked.connect(self.remove_self)
        layout.addWidget(remove_button)

    def remove_self(self):
        self.event_editor.remove_account(self)


class CrDrToggleButton(QPushButton):
    def __init__(self, account_item: AccountEventItem, is_credit: bool) -> None:
        super().__init__(account_item)

        self.account_item = account_item

        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )

        self.is_credit = is_credit
        self.update()
        self.clicked.connect(self.toggle)

    def toggle(self):
        self.is_credit = not self.is_credit
        self.update()
        self.account_item.event_editor.flip_account(self.account_item.account)

    def update(self):
        if self.is_credit:
            self.setText("Cr")
        else:
            self.setText("Dr")
