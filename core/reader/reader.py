import sys
from enum import Enum
from pathlib import Path
from typing import Union, List, Tuple, Optional

from PySide6.QtCore import QObject, Qt, QSize, Signal, QPointF, QRectF, QSizeF, Property, QTimer, QEvent, QPoint, QUrl, \
    QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtGui import QPixmap, QImageReader, QImage, QCloseEvent, QKeyEvent, QResizeEvent, QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QApplication, QScroller, \
    QScrollerProperties, QGraphicsProxyWidget, QGraphicsTextItem, QVBoxLayout

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from loguru import logger
from qfluentwidgets import SimpleCardWidget, SubtitleLabel
from qframelesswindow import TitleBar

from gui.common import RotableProgressRing
from utils import CBZArchive
from utils.scripts import get_cache_pixmap, delete_cache_pixmap

from core.reader.overlay import ReaderTitle, ReaderSlider, ReaderNavigation, ReaderSettings, ReaderAnimationManager, ReadMode, \
    FitMode, PositionFlags, ZoomWidget


class SlideDirection(Enum):
    UP = "Up"
    DOWN = "Down"
    LEFT = "Left"
    RIGHT = "Right"

class PagePixmapItem(QGraphicsPixmapItem, QObject):
    pixmapLoaded = Signal(QPixmap)

    PLACEHOLDER_SIZE = QSize(800, 1500)  # Used for boundingRect before image is loaded

    def __init__(self, path: Optional[Path] = None, index: int = 0):
        QGraphicsPixmapItem.__init__(self)
        QObject.__init__(self)

        self._viewport_size = None
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)

        self._page_path = path
        self._is_loaded = False
        self._expected_size = self.PLACEHOLDER_SIZE
        self._idx = index
        self._mode = FitMode.PAGED

        # Error text
        self.errorText = QGraphicsTextItem("", self)
        self.errorText.setDefaultTextColor(Qt.GlobalColor.red)
        self.errorText.setZValue(2)
        self.errorText.setVisible(False)

        # Error image
        self.errorImage = QGraphicsPixmapItem(self)
        self.errorImage.setZValue(2)
        self.errorImage.setVisible(False)

        # Progress ring setup
        self.progressRing = RotableProgressRing()
        self.progressRing.setStyleSheet("background: transparent;")
        self.progressRing.setRange(0, 100)
        self.progressRing.setValue(0)

        self.progressProxy = QGraphicsProxyWidget(self)
        self.progressProxy.setWidget(self.progressRing)
        self.progressProxy.setZValue(1)
        self.progressProxy.setVisible(False)

        if path is None:
            self.showLoading()

    def boundingRect(self):
        if self._is_loaded and not self.pixmap().isNull():
            return QRectF(self.pixmap().rect()).normalized()
        else:
            return QRectF(0, 0, self._expected_size.width(), self._expected_size.height())

    def _updatePlaceholderBoundingRect(self, size: QSize | QSizeF):
        """ Update Bounding Rect placeholder it give size"""
        self._expected_size = size


    # def sceneBoundingRect(self) -> QRectF:
    #     return self.mapToScene(self.boundingRect()).boundingRect()


    def setFitMode(self, mode: FitMode, viewport_size: Union[QSize, QSizeF]):
        if  mode is None or viewport_size is None:
            return
        # if mode == self._mode:
