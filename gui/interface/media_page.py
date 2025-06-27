import sys
from typing import List

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QPixmap
from qfluentwidgets import PushButton, Pivot, PivotItem, SegmentedWidget, TransparentToolButton, FluentIcon, \
    PopUpAniStackedWidget, FlowLayout, setTheme, Theme
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QFormLayout, QSpacerItem, \
    QSizePolicy
from gui.common import KineticScrollArea, MyLabel, Chip, OutlinedChip, WaitingLabel, MyImageLabel
from gui.components import MediaCardRelationSkeleton, MediaCard, MediaRelationCard, ViewMoreContainer
from gui.components.skeleton import ReviewSkeleton

class OverviewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.content_font_size = 16
        self.content_font_weight = QFont.Normal
        self.recommendation_container_height = 380

        self.description_label = MyLabel("this descriptions", self.content_font_size, self.content_font_weight, parent = self)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.type_label = MyLabel("this type", self.content_font_size, self.content_font_weight, parent = self)
        self.aired_label = MyLabel("this aired", self.content_font_size, self.content_font_weight, parent = self)
        self.status_label = MyLabel("this status", self.content_font_size, self.content_font_weight, parent = self)
        self.season_label = MyLabel("this season", self.content_font_size, self.content_font_weight, parent = self)
        self.source_label = MyLabel("this source", self.content_font_size, self.content_font_weight, parent = self)
        self.rating_label = MyLabel("this rating", self.content_font_size, self.content_font_weight, parent = self)
        self.duration_label = MyLabel("this duration", self.content_font_size, self.content_font_weight, parent = self)

        self.recommendation_container = ViewMoreContainer("Recommendation for you", self)
        self.recommendation_container.setMinimumHeight(self.recommendation_container_height)

        self._init_ui()

    def _init_ui(self):
        font_size = 20
        weight = QFont.Weight.DemiBold
        layout = QGridLayout(self)

        detail_heading = MyLabel("Details", font_size, weight)
        description_heading = MyLabel("Description", font_size, weight)
        description_heading.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(detail_heading, 0, 0)
        layout.addWidget(description_heading, 0, 1)

        form_layout = self._init_form()
        layout.addLayout(form_layout, 1, 0)
        layout.addWidget(self.description_label, 1, 1)
        layout.addWidget(self.recommendation_container, 2, 0, 1, 2)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)

    def _init_form(self):
        form_layout = QFormLayout(self)
        titles = {"Type": self.type_label, "Aired": self.aired_label, "Status": self.status_label,
                "Season": self.season_label, "Source": self.source_label, "Rating": self.rating_label,
                "Duration": self.duration_label}
        for key, value in titles.items():
            #Add to layout
            label = MyLabel(key,self.content_font_size, weight=QFont.Weight.DemiBold, parent = self)
            form_layout.addRow(label, value)

        return form_layout


class ReviewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title_label = MyLabel("Reviews", 20, QFont.Weight.DemiBold, parent=self)
        layout.addWidget(self.title_label)
        layout.setSpacing(40)


        self.skeletons: List[ReviewSkeleton] = [ReviewSkeleton() for i in range(4)]


        for skeleton in self.skeletons:
            skeleton.start()
            layout.addWidget(skeleton)





