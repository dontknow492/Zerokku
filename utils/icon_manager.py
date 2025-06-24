import os
import sys

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIconBase, Theme, getIconColor, ToolButton, FluentFontIconBase
from PySide6.QtWidgets import QApplication
from pathlib import Path
from enum import Enum
from utils.scripts import resource_path



class IconManager(FluentIconBase, Enum):
    BOT = "bot"
    BRUSH = "brush"
    CONTROL_MULTIMEDIA_PLAYER = "control-multimedia-player"
    DELETE = "delete"
    DOWNLOAD = "download"
    FOLDER_FAVOURITE_BOOKMARK = "folder-favourite-bookmark"
    FOLDER_FAVOURITE_STAR = "folder-favourite-star"
    FOLDER_OPEN = "folder-open"
    IMAGE_PEN = "image-pen"
    LOOP = "loop"
    MODEL_ALT = "model-alt"
    NO_IMAGE = "no-image"
    PAINT_BRUSH = "paint-brush"
    PASTE = "paste"
    PERSPECTIVE_DICE_RANDOM = "perspective-dice-random"
    PROCESS_BOX = "process-box"
    PROCESS = "process"
    PROMPT_EDIT = "prompt-edit"
    RECYCLE = "recycle"
    SCRIPT = "script"
    SKIP_FORWARD = "skip-forward"
    STAR_FALL = "star-fall"
    STOP = "stop"
    SWAP = "swap"
    TERMINAL = "terminal"
    TEXT_SIZE_BUTTON = "text-size-button"
    TEXT_SIZE = "text-size"
    UP_ARROW = "up-arrow"
    ASPECT_RATIO = "ar-zone"
    DATA = "data"
    TEMP_FOLDER = "temp-opened"
    SLIDER = "slider-01"
    CLOCK = "clock-three"
    LIVE = "live"
    PLAYLIST = "playlist"
    QUEUE = "queue"
    FAV = "favourite-star"
    SHUFFLE = "shuffle"
    NEXT = "next"
    NEXT_ARROW = "next-arrow"
    NEXT_SOLID = "next-solid"
    PREV_BK = "previous-back"
    PREV_ARROW = "previous-arrow"
    PREV_SOLID = "previous-solid"
    PLAYBACK_SPEED = "playback-speed"
    HEART_SOLID = "heart"
    REPEAT = "repeat"
    LIKE = "like"
    DOWN_CHEVRON = "down-chevron"
    UP_CHEVRON = "chevron-up"
    PLAYLIST_MUSIC = "playlist-2"
    STATS = "stats"
    MUSIC = "music"
    PLAY_CIRCLE = "play-circle"
    PAUSE_CIRCLE = "pause-circle"
    CHECK_BADGE = "check-badge"
    BACK_2 = "back-2"
    FORWARD_2 = "forward-2"
    HQ_FILL = "hq-fill"
    LOCK = "lock"
    MORE_VERTICAL = "more-vertical"
    SUBTITLE = "subtitle"
    UNLOCK = "lock-keyhole-unlocked"
    def path(self, theme=Theme.AUTO):
        # getIconColor() return "white" or "black" according to current theme
        return f'assets/icons/{getIconColor(theme)}/{self.value}-svgrepo-com.svg'

class FontAwesomeRegularIcon(FluentFontIconBase):
    DIR = "assets\\otfs"
    NAME = "Font Awesome 6 Free-Regular-400.otf"
    def path(self, theme=Theme.AUTO):
        return resource_path(f"{self.DIR}\\{self.NAME}")

class FontAwesomeSolidIcon(FluentFontIconBase):
    DIR = "assets\\otfs"
    NAME = "Font Awesome 6 Free-Solid-900.otf"
    def path(self, theme=Theme.AUTO):
        return resource_path(f"{self.DIR}\\{self.NAME}")

class FontAwesomeBrandIcon(FluentFontIconBase):
    DIR = "assets\\otfs"
    NAME = "Font Awesome 6 Brands-Regular-400.otf"
    def path(self, theme=Theme.AUTO):
        return resource_path(f"{self.DIR}\\{self.NAME}")