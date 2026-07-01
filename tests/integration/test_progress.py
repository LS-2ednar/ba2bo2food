from datetime import date, timedelta

from tests.conftest import login


def test_weight_checkin_reflected_in_progress_but_not_an_existing_plan(client, seeded_household):
    login(client, "alice@example.com")
    start = date.today() + timedelta(days=1)
    r = client.post("/plans", data={"start_date": start.isoformat(), "length": "7"})
    block_url = str(r.url)
    before = client.get(block_url).text

    r = client.post(
        "/profile/weight-checkins",
        data={"weight": "50", "recorded_at": date.today().isoformat()},
    )
    assert r.status_code == 200

    r = client.get("/profile/progress")
    assert "50" in r.text

    after = client.get(block_url).text
    assert before == after
