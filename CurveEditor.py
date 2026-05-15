from motion_interpolate import Segment, LinearSegment, BezierSegment, SteppedSegment, InverseSteppedSegment, Point
import sys

from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import Qt, QPointF, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QMouseEvent, QPainterPath, QColor


class CurveEditor(QWidget):
    SEG_TYPE_LINEAR = 0
    SEG_TYPE_BEZIER = 1
    SEG_TYPE_STEPPED = 2
    SEG_TYPE_INVERSE_STEPPED = 3

    segTypeChanged = Signal(int)

    curveValueChanged = Signal(float, float, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(300)

        # 分:秒:帧
        # 默认最大比例，屏幕50宽 => 00:00:01 帧
        self.scale = 30
        self.fps = 30
        self.duration = 60 # 默认总帧数120

        self.margin = 3
        self.origin = 50, 25
        self.chartSize = [self.duration * self.scale, 250]

        self.segments: list[Segment] = []

        self.points: list[Point] = []

        self.selectedPoint = None

        self.clickedX = self.origin[0]
        self.clickedY = 0
        self.moved = False

        self.selectedSegment: None | Segment = None

        self.selectedControlPoint: None | Point = None

        self.maxValue = 30
        self.minValue = -30

        self.cursorX = 0

        self.targetId = "TargetId"

        self.setMouseTracking(True)

        self.setFixedWidth(self.chartSize[0] + self.origin[0] * 2)

        self.defaultSegType = CurveEditor.SEG_TYPE_BEZIER

        self.noInterpolate = False
    
    def getNumFrames(self, x):
        return (x - self.origin[0]) / self.scale

    def timeToScreenX(self, t_seconds):
        return t_seconds * self.fps * self.scale + self.origin[0]

    def setNoInterpolate(self, noInterpolate: bool):
        self.noInterpolate = noInterpolate

    def setFps(self, fps: int):
        self.fps = fps
        self.setDuration(self.duration)

    def isEndReached(self):
        return self._alignX(self.clickedX) >= self.origin[0] + self.chartSize[0]

    def moveToLastFrame(self):
        self.clickedX = self.origin[0] + self.chartSize[0]

        self._changeValue()

        self.update()

    def moveToFirstFrame(self):
        self.clickedX = self.origin[0]

        self._changeValue()

        self.update()

    def moveToPrevFrame(self):
        if self.clickedX - self.scale < self.origin[0]:
            return
        
        self.clickedX = self._alignX(self.clickedX) - self.scale
        self._changeValue()

        self.update()
        return

    def moveToNextFrame(self):
        if self.clickedX + self.scale > self.origin[0] + self.chartSize[0]:
            return
        
        self.clickedX = self._alignX(self.clickedX) + self.scale
        self._changeValue()

        self.update()

    def setTarget(self, targetId: str, segments: list[Segment], maxValue: float, minValue: float):
        self.targetId = targetId
        self.segments = segments

        self.points = [seg.getStartPoint() for seg in segments] + [seg.getEndPoint() for seg in segments]

        self.maxValue = maxValue
        self.minValue = minValue

        self.selectedControlPoint = None
        self.selectedSegment = None
        self.selectedPoint = None

        self.update()

    def _alignX(self, x):
        return round((x - self.origin[0]) / self.scale, 0) * self.scale + self.origin[0]
    
    def _y2value(self, y):
        return (y - self.origin[1]) / self.chartSize[1] * (self.minValue - self.maxValue) + self.maxValue

    def getT(self):
        return self._alignX(self.clickedX)
    
    def percentOfY(self, y):
        return (y - self.origin[1]) / self.chartSize[1]

    def valueToScreenY(self, value, min_val, max_val):
        v_range = max_val - min_val if max_val != min_val else 1.0
        normalized = (value - min_val) / v_range
        return normalized * self.chartSize[1] + self.origin[1]

    @staticmethod
    def format_time(num_frames, fps):
        total_frames = int(round(num_frames))
        total_seconds = total_frames // fps
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        frames = total_frames % fps
        return "%02d:%02d:%02d" % (minutes, seconds, frames)

    def _changeValue(self):
        if self.clickedX < self.origin[0] or self.clickedX > self.origin[0] + self.chartSize[0]:
            return
        
        x = self._alignX(self.clickedX)
        num_frames = (x - self.origin[0]) / self.scale
        if not self.noInterpolate:
            for seg in self.segments:
                if seg.contains(x):
                    y = seg.interpolate(x)
                    value = self._y2value(y)
                    self.curveValueChanged.emit(num_frames, value, True)
                    break
            else:
                self.curveValueChanged.emit(num_frames, 0, False)
        else:
            self.curveValueChanged.emit(num_frames, 0, False)

    def setDuration(self, duration: int):
        self.duration = duration
        self.chartSize = [self.duration * self.scale, 250]
        self.setFixedWidth(self.chartSize[0] + self.origin[0] * 2)
        self.update()
    
    def setSegmentType(self, t: int):
        if t == self.defaultSegType:
            return
        
        self.defaultSegType = t

        if self.selectedSegment is None:
            return
        
        sp = self.selectedSegment.getStartPoint()
        ep = self.selectedSegment.getEndPoint()
        if t == CurveEditor.SEG_TYPE_BEZIER:
            idx = self.segments.index(self.selectedSegment)
            self.selectedSegment = BezierSegment(sp, Point(sp.t + (ep.t - sp.t) * 0.33, sp.value), Point(sp.t + (ep.t - sp.t) * 0.67, ep.value), ep)
            self.segments[idx] = self.selectedSegment
        elif t == CurveEditor.SEG_TYPE_LINEAR:
            idx = self.segments.index(self.selectedSegment)
            self.selectedSegment = LinearSegment(sp, ep)
            self.segments[idx] = self.selectedSegment
        elif t == CurveEditor.SEG_TYPE_STEPPED:
            idx = self.segments.index(self.selectedSegment)
            self.selectedSegment = SteppedSegment(sp, ep)
            self.segments[idx] = self.selectedSegment
        elif t == CurveEditor.SEG_TYPE_INVERSE_STEPPED:
            idx = self.segments.index(self.selectedSegment)
            self.selectedSegment = InverseSteppedSegment(sp, ep)
            self.segments[idx] = self.selectedSegment
        
        self.update()

    def setScale(self, scale: int):
        last_scale = self.scale
        self.scale = scale
        self.chartSize = [self.duration * self.scale, 250]

        for p in self.points:
            p.t = round((p.t - self.origin[0]) / last_scale, 0) * self.scale + self.origin[0]
        
        for seg in self.segments:
            if isinstance(seg, BezierSegment):
                seg.p1.t = (seg.p1.t - self.origin[0]) / last_scale * self.scale + self.origin[0]
                seg.p2.t = (seg.p2.t - self.origin[0]) / last_scale * self.scale + self.origin[0] 

        self.setFixedWidth(self.chartSize[0] + self.origin[0] * 2)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        self._draw_background(painter)

        self._draw_grid(painter)

        # self._draw_axes(painter)
        self._draw_t_hint(painter)

        self._draw_curves(painter)

        self._draw_points(painter)

        self._draw_control_points(painter)

        self._draw_current_t_hint(painter)  

    def _draw_t_hint(self, painter: QPainter):
        if self.cursorX < self.origin[0] or self.cursorX > self.origin[0] + self.chartSize[0]:
            return
        
        x = self._alignX(self.cursorX)
        
        painter.setPen(Qt.GlobalColor.cyan)
        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(x, self.origin[1], x, self.origin[1] + self.chartSize[1])
    
    def _draw_current_t_hint(self, painter: QPainter):
        if self.clickedX < self.origin[0] or self.clickedX > self.origin[0] + self.chartSize[0]:
            return
        
        x = self._alignX(self.clickedX)
        
        painter.setPen(Qt.GlobalColor.blue)
        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(x, self.origin[1], x, self.origin[1] + self.chartSize[1])

        path = QPainterPath()
        path.moveTo(x, self.origin[1])
        path.lineTo(x - 5, self.origin[1] - 3)
        path.lineTo(x - 5, self.origin[1] - 13)
        path.lineTo(x + 5, self.origin[1] - 13)
        path.lineTo(x + 5, self.origin[1] - 3)
        path.lineTo(x, self.origin[1])
        painter.fillPath(path, Qt.GlobalColor.blue)
    
    def _draw_background(self, painter: QPainter):
        margin = 3
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.fillRect(self.origin[0] - margin, self.origin[1] - margin, self.chartSize[0] + margin * 2, self.chartSize[1] + margin * 2, Qt.GlobalColor.gray)
        painter.fillRect(self.origin[0], self.origin[1], self.chartSize[0], self.chartSize[1], Qt.GlobalColor.white)

    def _draw_axes(self, painter: QPainter):
        painter.setPen(QPen(Qt.GlobalColor.black))
        # t
        painter.drawLine(self.origin[0], self.origin[1], self.origin[0] + self.chartSize[0], self.origin[1])
        # v
        painter.drawLine(self.origin[0], self.origin[1], self.origin[0], self.origin[1] - self.chartSize[1])

    def _draw_points(self, painter: QPainter):
        outline = QPainterPath()
        fill = QPainterPath()
        for p in self.points:
            c = QPointF(p.t, p.value)
            outline.clear()
            outline.addEllipse(c, 5, 5)
            painter.fillPath(outline, Qt.GlobalColor.red if self.selectedPoint == p else Qt.GlobalColor.black)
            fill.clear()
            fill.addEllipse(c, 4, 4)
            painter.fillPath(fill, Qt.GlobalColor.lightGray)

    def _draw_curves(self, painter: QPainter):
        if len(self.segments) <= 0:
            return
        # print(self.points)
        # print(self.segments)
        for seg in self.segments:
            points = []
            if isinstance(seg, BezierSegment):
                for i in range(31):
                    t = i / 30
                    points.append(QPointF(seg.p0.t + t * (seg.p3.t - seg.p0.t), seg.interpolate(seg.p0.t + t * (seg.p3.t - seg.p0.t))))
            elif isinstance(seg, LinearSegment):
                points.append(QPointF(seg.p0.t, seg.p0.value))
                points.append(QPointF(seg.p1.t, seg.p1.value))
            elif isinstance(seg, SteppedSegment):
                points.append(QPointF(seg.p0.t, seg.p0.value))
                points.append(QPointF(seg.p1.t, seg.p0.value))
                points.append(QPointF(seg.p1.t, seg.p1.value))
                points.append(QPointF(seg.p1.t, seg.p0.value))
            elif isinstance(seg, InverseSteppedSegment):
                points.append(QPointF(seg.p0.t, seg.p0.value))
                points.append(QPointF(seg.p0.t, seg.p1.value))
                points.append(QPointF(seg.p1.t, seg.p1.value))
                points.append(QPointF(seg.p0.t, seg.p1.value))
            painter.setPen(Qt.GlobalColor.black if seg != self.selectedSegment else Qt.GlobalColor.red)
            pen = painter.pen()
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawPolyline(points)

    def _draw_grid(self, painter: QPainter):
        last_i = 0
        for i in range(self.duration):
            x = self.origin[0] + i * self.scale
            painter.setPen(Qt.GlobalColor.lightGray)
            painter.drawLine(x, self.origin[1] - 5, x, self.origin[1] + self.chartSize[1])
            secs = i // self.fps
            frames = i % self.fps 
            if (i - last_i) * self.scale >= 50:
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(x, self.origin[1] - 5, "%d:%02d" % (secs, frames))
                last_i = i
        
        start_y = self.origin[1]
        for i in range(7):
            y = start_y + i * self.chartSize[1] / 6
            painter.setPen(Qt.GlobalColor.lightGray)
            painter.drawLine(self.origin[0] - 10, y, self.origin[0] + self.chartSize[0], y)
            value = self._y2value(y)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(10, y - 5, "%.2f" % value)

    def _draw_control_points(self, painter: QPainter):
        if self.selectedSegment is None:
            return
        
        outline = QPainterPath()
        fill = QPainterPath()
        if isinstance(self.selectedSegment, BezierSegment):
            # orange
            painter.setPen(QColor.fromRgb(255, 165, 0))
            pen = painter.pen()
            pen.setWidth(2)
            painter.setPen(pen)
            point = QPointF(self.selectedSegment.p1.t, self.selectedSegment.p1.value)
            outline.addEllipse(point, 5, 5)
            fill.addEllipse(point, 4, 4)

            painter.drawLine(point, QPointF(self.selectedSegment.p0.t, self.selectedSegment.p0.value))
            painter.fillPath(outline, Qt.GlobalColor.red if self.selectedControlPoint == self.selectedSegment.p1 else Qt.GlobalColor.blue)
            painter.fillPath(fill, Qt.GlobalColor.cyan)

            outline.clear()
            point = QPointF(self.selectedSegment.p2.t, self.selectedSegment.p2.value)
            outline.addEllipse(point, 5, 5)
            fill.addEllipse(point, 4, 4)

            painter.drawLine(point, QPointF(self.selectedSegment.p3.t, self.selectedSegment.p3.value))
            painter.fillPath(outline, Qt.GlobalColor.red if self.selectedControlPoint == self.selectedSegment.p2 else Qt.GlobalColor.blue)
            painter.fillPath(fill, Qt.GlobalColor.cyan)
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = event.pos().x(), event.pos().y()
            self.selectedPoint = self._get_selected_point(x, y)
            if self.selectedPoint is not None:
                for seg in self.segments:
                    # 只能通过起始点选择
                    if seg.getStartPoint() == self.selectedPoint:
                        self.selectedSegment = seg
                        break

            if self.selectedSegment is not None:
                if isinstance(self.selectedSegment, BezierSegment):
                    self.defaultSegType = self.SEG_TYPE_BEZIER
                    self.selectedControlPoint = self._get_selected_control_point(x, y)
                elif isinstance(self.selectedSegment, LinearSegment):
                    self.defaultSegType = self.SEG_TYPE_LINEAR
                    self.selectedControlPoint = None
                elif isinstance(self.selectedSegment, SteppedSegment):
                    self.defaultSegType = self.SEG_TYPE_STEPPED
                    self.selectedControlPoint = None
                elif isinstance(self.selectedSegment, InverseSteppedSegment):
                    self.defaultSegType = self.SEG_TYPE_INVERSE_STEPPED
                    self.selectedControlPoint = None
                self.segTypeChanged.emit(self.defaultSegType)
            if self.selectedPoint is None and self.selectedControlPoint is None:
                self.selectedSegment = None
                if x <= self.origin[0] + self.chartSize[0] and x >= self.origin[0]:
                    self.clickedX, self.clickedY = max(x, self.origin[0]), y
                self._changeValue()

            self.update()
    
    def show_coordinate(self, point: QPoint, x, y):
        num_frames = (x - self.origin[0]) / self.scale
        value = self._y2value(y)
        QToolTip.showText(point, "%s\n%s, %.2f" % (self.targetId, self.format_time(num_frames, self.fps), value))

    def mouseMoveEvent(self, event: QMouseEvent):
        x, y = event.pos().x(), event.pos().y()

        self.cursorX = x

        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.selectedControlPoint is not None:
                x = max(self.selectedSegment.p0.t + 1, x)
                x = min(x, self.selectedSegment.p3.t - 1)
                
                x = min(x, self.origin[0] + self.chartSize[0])
                x = max(x, self.origin[0])
                y = min(y, self.origin[1] + self.chartSize[1])
                y = max(y, self.origin[1])
                
                self.selectedControlPoint.t = x
                self.selectedControlPoint.value = y

                self.show_coordinate(event.globalPosition().toPoint(), x, y)

            elif self.selectedPoint is not None:
                selected_index = self.points.index(self.selectedPoint)

                x = self._alignX(x)

                if selected_index > 0 and self.points[selected_index - 1].t >= x:
                    return
                
                if selected_index < len(self.points) - 1 and self.points[selected_index + 1].t <= x:
                    return
                
                x = min(x, self.origin[0] + self.chartSize[0])
                x = max(x, self.origin[0])
                y = min(y, self.origin[1] + self.chartSize[1])
                y = max(y, self.origin[1])
                
                tt1 = -1
                tt2 = -1
                originX = self.selectedPoint.t
                self.selectedPoint.t = x
                self.selectedPoint.value = y

                for seg in self.segments:
                    if isinstance(seg, BezierSegment):
                        if seg.p0 == self.selectedPoint:
                            tt1 = (seg.p1.t - originX) / max(seg.p3.t - originX, 0.000001)
                            tt2 = (seg.p2.t - originX) / max(seg.p3.t - originX, 0.000001)
                            seg.p1.t = tt1 * (seg.p3.t - seg.p0.t) + seg.p0.t
                            seg.p2.t = tt2 * (seg.p3.t - seg.p0.t) + seg.p0.t
                        elif seg.p3 == self.selectedPoint:
                            tt1 = (seg.p1.t - seg.p0.t) / max(originX - seg.p0.t, 0.000001)
                            tt2 = (seg.p2.t - seg.p0.t) / max(originX - seg.p0.t, 0.000001)
                            seg.p1.t = tt1 * (seg.p3.t - seg.p0.t) + seg.p0.t
                            seg.p2.t = tt2 * (seg.p3.t - seg.p0.t) + seg.p0.t

                self.show_coordinate(event.globalPosition().toPoint(), x, y)

            elif (self.clickedX - x) ** 2 + (self.clickedY - y) ** 2 > 4:
                self.moved = True
                self.show_coordinate(event.globalPosition().toPoint(), x, y)
                x = event.pos().x()
                if x <= self.origin[0] + self.chartSize[0] and x >= self.origin[0]:
                    self.clickedX, self.clickedY = max(x, self.origin[0]), event.pos().y()
                    self._changeValue()
            else:
                self.show_coordinate(event.globalPosition().toPoint(), x, y)
                x = event.pos().x()
                if x <= self.origin[0] + self.chartSize[0] and x >= self.origin[0]:
                    self.clickedX, self.clickedY = max(x, self.origin[0]), event.pos().y()
                    self._changeValue()

        self.update()


    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.moved:
                self.moved = False
                return
            
            if self.selectedPoint is None and self.selectedControlPoint is None:
                x, y = event.pos().x(), event.pos().y()

                x = self._alignX(x)

                if len(self.points) > 0 and self.points[-1].t >= x:
                    return
                
                if x < self.origin[0] or x > self.origin[0] + self.chartSize[0]:
                    return
                
                if y < self.origin[1] or y > self.origin[1] + self.chartSize[1]:
                    return
                
                self.selectedPoint = Point(x, y)
                self._add_point(self.selectedPoint)

        elif event.button() == Qt.MouseButton.RightButton:
            x, y = event.pos().x(), event.pos().y()
            point = self._get_selected_point(x, y)
            if point is not None:
                self._remove_point(point)
                self.selectedControlPoint = None
                self.selectedSegment = None

        self.update()

        self.moved = False
    
    def _get_selected_point(self, x, y):
        for p in reversed(self.points):
            if (p.t - x) ** 2 + (p.value - y) ** 2 < 25:
                return p
        return None
    
    def _get_selected_control_point(self, x, y):
        if self.selectedSegment is None:
            return None
        
        if not isinstance(self.selectedSegment, BezierSegment):
            return None
        
        if (self.selectedSegment.p1.t - x) ** 2 + (self.selectedSegment.p1.value - y) ** 2 < 25:
            return self.selectedSegment.p1
        
        elif (self.selectedSegment.p2.t - x) ** 2 + (self.selectedSegment.p2.value - y) ** 2 < 25:
            return self.selectedSegment.p2
    
    def _add_point(self, p: Point):
        self.points.append(p)
        if len(self.points) > 1:
            sp = self.points[-2]
            ep = self.points[-1]
            if self.defaultSegType == self.SEG_TYPE_BEZIER:
                p1 = Point(sp.t + (ep.t - sp.t) / 3, sp.value)
                p2 = Point(sp.t + (ep.t - sp.t) * 2 / 3, ep.value)
                self.segments.append(BezierSegment(sp, p1, p2, ep))
            elif self.defaultSegType == self.SEG_TYPE_LINEAR:
                self.segments.append(LinearSegment(sp, ep))
            elif self.defaultSegType == self.SEG_TYPE_STEPPED:
                self.segments.append(SteppedSegment(sp, ep))
            elif self.defaultSegType == self.SEG_TYPE_INVERSE_STEPPED:
                self.segments.append(InverseSteppedSegment(sp, ep))

    def _remove_point(self, p: Point):
        self.points.remove(p)

        if len(self.points) <= 1:
            self.segments.clear()
            return

        idx = 0
        while True:
            if idx >= len(self.segments):
                break
            
            seg = self.segments[idx]
            next_seg = self.segments[idx + 1] if idx < len(self.segments) - 1 else None

            sp = seg.getStartPoint()
            ep = seg.getEndPoint()
            if sp == p: # 第一个段
                self.segments.remove(seg)
                break
            elif ep == p: # 其他段
                if next_seg:
                    seg.setEndPoint(next_seg.getEndPoint())
                    self.segments.remove(next_seg)
                else:
                    self.segments.remove(seg)
                break
            idx += 1
        



if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = CurveEditor()
    win.show()
    app.exec()