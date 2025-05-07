# 绘制动作曲线

segment_precision = 1 / 30 # 每秒30个采样点=>30帧

from typing import Callable

def segment2linear(segment: list[float]) -> list[tuple[float, float]]:
    # segment: [t0, p0, 0, t1, p1]
    # pt = (t - t0) / (t1 - t0) * (p1 - p0) + p0
    print("linear")
    print(segment)
    length = segment[3] - segment[0]
    points = []
    for i in range(1, 31):
        t = i / 30
        points.append((t * length + segment[0], segment[1] + (t - segment[0]) / (segment[3] - segment[0]) * (segment[4] - segment[1])))
    return points

def segment2bezier(segment: list[float]) -> list[tuple[float, float]]:
    # segment: [t0, p0, 1, t1, p1, t2, p2, t3, p3]
    # pt = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    print("bezier")
    print(segment)
    length = segment[7] - segment[0]
    points = []
    for i in range(1, 31):
        t = i / 30
        points.append((t * length + segment[0], (1 - t) ** 3 * segment[1] + 3 * (1 - t) ** 2 * t * segment[4] + 3 * (1 - t) * t ** 2 * segment[6] + t ** 3 * segment[8]))
    return points

def segment2stepped(segment: list[float]) -> list[tuple[float, float]]:
    # segment: [t0, p0, 2, t1, p1]
    # pt = p0 if t < t1 else p1
    print("stepped")
    print(segment)
    length = segment[3] - segment[0]
    points = []
    for i in range(1, 31):
        t =  i / 30
        # points.append((t, segment[1] if t < segment[3] else segment[5]))
    
    return points


def segment2inverseStepped(segment: list[float]) -> list[tuple[float, float]]:
    # segment: [t0, p0, 3, t1, p1]
    # pt = p0 if t < t1 else p1
    print("inverseStepped")
    print(segment)
    length = segment[3] - segment[0]
    points = []
    for i in range(1, 31):
        t =  i / 30
        # points.append((t, segment[1] if t < segment[3] else segment[4]))
    return points

def segments2curves(segments: list[float]) -> list[tuple[float, float]]:
    idx = 2
    size = len(segments)
    last_point = segments[0:2]

    curve = [tuple(last_point)]
    while idx < size:
        identifier = segments[idx]
        
        if identifier == 0:
            segment = segments[idx:idx+3]
            points = segment2linear(last_point + segment)
            idx += 3
        elif identifier == 1:
            segment = segments[idx:idx+7]
            points = segment2bezier(last_point + segment)
            idx += 7
        elif identifier == 2:
            segment = segments[idx:idx+3]
            points = segment2stepped(last_point + segment)
            idx += 3
        elif identifier == 3:
            segment = segments[idx:idx+3]
            points = segment2inverseStepped(last_point + segment)
        else:
            raise Exception("Invalid identifier")
        last_point = segments[idx-2:idx]
        curve.extend(points)
    return curve


if __name__ == "__main__":
    import json
    motion = json.load(open(
        # "Mao/motions/"
        # "mtn_01.motion3.json"
        # "special_01.motion3.json"
        # "monv.motion3.json"
        "test.motion3.json"
    ))
    import matplotlib.pyplot as plt
    for curve in motion["Curves"]:
        # print(curve["Id"])
        plt.title(curve["Id"])
        curve = segments2curves(curve["Segments"])
        # print(curve)
        plt.plot([x[0] for x in curve], [x[1] for x in curve])
        plt.show()