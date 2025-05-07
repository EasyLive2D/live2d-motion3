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

model.LoadExtraMotion("extra", 0, "monv.motion3.json")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            del model
            live2d.dispose()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                model.StartMotion("extra", 0, 3)
            elif event.key == pygame.K_r:
                model.StopAllMotions()
                model.ResetAllParameters()

    ct = time.time()
    delta = ct - lastCt
    lastCt = ct

    live2d.clearBuffer()
    
    updated = False
    model.LoadParameters()
    if not model.IsMotionFinished():
        updated = model.UpdateMotion(delta)
    model.SaveParameters()

    if updated:
        model.UpdateBlink(delta)
    
    model.UpdateBreath(delta)
    model.UpdateDrag(delta)
    model.UpdateExpression(delta)
    model.UpdatePhysics(delta)
    model.UpdatePose(delta)
    
    model.Draw()

    pygame.display.flip()
