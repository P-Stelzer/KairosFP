from PySide6.QtWidgets import (QPushButton, QVBoxLayout, QLineEdit, QDialog)
import db
from db import Tag

class TagEditor(QDialog):
    def __init__(self, tag: Tag) -> None:
        super().__init__()
        
        self.target_tag = tag
        
        # container (box)
        self.box = QVBoxLayout(self)
        
        # tag name
        self.tag_name_text_box = QLineEdit()
        self.tag_name_text_box.setPlaceholderText("Name...")
        self.tag_name_text_box.setText(tag.name)
        self.box.addWidget(self.tag_name_text_box)
        
        # tag description
        self.tag_description_text_box = QLineEdit()
        self.tag_description_text_box.setPlaceholderText("Description...")
        self.tag_description_text_box.setText(tag.description)
        self.box.addWidget(self.tag_description_text_box)
        
        # confirm button (button)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.attempt_confirm)
        self.box.addWidget(self.confirm_button)
        
    def attempt_confirm(self):
        name = self.tag_name_text_box.text()
        description = self.tag_description_text_box.text()

        self.target_tag.name = name
        self.target_tag.description = description

        if self.target_tag.id < 0:
            new_tag = db.register_tag(
                self.target_tag.name,
                self.target_tag.description,
            )

        else:
            db.alter_tags(self.target_tag)

        db.commit_changes()
        self.close()
