from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional

from .db import SessionLocal
from .models import Agent, CTA, TargetUser, SourceAccount, KeywordTrigger, PostLog
from .x_client import XClient
from .llm import craft_tweet, craft_reply, rewrite_tweet


scheduler = BackgroundScheduler(timezone="UTC")


def _x_client_for(agent: Agent) -> XClient:
    return XClient(
        consumer_key=agent.x_consumer_key,
        consumer_secret=agent.x_consumer_secret,
        access_token=agent.x_access_token,
        access_token_secret=agent.x_access_token_secret,
        bearer_token=agent.x_bearer_token,
    )


def _pick_cta(db: Session, agent: Agent, for_reply: bool) -> Optional[str]:
    q = [c for c in agent.ctas if (c.for_replies if for_reply else c.for_posts)]
    return q[0].url if q else None


def _should_include_cta(db: Session, agent: Agent, action: str) -> bool:
    # every N posts/replies
    if action == "tweet" and agent.cta_every_n_posts:
        count = db.query(PostLog).filter(PostLog.agent_id == agent.id, PostLog.action == "tweet").count()
        return (count + 1) % agent.cta_every_n_posts == 0
    if action == "reply" and agent.cta_every_n_replies:
        count = db.query(PostLog).filter(PostLog.agent_id == agent.id, PostLog.action == "reply").count()
        return (count + 1) % agent.cta_every_n_replies == 0
    return False


def job_post(agent_id: int):
    db: Session = SessionLocal()
    try:
        agent = db.query(Agent).get(agent_id)
        if not agent or not agent.enable_post:
            return
        x = _x_client_for(agent)
        cta = _pick_cta(db, agent, for_reply=False) if _should_include_cta(db, agent, "tweet") else None
        text = craft_tweet(agent.style_profile, topic=agent.description or agent.brand_name or "brand" , cta_url=cta)
        tweet_id = x.tweet(text)
        if tweet_id:
            db.add(PostLog(agent_id=agent.id, action="tweet", posted_tweet_id=tweet_id, included_cta=bool(cta)))
            agent.last_post_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def job_reply_targets(agent_id: int):
    db: Session = SessionLocal()
    try:
        agent = db.query(Agent).get(agent_id)
        if not agent or not agent.enable_reply:
            return
        x = _x_client_for(agent)
        for target in agent.targets:
            if not target.user_id and target.handle:
                uid = x.get_user_by_username(target.handle)
                if uid:
                    target.user_id = uid
            if not target.user_id:
                continue
            tweets = x.get_user_tweets(target.user_id, since_id=target.last_seen_tweet_id, max_results=5)
            for t in reversed(tweets):  # reply oldest first
                cta = _pick_cta(db, agent, for_reply=True) if _should_include_cta(db, agent, "reply") else None
                reply_text = craft_reply(agent.style_profile, original_tweet=t["text"], cta_url=cta)
                posted_id = x.tweet(reply_text, in_reply_to_tweet_id=t["id"])  
                if posted_id:
                    db.add(PostLog(agent_id=agent.id, action="reply", reference_tweet_id=t["id"], posted_tweet_id=posted_id, included_cta=bool(cta)))
                    target.last_seen_tweet_id = t["id"]
                    db.commit()
        agent.last_reply_scan_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def job_like_and_retweet(agent_id: int):
    db: Session = SessionLocal()
    try:
        agent = db.query(Agent).get(agent_id)
        if not agent or (not agent.enable_like and not agent.enable_retweet):
            return
        x = _x_client_for(agent)
        for target in agent.targets:
            if not target.user_id and target.handle:
                uid = x.get_user_by_username(target.handle)
                if uid:
                    target.user_id = uid
            if not target.user_id:
                continue
            tweets = x.get_user_tweets(target.user_id, since_id=None, max_results=3)
            for t in tweets:
                if agent.enable_like:
                    x.like(t["id"])
                    db.add(PostLog(agent_id=agent.id, action="like", reference_tweet_id=t["id"]))
                if agent.enable_retweet:
                    x.retweet(t["id"])
                    db.add(PostLog(agent_id=agent.id, action="retweet", reference_tweet_id=t["id"]))
                db.commit()
        agent.last_like_scan_at = datetime.utcnow()
        agent.last_retweet_scan_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def job_keyword_replies(agent_id: int):
    db: Session = SessionLocal()
    try:
        agent = db.query(Agent).get(agent_id)
        if not agent or not agent.enable_reply:
            return
        x = _x_client_for(agent)
        # naive union of keywords with OR
        if not agent.keywords:
            return
        query = " OR ".join([k.keyword for k in agent.keywords])
        results = x.search_recent(query=query, max_results=5)
        for t in results:
            cta = _pick_cta(db, agent, for_reply=True) if _should_include_cta(db, agent, "reply") else None
            reply_text = craft_reply(agent.style_profile, original_tweet=t["text"], cta_url=cta)
            posted_id = x.tweet(reply_text, in_reply_to_tweet_id=t["id"])  
            if posted_id:
                db.add(PostLog(agent_id=agent.id, action="reply", reference_tweet_id=t["id"], posted_tweet_id=posted_id, included_cta=bool(cta)))
                db.commit()
        agent.last_reply_scan_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def job_rewrite_sources(agent_id: int):
    db: Session = SessionLocal()
    try:
        agent = db.query(Agent).get(agent_id)
        if not agent or not agent.enable_post:
            return
        x = _x_client_for(agent)
        for src in agent.sources:
            if not src.user_id and src.handle:
                uid = x.get_user_by_username(src.handle)
                if uid:
                    src.user_id = uid
            if not src.user_id:
                continue
            tweets = x.get_user_tweets(src.user_id, since_id=src.last_rewritten_tweet_id, max_results=3)
            for t in reversed(tweets):
                rewritten = rewrite_tweet(agent.style_profile, source_tweet=t["text"]) 
                posted_id = x.tweet(rewritten)
                if posted_id:
                    db.add(PostLog(agent_id=agent.id, action="tweet", reference_tweet_id=t["id"], posted_tweet_id=posted_id, included_cta=False))
                    src.last_rewritten_tweet_id = t["id"]
                    db.commit()
        db.commit()
    finally:
        db.close()


