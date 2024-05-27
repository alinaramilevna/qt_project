import hashlib
import sqlite3
import uuid


class PasswordError(Exception):
    pass


class LengthError(PasswordError):
    pass


class LetterError(PasswordError):
    pass


class DigitError(PasswordError):
    pass


def is_have_digit(string: str):
    for i in string:
        if i.isdigit():
            return True
    return False


def is_alpha_lower_and_upper(string: str):
    count_lower = 0
    count_upper = 0
    for i in string:
        if i.islower():
            count_lower += 1
        elif i.isupper():
            count_upper += 1
    if all([count_upper, count_lower]):
        return True
    else:
        return False


def is_new_password(password):
    '''Принимает новый пароль, который ставит пользователь,
    и возвращает True, если до этого пользователь не ставил такой пароль,
    и False, если пользователь уже ставил такой пароль.'''
    con = sqlite3.connect('../db/passwords.sqlite')
    cur = con.cursor()
    res = cur.execute('SELECT hash, salt from password_history').fetchall()

    for i in res:
        salt = i[1]
        hash_object = hashlib.sha256(password.encode() + salt.encode())
        hex_dig = hash_object.hexdigest()

        if hex_dig == i[0]:
            return False

    return True


def check_password(string: str):
    if len(string) < 8:
        raise LengthError('Слишком короткий пароль')
    if not is_have_digit(string):
        raise DigitError('Пароль не содержит цифр')
    if not is_alpha_lower_and_upper(string):
        raise LetterError('Пароль не содержит букв в различном регистре')
    if not is_new_password(string):
        raise PasswordError('Вы уже ставили такой пароль когда-то, придумайте новый')
    return 'ok'
