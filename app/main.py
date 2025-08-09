from __future__ import annotations
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from .config import settings
from .db import Base, engine, get_db
from .models import Agent, CTA, TargetUser, KeywordTrigger, SourceAccount
from .style import build_style_profile_from_tweets
from .scheduler import start_scheduler, schedule_all_agents, schedule_agent_jobs
from .x_client import XClient


app = FastAPI(title="X Superfan Agent Platform")

# Initialize DB
Base.metadata.create_all(bind=engine)

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_event():
    start_scheduler()
    schedule_all_agents()


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    return templates.TemplateResponse("admin.html", {"request": request, "agents": agents})


@app.post("/agents/create")
async def create_agent(
    name: str = Form(...),
    brand_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    enable_post: bool = Form(False),
    enable_reply: bool = Form(False),
    enable_like: bool = Form(False),
    enable_retweet: bool = Form(False),
    post_interval_s: int = Form(14400),
    reply_interval_s: int = Form(120),
    like_interval_s: int = Form(600),
    retweet_interval_s: int = Form(36000),
    cta_every_n_posts: Optional[int] = Form(None),
    cta_every_n_replies: Optional[int] = Form(None),
    x_consumer_key: str = Form(...),
    x_consumer_secret: str = Form(...),
    x_access_token: str = Form(...),
    x_access_token_secret: str = Form(...),
    x_bearer_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    agent = Agent(
        name=name,
        brand_name=brand_name,
        description=description,
        enable_post=enable_post,
        enable_reply=enable_reply,
        enable_like=enable_like,
        enable_retweet=enable_retweet,
        post_interval_s=post_interval_s,
        reply_interval_s=reply_interval_s,
        like_interval_s=like_interval_s,
        retweet_interval_s=retweet_interval_s,
        cta_every_n_posts=cta_every_n_posts,
        cta_every_n_replies=cta_every_n_replies,
        x_consumer_key=x_consumer_key,
        x_consumer_secret=x_consumer_secret,
        x_access_token=x_access_token,
        x_access_token_secret=x_access_token_secret,
        x_bearer_token=x_bearer_token,
    )
    db.add(agent)
    db.commit()
    schedule_agent_jobs(agent.id)
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/agents/{agent_id}/cta")
async def add_cta(agent_id: int, url: str = Form(...), label: Optional[str] = Form(None), for_posts: bool = Form(True), for_replies: bool = Form(False), db: Session = Depends(get_db)):
    cta = CTA(agent_id=agent_id, url=url, label=label, for_posts=for_posts, for_replies=for_replies)
    db.add(cta)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/agents/{agent_id}/target")
async def add_target(agent_id: int, handle: str = Form(...), db: Session = Depends(get_db)):
    target = TargetUser(agent_id=agent_id, handle=handle)
    db.add(target)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/agents/{agent_id}/keyword")
async def add_keyword(agent_id: int, keyword: str = Form(...), db: Session = Depends(get_db)):
    kw = KeywordTrigger(agent_id=agent_id, keyword=keyword)
    db.add(kw)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/agents/{agent_id}/source")
async def add_source(agent_id: int, handle: str = Form(...), db: Session = Depends(get_db)):
    src = SourceAccount(agent_id=agent_id, handle=handle)
    db.add(src)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/agents/{agent_id}/style/upload")
async def upload_style(agent_id: int, tweets_csv: str = Form(...), db: Session = Depends(get_db)):
    """
    Accept a simple CSV string with one tweet per line (or semicolon/comma separated) to build a style profile.
    For production, replace with file upload parsing.
    """
    agent = db.query(Agent).get(agent_id)
    if not agent:
        return RedirectResponse(url="/admin", status_code=303)
    # Split heuristically
    raw = tweets_csv.replace("\r", "\n").replace(";", "\n").split("\n")
    samples = [r.strip() for r in raw if r.strip()]
    agent.style_profile = build_style_profile_from_tweets(samples[:200])
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/agents/{agent_id}/style/fetch")
async def fetch_style(agent_id: int, handle: str = Form(...), num_tweets: int = Form(50), db: Session = Depends(get_db)):
    agent = db.query(Agent).get(agent_id)
    if not agent:
        return RedirectResponse(url="/admin", status_code=303)
    x = XClient(
        consumer_key=agent.x_consumer_key,
        consumer_secret=agent.x_consumer_secret,
        access_token=agent.x_access_token,
        access_token_secret=agent.x_access_token_secret,
        bearer_token=agent.x_bearer_token,
    )
    uid = x.get_user_by_username(handle)
    if not uid:
        return RedirectResponse(url="/admin", status_code=303)
    tweets = x.get_user_tweets(uid, since_id=None, max_results=min(100, max(5, num_tweets)))
    samples = [t["text"] for t in tweets]
    agent.style_profile = build_style_profile_from_tweets(samples)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/agents/{agent_id}/reschedule")
async def reschedule(agent_id: int):
    schedule_agent_jobs(agent_id)
    return RedirectResponse(url="/admin", status_code=303)