#         #     logger.debug(f"Already setted to mode: {mode}")
        #     return
        if self.pixmap().isNull():
            # No pixmap loaded yet, no scaling
            self.setScale(1.0)
            return

        pixmap_size = self.pixmap().size()
        if pixmap_size.isEmpty():
            self.setScale(1.0)
            return

        scale_x = viewport_size.width() / pixmap_size.width()
        scale_y = viewport_size.height() / pixmap_size.height()

        if mode == FitMode.ORIGINAL:
            scale = 1.0

        elif mode == FitMode.FULLSCREEN:
            # Fit width exactly, keep aspect ratio
            scale = scale_x

        elif mode == FitMode.PAGED:
            # Fit entire page inside viewport (both width and height)
            scale = min(scale_x, scale_y)

        else:  # DEFAULT or fallback
            # Let's say default fits width but max 1.0 (no upscaling)
            scale = min(scale_x, 1.0)

        self.setScale(scale)

    def load(self):
        if self._is_loaded:
            logger.info("Page {} already loaded".format(self._idx))
            return

        if not self.path:
            self.showLoading()
            return

        reader = QImageReader(str(self._page_path))
        reader.setAutoTransform(True)
        img = reader.read()

        if img.isNull():
            self.showError("Failed to load image.")
            return

        pixmap = QPixmap.fromImage(img)
        self.setPixmap(pixmap)
        self._expected_size = pixmap.size()
        self._is_loaded = True
        self.prepareGeometryChange()
        self.pixmapLoaded.emit(pixmap)
        logger.info(f"Page loaded {self.index}: {pixmap.size()}")

    def unload(self):
        if not self._is_loaded:
            return
        self._updatePlaceholderBoundingRect(self.scaled_size) # updating placehodler bounding rect to pixmap size(scaled)
        self.setPixmap(QPixmap())

        self._is_loaded = False
        self.prepareGeometryChange()

    def showLoading(self):
        self._move_progress_to_center()
        # logger.debug(f"Page loading {self._idx}")
        self.progressRing.startRotation()
        self.progressProxy.setVisible(True)
        self.errorText.setVisible(False)
        self.errorImage.setVisible(False)

    def hideLoading(self):
        self.progressProxy.setVisible(False)
        self.progressRing.stopRotation()

    def updateProgress(self, value):
        self.progressRing.setValue(value)

    def showError(self, message: str, pixmap: QPixmap = None):
        self.hideLoading()
        self.errorText.setPlainText(message)
        self.errorText.setVisible(True)

        if pixmap and not pixmap.isNull():
            self.errorImage.setPixmap(pixmap)
            self.errorImage.setVisible(True)

            # Scale item to fit, instead of rescaling pixmap
            scale_factor = min(
                self.boundingRect().width() / pixmap.width(),
                self.boundingRect().height() / pixmap.height(),
                1.0
            )
            self.errorImage.setScale(scale_factor)
        else:
            self.errorImage.setVisible(False)

        self._position_error_elements()

    def _move_progress_to_center(self):
        if not self.progressProxy:
            return

        rect = self.boundingRect()
        size = self.progressRing.size()
        x = rect.center().x() - size.width() / 2
        y = rect.center().y() - size.height() / 2
        self.progressProxy.setPos(x, y)

    def _position_error_elements(self):
        rect = self.boundingRect()

        # Center error image
        if self.errorImage.isVisible():
            img_rect = self.errorImage.boundingRect()
            img_scale = self.errorImage.scale()
            x_img = rect.center().x() - img_rect.width() * img_scale / 2
            y_img = rect.center().y() - img_rect.height() * img_scale / 2 - 20
            self.errorImage.setPos(x_img, y_img)

        # Position error text
        text_rect = self.errorText.boundingRect()
        x_txt = rect.center().x() - text_rect.width() / 2
        y_txt = rect.center().y() + 30
        self.errorText.setPos(x_txt, y_txt)

    @property
    def original_size(self) -> QSize:
        return self.pixmap().size()

    @property
    def scaled_size(self) -> QSizeF:
        return QSizeF(self.original_size.width() * self.scale(),
                      self.original_size.height() * self.scale())

    def setPath(self, path: Path) -> None:
        self._page_path = path

    def getPath(self)->Optional[Path]:
        return self._page_path

    path = Property(Path, getPath, setPath)


    def set_index(self, index: int):
        self._idx = index

    def get_index(self):
        return self._idx

    index = Property(int, get_index, set_index, doc = "set the index of page used for layout, lazy loading")

    def loaded(self):
        return self._is_loaded

    def setPosition(self, pos: QPointF)->None:
        self.setPos(pos)

    def getPosition(self) -> QPointF:
        return self.pos()

    position = Property(QPointF, getPosition, setPosition)


class LayoutManager(QObject):
    """
        class for managing image scaling, reader adjustments, and event handling
        within a TargetContainer. Subclasses must implement all methods.
        """
    itemArranged = Signal()
    itemArranging = Signal()
    pageChanged = Signal(int)
    def __init__(self, view: QGraphicsView, mode: ReadMode, parent=None):
        super().__init__(parent)
        self.view = view
        self.scene = view.scene()
        self.view_mode = mode
        self.fit_mode = FitMode.DEFAULT
        self._layout_items: List[PagePixmapItem] = []

        self._view_size = QSize(1400, 780) #used for fit mode
        self._current = 0
        self._is_arranging = False

        #flags
        self._smooth_scrolling: bool = True
        self._page_animation: bool = True
        self._page_spacing = 10


        self.ani = QPropertyAnimation()
        self.ani.setDuration(400)
        self.ani.setEasingCurve(QEasingCurve.Type.InOutSine)

    def setPageSpacing(self, spacing: int):
        self._page_spacing = spacing
        self.arrange_items() #rearrange item with new spacing

    def getPageSpacing(self):
        return self._page_spacing

    pageSpacing = Property(int, getPageSpacing, setPageSpacing)

    def setArranging(self, is_arranging: bool):
        self._is_arranging = is_arranging

    def getArranging(self):
        return self._is_arranging

    arranging = Property(bool, getArranging, setArranging)

    def setViewMode(self, mode: ReadMode, starting_index: int = 0):
        if mode == self.view_mode:
            return
        self.view_mode = mode
        self.arrange_items(starting_index)

    def getViewMode(self):
        return self.view_mode

    viewMode = Property(ReadMode, getViewMode, setViewMode)

    def setFitMode(self, mode: FitMode):
        self.fit_mode = mode
        self.arrange_items()

    def getFitMode(self):
        return self.fit_mode

    fitMode = Property(FitMode, getFitMode, setFitMode)

    def setPageAnimation(self, is_animated: bool):
        self._page_animation = is_animated

    def getPageAnimation(self):
        return self._page_animation

    pageAnimation = Property(bool, getPageAnimation, setPageAnimation)

    def setSmoothScrolling(self, is_smooth: bool):
        self._smooth_scrolling = is_smooth
    def getSmoothScrolling(self):
        return self._smooth_scrolling

    smoothScrolling = Property(bool, getSmoothScrolling, setSmoothScrolling)

    @property
    def current_page(self)->int:
        return self._current

    def addItem(self, item: PagePixmapItem):
