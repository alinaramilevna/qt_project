import cv2
import time
import datetime as dt  # для получения текущего времени
import sqlite3
import numpy as np

import face_recognition


class VideoError(Exception):
    pass


def grab_contours(
        cnts):  # анаконда не поддерживала библиотеку, в которой была эта функция, поэтому пришлось сам код функции засунуть
    if len(cnts) == 2:
        return cnts[0]

    elif len(cnts) == 3:
        return cnts[1]

    else:
        raise Exception('Contours tuple must have length 2 or 3')


def insert_in_database(path: str, current_time: str, coords: (), frame):
    '''Добавляет в базу данных кадр с обьектом'''
    con = sqlite3.connect('db/frames_db.sqlite')
    cur = con.cursor()

    if len(cur.execute('''SELECT id FROM cameras WHERE path = ? ''',
                       (path,)).fetchall()) == 0:  # если до этого камеры небыло в бд, добавляем ее
        cur.execute('''INSERT INTO cameras(path) VALUES(?) ''', (path,))
        con.commit()

    id_cam = cur.execute('''SELECT id from cameras WHERE path = ?''', (path,)).fetchall()[0][0]
    cur.execute(
        '''INSERT INTO frames(camera_id, time, time_to_show, upper_left_coords, screenshot) VALUES(?, ?, ?, ?, ?) ''',
        (id_cam, current_time, str(current_time)[:-10], str(coords), frame,))

    con.commit()
    con.close()


def analyze_video(path, analyzer, min_area=500):
    '''Принимает на вход путь к камере/видео и минимальную площадь(???) человека/животного,
        анализирует видео, и при наличии изменений добавляет определенные данные в бд'''
    cap = cv2.VideoCapture(path)
    last_frame = None
    x, y, = None, None
    last_condition_entry_time = None

    alina_image = face_recognition.load_image_file("data/faces/alina.jpeg")
    alina_face_encoding = face_recognition.face_encodings(alina_image)[0]

    ramil_image = face_recognition.load_image_file("data/faces/ramil.jpeg")
    ramil_face_encoding = face_recognition.face_encodings(ramil_image)[0]

    varvara_image = face_recognition.load_image_file("data/faces/varvara.jpg")
    varvara_face_encoding = face_recognition.face_encodings(varvara_image)[0]

    gleb_image = face_recognition.load_image_file("data/faces/gleb.jpg")
    gleb_face_encoding = face_recognition.face_encodings(gleb_image)[0]

    # Create arrays of known face encodings and their names
    known_face_encodings = [
        alina_face_encoding,
        ramil_face_encoding,
        varvara_face_encoding,
        gleb_face_encoding
    ]
    known_face_names = [
        "Alina Kushmuhametova",
        'Ramil',
        'Varvara Starikova',
        'Beb'
    ]

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        is_move = False
        ret, frame = cap.read()
        if not ret:
            raise VideoError

        if process_this_frame:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #     first_match_index = matches.index(True)
            #     name = known_face_names[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)

        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            x, y = left, top
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # мы же не хотим, чтобы программа работала со скоростью улитки? тогда делаем, чтобы
        # кадр в бд добавлялся не чаще, чем раз в 1 секунду
        if face_names and (
                last_condition_entry_time is None or time.time() - last_condition_entry_time > 1):
            current_time = dt.datetime.now()
            frame_data = cv2.imencode('.jpg', frame)[1].tobytes()

            insert_in_database(path, current_time, (x, y), frame_data)
            last_condition_entry_time = time.time()  # обновление таймера
            print('фрейм был добавлен в бд')

        cv2.imshow('frame', frame)

        if cv2.waitKey(1) == ord('q') or cv2.getWindowProperty('frame', cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    analyze_video(0)
