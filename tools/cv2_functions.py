import cv2
import time
import datetime as dt  # для получения текущего времени
import sqlite3


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
    con = sqlite3.connect('../db/frames_db.sqlite')
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


def analyze_video(path, min_area=500):
    '''Принимает на вход путь к камере/видео и минимальную площадь(???) человека/животного,
        анализирует видео, и при наличии изменений добавляет определенные данные в бд'''
    cap = cv2.VideoCapture(path)
    last_frame = None
    x, y, = None, None
    last_condition_entry_time = None

    while True:
        is_move = False
        ret, frame = cap.read()
        if not ret:
            raise VideoError

        frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)  # чтобы убрать(размыть) лишнее

        if last_frame is None:
            last_frame = gray
            continue

        frame_diff = cv2.absdiff(last_frame, gray)
        thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]

        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = grab_contours(cnts)

        for c in cnts:
            if cv2.contourArea(c) >= min_area:
                is_move = True
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # мы же не хотим, чтобы программа работала со скоростью улитки? тогда делаем, чтобы
        # кадр в бд добавлялся не чаще, чем раз в 1 секунду
        if is_move and (
                last_condition_entry_time is None or time.time() - last_condition_entry_time > 1):

            current_time = dt.datetime.now()
            frame_data = cv2.imencode('.jpg', frame)[1].tobytes()

            insert_in_database(path, current_time, (x, y), frame_data)
            last_condition_entry_time = time.time()  # обновление таймера
            # print('фрейм был добавлен в бд')

        cv2.imshow('frame', frame)
        # cv2.imshow('gray', gray)
        last_frame = gray

        if cv2.waitKey(1) == ord('q') or cv2.getWindowProperty('frame', cv2.WND_PROP_VISIBLE) < 1:
            break



    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    analyze_video(0)
