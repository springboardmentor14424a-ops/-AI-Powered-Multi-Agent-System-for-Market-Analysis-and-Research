from app.database import SessionLocal
from app.models import SavedStock, User, UserPreference

PASSWORD = "Str0ngPassw0rd"


def sign_up_and_in(client, email, name="Some User"):
    client.cookies.clear()
    client.post(
        "/api/auth/register",
        json={"full_name": name, "email": email, "password": PASSWORD, "confirm_password": PASSWORD},
    )
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    return {"X-CSRF-Token": r.json()["csrf_token"]}


def add(client, h, ticker="AAPL", market="NASDAQ", **extra):
    return client.post("/api/watchlist", json={"ticker": ticker, "market": market, **extra}, headers=h)


# ---------- stock search ----------

def test_search_by_name_and_ticker_and_market(client):
    sign_up_and_in(client, "a@example.com")
    r = client.get("/api/stocks/search", params={"q": "reliance"}).json()
    assert {(s["market"], s["ticker"]) for s in r} == {("NSE", "RELIANCE"), ("BSE", "500325")}
    assert {s["provider_symbol"] for s in r} == {"RELIANCE.NS", "500325.BO"}

    r = client.get("/api/stocks/search", params={"q": "tcs", "market": "NSE"}).json()
    assert [s["ticker"] for s in r] == ["TCS"]

    r = client.get("/api/stocks/search", params={"q": "aapl"}).json()
    assert r[0]["company_name"] == "Apple Inc."  # exact ticker ranks first
    assert client.get("/api/stocks/search", params={"q": "zzzzqq"}).json() == []


def test_search_requires_auth_and_query(client):
    assert client.get("/api/stocks/search", params={"q": "a"}).status_code == 401
    sign_up_and_in(client, "a@example.com")
    assert client.get("/api/stocks/search").status_code == 422


# ---------- watchlist ----------

def test_watchlist_requires_auth_and_csrf(client):
    assert client.get("/api/watchlist").status_code == 401
    assert client.post("/api/watchlist", json={"ticker": "AAPL", "market": "NASDAQ"}).status_code == 401
    sign_up_and_in(client, "a@example.com")
    assert client.post("/api/watchlist", json={"ticker": "AAPL", "market": "NASDAQ"}).status_code == 403


def test_add_list_remove(client):
    h = sign_up_and_in(client, "a@example.com")
    r = add(client, h, ticker="aapl")
    assert r.status_code == 201
    saved = r.json()
    assert saved["ticker"] == "AAPL" and saved["company_name"] == "Apple Inc."  # looked up server-side

    add(client, h, ticker="TCS", market="NSE")
    assert {s["ticker"] for s in client.get("/api/watchlist").json()} == {"AAPL", "TCS"}

    assert client.delete(f"/api/watchlist/{saved['id']}", headers=h).status_code == 204
    assert [s["ticker"] for s in client.get("/api/watchlist").json()] == ["TCS"]
    assert client.delete(f"/api/watchlist/{saved['id']}", headers=h).status_code == 404


def test_duplicate_is_rejected(client):
    h = sign_up_and_in(client, "a@example.com")
    assert add(client, h).status_code == 201
    r = add(client, h, ticker="AAPL")
    assert r.status_code == 409 and "Already" in r.json()["detail"]
    assert len(client.get("/api/watchlist").json()) == 1


def test_unsupported_and_badly_formatted_stocks(client):
    h = sign_up_and_in(client, "a@example.com")
    assert add(client, h, ticker="ZZZZ").status_code == 404          # valid format, not in list
    assert add(client, h, ticker="AAPL", market="NSE").status_code == 404  # wrong market
    r = add(client, h, ticker="12345", market="NASDAQ")
    assert r.status_code == 422 and "ticker" in r.json()["errors"]
    assert "market" in add(client, h, market="LSE").json()["errors"]


def test_provider_suffix_is_accepted(client):
    h = sign_up_and_in(client, "a@example.com")
    assert add(client, h, ticker="RELIANCE.NS", market="NSE").json()["ticker"] == "RELIANCE"
    assert add(client, h, ticker="500325.BO", market="BSE").json()["ticker"] == "500325"


