from PySide6.QtCore import (
    QPropertyAnimation, QRect, QPoint, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, QSize, Qt, QTimer
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from enum import Enum, auto
from typing import Union, List, Optional


class AnimationDirection(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()

class AnimationType(Enum):
    SLIDE_IN = auto()
    SLIDE_OUT = auto()
    FADE_IN = auto()
    FADE_OUT = auto()
    UNFOLD_HORIZONTAL = auto()
    UNFOLD_VERTICAL = auto()
    POP = auto()
    SNAKE = auto()
    PULSE = auto()


class AnimationManager:
    def __init__(self):
        self._animations = []
        self._effects = {}  # Track effects to prevent memory leaks

    def _track(self, group):
        """Track animation groups for cleanup"""
        self._animations.append(group)
        group.finished.connect(lambda: self._animations.remove(group))

    def _ensure_list(self, widgets: Union[QWidget, List[QWidget]]) -> List[QWidget]:
        """Ensure input is always a list of widgets"""
        if isinstance(widgets, QWidget):
            return [widgets]
        return widgets

    def _cleanup_effect(self, widget: QWidget):
        """Clean up effects when no longer needed"""
        if widget in self._effects:
            effect = self._effects.pop(widget)
            effect.setEnabled(False)
            widget.setGraphicsEffect(None)

    def fade_in(self, widgets: Union[QWidget, List[QWidget]],
                duration: int = 500, easing: QEasingCurve.Type = QEasingCurve.OutCubic,
                on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Fade in widgets with opacity animation"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            effect = QGraphicsOpacityEffect(widget)
            self._effects[widget] = effect
            widget.setGraphicsEffect(effect)
            effect.setOpacity(0)
            widget.show()  # Ensure widget is visible

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(duration)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(easing)
            group.addAnimation(anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def fade_out(self, widgets: Union[QWidget, List[QWidget]],
                 duration: int = 500, easing: QEasingCurve.Type = QEasingCurve.InCubic,
                 hide_on_finish: bool = True, on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Fade out widgets with opacity animation"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            effect = widget.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(widget)
                self._effects[widget] = effect
                widget.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(duration)
            anim.setStartValue(1)
            anim.setEndValue(0)
            anim.setEasingCurve(easing)
            group.addAnimation(anim)

            if hide_on_finish:
                anim.finished.connect(lambda: widget.hide())

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def slide_in(self, widgets: Union[QWidget, List[QWidget]],
                 direction: AnimationDirection = AnimationDirection.LEFT,
                 distance: int = 300, duration: int = 500,
                 easing: QEasingCurve.Type = QEasingCurve.OutBack,
                 fade: bool = False, on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Slide in widgets from specified direction"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            start_pos = widget.pos()
            offset = QPoint(0, 0)

            if direction == AnimationDirection.LEFT:
                offset = QPoint(-distance, 0)
            elif direction == AnimationDirection.RIGHT:
                offset = QPoint(distance, 0)
            elif direction == AnimationDirection.TOP:
                offset = QPoint(0, -distance)
            elif direction == AnimationDirection.BOTTOM:
                offset = QPoint(0, distance)

            widget.move(start_pos + offset)
            widget.show()

            # Position animation
            pos_anim = QPropertyAnimation(widget, b"pos")
            pos_anim.setDuration(duration)
            pos_anim.setStartValue(widget.pos())
            pos_anim.setEndValue(start_pos)
            pos_anim.setEasingCurve(easing)
            group.addAnimation(pos_anim)

            # Optional fade animation
            if fade:
                effect = QGraphicsOpacityEffect(widget)
                self._effects[widget] = effect
                widget.setGraphicsEffect(effect)
                effect.setOpacity(0)

                fade_anim = QPropertyAnimation(effect, b"opacity")
                fade_anim.setDuration(duration)
                fade_anim.setStartValue(0)
                fade_anim.setEndValue(1)
                group.addAnimation(fade_anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def slide_out(self, widgets: Union[QWidget, List[QWidget]],
                  direction: AnimationDirection = AnimationDirection.LEFT,
                  distance: int = 300, duration: int = 500,
                  easing: QEasingCurve.Type = QEasingCurve.InBack,
                  fade: bool = False, hide_on_finish: bool = True,
                  on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Slide out widgets to specified direction"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            start_pos = widget.pos()
            offset = QPoint(0, 0)

            if direction == AnimationDirection.LEFT:
                offset = QPoint(-distance, 0)
            elif direction == AnimationDirection.RIGHT:
                offset = QPoint(distance, 0)
            elif direction == AnimationDirection.TOP:
                offset = QPoint(0, -distance)
            elif direction == AnimationDirection.BOTTOM:
                offset = QPoint(0, distance)

            # Position animation
            pos_anim = QPropertyAnimation(widget, b"pos")
            pos_anim.setDuration(duration)
            pos_anim.setStartValue(start_pos)
            pos_anim.setEndValue(start_pos + offset)
            pos_anim.setEasingCurve(easing)
            group.addAnimation(pos_anim)

            # Optional fade animation
            if fade:
                effect = widget.graphicsEffect()
                if not isinstance(effect, QGraphicsOpacityEffect):
                    effect = QGraphicsOpacityEffect(widget)
                    self._effects[widget] = effect
                    widget.setGraphicsEffect(effect)

                fade_anim = QPropertyAnimation(effect, b"opacity")
                fade_anim.setDuration(duration)
                fade_anim.setStartValue(1)
                fade_anim.setEndValue(0)
                group.addAnimation(fade_anim)

            if hide_on_finish:
                pos_anim.finished.connect(lambda: widget.hide())

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def unfold_horizontal(self, widgets: Union[QWidget, List[QWidget]],
                          duration: int = 400, easing: QEasingCurve.Type = QEasingCurve.OutElastic,
                          fade: bool = True, on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Unfold widgets horizontally with optional fade effect"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            final_rect = widget.geometry()
            center = final_rect.center()
            start_rect = QRect(center.x(), final_rect.y(), 0, final_rect.height())
            widget.setGeometry(start_rect)
            widget.show()

            # Geometry animation
            anim = QPropertyAnimation(widget, b"geometry")
            anim.setDuration(duration)
            anim.setStartValue(start_rect)
            anim.setEndValue(final_rect)
            anim.setEasingCurve(easing)
            group.addAnimation(anim)

            # Optional fade animation
            if fade:
                effect = QGraphicsOpacityEffect(widget)
                self._effects[widget] = effect
                widget.setGraphicsEffect(effect)
                effect.setOpacity(0)

                fade_anim = QPropertyAnimation(effect, b"opacity")
                fade_anim.setDuration(duration)
                fade_anim.setStartValue(0)
                fade_anim.setEndValue(1)
                group.addAnimation(fade_anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def unfold_vertical(self, widgets: Union[QWidget, List[QWidget]],
                        duration: int = 400, easing: QEasingCurve.Type = QEasingCurve.OutElastic,
                        fade: bool = True, on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Unfold widgets vertically with optional fade effect"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            final_rect = widget.geometry()
            center = final_rect.center()
            start_rect = QRect(final_rect.x(), center.y(), final_rect.width(), 0)
            widget.setGeometry(start_rect)
            widget.show()

            # Geometry animation
            anim = QPropertyAnimation(widget, b"geometry")
            anim.setDuration(duration)
            anim.setStartValue(start_rect)
            anim.setEndValue(final_rect)
            anim.setEasingCurve(easing)
            group.addAnimation(anim)

            # Optional fade animation
            if fade:
                effect = QGraphicsOpacityEffect(widget)
                self._effects[widget] = effect
                widget.setGraphicsEffect(effect)
                effect.setOpacity(0)

                fade_anim = QPropertyAnimation(effect, b"opacity")
                fade_anim.setDuration(duration)
                fade_anim.setStartValue(0)
                fade_anim.setEndValue(1)
                group.addAnimation(fade_anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def pop(self, widgets: Union[QWidget, List[QWidget]],
            scale_factor: float = 1.2, duration: int = 300,
            easing: QEasingCurve.Type = QEasingCurve.OutBack,
            on_finished: Optional[callable] = None) -> QSequentialAnimationGroup:
        """Create a pop animation (scale up then down)"""
        widgets = self._ensure_list(widgets)
        group = QSequentialAnimationGroup()
        scale_up = QParallelAnimationGroup()
        scale_down = QParallelAnimationGroup()

        for widget in widgets:
            original_size = widget.size()
            scaled_size = QSize(original_size.width() * scale_factor,
                                original_size.height() * scale_factor)

            # Scale up animation
            up_anim = QPropertyAnimation(widget, b"size")
            up_anim.setDuration(duration // 2)
            up_anim.setStartValue(original_size)
            up_anim.setEndValue(scaled_size)
            up_anim.setEasingCurve(QEasingCurve.OutQuad)
            scale_up.addAnimation(up_anim)

            # Scale down animation
            down_anim = QPropertyAnimation(widget, b"size")
            down_anim.setDuration(duration // 2)
            down_anim.setStartValue(scaled_size)
            down_anim.setEndValue(original_size)
            down_anim.setEasingCurve(easing)
            scale_down.addAnimation(down_anim)

        group.addAnimation(scale_up)
        group.addAnimation(scale_down)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def shake(self, widgets: Union[QWidget, List[QWidget]],
              intensity: int = 10, duration: int = 500,
              on_finished: Optional[callable] = None) -> QSequentialAnimationGroup:
        """Create a shake animation"""
        widgets = self._ensure_list(widgets)
        group = QSequentialAnimationGroup()

        for widget in widgets:
            original_pos = widget.pos()
            shake_anim = QPropertyAnimation(widget, b"pos")
            shake_anim.setDuration(duration)

            # Create key frames for shaking
            shake_anim.setKeyValues([
                (0.0, original_pos),
                (0.1, original_pos + QPoint(intensity, 0)),
                (0.2, original_pos + QPoint(-intensity, 0)),
                (0.3, original_pos + QPoint(intensity, 0)),
                (0.4, original_pos + QPoint(-intensity, 0)),
                (0.5, original_pos + QPoint(intensity, 0)),
                (0.6, original_pos + QPoint(-intensity, 0)),
                (0.7, original_pos + QPoint(intensity, 0)),
                (0.8, original_pos + QPoint(-intensity, 0)),
                (0.9, original_pos + QPoint(intensity // 2, 0)),
                (1.0, original_pos)
            ])

            shake_anim.setEasingCurve(QEasingCurve.InOutQuad)
            group.addAnimation(shake_anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def pulse(self, widgets: Union[QWidget, List[QWidget]],
              scale_factor: float = 1.1, duration: int = 1000,
              loops: int = -1, on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Create a continuous pulsing animation"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            original_size = widget.size()
            scaled_size = QSize(original_size.width() * scale_factor,
                                original_size.height() * scale_factor)

            anim = QPropertyAnimation(widget, b"size")
            anim.setDuration(duration)
            anim.setStartValue(original_size)
            anim.setKeyValueAt(0.5, scaled_size)
            anim.setEndValue(original_size)
            anim.setEasingCurve(QEasingCurve.InOutSine)
            anim.setLoopCount(loops)
            group.addAnimation(anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def add_shadow(self, widgets: Union[QWidget, List[QWidget]],
                   color: QColor = QColor(0, 0, 0, 150),
                   blur_radius: float = 15.0, offset: QPoint = QPoint(3, 3),
                   duration: int = 300, on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Add shadow effect with animation"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            effect = QGraphicsDropShadowEffect(widget)
            self._effects[widget] = effect
            widget.setGraphicsEffect(effect)

            effect.setColor(color)
            effect.setBlurRadius(0)
            effect.setOffset(offset)

            anim = QPropertyAnimation(effect, b"blurRadius")
            anim.setDuration(duration)
            anim.setStartValue(0)
            anim.setEndValue(blur_radius)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            group.addAnimation(anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def remove_shadow(self, widgets: Union[QWidget, List[QWidget]],
                      duration: int = 300, on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Remove shadow effect with animation"""
        widgets = self._ensure_list(widgets)
        group = QParallelAnimationGroup()

        for widget in widgets:
            effect = widget.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                anim = QPropertyAnimation(effect, b"blurRadius")
                anim.setDuration(duration)
                anim.setStartValue(effect.blurRadius())
                anim.setEndValue(0)
                anim.setEasingCurve(QEasingCurve.InCubic)
                anim.finished.connect(lambda: self._cleanup_effect(widget))
                group.addAnimation(anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        self._track(group)
        return group

    def delayed_execution(self, delay: int, callback: callable) -> QTimer:
        """Execute a callback after a delay"""
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(delay)
        return timer

    def stop_all(self):
        """Stop all running animations"""
        for anim in self._animations[:]:  # Create a copy to avoid modification during iteration
            anim.stop()
            if hasattr(anim, 'deleteLater'):
                anim.deleteLater()
        self._animations.clear()

        # Clean up all effects
        for widget, effect in self._effects.items():
            effect.setEnabled(False)
            widget.setGraphicsEffect(None)
        self._effects.clear()