#         logger.debug(f"Adding Item: {item}")
        self._layout_items.append(item)
        if item not in self.scene.items():
            self.scene.addItem(item)

        self.arrange_items()

    def addItems(self, items: List[PagePixmapItem]):
#         logger.debug(f"Adding {len(items)} items to layout")
        for item in items:
            self._layout_items.append(item)
            if item not in self.scene.items():
                self.scene.addItem(item)
        self.arrange_items()

    def items(self)-> List[PagePixmapItem]:
        return self._layout_items

    def itemAt(self, index: int) -> PagePixmapItem:
        return self._layout_items[index]

    def sort_layout_items(self):
        self._layout_items.sort(key=lambda item: item.index)


    def arrange_items(self, starting_index: int = 0):
        if not len(self._layout_items):
#             logger.debug("No layout items to arrange")
            return
        self.itemArranging.emit()
        self._is_arranging = True
        starting_index = min(starting_index, len(self._layout_items) - 1 ) if starting_index else 0
        match self.view_mode:
            case ReadMode.CONTINUOUS_VERTICAL:
                self._arrange_continuous_vertical(starting_index = starting_index)
            case ReadMode.CONTINUOUS_VERTICAL_GAPS:
                self._arrange_continuous_vertical(self._page_spacing, starting_index = starting_index)
            case ReadMode.LEFT2RIGHT:
                self._arrange_paged(starting_index = starting_index)
            case ReadMode.RIGHT2LEFT:
                self._arrange_paged(starting_index = starting_index)
            case _:
                logger.debug(f"Unknown mode: {self.view_mode}")

#         # logger.debug(f"arranged {len(self._layout_items)} items")
        self.itemArranged.emit()
        self._is_arranging = False

    def _arrange_continuous_vertical(self, page_spacing: int = 0, starting_index: int = 0):
#         logger.debug(f"Arranging continuous vertical  with {page_spacing} page spacing")
        # Ensure items are sorted by their index
        self.sort_layout_items()

        # Get starting Y position
        item = self._layout_items[starting_index]
        y = 0 #item.y() + item.get_scaled_height() + page_spacing
        des = 0

        # Default to no spacing if none is provided
        page_spacing = page_spacing if page_spacing is not None else 0

        for item in self._layout_items[starting_index:]:
            fit_mode = FitMode.FULLSCREEN if self.fit_mode == FitMode.DEFAULT else self.fit_mode
            view_size = self._view_size
            if self.fit_mode == FitMode.DEFAULT:
                view_size  = QSizeF(self._view_size.width() * 0.7, self._view_size.height() * 0.7)
            item.setFitMode(fit_mode, view_size)
            item.setVisible(True)
            item.setPos(0, y)

            item_bounding_rect = item.sceneBoundingRect()
#             # logger.debug(f"Item bounding rect: {item_bounding_rect}, page: {item.index}, "
            #              f"page_spacing: {page_spacing}, pos: {y}")

            if item.index == self._current:
                # self.view.verticalScrollBar().setValue(y)
                des = y  # track position to scroll to current

            y += item_bounding_rect.height() + page_spacing

        self.resetSceneRect()

        # Optionally scroll to `des` using view (if needed)
        # self._graphics_view.ensureVisible(0, des, 1, 1)

    def _arrange_paged(self, direction: ReadMode = ReadMode.RIGHT2LEFT, starting_index: int = 0):
