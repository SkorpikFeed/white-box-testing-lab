from auth import authenticate_user

def test_missing_credentials():
    db = {}
    assert authenticate_user("", "pass", db) == "Missing credentials"
    assert authenticate_user("user", "", db) == "Missing credentials"

def test_user_not_found():
    db = {}
    assert authenticate_user("user", "pass", db) == "User not found"

def test_account_locked():
    db = {"user": {"password": "pass", "attempts": 3}}
    assert authenticate_user("user", "pass", db) == "Account locked"

def test_invalid_password():
    db = {"user": {"password": "pass", "attempts": 0}}
    assert authenticate_user("user", "wrong", db) == "Invalid password"
    assert db["user"]["attempts"] == 1

def test_success():
    db = {"user": {"password": "pass", "attempts": 1}}
    assert authenticate_user("user", "pass", db) == "Authenticated"
    assert db["user"]["attempts"] == 0
