import random
import pygame
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import time

# Initialize Pygame
pygame.init()

# Create Window/Display
width, height = 1280, 720
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Balloon Pop")

# Initialize Clock for FPS
fps = 30
clock = pygame.time.Clock()

# Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # width
cap.set(4, 720)  # height

# Load Balloon Image
imgBalloon = pygame.image.load('BalloonRed.png').convert_alpha()
rectBalloon = imgBalloon.get_rect()
rectBalloon.x, rectBalloon.y = 500, 300

# Game Variables
speed = 14
score = 0
startTime = time.time()
totalTime = 30

# Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Reset Balloon Position
def resetBalloon():
    rectBalloon.x = random.randint(100, width - 100)
    rectBalloon.y = height + 50

# Main Game Loop
start = True
while start:
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            start = False
            pygame.quit()

    # Calculate Remaining Time
    timeRemain = int(totalTime - (time.time() - startTime))
    
    if timeRemain < 0:
        window.fill((255, 255, 255))
        font = pygame.font.SysFont('Arial', 50)
        textScore = font.render(f'Your Score: {score}', True, (50, 50, 255))
        textTime = font.render('Time UP', True, (50, 50, 255))
        window.blit(textScore, (450, 350))
        window.blit(textTime, (530, 275))
    else:
        # Read from webcam
        success, img = cap.read()
        if not success:
            continue  # Skip loop if frame is not read properly

        img = cv2.flip(img, 1)
        hands, img = detector.findHands(img, flipType=False)

        # Move the balloon up
        rectBalloon.y -= speed

        # If balloon reaches top without being popped
        if rectBalloon.y < 0:
            resetBalloon()
            speed += 1.5
            if speed > 22:
                speed = 22

        # Check if hand pops the balloon
        if hands:
            hand = hands[0]
            x, y = hand['lmList'][8][0:2]  # Index fingertip
            if rectBalloon.collidepoint(x, y):
                resetBalloon()
                score += 10
                speed += 1.5
                if speed > 22:
                    speed = 22

        # Convert and display OpenCV frame in pygame
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        imgRGB = np.rot90(imgRGB)
        frame = pygame.surfarray.make_surface(imgRGB).convert()
        frame = pygame.transform.flip(frame, True, False)
        window.blit(frame, (0, 0))
        window.blit(imgBalloon, rectBalloon)

        # Score and Time UI
        font = pygame.font.Font('Marcellus-Regular.ttf', 50)  # Replace with Arial if needed
        textScore = font.render(f'Score: {score}', True, (50, 50, 255))
        textTime = font.render(f'Time: {timeRemain}', True, (50, 50, 255))
        window.blit(textScore, (35, 35))
        window.blit(textTime, (1000, 35))

    # Update Display
    pygame.display.update()
    clock.tick(fps)