#         logger.debug(f"Arranging in Stacked format: {direction.value} from {starting_index}")
        current_item = None
        for item in self._layout_items[starting_index:]:
            fit_mode = FitMode.PAGED if self.fit_mode == FitMode.DEFAULT else self.fit_mode
            item.setFitMode(fit_mode, self._view_size) # fit page to screen
            item.setPos(0, 0)
            if item.index != self._current:

                item.setVisible(False)
            else:
                item.setVisible(True)
                current_item = item

            self.moveItemToCenter(item)

        self.adjustSceneRectToItem(current_item)
        self.scrollTo(QPoint(0, 0), 0)


    def adjustSceneRectToItem(self, current_item: PagePixmapItem):
        if not current_item or not current_item.pixmap() or current_item.pixmap().isNull():
            return

        # Get scaled bounding rect of current image item in reader coordinates
        item_rect = current_item.sceneBoundingRect() #current_item.mapToScene(current_item.boundingRect()).boundingRect()

        # Optionally add some padding if you want space around image
        padding = 10
        scene_rect = item_rect.adjusted(-padding, -padding, padding, padding)

        # Set the reader rect explicitly to fit the current item tightly
        self.view.scene().setSceneRect(scene_rect)

        # Resize QGraphicsView scrollbars policies accordingly
        view_size = self.view.viewport().size()

        if scene_rect.width() <= view_size.width() and scene_rect.height() <= view_size.height():
            # Image fits inside viewport: disable scrollbars or hide them
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            # Image larger than viewport: enable scrollbars as needed
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def resetSceneRect(self):
        self.view.scene().setSceneRect(self.view.scene().itemsBoundingRect())

    def moveItemToCenter(self, item: PagePixmapItem):
        if not item or not item.pixmap() or item.pixmap().isNull():
            return
        self.view.centerOn(item)


    def go_to_page(self, page_num: int,  direction: SlideDirection = SlideDirection.UP, duration: int = 0,) -> None:
        logger.debug(f"Going to page {page_num}")
        if page_num < 0 or page_num >= len(self._layout_items):
            logger.debug(f"page {page_num} is out of range")
            return
        page_num = min(page_num, len(self._layout_items) - 1)
        page_num = max(page_num, 0)
        result_item = None

        if self.viewMode in [ReadMode.CONTINUOUS_VERTICAL, ReadMode.CONTINUOUS_VERTICAL_GAPS]:
            item = self._layout_items[page_num]
            self.view.ensureVisible(item)
            self._current = page_num


        if self.viewMode in [ReadMode.LEFT2RIGHT, ReadMode.RIGHT2LEFT]:
            for item in self._layout_items:
                if page_num == item.index:
                    self.adjustSceneRectToItem(item)
                    self.moveItemToCenter(item)
                    self.scrollTo(QPointF(0, 0), 0)
                    result_item = item
                else:
                    item.setVisible(False)

            self._current = page_num
            result_item.setVisible(True)
            if result_item.loaded():
                if self.pageAnimation:
                    self.slide_animation(result_item, direction, duration)
                QTimer.singleShot(self.ani.duration()+20, lambda: self.pageChanged.emit(page_num)) #slight delay to let slide animation finish(same as ani duration)
            else:
                QTimer.singleShot(0, lambda :self.pageChanged.emit(page_num))

    def go_left_page(self, current: int, duration: int = 0) -> None:
        if self.viewMode == ReadMode.LEFT2RIGHT:
            direction = SlideDirection.LEFT
            self.go_to_page(current-1, direction, duration)
        elif self.viewMode == ReadMode.RIGHT2LEFT:
            direction = SlideDirection.RIGHT
            self.go_to_page(current+1, direction, duration)

    def go_right_page(self, current: int, duration: int = 0) -> None:
        if self.viewMode == ReadMode.LEFT2RIGHT:
            direction = SlideDirection.RIGHT
            self.go_to_page(current+1, direction, duration)
        elif self.viewMode == ReadMode.RIGHT2LEFT:
            direction = SlideDirection.LEFT
            self.go_to_page(current-1, direction, duration)




    def scrollTo(self, pos: Union[QPoint, QPointF], duration: int = 0) -> None:
#         logger.debug(f"Scrolling to {pos} in {duration}ms")
        scroller = QScroller.scroller(self.view.viewport())
        scroller.scrollTo(pos, duration)

    def slide_animation(self, item: PagePixmapItem,
                        direction: SlideDirection = SlideDirection.LEFT, duration: Optional[int] = None) -> None:
        if not item or not item.pixmap() or item.pixmap().isNull():
            return
        if self.ani and self.ani.state() == QAbstractAnimation.Running:
            self.ani.stop()
            pre_item = self.ani.targetObject()
            pre_item.setPos(self.ani.endValue())
            return

        if duration:
            self.ani.setDuration(duration)

        end = item.pos()
#         logger.debug(f"SlideAnimation {direction}: {end}")
        if direction == SlideDirection.LEFT:
            start = QPointF(500, 0)
        elif direction == SlideDirection.RIGHT:
            start = QPointF(-500, 0)
        elif direction == SlideDirection.UP:
            start = QPointF(0, 500)
        else:
            start = QPointF(0, -500)
        item.setPos(start)
#         logger.debug(f"SlideAnimation- duration: {duration}, start: {start}, end: {end}, direction: {direction}")
        self.ani.setTargetObject(item)
        self.ani.setPropertyName(b"position")
        self.ani.setStartValue(start)
        self.ani.setEndValue(end)

        self.ani.start()


