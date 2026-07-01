import re

from tests.conftest import PASSWORD, login


def register(client, **overrides):
    data = {
        "name": "Alice",
        "email": "alice@example.com",
        "password": PASSWORD,
        "dob": "1990-01-01",
        "sex": "female",
        "height": "170",
        "weight": "70",
        "goal_weight": "65",
        "goal_date": "2030-01-01",
        "trainings_per_week": "3",
        "household_mode": "create",
        "household_name": "Alice HH",
        "invite_code": "",
    }
    data.update(overrides)
    return client.post("/register", data=data)


def test_register_creates_household_with_invite_code(client):
    r = register(client)
    assert r.status_code == 200
    r = client.get("/household")
    assert re.search(r"<code>[^<]+</code>", r.text)


def test_second_registration_with_invite_code_joins_same_household(client):
    register(client)
    r = client.get("/household")
    invite_code = re.search(r"<code>([^<]+)</code>", r.text).group(1)

    with_client2 = client.__class__(client.app, follow_redirects=True)
    r = with_client2.post(
        "/register",
        data={
            "name": "Bob",
            "email": "bob@example.com",
            "password": PASSWORD,
            "dob": "1988-01-01",
            "sex": "male",
            "height": "180",
            "weight": "85",
            "goal_weight": "80",
            "goal_date": "2030-01-01",
            "trainings_per_week": "4",
            "household_mode": "join",
            "household_name": "",
            "invite_code": invite_code,
        },
    )
    assert r.status_code == 200
    r = with_client2.get("/household")
    assert "Alice" in r.text and "Bob" in r.text


def test_register_rejects_unknown_invite_code(client):
    r = register(client, email="someone@example.com", household_mode="join", invite_code="bogus")
    assert r.status_code == 400


def test_protected_page_redirects_to_login_when_logged_out(client):
    r = client.get("/profile")
    assert r.status_code == 200
    assert "/login" in str(r.url)


def test_login_then_logout(client):
    register(client)
    client.post("/logout")
    r = client.get("/profile")
    assert "/login" in str(r.url)

    r = login(client, "alice@example.com")
    assert r.status_code == 200
    r = client.get("/profile")
    assert "/profile" in str(r.url)


def test_login_with_wrong_password_fails(client):
    register(client)
    client.post("/logout")
    r = login(client, "alice@example.com", password="wrong-password")
    assert r.status_code == 400
