from auth import authenticate_user
import pytest

# Базові тести з завдання
def test_missing_credentials():
    db = {}
    # MC/DC для умови (not username or not password)
    # Перевіряємо вплив username незалежно
    assert authenticate_user("", "pass", db) == "Missing credentials"
    # Перевіряємо вплив password незалежно
    assert authenticate_user("user", "", db) == "Missing credentials"

def test_user_not_found():
    db = {}
    # Тестуємо випадок, коли користувача немає в БД
    assert authenticate_user("user", "pass", db) == "User not found"
    
    # Розширений тест для перевірки випадку, коли є інші користувачі
    db = {"other_user": {"password": "pass"}}
    assert authenticate_user("user", "pass", db) == "User not found"

def test_account_locked():
    # MC/DC для умови (attempts >= 3)
    # Граничне значення - рівно 3 спроби
    db = {"user": {"password": "pass", "attempts": 3}}
    assert authenticate_user("user", "pass", db) == "Account locked"
    
    # Перевірка значення більше граничного
    db = {"user": {"password": "pass", "attempts": 4}}
    assert authenticate_user("user", "pass", db) == "Account locked"

def test_invalid_password():
    # MC/DC для умови (db[username]["password"] != password)
    db = {"user": {"password": "pass", "attempts": 0}}
    assert authenticate_user("user", "wrong", db) == "Invalid password"
    assert db["user"]["attempts"] == 1
    
    # Перевірка інкременту спроб при послідовних невдалих входах
    db = {"user": {"password": "pass", "attempts": 1}}
    assert authenticate_user("user", "wrong", db) == "Invalid password"
    assert db["user"]["attempts"] == 2
    
    # Перевірка блокування після досягнення ліміту спроб
    assert authenticate_user("user", "wrong", db) == "Invalid password"
    assert db["user"]["attempts"] == 3
    assert authenticate_user("user", "wrong", db) == "Account locked"

def test_success():
    # Перевірка успішної автентифікації та скидання лічильника спроб
    db = {"user": {"password": "pass", "attempts": 1}}
    assert authenticate_user("user", "pass", db) == "Authenticated"
    assert db["user"]["attempts"] == 0
    
    # Перевірка успішної автентифікації з нульовим лічильником
    db = {"user": {"password": "pass", "attempts": 0}}
    assert authenticate_user("user", "pass", db) == "Authenticated"
    assert db["user"]["attempts"] == 0

def test_attempts_not_specified():
    # Перевірка поведінки, коли ключ "attempts" не існує
    db = {"user": {"password": "pass"}}
    assert authenticate_user("user", "pass", db) == "Authenticated"
    assert db["user"]["attempts"] == 0
    
    # Перевірка інкременту спроб, коли ключ "attempts" не існує
    db = {"user": {"password": "pass"}}
    assert authenticate_user("user", "wrong", db) == "Invalid password"
    assert db["user"]["attempts"] == 1

# Комбіновані тестові шляхи для Path Coverage
def test_path_coverage():
    # Шлях 1: Missing credentials -> return
    db = {}
    assert authenticate_user("", "pass", db) == "Missing credentials"
    
    # Шлях 2: User not found -> return
    assert authenticate_user("user", "pass", db) == "User not found"
    
    # Шлях 3: Account locked -> return
    db = {"user": {"password": "pass", "attempts": 3}}
    assert authenticate_user("user", "pass", db) == "Account locked"
    
    # Шлях 4: Invalid password -> increment attempts -> return
    db = {"user": {"password": "pass", "attempts": 0}}
    assert authenticate_user("user", "wrong", db) == "Invalid password"
    
    # Шлях 5: Success -> reset attempts -> return
    db = {"user": {"password": "pass", "attempts": 1}}
    assert authenticate_user("user", "pass", db) == "Authenticated"