class LazyLoader(QObject):
    pageChanged = Signal(int)
    def __init__(self, view: QGraphicsView, layout_manager: LayoutManager, preload_margin: int = 1):
        super().__init__()
        self.view = view
        self.scene = view.scene()
        self.layoutManager = layout_manager
        self.preload_margin = preload_margin  # Extra margin pages for preloading

        self._scroll_timer = QTimer()
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(50)
        self._scroll_timer.timeout.connect(self._updateView)

        self._current_idx = 0
        self._current_range: Tuple[int, int] = (0, self.preload_margin)

        self._signal_handler()

    def _signal_handler(self):
        self.layoutManager.pageChanged.connect(self._updateView)

    def start_check_timer(self):
        self._updateView()
        # self._scroll_timer.start()

    def stop_check_timer(self):
        self._scroll_timer.stop()

    def get_current_idx(self) -> int:
        current =  self._findVisibleInViewport()
        return current

    def _updateView(self):
#         logger.debug(f"updating view ")
        current = self.get_current_idx()
        if current == -1:
            logger.warning(f"current index is out of range: {current}")
            return
        if self._current_idx == current:
#             logger.debug(f"Currently at same index no need to update: {self._current_idx}")
            return

        self._updateViewFor(current)
        # self._updateViewFor(current)

    def _updateViewFor(self, current: int) -> None:
