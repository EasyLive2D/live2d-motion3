# live2d-motion3

使用纯 Python 读取 `motion3.json` 文件，并使用 `live2d-py` 的 `SetParameterValue` 控制模型动画

`motion3.json` 本质是一系列控制曲线，曲线由多段差值函数组成。

被控制的对象有：模型透明度、Part透明度、Parameter 的值等。

本仓库以 Parameter 为例，其他对象类似。

[motion_interploate.py](./motion_interpolate.py)：实现插值函数，读取 `motion3.json` 文件并播放动画。

按空格键播放动画：

![动画](./docs/Snipaste_2025-04-22_17-28-10.png)

[motion_visualize.py](./motion_visualize.py)：将 `motion3.json` 中各个 Parameter 的曲线可视化

使用 matplotlib 绘制曲线：

![曲线](./docs/Snipaste_2025-04-22_17-27-40.png)

[Main.py](./Main.py): motion3 动作编辑器

- **新建**：选择模型文件，创建空白动作
- **打开**：选择模型 + 已有 `.motion3.json` 文件，加载并编辑
- **保存**：导出为 `.motion3.json`

曲线编辑支持直线、三次贝塞尔、前后键水平插值四种段类型，可调节帧率和总帧数。

![编辑器](./docs/2025-04-25%2011-46-16%2000_00_04-00_00_09.gif)

## 依赖

- Python 3.10+
- PySide6 — GUI 框架
- live2d-py — Live2D 渲染
- matplotlib — 曲线可视化（仅 motion_visualize.py）
- pygame — 动画测试（仅 test_motion.py）
