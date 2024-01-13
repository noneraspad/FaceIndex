import cv2
import numpy as np
import sqlite3
import os
import face_recognition
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk


def create_table():
    conn = sqlite3.connect('database_normal.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Faces (
            idFace INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            ImagePath TEXT
        )
    ''')
    conn.commit()
    conn.close()


def add_person():
    name = input('Введите полное имя человека: ')
    image_path = input('Введите путь к фотографии: ')

    conn = sqlite3.connect('database_normal.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Faces (Name, ImagePath) VALUES (?, ?)', (name, image_path))
    conn.commit()
    conn.close()


def recognize_by_name():
    name_to_find = input('Введите имя для поиска: ')

    conn = sqlite3.connect('database_normal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ImagePath FROM Faces WHERE Name = ?', (name_to_find,))
    result = cursor.fetchone()

    if result:
        image_path = result[0]
        show_photo_and_recognize(image_path)
        print(f'Человек по имени {name_to_find} найден.')
        conn.close()
    else:
        print(f'Человек с именем {name_to_find} не найден в базе данных.')
        conn.close()


def recognize_by_photo():
    image_path = input('Введите путь к фотографии: ')
    show_photo_and_recognize(image_path)


def find_unknown_person():
    unknown_image_path = input('Введите путь к фотографии неизвестного человека: ')

    # Загрузка неизвестного изображения
    unknown_image = face_recognition.load_image_file(unknown_image_path)

    # Получение face_encodings для неизвестного изображения
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_face_encodings:
        print('На фотографии не найдено лицо.')
        return

    # Получение списка известных лиц из базы данных
    known_face_encodings = []
    known_face_names = []

    conn = sqlite3.connect('database_normal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT Name, ImagePath FROM Faces')
    records = cursor.fetchall()
    conn.close()

    for record in records:
        known_face_names.append(record[0])
        known_face_image = face_recognition.load_image_file(record[1])
        known_face_encodings.append(face_recognition.face_encodings(known_face_image)[0])

    # Сравнение лиц на фотографии с известными лицами
    for i, unknown_face_encoding in enumerate(unknown_face_encodings):
        results = face_recognition.compare_faces(known_face_encodings, unknown_face_encoding)

        for j, result in enumerate(results):
            if result:
                print(f'Обнаружено совпадение с {known_face_names[j]}')
                answer = input('Это правильное совпадение? (y/n): ')
                if answer.lower() == 'y':
                    show_photo_and_recognize(records[j][1])
                    return

    print('Не удалось найти совпадение с известными лицами.')


def show_photo_and_recognize(image_path):
    img = cv2.imread(image_path)
    if img is not None:
        cv2.imshow('Photo', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        conn = sqlite3.connect('database_normal.db')
        cursor = conn.cursor()
        cursor.execute('SELECT Name FROM Faces WHERE ImagePath = ?', (image_path,))
        result = cursor.fetchone()
        conn.close()

        if result:
            print(f'Распознанное имя: {result[0]}')
        else:
            print('Не удалось распознать человека по фотографии.')
    else:
        print(f'Не удалось загрузить фотографию по пути: {image_path}')

def load_known_faces(folder_path):
    known_faces = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            image_path = os.path.join(folder_path, filename)
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            if len(face_encodings) > 0:
                known_faces[filename] = face_encodings
    return known_faces

def recognize_faces(frame, known_faces):
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = {}
        for filename, known_encodings in known_faces.items():
            for known_encoding in known_encodings:
                match = face_recognition.compare_faces([known_encoding], face_encoding)
                if True in match:
                    matches[filename] = matches.get(filename, 0) + 1

        if matches:
            name = max(matches, key=matches.get)
        else:
            name = "Unknown"

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name.split('.')[0], (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return frame


if __name__ == "__main__":
    create_table()



    while True:
        print('\nВыберите действие:')
        print('1. Внести человека в БД')
        print('2. Определить человека по имени')
        print('3. Определить человека по фотографии')
        print('4. Определить неизвестного человека')
        print('5. Определить человека на вебкамере')
        print('6. Выйти')

        choice = input('Введите номер действия: ')

        if choice == '1':
            add_person()
        elif choice == '2':
            recognize_by_name()
        elif choice == '3':
            recognize_by_photo()
        elif choice == '4':
            find_unknown_person()
        elif choice == '5':
            folder_path = "img"  # Путь к папке с изображениями
            known_faces = load_known_faces(folder_path)

            video_capture = cv2.VideoCapture(0)

            while True:
                ret, frame = video_capture.read()

                frame = recognize_faces(frame, known_faces)

                cv2.imshow('Video', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        elif choice == '6':
            break
        else:
            print('Некорректный ввод. Пожалуйста, введите номер действия от 1 до 6.')
