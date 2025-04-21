import os
import random
import pygame
import mediapipe as mp
import cv2
import numpy as np
from Fruit import Fruit
import pymunk
import time

def main_menu():
    pygame.init()
    width, height = 1200, 686
    window = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fruit Slicer - Choose Level")

    font = pygame.font.Font(None, 80)
    options = ["Easy", "Medium", "Hard"]
    selected = 0

    while True:
        window.fill((255, 245, 225))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                if event.key == pygame.K_RETURN:
                    return selected + 1

        for i, text in enumerate(options):
            color = (41, 89, 191) if i == selected else (100, 100, 100)
            text_render = font.render(text, True, color)
            window.blit(text_render, (500, 200 + i * 100))

        pygame.display.update()


def Game(level=1):
    pygame.init()
    pygame.event.clear()

    width, height = 1200, 686
    window = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fruit Slicer")

    fps = 15
    clock = pygame.time.Clock()

    imgGameOver = pygame.image.load("./fru.jpg").convert()
    imgWin = pygame.image.load("./img.png").convert()
    imgWin = pygame.transform.scale(imgWin, (width, height))

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    space = pymunk.Space()
    space.gravity = 0.0, -500.0

    # Настройки уровней
    if level == 1:
        fruit_speed = 2
        bomb_chance = 0
        fruit_size = (1.0, 1.2)
    elif level == 2:
        fruit_speed = 4
        bomb_chance = 0.3
        fruit_size = (0.8, 1.0)
    else:
        fruit_speed = 6
        bomb_chance = 0.5
        fruit_size = (0.6, 0.8)

    # Инициализация звуков с регулировкой громкости
    pygame.mixer.init()
    slice_sound = pygame.mixer.Sound("./slice.wav")
    slice_sound.set_volume(0.1)  # 0.3 - можно менять от 0.0 до 1.0

    explosion_sound = pygame.mixer.Sound("./explosion.wav")
    explosion_sound.set_volume(0.1)  # Можно менять по аналогии

    timeTotal = 60
    fruitList = []
    timeGenerator = time.time()
    timeStart = time.time()
    gameOver = False
    gameWin = False
    score = 0

    pathFruitFolder = "./Fruits"
    pathListFruit = os.listdir(pathFruitFolder)

    def generateFruit():
        randomScale = round(random.uniform(*fruit_size), 2)
        if random.random() < bomb_chance:
            fruitPath = random.choice([p for p in pathListFruit if "bomb" in p])
            is_bomb = True
        else:
            fruitPath = random.choice([p for p in pathListFruit if "bomb" not in p])
            is_bomb = False

        fruitList.append(Fruit(space, path=os.path.join(pathFruitFolder, fruitPath),
                               grid=(4, 4), animationFrames=14, scale=randomScale,
                               speed=fruit_speed, pathSoundSlice=None))  # Отключаем старый звук

    while cap.isOpened():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                cap.release()
                Game(level)
                return

        if not gameOver and not gameWin:
            success, img = cap.read()
            img = cv2.flip(img, 1)
            h, w = img.shape[:2]
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            keypoints = pose.process(img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            try:
                nose_x = int(keypoints.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * w)
                nose_y = int(keypoints.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * h)
            except AttributeError:
                continue

            cv2.circle(img, (nose_x, nose_y), 20, (0, 255, 255), -1)
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            imgRGB = np.rot90(imgRGB)
            frame = pygame.surfarray.make_surface(imgRGB).convert()
            frame = pygame.transform.flip(frame, True, False)
            window.blit(frame, (0, 0))

            if time.time() - timeGenerator > 1:
                generateFruit()
                timeGenerator = time.time()

            x, y = nose_x, nose_y
            for i, fruit in enumerate(fruitList):
                if fruit:
                    fruit.draw(window)
                    checkSlice = fruit.checkSlice(x, y)
                    if checkSlice == 2:  # Если это бомба
                        explosion_sound.play()
                        gameOver = True
                    if checkSlice == 1:  # Если фрукт разрезан
                        slice_sound.play()
                        fruitList[i] = False
                        score += 1

            if gameOver:
                cap.release()
                window.blit(imgGameOver, (0, 0))
                font = pygame.font.Font(None, 150)
                textLose = font.render("You Lose!", True, (0, 0, 0))
                window.blit(textLose, (400, 143))
                pygame.display.update()
                time.sleep(2)
                main_menu()
                return

            if score >= 10 and level == 3:
                cap.release()
                window.blit(imgWin, (0, 0))
                font = pygame.font.Font(None, 150)
                textWin = font.render("You Win!", True, (0, 0, 0))
                window.blit(textWin, (450, 300))
                pygame.display.update()
                time.sleep(2)
                main_menu()
                return

            if score >= 10 and level < 3:
                cap.release()
                Game(level + 1)
                return

            timeLeft = int(timeTotal - (time.time() - timeStart))
            if timeLeft <= 0:
                gameOver = True

            font = pygame.font.Font(None, 60)
            window.blit(font.render(str(score), True, (255, 127, 0)), (225, 35))
            window.blit(font.render(str(timeLeft), True, (255, 127, 0)), (1100, 38))

        pygame.display.update()
        clock.tick(fps)
        space.step(1 / fps)


if __name__ == "__main__":
    selected_level = main_menu()
    if selected_level:
        Game(selected_level)
