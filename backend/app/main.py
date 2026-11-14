from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.schemas import (LoginRequest, TokenResponse)
from app.security import (
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import (Base, engine, get_db)
from app.models import (User, ResearchTask, SavedStock, UserPreferences)
from app.schemas import (UserRegister, UserResponse, ResearchTaskCreate, ResearchTaskResponse, ResearchReportResponse, StockSearchResult, SavedStockCreate, SavedStockResponse, UserPreferencesResponse, UserPreferencesCreate)
from app.security import (hash_password, SECRET_KEY, ALGORITHM)
from app.yahoo_data_service import (get_stock_data,get_stock_list, search_stocks, get_stock_by_ticker, validate_stock_for_market)
from app.research_service import (
    start_research,
    complete_research,
    fail_research
)

app = FastAPI(title="Stock Research Analyst API")

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "Stock Research Analyst API is running"}


@app.post("/register", response_model=UserResponse, status_code=201)
def register_user(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    full_name = user.full_name.strip()
    email = str(user.email).lower()

    if len(full_name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid full name"
        )

    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must not exceed 72 bytes"
        )

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        full_name=full_name,
        email=email,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Registration failed. Please try again."
        )


# JWT authentication
bearer_scheme = HTTPBearer(auto_error=False)


# USER LOGIN
@app.post("/login", response_model=TokenResponse)
def login_user(
    user: LoginRequest,
    db: Session = Depends(get_db)
):
    email = str(user.email).lower()

    # Find registered user
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    # Check whether email exists
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # bcrypt supports a maximum of 72 password bytes
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify entered password
    if not verify_password(
        user.password,
        existing_user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Generate JWT token
    access_token = create_access_token(
    user_id=existing_user.id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Login successful"
    }


# GET LOGGED-IN USER DETAILS

@app.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db)
):
    # Check whether token was supplied
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    token = credentials.credentials

    try:
        # Verify token signature and expiry
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Find authenticated user using their ID
    current_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "message": "Authenticated successfully"
    }


bearer_scheme = HTTPBearer(auto_error=False)


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user




@app.post(
    "/research",
    response_model=ResearchTaskResponse,
    status_code=201
)
def create_research_task(
    research: ResearchTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    # 1. Validate stock ticker and market
    try:
        validate_stock_for_market(
            research.stock_ticker,
            research.market
        )
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # 2. Create a task for the logged-in user
    new_task = ResearchTask(
        user_id=current_user.id,
        company_name=research.company_name.strip(),
        stock_ticker=research.stock_ticker.strip().upper(),
        market=research.market.strip().upper(),
        analysis_period=research.analysis_period.strip(),
        status="Pending"
    )

    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        task_id = new_task.id

        # 3. Update status to Processing
        start_research(db, task_id)

        # 4. Load and analyse Yahoo Finance dataset
        result = get_stock_data(
            ticker=new_task.stock_ticker,
            analysis_period=new_task.analysis_period
        )

        # 5. Prepare analysis summary
        analysis_summary = "\n".join([
            "YAHOO FINANCE HISTORICAL STOCK ANALYSIS",
            "=" * 45,
            f"Company: {new_task.company_name}",
            f"Ticker: {result['ticker']}",
            f"Market: {new_task.market}",
            f"Analysis Period: {result['analysis_period']}",
            f"Data Start: {result['data_start_date']}",
            f"Data End: {result['data_end_date']}",
            f"Records Analysed: {result['records_count']}",
            f"Starting Price: {result['starting_price']}",
            f"Ending Price: {result['ending_price']}",
            f"Highest Price: {result['highest_price']}",
            f"Lowest Price: {result['lowest_price']}",
            f"Average Price: {result['average_price']}",
            f"Average Volume: {result['average_volume']}",
            f"Price Change: {result['price_change']}",
            f"Percentage Change: {result['percentage_change']}%"
        ])

        # 6. Save analysis and mark task Completed
        complete_research(
            db,
            task_id,
            analysis_summary
        )

        db.refresh(new_task)
        return new_task

    except Exception as error:
        db.rollback()

        try:
            fail_research(
                db,
                new_task.id,
                str(error)
            )
            db.refresh(new_task)
            return new_task

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to process research task"
            )