class SubMediaPage(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title_label = MyLabel(title, 20, QFont.Weight.DemiBold, parent = self)
        self.flow_layout = FlowLayout()
        self.flow_layout.setVerticalSpacing(40)
        self.flow_layout.setHorizontalSpacing(40)

        self.skeletons: List[MediaCardRelationSkeleton] = [MediaCardRelationSkeleton() for i in range(10)]

        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addSpacing(20)
        layout.addLayout(self.flow_layout, stretch=1)

        for skeleton in self.skeletons:
            skeleton.start()
            self.flow_layout.addWidget(skeleton)

    def addCard(self, image: QPixmap, title: str, body: str):
        card = MediaRelationCard(parent=self)
        card.setTitle(title)
        card.setBody(body)

        self.flow_layout.addWidget(card)

class RelationPage(SubMediaPage):
    def __init__(self, parent=None):
        super().__init__("Relations", parent)

class StaffPage(SubMediaPage):
    def __init__(self, parent=None):
        super().__init__("Staff", parent)


class CharacterPage(SubMediaPage):
    def __init__(self, parent=None):
        super().__init__("Characters", parent)


class MediaPage(KineticScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        central_widget = QWidget()
        self.page_layout = QVBoxLayout(central_widget)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.setWidget(central_widget)
        self.setWidgetResizable(True)



        self.banner_size = QSize(self.screen_geometry.width() - 18, int(self.screen_geometry.height() * 0.5))
        self.cover_size = QSize(220, 330)
        self.recommendation_container_height = 380


        self.banner_label = WaitingLabel(parent = self)
        self.banner_label.setFixedSize(self.banner_size)
        self.banner_label.start()
        self.cover_label = WaitingLabel(parent = self)
        self.cover_label.setFixedSize(self.cover_size)
        self.cover_label.start()
        self.title_label = MyLabel("Solo Leveling", 34, QFont.Weight.Bold, parent = self)
        self.info_label = MyLabel("Mapa Studio 26 episode. anime", parent = self)
        self.rating_button = PushButton(FluentIcon.ASTERISK, "8.7", parent = self)

        self.watch_button = PushButton(FluentIcon.VIEW, "Watching", self)
        self.rate_button = PushButton(FluentIcon.LIBRARY, "Review", self)
        self.like_button = PushButton(FluentIcon.HEART, "Like", self)
        self.save_to_library = PushButton(FluentIcon.ADD_TO, "Add to Library", self)
        # self.like_button = TransparentToolButton(FluentIcon.HEART, self)
        # self.save_to_library = TransparentToolButton(FluentIcon.ADD_TO, self)

        self.page_pivot = SegmentedWidget(parent = self)
        self.pivot_stack = PopUpAniStackedWidget(parent = self)
        self.overview_page = OverviewPage(self)
        self.review_page = ReviewPage(self)
        self.staff_page = StaffPage(self)
        self.character_page = CharacterPage(self)
        self.relation_page = RelationPage(self)

        self.pivot_stack.addWidget(self.overview_page)
        self.pivot_stack.addWidget(self.review_page)
        self.pivot_stack.addWidget(self.staff_page)
        self.pivot_stack.addWidget(self.character_page)
        self.pivot_stack.addWidget(self.relation_page)

        # self.recommendation_container= Container("Recommendation for you", self)
        # self.recommendation_container.setMinimumHeight(self.recommendation_container_height)




        self._setup_pivot()
        self._init_ui()

    def _setup_pivot(self):
        self.page_pivot.addItem(routeKey="overviewInterface", text="Overview",
                                onClick=lambda: self.pivot_stack.setCurrentWidget(self.overview_page))
        self.page_pivot.addItem(routeKey="relationInterface", text="Relations",
                                onClick=lambda: self.pivot_stack.setCurrentWidget(self.relation_page))
        self.page_pivot.addItem(routeKey="characterInterface", text="Characters",
                                onClick=lambda: self.pivot_stack.setCurrentWidget(self.character_page))
        self.page_pivot.addItem(routeKey="staffInterface", text="Staff",
                                onClick=lambda: self.pivot_stack.setCurrentWidget(self.staff_page))
        self.page_pivot.addItem(routeKey="reviewInterface", text="Reviews",
                                onClick=lambda: self.pivot_stack.setCurrentWidget(self.review_page))
        self.page_pivot.setFixedWidth(self.screen_geometry.width()//2)
        self.page_pivot.setCurrentItem("overviewInterface")

    def _init_ui(self):


        self.page_layout.addWidget(self.banner_label)
        self.page_layout.addSpacing(-100)

        vboxLayout = QVBoxLayout()
        vboxLayout.setContentsMargins(150, 0, 50, 0)

        cover_layout = QHBoxLayout()
        cover_layout.setSpacing(50)
        cover_layout.addWidget(self.cover_label)

        sub_cover_layout = QVBoxLayout()
        sub_cover_layout.setSpacing(10)
        sub_cover_layout.addStretch()
        sub_cover_layout.addWidget(self.title_label)
        sub_cover_layout.addSpacing(-10)
        sub_cover_layout.addWidget(self.info_label)
        sub_cover_layout.addSpacing(20)
        sub_cover_layout.addWidget(self.rating_button, alignment=Qt.AlignmentFlag.AlignLeft)

        h_cover_layout = QHBoxLayout()
        h_cover_layout.addWidget(self.watch_button)
        h_cover_layout.addWidget(self.rate_button)
        h_cover_layout.addWidget(self.like_button)
        h_cover_layout.addWidget(self.save_to_library)
        h_cover_layout.addStretch()

        sub_cover_layout.addLayout(h_cover_layout)
        sub_cover_layout.addStretch()

        cover_layout.addLayout(sub_cover_layout)
        # sub_cover_layout = QVBoxLayout()


        vboxLayout.addLayout(cover_layout)
        vboxLayout.addWidget(self.page_pivot)
        vboxLayout.addWidget(self.pivot_stack)
        # vboxLayout.addWidget(self.recommendation_container)





        self.page_layout.addLayout(vboxLayout)
        # self.page_layout.addStretch()


if __name__ == '__main__':
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    # main = OverviewPage()
    main = MediaPage()
    main.show()
    sys.exit(app.exec())