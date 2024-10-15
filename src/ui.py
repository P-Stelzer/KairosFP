from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt


class Week(QHBoxLayout):
    def __init__(self, n) -> None:
        super().__init__()

        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # day_row_layout = QHBoxLayout()
        # day_row_layout.setSpacing(0)
        # day_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.setLayout(day_row_layout)
        self.setSpacing(0)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for _ in range(7):
            day_button = QPushButton(str(n))
            day_button.setStyleSheet("border-radius : 0; border : 2px solid black")
            day_button.setMinimumSize(100, 100)
            # day_row_layout.addWidget(day_button)
            self.addWidget(day_button)


class InfiniteScrollArea(QScrollArea):
    def __init__(self) -> None:
        super().__init__()

        self.setWidgetResizable(True)

        area_widget = QWidget()
        # area_widget.setSizePolicy(
        #     QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        # )
        self.area_layout = QVBoxLayout()
        self.area_layout.setSpacing(0)
        self.area_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        area_widget.setLayout(self.area_layout)
        # area_widget.layout().addWidget(QPushButton("test"))
        # self.area_layout.addStretch()
        # area_widget.setMinimumHeight(500)

        self.setWidget(area_widget)

        self.min = 0
        self.max = 0

        self.slider_max = self.verticalScrollBar().maximum()

        self.verticalScrollBar().valueChanged.connect(self.scrolled)
        self.verticalScrollBar().rangeChanged.connect(self.correct_slider)
        # self.verticalScrollBar().setVisible(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.extend_upwards(5)
        self.extend_downwards(10)
        # self.area_layout.addStretch()
        # self.setWidget(area_widget)
        self.show()

    def scrolled(self, value):
        if value == self.verticalScrollBar().maximum():
            self.extend_downwards(5)
        elif value == self.verticalScrollBar().minimum():
            self.extend_upwards(5)
            # self.verticalScrollBar().setSliderPosition(150)

    def extend_downwards(self, n):
        for _ in range(n):
            # self.area_layout.addWidget(QPushButton(str(self.max)))
            self.area_layout.addLayout(Week(self.max))
            self.max += 1
            # self.setWidget(self.widget())

    def extend_upwards(self, n):
        for _ in range(n):
            self.min -= 1
            self.area_layout.insertLayout(0, Week(self.min))
            # self.area_layout.insertWidget(0, QPushButton(str(self.min)))

    def correct_slider(self, min, max):
        if self.verticalScrollBar().value() == min:
            self.verticalScrollBar().setValue(max - self.slider_max)
        self.slider_max = max
