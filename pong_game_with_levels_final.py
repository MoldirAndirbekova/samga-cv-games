import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import numpy as np
from flask import Flask, render_template, Response, request, redirect, url_for

app = Flask(__name__)

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

imgBackground = cv2.imread("Resources/tennis-field.png")
imgGameOver = cv2.imread("Resources/game-over.png")
imgBall = cv2.imread("Resources/tennisl-ball.png", cv2.IMREAD_UNCHANGED)
imgBat1 = cv2.imread("Resources/right-side.png", cv2.IMREAD_UNCHANGED)
imgBat2 = cv2.imread("Resources/left-side.png", cv2.IMREAD_UNCHANGED)


if any(img is None for img in [imgBall, imgBat1, imgBat2, imgBackground, imgGameOver]):
    print("Ошибка загрузки изображений! Проверь путь к файлам.")
    exit()


detector = HandDetector(detectionCon=0.8, maxHands=2)

ballPosition = [100, 100]
speedX, speedY = 15, 15
gameOver = False
score = [0, 0]
level = 1
difficulty = "easy"  # по умолчанию

# Функция сброса игры
def reset_game():
    global ballPosition, speedX, speedY, gameOver, score, level, imgBat1, imgBat2

    ballPosition = [100, 100]
    gameOver = False
    score = [0, 0]

    if difficulty == "easy":
        speedX, speedY = 15, 15
        level = 1
        imgBat1 = cv2.resize(cv2.imread("Resources/right-side.png", cv2.IMREAD_UNCHANGED), (34, 250))
        imgBat2 = cv2.resize(cv2.imread("Resources/left-side.png", cv2.IMREAD_UNCHANGED), (34, 250))
    elif difficulty == "medium":
        speedX, speedY = 20, 20
        level = 2
        imgBat1 = cv2.resize(cv2.imread("Resources/right-side.png", cv2.IMREAD_UNCHANGED), (34, 200))
        imgBat2 = cv2.resize(cv2.imread("Resources/left-side.png", cv2.IMREAD_UNCHANGED), (34, 200))
    elif difficulty == "hard":
        speedX, speedY = 25, 25
        level = 3
        imgBat1 = cv2.resize(cv2.imread("Resources/right-side.png", cv2.IMREAD_UNCHANGED), (34, 150))
        imgBat2 = cv2.resize(cv2.imread("Resources/left-side.png", cv2.IMREAD_UNCHANGED), (34, 150))

# Функция генерации кадров
def generate_frames():
    global ballPosition, speedX, speedY, gameOver, score, level

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        hands, img = detector.findHands(img, flipType=False, draw=False)

        img = cv2.addWeighted(img, 0.3, imgBackground, 0.7, 0)

        if hands:
            for hand in hands:
                x, y, w, h = hand['bbox']
                h1, w1, _ = imgBat1.shape
                y1 = np.clip(y - h1 // 2, 20, 415)

                if hand['type'] == "Left":
                    img = cvzone.overlayPNG(img, imgBat1, (59, y1))
                    if 59 < ballPosition[0] < 59 + w1 and y1 < ballPosition[1] < y1 + h1:
                        speedX = -speedX
                        ballPosition[0] += 30
                        score[0] += 1

                if hand['type'] == "Right":
                    img = cvzone.overlayPNG(img, imgBat2, (1194, y1))
                    if 1195 - 50 < ballPosition[0] < 1195 - 30 + w1 and y1 < ballPosition[1] < y1 + h1:
                        speedX = -speedX
                        ballPosition[0] -= 30
                        score[1] += 1

        totalScore = score[0] + score[1]

        # Проверка на Game Over
        if ballPosition[0] < 40 or ballPosition[0] > 1200:
            gameOver = True

        if gameOver:
            img = imgGameOver.copy()
            display_score = str(totalScore).zfill(2)
            cv2.putText(img, display_score, (585, 360), cv2.FONT_HERSHEY_COMPLEX, 3, (200, 0, 200), 6)
        else:
            if ballPosition[1] >= 500 or ballPosition[1] <= 10:
                speedY = -speedY

            ballPosition[0] += speedX
            ballPosition[1] += speedY
            img = cvzone.overlayPNG(img, imgBall, ballPosition)

            cv2.putText(img, f"Level: {level}", (500, 80), cv2.FONT_HERSHEY_COMPLEX, 2.5, (0, 255, 0), 6)
            cv2.putText(img, str(score[0]), (290, 670), cv2.FONT_HERSHEY_COMPLEX, 3, (200, 0, 200), 6)
            cv2.putText(img, str(score[1]), (910, 670), cv2.FONT_HERSHEY_COMPLEX, 3, (200, 0, 200), 6)
            # cv2.putText(img, str(score[0]), (290, 670), cv2.FONT_HERSHEY_COMPLEX, 3, (255, 255, 255), 5)
            # cv2.putText(img, str(score[1]), (910, 670), cv2.FONT_HERSHEY_COMPLEX, 3, (255, 255, 255), 5)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Маршруты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('gameDi.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/restart', methods=['POST'])
def restart():
    reset_game()
    return redirect(url_for('game'))

@app.route('/set_difficulty/<level>')
def set_difficulty(level):
    global difficulty
    difficulty = level
    reset_game()
    return redirect(url_for('game'))

# Запуск сервера
if __name__ == "__main__":
    app.run(debug=True)
