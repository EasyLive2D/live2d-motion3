# 实现读取动作并播放

from abc import ABC, abstractmethod
import json
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import live2d.v3 as live2d


class Point:

    def __init__(self, t: float, value: float):
        self.t = t
        self.value = value

    def __repr__(self):
        return f"Point({self.t}, {self.value})"


class Segment(ABC):

    @abstractmethod
    def interpolate(self, t: float) -> float: pass

    def contains(self, t: float) -> bool:
        return self.getStartPoint().t <= t <= self.getEndPoint().t

    @abstractmethod
    def getEndPoint(self) -> Point: pass

    @abstractmethod
    def getStartPoint(self) -> Point: pass

    @abstractmethod
    def setStartPoint(self, p: Point): pass

    @abstractmethod
    def setEndPoint(self, p: Point): pass

    @abstractmethod
    def get_all_points(self) -> list[Point]: pass


class LinearSegment(Segment):

    def __init__(self, p0: Point, p1: Point):
        self.p0 = p0
        self.p1 = p1
    
    def getEndPoint(self) -> Point:
        return self.p1
    
    def getStartPoint(self) -> Point:
        return self.p0
    
    def setStartPoint(self, p: Point):
        self.p0 = p

    def setEndPoint(self, p: Point):
        self.p1 = p

    def get_all_points(self) -> list[Point]:
        return [self.p0, self.p1]

    def interpolate(self, t: float) -> float:
        return self.p0.value + (self.p1.value - self.p0.value) * (t - self.p0.t) / (self.p1.t - self.p0.t)
    
    def __repr__(self) -> str:
        return f"LinearSegment({self.p0}, {self.p1})"


class BezierSegment(Segment):

    def __init__(self, p0: Point, p1: Point, p2: Point, p3: Point):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
    
    def getEndPoint(self) -> Point:
        return self.p3
    
    def getStartPoint(self) -> Point:
        return self.p0
    
    def setStartPoint(self, p: Point):
        self.p0 = p

    def setEndPoint(self, p: Point):
        self.p3 = p

    def get_all_points(self) -> list[Point]:
        return [self.p0, self.p1, self.p2, self.p3]

    def interpolate(self, t):
        tt = self.__solve_tt(t)
        return self.__interpolate_value(tt)
    
    def __solve_tt(self, t) -> float:
        # 二分法找到tt
        tolerance = 0.0001
        max_tt = 1
        min_tt = 0

        for _ in range(20):
            tt = (min_tt + max_tt) / 2
            sot = self.__interpolate_t(tt)
            if abs(sot - t) < tolerance:
                return tt
            elif sot > t:
                max_tt = tt
            else:
                min_tt = tt
        
        return (min_tt + max_tt) / 2
            

    def __interpolate_value(self, tt) -> float:
        return (1 - tt) ** 3 * self.p0.value + \
                3 * (1 - tt) ** 2 * tt * self.p1.value + \
                3 * (1 - tt) * tt ** 2 * self.p2.value + \
                tt ** 3 * self.p3.value
    
    def __interpolate_t(self, tt) -> float:
        return (1 - tt) ** 3 * self.p0.t + \
                3 * (1 - tt) ** 2 * tt * self.p1.t + \
                3 * (1 - tt) * tt ** 2 * self.p2.t + \
                tt ** 3 * self.p3.t
    
    def __repr__(self) -> str:
        return f"BezierSegment(p0={self.p0}, p1={self.p1}, p2={self.p2}, p3={self.p3})"
    

class SteppedSegment(Segment):

    def __init__(self, p0: Point, p1: Point):
        self.p0 = p0
        self.p1 = p1
    
    def getEndPoint(self) -> Point:
        return self.p1
    
    def getStartPoint(self) -> Point:
        return self.p0
    
    def setStartPoint(self, p: Point):
        self.p0 = p

    def setEndPoint(self, p: Point):
        self.p1 = p

    def get_all_points(self) -> list[Point]:
        return [self.p0, self.p1]

    def interpolate(self, t):
        return self.p0.value if t < self.p0.t else self.p1.value
    
    def __repr__(self):
        return f"SteppedSegment(p0={self.p0}, p1={self.p1})"


class InverseSteppedSegment(Segment):

    def __init__(self, p0: Point, p1: Point):
        self.p0 = p0
        self.p1 = p1

    def getEndPoint(self) -> Point:
        return self.p1

    def getStartPoint(self) -> Point:
        return self.p0

    def setStartPoint(self, p: Point):
        self.p0 = p

    def setEndPoint(self, p: Point):
        self.p1 = p

    def get_all_points(self) -> list[Point]:
        return [self.p0, self.p1]

    def interpolate(self, t):
        return self.p1.value
    
    def __repr__(self):
        return f"InverseSteppedSegment(p0={self.p0}, p1={self.p1})"


