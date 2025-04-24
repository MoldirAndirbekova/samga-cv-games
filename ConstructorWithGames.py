import cv2
from cvzone.HandTrackingModule import HandDetector
import cvzone
import os
import time
import random

WIN_WIDTH, WIN_HEIGHT = 1280, 720

levels = [
    {"level": 1, "folder": "mushroom", "duration": 120, "speed": 0},
    {"level": 2, "folder": "flower", "duration": 120, "speed": 0},
    {"level": 3, "folder": "car", "duration": 140, "speed": 0},
    {"level": 4, "folder": "tree", "duration": 140, "speed": 0},
    {"level": 5, "folder": "train", "duration": 140, "speed": 0},
    {"level": 6, "folder": "rainbow", "duration": 200, "speed": 0},
    {"level": 7, "folder": "home", "duration": 220, "speed": 0},
    {"level": 8, "folder": "worm", "duration": 220, "speed": 0},
    {"level": 9, "folder": "castle", "duration": 240, "speed": 0}
]

class DragImg:
    def __init__(self, path, posOrigin, move_speed):
        print(f"Loading image: {path}")
        self.posOrigin = list(posOrigin)
        self.path = path
        self.isDragging = False
        self.move_speed = move_speed

        self.img = cv2.imread(self.path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            print(f"❌ Error loading image: {self.path}")
            return

        if self.img.shape[-1] == 3:
            self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)

        scale_factor = 0.5
        self.img = cv2.resize(self.img, (0, 0), fx=scale_factor, fy=scale_factor)
        self.size = self.img.shape[:2]

        if self.move_speed > 0:
            self.vx = random.choice([-1, 1]) * self.move_speed
            self.vy = random.choice([-1, 1]) * self.move_speed
        else:
            self.vx, self.vy = 0, 0

    def update(self, cursor, fingers):
        ox, oy = self.posOrigin
        h, w = self.size

        if ox < cursor[0] < ox + w and oy < cursor[1] < oy + h:
            if fingers[1] == 1 and fingers[2] == 1:
                self.isDragging = True

        if self.isDragging:
            self.posOrigin = [cursor[0] - w // 2, cursor[1] - h // 2]

        if fingers[1] == 0 and fingers[2] == 0:
            self.isDragging = False

        if not self.isDragging and self.move_speed > 0:
            self.posOrigin[0] += self.vx
            self.posOrigin[1] += self.vy

            if self.posOrigin[0] < 0 or self.posOrigin[0] + w > WIN_WIDTH:
                self.vx = -self.vx
            if self.posOrigin[1] < 0 or self.posOrigin[1] + h > WIN_HEIGHT:
                self.vy = -self.vy

cap = cv2.VideoCapture(0)
cap.set(3, WIN_WIDTH)
cap.set(4, WIN_HEIGHT)

detector = HandDetector(detectionCon=0.8)

for lvl in levels:
    level_num = lvl["level"]
    folder = lvl["folder"]
    game_duration = lvl["duration"]
    move_speed = lvl["speed"]

    if not os.path.exists(folder):
        print(f"❌ Папка '{folder}' не найдена.")
        continue

    preview_path = os.path.join(folder, f"level{level_num}.png")

    if os.path.exists(preview_path):
        preview_img = cv2.imread(preview_path)

        if preview_img is None:
            print(f"❌ Не удалось загрузить изображение: {preview_path}")
            continue

        # Показываем превью на 5 секунд
        show_time = 10
        start_preview = time.time()
        while time.time() - start_preview < show_time:
            cv2.imshow("Memorize the Pattern", preview_img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                exit()
        cv2.destroyWindow("Memorize the Pattern")
    else:
        print(f"⚠️ Нет превью-файла: {preview_path}")



    # === LOAD LEVEL IMAGES ===
    myList = os.listdir(folder)
    myList = [img for img in myList if not img.lower().startswith("level")]
    print(f"[Level {level_num}] Loaded images: {len(myList)}")

    listImg = []
    for i, imgName in enumerate(myList):
        imgPath = os.path.join(folder, imgName)
        x_pos = 50 + (i % 4) * 250
        y_pos = 100 if i < 4 else 300
        listImg.append(DragImg(imgPath, [x_pos, y_pos], move_speed))

    start_time = time.time()

    while True:
        success, img = cap.read()
        if not success:
            print("❌ Camera not working.")
            break

        img = cv2.flip(img, 1)
        hands, img = detector.findHands(img, flipType=False)

        if hands:
            lmList = hands[0]['lmList']
            fingers = detector.fingersUp(hands[0])
            cursor = lmList[8]

            for imgObject in listImg:
                imgObject.update(cursor, fingers)

        for imgObject in listImg:
            h, w = imgObject.size
            ox, oy = imgObject.posOrigin
            img = cvzone.overlayPNG(img, imgObject.img, [ox, oy])

        elapsed_time = time.time() - start_time
        remaining_time = max(0, game_duration - elapsed_time)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, f'Level: {level_num}', (10, 40), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(img, f'Time: {int(remaining_time)}s', (10, 80), font, 1, (255, 0, 0), 2, cv2.LINE_AA)

        cv2.imshow("Game", img)

        if remaining_time == 0:
            cv2.putText(img, "Level Complete!", (WIN_WIDTH//2 - 250, WIN_HEIGHT//2), font, 2, (0, 0, 255), 4, cv2.LINE_AA)
            cv2.imshow("Game", img)
            cv2.waitKey(2000)
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

print("All levels completed!")
cap.release()
cv2.destroyAllWindows()