"""
News and Sentiment Agent.
Integrates Finnhub API (with Yahoo Finance news fallback) to retrieve real financial news:
headlines, descriptions, sources, publication dates, and original URLs.
Analyzes sentiment with Google Gemini API and structured classification.
"""

from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime, timedelta
import yfinance as yf
from app.config import get_settings
from app.schemas.agent_schemas import NewsArticle, NewsSentimentResponse
from app.services.gemini_service import generate_gemini_content

logger = logging.getLogger(__name__)


def _classify_sentiment_heuristic(text: str) -> tuple[str, float]:
    """
    Financial sentiment lexicons for robust, deterministic classification.
    Returns (label, score between -1.0 and 1.0).
    """
    lower = text.lower()
    
    pos_words = [
        "surge", "surges", "gain", "gains", "jump", "jumps", "rally", "rallies",
        "beat", "beats", "record", "growth", "profit", "profits", "bull", "bullish",
        "upgrade", "upgrades", "outperform", "soar", "soars", "high", "positive",
        "boost", "dividend", "revenue up", "strong", "breakthrough", "expands"
    ]
    neg_words = [
        "plunge", "plunges", "drop", "drops", "fall", "falls", "slump", "slumps",
        "loss", "losses", "miss", "misses", "bear", "bearish", "downgrade", "downgrades",
        "underperform", "lawsuit", "investigation", "decline", "declines", "warning",
        "layoffs", "debt crisis", "fraud", "scandal", "crash", "recession", "weak"
    ]
    
    pos_count = sum(1 for w in pos_words if w in lower)
    neg_count = sum(1 for w in neg_words if w in lower)
    
    total = pos_count + neg_count
    if total == 0:
        return "Neutral", 0.0
    
    score = (pos_count - neg_count) / float(total)
    score = round(max(-1.0, min(1.0, score)), 2)
    
    if score >= 0.2:
        return "Positive", score
    elif score <= -0.2:
        return "Negative", score
    else:
        return "Neutral", score


def fetch_raw_news(symbol: str) -> List[Dict[str, Any]]:
    """
    Fetches real news from Finnhub API if FINNHUB_API_KEY is available;
    falls back cleanly to yfinance news feed so real market news is ALWAYS retrieved.
    """
    settings = get_settings()
    finnhub_key = settings.FINNHUB_API_KEY or os.getenv("FINNHUB_API_KEY") or ""
    articles: List[Dict[str, Any]] = []

    # 1. Try Finnhub API
    if finnhub_key:
        try:
            import finnhub
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            to_date = datetime.utcnow().strftime("%Y-%m-%d")
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
            raw = finnhub_client.company_news(symbol, _from=from_date, to=to_date)
            if raw and isinstance(raw, list):
                for item in raw[:15]:
                    dt_str = datetime.utcfromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d %H:%M UTC") if item.get("datetime") else "Recent"
                    articles.append({
                        "headline": item.get("headline", ""),
                        "description": item.get("summary", ""),
                        "source": item.get("source", "Finnhub News"),
                        "published_at": dt_str,
                        "url": item.get("url", f"https://finance.yahoo.com/quote/{symbol}"),
                    })
        except Exception as e:
            logger.warning(f"Finnhub news query error for {symbol}: {e}")

    # 2. Fallback to Yahoo Finance News (real live financial news with dates & links)
    if not articles:
        try:
            ticker = yf.Ticker(symbol)
            yf_news = getattr(ticker, "news", [])
            if yf_news and isinstance(yf_news, list):
                for item in yf_news[:12]:
                    # yfinance news schema can have title, publisher, link, providerPublishTime
                    title = item.get("title") or item.get("headline") or ""
                    link = item.get("link") or item.get("url") or f"https://finance.yahoo.com/quote/{symbol}"
                    publisher = item.get("publisher") or item.get("source") or "Yahoo Finance"
                    pub_time = item.get("providerPublishTime")
                    if pub_time:
                        dt_str = datetime.utcfromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M UTC")
                    else:
                        dt_str = "Recent"
                    
                    summary = ""
                    # Content preview or related tickers
                    if "summary" in item:
                        summary = item["summary"]
                    elif "relatedTickers" in item and item["relatedTickers"]:
                        summary = f"Related tickers: {', '.join(item['relatedTickers'])}"

                    if title:
                        articles.append({
                            "headline": title,
                            "description": summary,
                            "source": publisher,
                            "published_at": dt_str,
                            "url": link,
                        })
        except Exception as e:
            logger.warning(f"Yahoo Finance news query error for {symbol}: {e}")

    return articles