@app.get(
    "/research",
    response_model=list[ResearchTaskResponse]
)
def get_research_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    tasks = db.query(ResearchTask).filter(
        ResearchTask.user_id == current_user.id
    ).order_by(
        ResearchTask.research_date.desc()
    ).all()

    return tasks


@app.get(
    "/research/{task_id}/report",
    response_model=ResearchReportResponse
)
def get_research_report(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    task = db.query(ResearchTask).filter(
        ResearchTask.id == task_id,
        ResearchTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    if task.status != "Completed" or not task.report_content:
        raise HTTPException(
            status_code=409,
            detail="Research report is not available yet"
        )

    return {
        "id": task.id,
        "company_name": task.company_name,
        "stock_ticker": task.stock_ticker,
        "status": task.status,
        "report_content": task.report_content
    }


# ==========================================
# MODULE 5: SAVED STOCKS AND WATCHLIST
# ==========================================


# 1. Search stocks by company name or ticker
@app.get(
    "/stocks/search",
    response_model=list[StockSearchResult]
)
def search_stock_api(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a company name or ticker."
        )

    try:
        results = search_stocks(q)
        return results

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Stock search failed: {str(error)}"
        )


# 2. Add a stock to the logged-in user's watchlist
@app.post(
    "/watchlist",
    response_model=SavedStockResponse,
    status_code=201
)
def add_to_watchlist(
    stock: SavedStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    ticker = stock.stock_ticker.strip().upper()

    stock_info = get_stock_by_ticker(ticker)

    if not stock_info:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in the available dataset."
        )

    existing_stock = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.id,
        SavedStock.stock_ticker == ticker
    ).first()

    if existing_stock:
        raise HTTPException(
            status_code=409,
            detail="This stock is already in your watchlist."
        )

    new_stock = SavedStock(
        user_id=current_user.id,
        company_name=stock_info["company_name"],
        stock_ticker=ticker
    )

    try:
        db.add(new_stock)
        db.commit()
        db.refresh(new_stock)

        return new_stock

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This stock is already in your watchlist."
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save stock."
        )


# 3. View only the logged-in user's saved stocks
@app.get(
    "/watchlist",
    response_model=list[SavedStockResponse]
)
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    return (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.id)
        .order_by(SavedStock.saved_date.desc())
        .all()
    )


# 4. Remove a stock from the logged-in user's watchlist
@app.delete("/watchlist/{ticker}")
def remove_from_watchlist(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    ticker = ticker.strip().upper()

    saved_stock = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.id,
        SavedStock.stock_ticker == ticker
    ).first()

    if not saved_stock:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in your watchlist."
        )

    db.delete(saved_stock)
    db.commit()

    return {
        "message": f"{ticker} removed from your watchlist."
    }


# ==========================================
# MODULE 6: USER PREFERENCES
# ==========================================


# 1. Get logged-in user's preferences
@app.get(
    "/preferences",
    response_model=UserPreferencesResponse
)
def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()

    # Create default preferences for a new user
    if not preferences:
        preferences = UserPreferences(
            user_id=current_user.id,
            market="NASDAQ",
            analysis_period="3 Months"
        )

        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return preferences


# 2. Save or update logged-in user's preferences
@app.put(
    "/preferences",
    response_model=UserPreferencesResponse
)
def save_user_preferences(
    preference_data: UserPreferencesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user)
):
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()

    if preferences:
        preferences.market = preference_data.market
        preferences.analysis_period = preference_data.analysis_period
    else:
        preferences = UserPreferences(
            user_id=current_user.id,
            market=preference_data.market,
            analysis_period=preference_data.analysis_period
        )
        db.add(preferences)

    db.commit()
    db.refresh(preferences)

    return preferences
