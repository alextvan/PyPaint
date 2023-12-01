import pygame
import sys
import collections

pygame.init()
pygame.display.set_caption("PyPaint")

WIDTH = 900
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH,HEIGHT))

clock = pygame.time.Clock()

#Images
pencilIcon = pygame.image.load("PencilIcon.png")
paintIcon = pygame.image.load("PaintIcon.png")
eraserIcon = pygame.image.load("EraserIcon.png")
fillIcon = pygame.transform.scale(pygame.image.load("FillIcon.png"),(95, 95))
logo = pygame.image.load("PyPaintLogo.png")
scaledLogo = pygame.transform.scale(logo,(300, 70))
background = pygame.image.load("Background.png")

# Start Icons
pygame.display.set_icon(paintIcon) # Icon Image
# Background images/Icons 
screen.blit(background, (0,0))

# Canvas Features
CANVASORIGINPOS = [100, 70] # Starts at x = 100, y = 55
CANVASDIMENSIONS = [600, 400] # 600 x 400 canvas
pygame.draw.rect(screen, (255,255,255), (CANVASORIGINPOS[0], CANVASORIGINPOS[1], CANVASDIMENSIONS[0], CANVASDIMENSIONS[1]), 0, 5)

# Colorbar (bottom bar) Features
COLORBARPOS = [CANVASORIGINPOS[0], CANVASORIGINPOS[1] + CANVASDIMENSIONS[1] + 20]
COLORBARDIMENSIONS = [CANVASDIMENSIONS[0], 90]

pygame.draw.rect(screen, (255,255,255), (COLORBARPOS[0], COLORBARPOS[1], COLORBARDIMENSIONS[0], COLORBARDIMENSIONS[1]), 0, 5)

YBARCENTER = COLORBARDIMENSIONS[1]//2 + COLORBARPOS[1]

# Circle background for selected brush color
pygame.draw.circle(screen, (200,200,200), (CANVASORIGINPOS[0]+30, YBARCENTER), 20)

canvasBoundH = CANVASORIGINPOS[0] + CANVASDIMENSIONS[0]
canvasBoundV = CANVASORIGINPOS[1] + CANVASDIMENSIONS[1]

# FLAGS FOR TOOLS AND BUTTONS
# disable/enable drawing inside the canvas
drawFlag = False

# flags for pencil/drawing button
drawButtonFlag, drawEnable = False, False

eraserButtonFlag, eraserEnable = False, False

fillButtonFlag, fillEnable = False, False
global fillInProcess
fillInProcess = False

# Default brush size circle has radius 4, 
# Default brush size line has default width 7
brushSizeC, brushSizeL = 4, 7

# COLORS
HIGHLIGHTCOLOR = (230,230,230)
BLACK = (0,0,0)
WHITE = (255,255,255)
DBLUE = (55, 69, 229)
PINK = (229, 55, 159)
RED = (203, 32, 41)
YELLOW = (255, 248, 77)
GREEN = (38, 172, 66)

brushColor = BLACK


# Drawing mechanic
def toolFunc():
    if drawFlag:

        # Cumulative relative mouse position
        relX = mx+umx
        relY = my+umy

        # Check that all positions (cumualtive and non-cumulative) are within the canvas
        inBounds = mx > CANVASORIGINPOS[0] and mx < canvasBoundH and my > CANVASORIGINPOS[1] and my < canvasBoundV and relX > CANVASORIGINPOS[0] and relX < canvasBoundH and relY > CANVASORIGINPOS[1] and relY < canvasBoundV

        global fillInProcess

        if drawEnable and inBounds:
            # Draw circles & lines of a specified color
            pygame.draw.circle(screen, brushColor, (mx,my), brushSizeC)
            pygame.draw.line(screen, brushColor, (mx,my),(relX, relY), brushSizeL)

        elif eraserEnable and inBounds:
            # Draw circles & lines of white
            pygame.draw.circle(screen, WHITE, (mx,my), brushSizeC)
            pygame.draw.line(screen, WHITE, (mx,my),(relX, relY), brushSizeL)

        elif fillEnable and inBounds and fillInProcess == False:
            fillInProcess = True
            col = screen.get_at((mx,my))
            print(col)
            #q = collections.deque((mx,my))

            #while q:
            fillInProcess = False



# Update starts here
while True:

    # Mouse position
    mx, my = pygame.mouse.get_pos()
    umx, umy = pygame.mouse.get_rel()

    # Left Icon Buttons/Tools
    drawButton = pygame.Rect(12.5,70, 75, 75)
    eraserButton = pygame.Rect(12.5,170, 75, 75)
    fillButton = pygame.Rect(12.5,270, 75, 75)

    # Highlight Mechanic for Draw Button
    if drawEnable:
        pygame.draw.rect(screen, HIGHLIGHTCOLOR, drawButton, 0, 5)
    else:
        pygame.draw.rect(screen, WHITE, drawButton, 0, 5)
    
    # Highlight Mechanic for Eraser Button
    if eraserEnable:
        pygame.draw.rect(screen, HIGHLIGHTCOLOR, eraserButton, 0, 5)
    else:
        pygame.draw.rect(screen, WHITE, eraserButton, 0, 5)
    
    # Highlight Mechanic for Fill Button
    if fillEnable:
        pygame.draw.rect(screen, HIGHLIGHTCOLOR, fillButton, 0, 5)
    else:
        pygame.draw.rect(screen, WHITE, fillButton, 0, 5)
    

        
    # Overlay icon for tools
    screen.blit(pencilIcon, (0,50))
    screen.blit(eraserIcon, (0, 155))
    screen.blit(fillIcon, (4,256))
    screen.blit(scaledLogo, (5,-5))
    
    # Clicking Mechanic for Draw Button
    if drawButton.collidepoint((mx,my)):
        if pygame.mouse.get_pressed()[0] == True:
            drawButtonFlag = True
        else:
            if drawButtonFlag == True:
                # Any one time button click code goes here
                drawEnable = not drawEnable
                drawButtonFlag = False

                #Change other buttons to unhighlight/false
                eraserEnable = False
                fillEnable = False

    # Clicking Mechanic for Eraser Button
    elif eraserButton.collidepoint((mx,my)):
        if pygame.mouse.get_pressed()[0] == True:
            eraserButtonFlag = True
        else:
            if eraserButtonFlag == True:
                # Any one time button click code goes here
                eraserEnable = not eraserEnable
                eraserButtonFlag = False

                #Change other buttons to unhighlight/false
                drawEnable = False
                fillEnable = False

    # Clicking Mechanic for Fill Button
    elif fillButton.collidepoint((mx,my)):
        if pygame.mouse.get_pressed()[0] == True:
            fillButtonFlag = True
        else:
            if fillButtonFlag == True:
                # Any one time button click code goes here
                fillEnable = not fillEnable
                fillButtonFlag = False

                #Change other buttons to unhighlight/false
                drawEnable = False
                eraserEnable = False
    
    # Renders the right color for the brush color selected
    pygame.draw.circle(screen, brushColor, (CANVASORIGINPOS[0]+30, YBARCENTER), 15)

    pygame.draw.circle(screen, BLACK, (CANVASORIGINPOS[0]+80, YBARCENTER-20), 10)




    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                drawFlag = True
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                drawFlag = False

    toolFunc()
    pygame.display.update()
    clock.tick(60)