def run_news_sentiment_analysis(symbol: str) -> NewsSentimentResponse:
    """
    Retrieves company news and runs sentiment analysis using Google Gemini and structured classification.
    """
    raw_articles = fetch_raw_news(symbol)
    
    parsed_articles: List[NewsArticle] = []
    total_score = 0.0
    pos_count = 0
    neg_count = 0
    neu_count = 0

    headlines_for_ai: List[str] = []

    for art in raw_articles:
        headline = art.get("headline", "").strip()
        desc = art.get("description", "").strip()
        full_text = f"{headline}. {desc}"
        
        label, score = _classify_sentiment_heuristic(full_text)
        
        if label == "Positive":
            pos_count += 1
        elif label == "Negative":
            neg_count += 1
        else:
            neu_count += 1
            
        total_score += score
        headlines_for_ai.append(f"[{art.get('published_at')}] ({art.get('source')}) {headline}")

        parsed_articles.append(
            NewsArticle(
                headline=headline,
                description=desc if desc else None,
                source=art.get("source", "Market News"),
                published_at=art.get("published_at", "Recent"),
                url=art.get("url", f"https://finance.yahoo.com/quote/{symbol}"),
                sentiment=label,
                sentiment_score=score,
                summary=desc[:160] + "..." if len(desc) > 160 else (desc if desc else None),
            )
        )

    # Compute overall metrics
    n = len(parsed_articles)
    if n > 0:
        overall_score = round(total_score / float(n), 2)
    else:
        overall_score = 0.0

    if overall_score >= 0.15:
        overall_sentiment = "Positive"
    elif overall_score <= -0.15:
        overall_sentiment = "Negative"
    else:
        overall_sentiment = "Neutral"

    # AI Executive Summary via Gemini
    if headlines_for_ai:
        prompt = f"""
You are an expert market news and sentiment analyst. Synthesize the following news headlines for {symbol}:

{chr(10).join(headlines_for_ai[:10])}

Aggregate Metrics:
- Positive Articles: {pos_count}
- Negative Articles: {neg_count}
- Neutral Articles: {neu_count}
- Overall Sentiment Score: {overall_score} ({overall_sentiment})

Provide a concise, 3-4 sentence executive synthesis covering:
1. Prevailing media narratives and catalyst events
2. Market reception / investor sentiment tone
3. Near-term risks or opportunities highlighted in the press
"""
        system_instruction = "You are a quantitative financial sentiment analyst specializing in news catalyst analysis."
        ai_summary = generate_gemini_content(prompt=prompt, system_instruction=system_instruction)
    else:
        ai_summary = None

    if not ai_summary:
        if n > 0:
            ai_summary = (
                f"Recent media coverage for {symbol} is predominantly {overall_sentiment.lower()} "
                f"with a composite sentiment score of {overall_score:+.2f} based on {n} curated articles "
                f"({pos_count} positive, {neg_count} negative, {neu_count} neutral). "
                f"Market narrative is tracking underlying corporate execution and sector dynamics."
            )
        else:
            ai_summary = f"No recent headlines detected for {symbol}. Market sentiment remains neutral."

    return NewsSentimentResponse(
        symbol=symbol,
        articles=parsed_articles,
        overall_sentiment=overall_sentiment,
        overall_score=overall_score,
        positive_count=pos_count,
        negative_count=neg_count,
        neutral_count=neu_count,
        executive_summary=ai_summary,
    )
