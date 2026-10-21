"""The Host's two inscriptions, with the existing Framework button input."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from raven_framework.components.button import Button


class HostChoice(Button):
    """Only painting changes; click, hover and dwell remain Framework behavior."""

    def __init__(self, label: str):
        super().__init__(center_text=label, width=180, height=56,
                         use_fill_dwell=False, use_gradient_border=False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(.5 if self.disabled else 1.)
        ink = QColor("#F7EFDC")
        brass = QColor("#91774F")
        font = QFont("Georgia")
        font.setStyleHint(QFont.StyleHint.Serif)
        font.setPixelSize(28)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font)
        painter.setPen(ink)
        painter.drawText(QRectF(10, 0, 160, 40), Qt.AlignmentFlag.AlignCenter, self.text)
        painter.setPen(QPen(brass, 1))
        painter.drawLine(QPointF(24, 44), QPointF(156, 44))
        painter.setBrush(brass)
        for x in (17, 163):
            painter.drawPolygon(QPolygonF([
                QPointF(x, 41), QPointF(x + 3, 44),
                QPointF(x, 47), QPointF(x - 3, 44),
            ]))
        # Existing input progress stays visible without a bright filled plate.
        if self.progress > 0:
            painter.setPen(QPen(ink, 2))
            painter.drawLine(QPointF(24, 44),
                             QPointF(24 + 132 * min(1., self.progress / 100), 44))