def schedule_agent_jobs(agent_id: int):
    # Remove existing jobs for this agent
    for job in list(scheduler.get_jobs()):
        if job.id.startswith(f"agent-{agent_id}-"):
            scheduler.remove_job(job.id)

    db: Session = SessionLocal()
    try:
        agent = db.query(Agent).get(agent_id)
        if not agent:
            return
        # Schedule post job
        if agent.enable_post:
            scheduler.add_job(job_post, "interval", seconds=agent.post_interval_s, id=f"agent-{agent_id}-post", args=[agent_id], replace_existing=True, coalesce=True, max_instances=1)
            # Also schedule rewrite-from-sources on the same cadence for simplicity
            scheduler.add_job(job_rewrite_sources, "interval", seconds=agent.post_interval_s, id=f"agent-{agent_id}-rewrite-sources", args=[agent_id], replace_existing=True, coalesce=True, max_instances=1)
        # Schedule replies to targets
        if agent.enable_reply:
            scheduler.add_job(job_reply_targets, "interval", seconds=agent.reply_interval_s, id=f"agent-{agent_id}-reply-targets", args=[agent_id], replace_existing=True, coalesce=True, max_instances=1)
            # Keyword replies use same cadence
            scheduler.add_job(job_keyword_replies, "interval", seconds=agent.reply_interval_s, id=f"agent-{agent_id}-keyword-replies", args=[agent_id], replace_existing=True, coalesce=True, max_instances=1)
        # Schedule likes/retweets
        if agent.enable_like or agent.enable_retweet:
            seconds = max(60, min(agent.like_interval_s or 600, agent.retweet_interval_s or 36000))
            scheduler.add_job(job_like_and_retweet, "interval", seconds=seconds, id=f"agent-{agent_id}-likes-rts", args=[agent_id], replace_existing=True, coalesce=True, max_instances=1)
    finally:
        db.close()


def schedule_all_agents():
    db: Session = SessionLocal()
    try:
        for agent in db.query(Agent).all():
            schedule_agent_jobs(agent.id)
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()