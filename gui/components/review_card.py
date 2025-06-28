import sys
from datetime import datetime, timedelta
from typing import Union

from PySide6.QtGui import QFont, QPixmap, QImage, Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout
from qfluentwidgets import SimpleCardWidget, AvatarWidget

from gui.common import MyLabel, MultiLineElideLabel

class ReviewCard(SimpleCardWidget):
    AVATAR_SIZE = 50
    def __init__(self, parent=None):
        super().__init__(parent)


        self.avatar_label = AvatarWidget(self)
        self.avatar_label.setFixedSize(self.AVATAR_SIZE, self.AVATAR_SIZE)
        self.title_label = MultiLineElideLabel("Title", 2,
                                               18,  weight=QFont.Weight.Bold, parent=self)
        self.title_label.setWordWrap(True)
        self.username_label = MyLabel("Username", parent = self)
        font = self.username_label.font()
        font.setItalic(True)
        self.username_label.setFont(font)
        self.date_label = MyLabel("Date", parent = self)
        self.date_label.setStyleSheet("color: gray")
        self.body_label = MultiLineElideLabel("Comment", 4, parent = self)
        self.body_label.setWordWrap(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignTop)

        title_layout = QHBoxLayout(self)
        title_layout.addWidget(self.avatar_label)

        title_sub_layout = QVBoxLayout(self)
        title_sub_layout.setSpacing(0)
        title_sub_layout.addStretch()
        title_sub_layout.addWidget(self.title_label)
        user_layout = QHBoxLayout(self)
        user_layout.setSpacing(6)
        user_layout.addWidget(self.username_label)
        user_layout.addWidget(MyLabel("·", weight=QFont.Weight.Bold, parent=self))
        user_layout.addWidget(self.date_label)
        user_layout.addStretch()

        title_sub_layout.addLayout(user_layout)
        title_sub_layout.addStretch()

        title_layout.addLayout(title_sub_layout)


        layout.addLayout(title_layout)
        layout.addWidget(self.body_label, stretch = 1, alignment=Qt.AlignmentFlag.AlignTop)

    def setUsername(self, username):
        self.username_label.setText(username)

    def setDate(self, date: datetime):
        now = datetime.now()
        delta = now - date

        if delta < timedelta(minutes=1):
            seconds = int(delta.total_seconds())
            date_str = "Just now" if seconds < 5 else f"{seconds} seconds ago"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() // 60)
            date_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() // 3600)
            date_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            date_str = date.strftime("%B %d, %Y")

        self.date_label.setText(date_str)

    def setBody(self, body: str):
        self.body_label.setText(body)

    def setAvatar(self, avatar: Union[QPixmap, str, QImage]):
        self.avatar_label.setImage(avatar)
        self.avatar_label.setFixedSize(self.AVATAR_SIZE, self.AVATAR_SIZE)
        self.avatar_label.setRadius(self.AVATAR_SIZE//2)

    def setTitle(self, title: str):
        self.title_label.setText(title)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    path = r"D:\Program\Zerokku\demo\avatar.png"
    username = "DontKnow492"
    title = "Cowboy Bebop is a smash-hit jam session"
    date = datetime.now()
    comment = "Overall a great show for me with good main charecters. If you cannot stand a slow pace though, it may not be for you."
    card = ReviewCard()
    card.setUsername(username)
    card.setDate(date)
    card.setBody(comment)
    card.setAvatar(path)
    card.setTitle(title)
    card.show()
    app.exec()