#         if current == -1:
#             logger.warning(f"current index is out of range: {current}")
#             return
#         if self._current_idx == current:
#             logger.debug(f"Currently at same index no need to update: {self._current_idx}")
#             return
# #         logger.debug(f"Updating view for: {current} -> {self._current_idx}")
#         self._current_idx = current
        # item = self.layoutManager.itemAt(current)
        # self.load_item(item)

        minimum, maximum = self._findVisibleImageRange()
        logger.debug(f"current index: {current}, visible range: {minimum}, {maximum}")
        minimum = max(minimum-self.preload_margin, 0)
        maximum = min(maximum+self.preload_margin, len(self.layoutManager.items()))
        self.lazy_load(minimum, maximum)
        self.pageChanged.emit(current)

    def _isVisibleInViewport(self, item: PagePixmapItem):
        """Checks if an image is visible in the current viewport."""
        item_rect = item.sceneBoundingRect()
        viewport_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        if viewport_rect.intersects(item_rect):
            logger.debug(f"Item rect: {item_rect}, viewport rect: {viewport_rect}, Item: {item.index} is visible: {viewport_rect.intersects(item_rect)}")
        return viewport_rect.intersects(item_rect)

    def _findVisibleInViewport(self)->int:
        mode: ReadMode = self.layoutManager.viewMode
        items = self.layoutManager.items()
        items_len = len(items)

        # **1. Get the Y-coordinate of the viewport center**
        rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        viewport_center_y = rect.y() + (rect.height() // 2)


        if mode in [ReadMode.CONTINUOUS_VERTICAL, ReadMode.CONTINUOUS_VERTICAL_GAPS]:
            low, high = 0, items_len - 1
            found_idx = -1

            # Perform binary search to find a visible image**
            while low <= high:
                mid = (low + high) // 2
                real_idx = self._get_img_idx(mid, items_len - 1)  # Adjust for reverse order
                image = items[real_idx]

                if self._isVisibleInViewport(image):
                    found_idx = mid
                    break  # Stop once a visible image is found
                elif image.y() < viewport_center_y:
                    low = mid + 1  # Search upwards
                else:
                    high = mid - 1  # Search downwards

            # If no visible image is found, fallback to a linear search**
            if found_idx == -1:
                for i, item in enumerate(items):
                    if self._isVisibleInViewport(item):
                        found_idx = i
                        break

            return found_idx

        elif mode in [ReadMode.LEFT2RIGHT, ReadMode.RIGHT2LEFT]:
            for item in items:
                if item.isVisible() and self._isVisibleInViewport(item):
                    return item.index

        return -1

    def _findVisibleImageRange(self):
        """
        Finds the first and last visible image indices efficiently using binary search.
        Returns: (first_visible_idx, last_visible_idx)
        """
        images = self.layoutManager.items()
        imgs_len = len(images)
        found_idx = self._findVisibleInViewport()

        # **1. Get the Y-coordinate of the viewport center**
        if self.layoutManager.viewMode in [ReadMode.CONTINUOUS_VERTICAL, ReadMode.CONTINUOUS_VERTICAL_GAPS]:
            # **4. Expand left to find the first visible image**
            first_visible_idx = found_idx
            while first_visible_idx > 0:
                real_idx = self._get_img_idx(first_visible_idx - 1, imgs_len - 1)
                if self._isVisibleInViewport(images[real_idx]):
                    first_visible_idx -= 1
                else:
                    break

            # **5. Expand right to find the last visible image**
            last_visible_idx = found_idx
            while last_visible_idx < imgs_len - 1:
                real_idx = self._get_img_idx(last_visible_idx + 1, imgs_len - 1)
                if self._isVisibleInViewport(images[real_idx]):
                    last_visible_idx += 1
                else:
                    break

            return first_visible_idx, last_visible_idx

        elif self.layoutManager.viewMode in [ReadMode.LEFT2RIGHT, ReadMode.RIGHT2LEFT]:
            return found_idx, found_idx

        return found_idx, found_idx

    def _get_img_idx(self, idx: int, from_max: int) -> int:
        """Handles reversed order in RightToLeft or BottomToTop scrolling."""
        return idx

    def lazy_load(self, minimum: int, maximum: int):
#         logger.debug(f"lazy loading {minimum}, {maximum}")
        for item in self.layoutManager.items():
            if item.index >= minimum and item.index <= maximum:
                self.load_item(item)
            else:
                self.unload_item(item)
        self.layoutManager.arrange_items()

    def load_item(self, item: PagePixmapItem):
        item.load()

    def unload_item(self, item: PagePixmapItem):
        item.unload()


class PageManager:
    def __init__(self):
        self.items: List[PagePixmapItem] = list()

    def add_page(self, item: PagePixmapItem):
        self.items.append(item)


class ComicReader(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        gl_widget = QOpenGLWidget()
        self.setViewport(gl_widget)
        self.cbz_archive: CBZArchive = None
        self.viewport().installEventFilter(self)
        self._screen_geometry = QApplication.primaryScreen().availableGeometry() # QRect(0, 0, 1463, 823)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.zoom_factor = 1.15
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.current_scale = 1.0
        self.layout = LayoutManager(self, ReadMode.CONTINUOUS_VERTICAL, parent=self)
        self.layout.pageSpacing = 50
        self.lazy_loader = LazyLoader(self, self.layout, 1)

        #overlay
        self.top_nav = ReaderTitle(self)
        self.bottom_nav = ReaderNavigation(self)
        self.slider = ReaderSlider(Qt.Orientation.Vertical, self)
        self.settings = ReaderSettings(self)
        self.settings_position = PositionFlags.LEFT
        self.settings.setVisible(False)
        self.top_nav.setVisible(False)
        self.bottom_nav.setVisible(False)
        self.slider.setVisible(False)

        self.zoom_widget = ZoomWidget(self)

        # self.settings.raise_()

        #animation
        self.ani_manager = ReaderAnimationManager(self.top_nav, self.bottom_nav, self.settings)

        self._setup_scroller()
        self._signal_handler()

        self._updateSliderPosition(force=True)
        self._updateSettingPosition(force=True)

    def _onScrollChanged(self):
        self.hideOptions()
        if self.layout.arranging and self.layout.viewMode in [ReadMode.LEFT2RIGHT, ReadMode.RIGHT2LEFT]:
            self.lazy_loader.stop_check_timer()
        else:
            self.lazy_loader.start_check_timer()

    def _setup_scroller(self):
        scroller = QScroller.scroller(self.viewport())
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.DragVelocitySmoothingFactor, 0.6)
        props.setScrollMetric(QScrollerProperties.DecelerationFactor, 0.2)
        scroller.setScrollerProperties(props)


        # Use QScroller class method to grab gesture
        QScroller.grabGesture(self.viewport(), QScroller.LeftMouseButtonGesture)

    def _signal_handler(self):
        self.verticalScrollBar().valueChanged.connect(self._onScrollChanged)
        self.lazy_loader.pageChanged.connect(self.slider.setCurrentPageIndex) #slider show page from 1
        self.slider.pageIndexChanged.connect(self.layout.go_to_page)

        #bottom nav
        self.bottom_nav.settingsSignal.connect(self.toggleSettings)
        self.bottom_nav.zoomInSignal.connect(self._zoom_in)
        self.bottom_nav.zoomOutSignal.connect(self._zoom_out)

        # settings
        self.settings.viewModeChanged.connect(self.setViewMode)
        self.settings.fitModeChanged.connect(self.setFitMode)
        self.settings.zoomStepChanged.connect(self.setZoomSteps)
        self.settings.pageGapChanged.connect(self.setPageGap)
        self.settings.autoCropBorderToggled.connect(self.autoCropBorder)
        self.settings.backgroundColorChanged.connect(self.setBackgroundColor)
        #navigation settings
        self.settings.autoScrollChanged.connect(self.autoScroll)
        self.settings.scrollSensitivityChanged.connect(self.setScrollSensitivity)
        self.settings.pageSnappingToggled.connect(self.setPageSnap)
        self.settings.pageTurnAnimationToggled.connect(self.pageTurnAnimation)
        self.settings.showPageNumToggled.connect(self.showPageNumber)
        #advance settings
        self.settings.cacheImageToggled.connect(self.cacheImage)
        self.settings.smoothScrollToggled.connect(self.setSmoothScroll)
        self.settings.grayScaleToggled.connect(self.grayScaleImage)
        self.settings.invertToggled.connect(self.invertImage)
        self.settings.settingPositionChanged.connect(self.setSettingsPosition)
        self.settings.settingWidthChanged.connect(self.setSettingsWidth)
        self.settings.forceHorizontalSliderToggled.connect(self.forceHorizontalSlider)





    def setNavColor(self, color: QColor):
        self.top_nav.setBackgroundColor(color)
        self.bottom_nav.setBackgroundColor(color)
        self.settings.setBackgroundColor(color)
        self.slider.setBackgroundColor(color)

    def setTitle(self, title: str):
        self.top_nav.setTitle(title)

    def setDescription(self, description: str):
        self.top_nav.setDescription(description)

    def setViewMode(self, mode: ReadMode):
#         logger.debug(f"Updating view: {mode}")
        if mode in [ReadMode.LEFT2RIGHT, ReadMode.RIGHT2LEFT]:
            self.verticalScrollBar().valueChanged.disconnect(self._onScrollChanged)
        elif mode in [ReadMode.CONTINUOUS_VERTICAL, ReadMode.CONTINUOUS_VERTICAL_GAPS]:
            self.verticalScrollBar().valueChanged.connect(self._onScrollChanged)
        self.layout.viewMode = mode

    def getViewMode(self):
        return self.layout.viewMode

    def getFitMode(self):
        pass

    def setFitMode(self, mode: FitMode):
        self.layout.fitMode = mode

    def setZoomSteps(self, steps: float):
        self.zoom_factor = 1 + steps # .15 = 1.15

    def setPageGap(self, gap: int):
        self.layout.pageSpacing = gap

    def autoCropBorder(self, crop: bool):
        pass

    def setBackgroundColor(self, color: QColor):
        pass


    def autoScroll(self, enable: bool, speed: int = 100):
        speed = speed * 100
        scroller = QScroller.scroller(self.viewport())
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.ScrollMetric.ScrollingCurve, QEasingCurve.Linear)
        scroller.setScrollerProperties(props)
        if not enable:
            scroller.stop()
            return

        # Compute destination and dynamic duration
        current_y = self.verticalScrollBar().value()
        max_y = self.verticalScrollBar().maximum()
        remaining_distance = max_y - current_y

        # Clamp speed to avoid division errors
        speed = max(speed, 1)  # pixels per second

        duration_ms = int((remaining_distance / speed)*1000)  # convert to milliseconds

        # Scroll to bottom smoothly
        logger.info(f"Duration: {duration_ms} ms")
        scroller.scrollTo(QPoint(0, max_y), duration_ms)


    def setScrollSensitivity(self, sensitivity: float):
        # Clamp the value between 0 and 1
        sensitivity = max(0.0, min(sensitivity, 1.0))

        scroller = QScroller.scroller(self.viewport())  # get scroller for the widget
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.DecelerationFactor, 1 - sensitivity)
        scroller.setScrollerProperties(props)



    def setPageSnap(self, snap: bool):
        pass

    def pageTurnAnimation(self, enable: bool):
        self.layout.pageAnimation = enable

    def showPageNumber(self, bool):
        pass

    def cacheImage(self, enabled: bool):
        pass

    def setSmoothScroll(self, enabled: bool):