def get_segment_type(t: Segment) -> int:
    if isinstance(t, LinearSegment):
        return 0
    elif isinstance(t, BezierSegment):
        return 1
    elif isinstance(t, SteppedSegment):
        return 2
    elif isinstance(t, InverseSteppedSegment):
        return 3
    else:
        raise Exception("Invalid segment type")


class Curve:

    def __init__(self, paramId: str):
        self.paramId = paramId
        self.segments: list[Segment] = []
    
    def __repr__(self):
        return f"Curve(paramId={self.paramId}, duration={self.duration}, segments={self.segments})"
    
    def interpolate(self, t: float) -> float | None:
        for segment in self.segments:
            if segment.contains(t):
                return segment.interpolate(t)
            
        return None
    
    def to_json(self, map_t = lambda x: x, map_value = lambda x: x):
        if not self.segments:
            return None

        data = {
            "Target": "Parameter",
            "Id": self.paramId,
            "Segments": []
        }
        for i, seg in enumerate(self.segments):
            points = seg.get_all_points()
            if i == 0:
                data["Segments"].extend([map_t(points[0].t), map_value(points[0].value)])
            t = get_segment_type(seg)
            data["Segments"].append(t)
            for p in points[1:]:
                data["Segments"].extend([map_t(p.t), map_value(p.value)])
        return data

    @staticmethod
    def create(paramId: str, segments: list[float]) -> 'Curve':
        curve = Curve(paramId)
        idx = 2
        size = len(segments)
        last_point = segments[0:2]

        while idx < size:
            identifier = segments[idx]
            
            if identifier == 0:
                segment = segments[idx+1:idx+3]
                seg = LinearSegment(
                    Point(last_point[0], last_point[1]),
                    Point(segment[0], segment[1])
                )
                idx += 3
            elif identifier == 1:
                segment = segments[idx+1:idx+7]
                seg = BezierSegment(
                    Point(last_point[0], last_point[1]),
                    Point(segment[0], segment[1]),
                    Point(segment[2], segment[3]),
                    Point(segment[4], segment[5])
                )
                idx += 7
            elif identifier == 2:
                segment = segments[idx+1:idx+3]
                seg = SteppedSegment(
                    Point(last_point[0], last_point[1]),
                    Point(segment[0], segment[1])
                )
                idx += 3
            elif identifier == 3:
                segment = segments[idx+1:idx+3]
                seg = InverseSteppedSegment(
                    Point(last_point[0], last_point[1]),
                    Point(segment[0], segment[1])
                )
                idx += 3
            else:
                raise Exception("Invalid identifier")
            last_point = segments[idx-2:idx]

            curve.segments.append(seg)
        return curve
    

class Motion:

    def __init__(self):
        self.curves: list[Curve] = []
        self.timeElapsed = 0
        self.duration = 0
        self.fps = 30
        self.started = False

    @staticmethod
    def create(filePath: str) -> 'Motion':
        motion = Motion()
        with open(filePath) as f:
            data = json.load(f)
            curves = motion.curves
            for curveData in data["Curves"]:
                curve = Curve.create(curveData["Id"], curveData["Segments"])
                curves.append(curve)
        motion.duration = data['Meta']["Duration"]
        motion.fps = data['Meta'].get("Fps", 30)
        return motion
    
    def update(self, delta: float, model: 'live2d.Model'):
        self.timeElapsed += delta
        for curve in self.curves:
            v = curve.interpolate(self.timeElapsed)
            if v is None:
                continue
            model.SetParameterValueById(curve.paramId, v)

        if self.timeElapsed >= self.duration:
            self.started = False
    
    def isFinished(self) -> bool:
        return not self.started

    def start(self):
        self.started = True
        self.timeElapsed = 0


if __name__ == "__main__":
    
    import live2d.v3 as live2d
    import pygame
    import time

    pygame.init()
    live2d.init()

    pygame.display.set_mode((800, 600), pygame.DOUBLEBUF | pygame.OPENGL)
    live2d.glInit()
    model = live2d.Model()
    model.LoadModelJson("Mao/Mao.model3.json")
    model.Resize(800, 600)

    model.CreateRenderer(2)

    started = False
    lastCt = time.time()

    motion = Motion.create("Mao.motion3.json")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                del model
                live2d.dispose()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    motion.start()

        ct = time.time()
        delta = ct - lastCt
        lastCt = ct

        live2d.clearBuffer()
        
        finished = motion.isFinished()
        model.LoadParameters()
        if not finished:
            motion.update(delta, model)
        model.SaveParameters()

        if finished:
            model.UpdateBlink(delta)
        
        model.UpdateBreath(delta)
        model.UpdateDrag(delta)
        model.UpdateExpression(delta)
        model.UpdatePhysics(delta)
        model.UpdatePose(delta)
        
        model.Draw()

        pygame.display.flip()
