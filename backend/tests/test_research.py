from app.database import SessionLocal
from app.models import PROCESSING, ResearchTask, User
from app.workflow import mark_interrupted_tasks

PASSWORD = "Str0ngPassw0rd"
TASK = {
    "company_name": "Apple Inc.",
    "ticker": "aapl",
    "market": "NASDAQ",
    "analysis_period": "6 months",
}


def sign_up_and_in(client, email, name="Some User"):
    client.cookies.clear()
    client.post(
        "/api/auth/register",
        json={"full_name": name, "email": email, "password": PASSWORD, "confirm_password": PASSWORD},
    )
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    return {"X-CSRF-Token": r.json()["csrf_token"]}


def start(client, headers, **overrides):
    return client.post("/api/research", json={**TASK, **overrides}, headers=headers)


def test_requires_authentication(client):
    assert client.get("/api/research").status_code == 401
    assert client.get("/api/research/1").status_code == 401
    assert client.post("/api/research", json=TASK).status_code == 401


def test_cookie_post_requires_csrf(client):
    sign_up_and_in(client, "a@example.com")
    assert client.post("/api/research", json=TASK).status_code == 403


def test_task_lifecycle_and_report(client):
    h = sign_up_and_in(client, "a@example.com")
    r = start(client, h)
    assert r.status_code == 201
    created = r.json()
    assert created["status"] == "pending"
    assert created["ticker"] == "AAPL"  # normalised

    # background workflow has finished by now
    listing = client.get("/api/research").json()
    assert [t["status"] for t in listing] == ["completed"]
    assert "report" not in listing[0]  # list stays light

    detail = client.get(f"/api/research/{created['id']}").json()
    assert detail["status"] == "completed" and detail["completed_at"]
    assert "Apple Inc." in detail["report"] and "AAPL" in detail["report"]


def test_status_is_processing_while_agents_run(client, monkeypatch):
    seen = []

    def fake(task):
        with SessionLocal() as db:
            seen.append(db.get(ResearchTask, task.id).status)
        return "report text"

    monkeypatch.setattr("app.workflow.generate_report", fake)
    h = sign_up_and_in(client, "a@example.com")
    start(client, h)
    assert seen == ["processing"]
    assert client.get("/api/research").json()[0]["status"] == "completed"


def test_failure_is_recorded_clearly(client, monkeypatch):
    def boom(task):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr("app.workflow.generate_report", boom)
    h = sign_up_and_in(client, "a@example.com")
    tid = start(client, h).json()["id"]

    detail = client.get(f"/api/research/{tid}").json()
    assert detail["status"] == "failed"
    assert detail["report"] is None
    assert "could not be completed" in detail["error"]
    assert "secret internal detail" not in detail["error"]  # no internals leaked


def test_missing_price_data_fails_the_task_with_a_clear_message(client, monkeypatch):
    from app.data import DataUnavailable

    def offline(*args):
        raise DataUnavailable("no internet")

    monkeypatch.setattr("app.data.prices.get_prices", offline)
    h = sign_up_and_in(client, "a@example.com")
    tid = start(client, h).json()["id"]
    detail = client.get(f"/api/research/{tid}").json()
    assert detail["status"] == "failed" and detail["report"] is None
    assert "No price data could be retrieved for AAPL" in detail["error"]


def test_users_only_see_their_own_research(client):
    ha = sign_up_and_in(client, "a@example.com", "Alice")
    a_id = start(client, ha, ticker="TSLA", company_name="Tesla").json()["id"]
    assert len(client.get("/api/research").json()) == 1

    sign_up_and_in(client, "b@example.com", "Bob")
    assert client.get("/api/research").json() == []
    r = client.get(f"/api/research/{a_id}")  # Alice's task, Bob's session
    assert r.status_code == 404


def test_user_id_in_body_is_ignored(client):
    sign_up_and_in(client, "a@example.com", "Alice")
    hb = sign_up_and_in(client, "b@example.com", "Bob")
    with SessionLocal() as db:
        alice_id = db.query(User).filter_by(email="a@example.com").one().id
        bob_id = db.query(User).filter_by(email="b@example.com").one().id

    start(client, hb, user_id=alice_id)  # Bob tries to file it under Alice
    with SessionLocal() as db:
        assert db.query(ResearchTask).one().user_id == bob_id


def test_validation(client):
    h = sign_up_and_in(client, "a@example.com")
    r = start(client, h, ticker="NOT A TICKER!")
    assert r.status_code == 422 and "ticker" in r.json()["errors"]
    assert "market" in start(client, h, market="MARS").json()["errors"]
    assert "analysis_period" in start(client, h, analysis_period="forever").json()["errors"]
    assert "company_name" in start(client, h, company_name=" ").json()["errors"]
    assert client.get("/api/research").json() == []


def test_unknown_task_is_404(client):
    sign_up_and_in(client, "a@example.com")
    assert client.get("/api/research/9999").status_code == 404


def test_interrupted_tasks_marked_failed_on_startup(client):
    sign_up_and_in(client, "a@example.com")
    with SessionLocal() as db:
        uid = db.query(User).one().id
        db.add(ResearchTask(user_id=uid, status=PROCESSING, **TASK))
        db.commit()
    mark_interrupted_tasks()
    t = client.get("/api/research").json()[0]
    assert t["status"] == "failed" and "restart" in t["error"]