def test_watchlists_are_private(client):
    ha = sign_up_and_in(client, "a@example.com", "Alice")
    saved_id = add(client, ha).json()["id"]

    hb = sign_up_and_in(client, "b@example.com", "Bob")
    assert client.get("/api/watchlist").json() == []
    assert client.delete(f"/api/watchlist/{saved_id}", headers=hb).status_code == 404
    assert add(client, hb).status_code == 201  # Bob may save the same stock himself

    client.cookies.clear()
    sign_up_and_in(client, "a@example.com")  # log back in as Alice (register is a no-op 409)
    assert len(client.get("/api/watchlist").json()) == 1


def test_user_id_in_body_is_ignored(client):
    sign_up_and_in(client, "a@example.com", "Alice")
    hb = sign_up_and_in(client, "b@example.com", "Bob")
    with SessionLocal() as db:
        alice = db.query(User).filter_by(email="a@example.com").one().id
        bob = db.query(User).filter_by(email="b@example.com").one().id
    add(client, hb, user_id=alice, company_name="Hacked")
    with SessionLocal() as db:
        row = db.query(SavedStock).one()
        assert row.user_id == bob and row.company_name == "Apple Inc."


# ---------- preferences ----------

def test_preferences_defaults_save_and_reload(client):
    h = sign_up_and_in(client, "a@example.com")
    assert client.get("/api/preferences").json() == {"market": "NASDAQ", "analysis_period": "6 months"}

    r = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "1 year"}, headers=h)
    assert r.status_code == 200
    assert client.get("/api/preferences").json() == {"market": "NSE", "analysis_period": "1 year"}

    client.put("/api/preferences", json={"market": "BSE", "analysis_period": "5 years"}, headers=h)
    with SessionLocal() as db:
        assert db.query(UserPreference).count() == 1  # updated in place, not duplicated
    assert client.get("/api/preferences").json()["market"] == "BSE"


def test_preferences_validation_auth_and_privacy(client):
    assert client.get("/api/preferences").status_code == 401
    ha = sign_up_and_in(client, "a@example.com")
    assert client.put("/api/preferences", json={"market": "NSE", "analysis_period": "1 year"}).status_code == 403
    r = client.put("/api/preferences", json={"market": "MARS", "analysis_period": "1 year"}, headers=ha)
    assert r.status_code == 422 and "market" in r.json()["errors"]
    r = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "forever"}, headers=ha)
    assert "analysis_period" in r.json()["errors"]

    client.put("/api/preferences", json={"market": "NSE", "analysis_period": "1 year"}, headers=ha)
    sign_up_and_in(client, "b@example.com")
    assert client.get("/api/preferences").json()["market"] == "NASDAQ"  # Bob has his own


# ---------- preferences feed the research workflow ----------

def test_market_and_period_reach_the_report(client):
    h = sign_up_and_in(client, "a@example.com")
    r = client.post(
        "/api/research",
        json={"company_name": "Reliance Industries", "ticker": "reliance.ns", "market": "NSE", "analysis_period": "1 year"},
        headers=h,
    )
    assert r.status_code == 201 and r.json()["ticker"] == "RELIANCE"
    report = client.get(f"/api/research/{r.json()['id']}").json()["report"]
    assert "~365 days" in report and "RELIANCE.NS" in report


def test_research_ticker_format_is_checked_per_market(client):
    h = sign_up_and_in(client, "a@example.com")
    base = {"company_name": "Some Company", "analysis_period": "1 year"}
    bad = [("BSE", "RELIANCE"), ("NASDAQ", "RELIANCE"), ("NYSE", "123")]
    for market, ticker in bad:
        r = client.post("/api/research", json={**base, "market": market, "ticker": ticker}, headers=h)
        assert r.status_code == 422 and "ticker" in r.json()["errors"], (market, ticker)
    ok = client.post("/api/research", json={**base, "market": "BSE", "ticker": "500325"}, headers=h)
    assert ok.status_code == 201