#         logger.debug(f"Updating smooth scroll: {enabled}")
        viewport = self.viewport()

        try:
            if enabled:
                QScroller.grabGesture(viewport, QScroller.LeftMouseButtonGesture)
                QScroller.grabGesture(viewport, QScroller.MiddleMouseButtonGesture)
            else:
                QScroller.ungrabGesture(self.viewport())
        except Exception as e:
            logger.exception(f"Failed to toggle smooth scroll: {e}")

    def grayScaleImage(self, enabled: bool):
        pass

    def invertImage(self, enabled: bool):
        pass

    def setSettingsPosition(self, position: PositionFlags):
        self.settings_position = position
        self._updateSettingPosition()

    def setSettingsWidth(self, width: int):
        self.settings.setFixedWidth(width)
        self._updateSettingPosition()

    def forceHorizontalSlider(self, forced: bool):
        if forced:
            self.slider.setOrientation(Qt.Orientation.Horizontal)
        else:
            if self.layout.viewMode in [ReadMode.LEFT2RIGHT, ReadMode.RIGHT2LEFT]:
                self.slider.setOrientation(Qt.Orientation.Horizontal)
            else:
                self.slider.setOrientation(Qt.Orientation.Vertical)

        self._updateSliderPosition(True)



    #
    def showOptions(self):
        if self.top_nav.isVisible():
            return
        self._updateNavPosition()
        self._updateSliderPosition(force=True)
        self.ani_manager.show_nav()
        self.zoom_widget.fade_in(400)
        self.slider.fade_in(400)

    def hideOptions(self):
        self.zoom_widget.fade_out(400)
        if not self.top_nav.isVisible():
            return
        # if self.settings.isVisible():
        self.settings.setVisible(False)
        self.ani_manager.hide_nav()

        self.slider.fade_out(400)

    def toggleSettings(self):
        visible = self.settings.isVisible()
