import face_recognition
import cv2
import time

video_capture = cv2.VideoCapture(0)  # Веб-камера
user_is_here = False

"""
Задача данного модуля:
1. Распознавание пользователей.
2. Сбор информации о пользователе для последующего анализа.
3. Генерация простых предложений для взаимодействия с пользователем.
4. Поиск объектов на фото, распознавание лиц людей на фото. Составление отчёта о найденных объектах на фото + обнаруженных людях.
"""

def load():
    global known_image
    global known_encoding
    # Загружаем эталонное лицо
    known_image = face_recognition.load_image_file("person.jpg")
    known_encoding = face_recognition.face_encodings(known_image)[0]



def identify_person(video_capture):
    ret, frame = video_capture.read()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Находим все лица в кадре
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    for face_encoding in face_encodings:
        # Сравниваем с эталоном
        match = face_recognition.compare_faces([known_encoding], face_encoding)[0]
        color = (0, 255, 0) if match else (0, 0, 255)  # Зеленый/красный прямоугольник
        
        """
        Теперь в это нужно добавить функцию радостного приветствия пользователя.

        Всё же просто возвращаем состояние пользователя True/False.
        """

        return True if match else False

def check_user(last_command_time):
    current_time = time.time()
    flag = False
    user_is_here = False
    if current_time - last_command_time >= 30:
        flag = True
        status = identify_person(video_capture)

        if status == False:
            user_is_here = False

        if status == True:
            user_is_here = True

    return user_is_here, flag

def image2data(image_path):
    from ultralytics import YOLO

    # Загрузка предобученной модели YOLO (например, YOLOv8)
    model = YOLO('yolov8m.pt')  # 'yolov8n.pt' — базовая версия. Есть и другие: yolov8s.pt, yolov8m.pt и т.д.

    # # Предсказание на изображении
    # results = model(image_path)
    results = model(image_path)

    # Визуализация результатов
    annotated_frame = results[0].plot()  # Рисует bounding boxes и подписи

    # Сохранение или отображение результата
    cv2.imwrite('output.jpg', annotated_frame)
    cv2.imshow('YOLO Result', annotated_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    """
    Здесь должно быть YOLO для распознавания объектов на фото. Данные об объектах должны быть преобразованы в читабельный для простого
    человека текст. Не "Объект Машина по координатам 100, 150.", а "В левой части фото машина" или "Слева на фото видна машина".
    Пользователь не будет спрашивать конкретные координаты объектов, он будет говорить, где они должны находиться.
    Варианты глобального расположения объектов:
    Слева, по центру, справа.
    Локально:
    Левее, правее.

    Ближе/Дальше будет сложно определить на начальных этапах, это может быть улучшением в будущем.
    """

def data2text():
    pass

    """
    Перевод координат и данных об объекте в понятные человеку слова.
    """

# Тесты
if __name__ == "__main__":
    last_time = time.time()
    while True:
        last_user_status = user_is_here
        user_is_here, flag = check_user(last_time)

        if flag == True:
            last_time = time.time()

        # Эта система не предназначена для расширения, потому так сделать проще

        if not last_user_status and not user_is_here:
            print("Пользователь не приходил")

        if last_user_status and not user_is_here:
            print("Пользователь пришёл")

        if last_user_status and not user_is_here:
            print("Пользователь ушёл")

        if last_user_status and user_is_here:
            print("Пользователь не уходил")


while True:
    pass

    """
    Здесь должна быть основная логика этого модуля


    Логика распознавания лица пользователя:
    Если флаг наличия пользователя не равен 'Присутствует', то нужно искать пользователя в кадре.
    условия флага:
    1. При включении Миты флаг равен None.
    2. Если пользователь не говорил с Митой более 5 минут, то включается режим 'Отошёл'.

    Время проверки наличия пользователя - каждую минуту, чтобы не тратить энергию.

    Если пользователь отходил: куда вы отходили?
    Если пользователь только пришёл: привет! + Какой либо случайный вопрос, но нейтральный вопрос.
    Если пользователь не отходил, а просто притих: что-то вы притихли, о чём думаете?


    Сейчас мне придётся отложить распознавание лиц у Миты на время - мой ПК не работает (HDD вышел из строя),
    а у ноутбука не подключена камера (ошибка сервисного центра).
    """