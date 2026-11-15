import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
import sys
import asyncio
from app.database import Base, engine, SessionLocal
from app.models import User, SavedStock, ResearchTask, UserPreference
from app.schemas import UserRegister, UserLogin, SavedStockCreate, ResearchTaskCreate, UserPreferenceUpdate
from app.routers.auth import register, login, get_me
from app.routers.watchlist import add_to_watchlist, get_watchlist, remove_from_watchlist
from app.routers.history import (
    create_research_task, 
    get_research_history, 
    get_task_details,
    get_task_report,
    get_task_agents,
    get_task_sources
)
from app.routers.preferences import get_preferences, update_preferences
from app.routers.stocks import search_stocks, get_stock_quote
from app.security import decode_access_token, verify_password
from fastapi.security import HTTPAuthorizationCredentials
from app.dependencies import get_current_user
from fastapi import HTTPException

def test_all():
    print("==================================================")
    print("RUNNING DIRECT FASTAPI & SQLALCHEMY SERVICE TESTS")
    print("==================================================")

    # 1. Initialize Tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clean existing test user if present
    test_email = "analyst@stockresearch.ai"
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()

    # 2. Registration Test
    reg_in = UserRegister(full_name="Arjun Sharma", email=test_email, password="SecurePassword123!")
    user = register(reg_in, db)
    assert user.user_id is not None
    assert user.email == test_email
    assert user.full_name == "Arjun Sharma"
    assert verify_password("SecurePassword123!", user.password_hash)
    print(f"[PASS] User Registration (user_id={user.user_id}, full_name='{user.full_name}')")

    # Duplicate registration prevention
    try:
        register(reg_in, db)
        assert False, "Should have raised HTTPException for duplicate email"
    except HTTPException as e:
        assert e.status_code == 400
        print("[PASS] Duplicate Registration Blocked (HTTP 400)")

    # 3. Login Test
    login_in = UserLogin(email=test_email, password="SecurePassword123!")
    token_response = login(login_in, db)
    token = token_response["access_token"]
    assert token is not None
    payload = decode_access_token(token)
    assert payload["user_id"] == user.user_id
    assert payload["sub"] == str(user.user_id)
    print(f"[PASS] User Login & Signed JWT Generation (sub={payload['sub']}, exp={payload['exp']})")

    # Bad password rejection
    try:
        login(UserLogin(email=test_email, password="WrongPassword"), db)
        assert False, "Should have rejected invalid password"
    except HTTPException as e:
        assert e.status_code == 401
        print("[PASS] Invalid Password Rejected (HTTP 401)")

    # 4. JWT Auth Dependency Test (get_current_user)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    curr_user = get_current_user(creds, db)
    assert curr_user.user_id == user.user_id
    print(f"[PASS] JWT Authentication Dependency (Authenticated user: {curr_user.full_name})")

    # Invalid token rejection in dependency
    try:
        bad_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.signature")
        get_current_user(bad_creds, db)
        assert False, "Should have rejected invalid token"
    except HTTPException as e:
        assert e.status_code == 401
        print("[PASS] Invalid JWT Signature Denied (HTTP 401)")

    # 5. Preferences Test
    prefs = get_preferences(curr_user, db)
    assert prefs.preferred_market in ["NSE", "BSE", "NASDAQ", "NYSE"]
    print(f"[PASS] GET /preferences (Market: {prefs.preferred_market}, Period: {prefs.preferred_analysis_period})")

    updated_prefs = update_preferences(
        UserPreferenceUpdate(preferred_market="BSE", preferred_analysis_period="1 Year"),
        curr_user,
        db
    )
    assert updated_prefs.preferred_market == "BSE"
    assert updated_prefs.preferred_analysis_period == "1 Year"
    print(f"[PASS] PUT /preferences (Updated to Market: {updated_prefs.preferred_market}, Period: {updated_prefs.preferred_analysis_period})")

    # 6. Watchlist Tests
    # Add RELIANCE
    stock1 = add_to_watchlist(SavedStockCreate(ticker="RELIANCE"), curr_user, db)
    assert stock1.ticker == "RELIANCE"
    assert stock1.user_id == curr_user.user_id
    print(f"[PASS] POST /watchlist (Added: {stock1.ticker})")

    # Add TCS
    stock2 = add_to_watchlist(SavedStockCreate(ticker="TCS"), curr_user, db)
    assert stock2.ticker == "TCS"
    print(f"[PASS] POST /watchlist (Added: {stock2.ticker})")

    # Duplicate stock prevention
    try:
        add_to_watchlist(SavedStockCreate(ticker="RELIANCE"), curr_user, db)
        assert False, "Should have prevented duplicate ticker in watchlist"
    except HTTPException as e:
        assert e.status_code == 400
        print("[PASS] Watchlist Duplicate Stock Blocked (HTTP 400)")

    # Get watchlist
    wl = get_watchlist(curr_user, db)
    assert len(wl) == 2
    tickers = [s.ticker for s in wl]
    assert "RELIANCE" in tickers and "TCS" in tickers
    print(f"[PASS] GET /watchlist (Retrieved {len(wl)} items: {tickers})")

    # Remove stock
    del_res = remove_from_watchlist("RELIANCE", curr_user, db)
    assert del_res["ticker"] == "RELIANCE"
    wl_after = get_watchlist(curr_user, db)
    assert len(wl_after) == 1
    print("[PASS] DELETE /watchlist/RELIANCE")

    # 7. Research Tasks & History Tests
    new_task = create_research_task(
        ResearchTaskCreate(ticker="INFY", market="NSE", requested_period="6 Months"),
        curr_user,
        db
    )
    assert new_task.task_id is not None
    assert new_task.ticker == "INFY"
    assert new_task.status == "Completed"
    assert new_task.recommendation in ["Strong Buy", "Buy", "Hold", "Sell"]
    print(f"[PASS] POST /tasks (Launched Task #{new_task.task_id} for {new_task.ticker}, Recommendation: {new_task.recommendation})")

    # History list
    history = get_research_history(curr_user, db)
    assert len(history) >= 1
    assert any(h.task_id == new_task.task_id for h in history)
    print(f"[PASS] GET /history (Retrieved {len(history)} research tasks)")

    # Task details
    task_detail = get_task_details(new_task.task_id, curr_user, db)
    assert task_detail.task_id == new_task.task_id
    assert "Multi-Agent" in task_detail.summary
    assert task_detail.company_name is not None
    print(f"[PASS] GET /tasks/{new_task.task_id} (Full Report: '{task_detail.summary[:50]}...', Company: {task_detail.company_name})")

    # Research Report record verification
    report_record = get_task_report(new_task.task_id, curr_user, db)
    assert report_record.task_id == new_task.task_id
    assert report_record.summary is not None
    print(f"[PASS] GET /tasks/{new_task.task_id}/report (Consolidated Report Record Verified)")

    # Agent Results records verification
    agents_list = get_task_agents(new_task.task_id, curr_user, db)
    assert len(agents_list) == 5
    agent_names = [a.agent_name for a in agents_list]
    assert "Fundamental Agent" in agent_names
    assert "Lead Analyst Synthesizer" in agent_names
    print(f"[PASS] GET /tasks/{new_task.task_id}/agents (5 Autonomous Agents Verified: {agent_names})")

    # Source Documents verification
    sources_list = get_task_sources(new_task.task_id, curr_user, db)
    assert len(sources_list) >= 3
    print(f"[PASS] GET /tasks/{new_task.task_id}/sources ({len(sources_list)} Verified Data Sources)")

    # 8. Stocks Search & Quote Tests
    results = search_stocks("TAT")
    assert any("TATAMOTORS" in r["ticker"] for r in results)
    print(f"[PASS] GET /stocks/search?query=TAT (Matched {len(results)} stocks)")

    quote = get_stock_quote("RELIANCE", "NSE")
    assert quote["ticker"] == "RELIANCE"
    assert quote["price"] > 0
    print(f"[PASS] GET /stocks/quote/RELIANCE (Price: {quote['currency']} {quote['price']}, Change: {quote['change_pct']}%)")

    db.close()
    print("==================================================")
    print("ALL 12 FASTAPI AUTH & WORKSPACE TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_all()