#         logger.debug(f"Toggling Navigation: {visible}")
        self._updateSettingPosition(True)
        if not visible:
            self.ani_manager.show_settings(self.settings_position)
        else:
            self.ani_manager.hide_settings(self.settings_position)




    def load_cbz(self, cbz_path: Path, current: int = 0):
        del self.cbz_archive
        self.cbz_archive = CBZArchive(cbz_path)
        load = False
        for x in range(self.cbz_archive.page_count()):
            path = self.cbz_archive.get_path(x)
            if x<=1:
                load = True
            else:
                load = False
            self.add_page(path, x, load)

        #setting slider total pages
        self.slider.setTotalPages(self.cbz_archive.page_count())

    def add_page(self, page: Union[Path, QUrl], page_index: int, preload: bool = False):
        page = self.create_page(page, page_index)
        if preload:
            page.load()
        self.layout.addItem(page)

    def create_page(self, page: Union[Path, QUrl], page_idx: int):
        if isinstance(page, QUrl):
            page = None
            #todo: add it to download queue (and create download queue)
        page = PagePixmapItem(page, page_idx)
        return page

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and QApplication.keyboardModifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            return True
        return super().eventFilter(obj, event)

    def _zoom_in(self):
        if self.current_scale < self.max_zoom:
            self.scale(self.zoom_factor, self.zoom_factor)
            self.current_scale *= self.zoom_factor
            self.zoom_widget.setZoom(self.current_scale)


    def _zoom_out(self):
        if self.current_scale > self.min_zoom:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
            self.current_scale /= self.zoom_factor
            self.zoom_widget.setZoom(self.current_scale)


    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key == Qt.Key_Left:
            current = self.lazy_loader.get_current_idx()
            self.layout.go_left_page(current)  # Left arrow → previous page

        elif key == Qt.Key_Right:
            current = self.lazy_loader.get_current_idx()
            self.layout.go_right_page(current)  # Right arrow → next page

        else:
            # Handle all other keys normally
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event, /):
        super().mouseDoubleClickEvent(event)
        # self.toggleSettings()
        if not self.top_nav.isVisible():
            self.showOptions()
        else:
            self.hideOptions()


    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.zoom_widget.move((self.width() - self.zoom_widget.width())//2, 0)

        self._updateNavPosition()
        self._updateSliderPosition()
        self._updateSettingPosition()

    def _updateNavPosition(self):
        self.top_nav.adjustSize()
        self.top_nav.setFixedSize(self.width(), self.top_nav.height())
        self.top_nav.move(0, 0)

        self.bottom_nav.adjustSize()
        self.bottom_nav.setFixedSize(self.width(), self.bottom_nav.height())
        self.bottom_nav.move(0, self.height() - self.bottom_nav.height())

    def _updateSettingPosition(self, force=False):
        if not self.settings.isVisible() and not force:
            return

        self.settings.setFixedHeight(self.height())

        if self.settings_position == PositionFlags.LEFT:
            x = 0
        else:  # Assume RIGHT
            x = self.width() - self.settings.width()

        self.settings.move(x, 0)

    def _updateSliderPosition(self, force=False):
        if not self.slider.isVisible() and not force:
            return

        self.slider.adjustSize()

        if self.slider.getOrientation() == Qt.Vertical:
            slider_width = self.slider.slider_v.width() + 20
            slider_height = self.height() - self.top_nav.height() - self.bottom_nav.height()
            x = self.width() - slider_width - 20
            y = self.top_nav.height()

            self.slider.setFixedSize(slider_width, slider_height)
            self.slider.move(x, y)

        else:  # Horizontal
            slider_height = self.slider.slider_h.height() + 20
            x = 0
            y = self.height() - slider_height - self.bottom_nav.height() - 20

            self.slider.setFixedSize(self.width(), slider_height)
            self.slider.move(x, y)


    def closeEvent(self, event: QCloseEvent):
        del self.cbz_archive

        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    path = Path(r"/demo/Chapter 44.cbz")
    color = QColor(255, 255, 255, 150)
    title = "The Legend of the Northern Blade"
    description = "Chapter 44: The Revenge of Asura"
    comicReader = ComicReader()
    comicReader.load_cbz(path)
    # comicReader.setFitMode(FitMode.PAGED)
    # comicReader.setNavColor(color)
    comicReader.setTitle(title)
    comicReader.setDescription(description)
    comicReader.show()
    app.exec()