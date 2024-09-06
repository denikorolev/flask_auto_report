# calculating.py

from datetime import datetime  

def calculate_age(birthdate_str):
    try:
        # Преобразуем строку даты рождения в объект даты и вычисляем возраст
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age
    except ValueError:
        return None