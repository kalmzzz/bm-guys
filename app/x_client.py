from __future__ import annotations
from typing import Optional, List
import tweepy


class XClient:
    def __init__(
        self,
        *,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str,
        bearer_token: Optional[str] = None,
    ) -> None:
        self.client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            bearer_token=bearer_token,
            wait_on_rate_limit=True,
        )

    # Posting
    def tweet(self, text: str, in_reply_to_tweet_id: Optional[str] = None) -> Optional[str]:
        resp = self.client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to_tweet_id)
        if resp and resp.data and "id" in resp.data:
            return str(resp.data["id"])
        return None

    # Likes
    def like(self, tweet_id: str) -> None:
        self.client.like(tweet_id=tweet_id)

    # Retweet
    def retweet(self, tweet_id: str) -> None:
        self.client.retweet(tweet_id=tweet_id)

    # Lookups
    def get_user_by_username(self, username: str) -> Optional[str]:
        r = self.client.get_user(username=username)
        if r and r.data:
            return str(r.data.id)
        return None

    def get_user_tweets(self, user_id: str, since_id: Optional[str] = None, max_results: int = 5) -> List[dict]:
        r = self.client.get_users_tweets(
            id=user_id,
            since_id=since_id,
            max_results=max_results,
            tweet_fields=["id", "text", "created_at", "author_id", "referenced_tweets"],
        )
        tweets = []
        if r and r.data:
            for t in r.data:
                tweets.append({"id": str(t.id), "text": t.text})
        return tweets

    def search_recent(self, query: str, since_id: Optional[str] = None, max_results: int = 10) -> List[dict]:
        r = self.client.search_recent_tweets(
            query=query,
            since_id=since_id,
            max_results=max_results,
            tweet_fields=["id", "text", "created_at", "author_id"],
        )
        tweets = []
        if r and r.data:
            for t in r.data:
                tweets.append({"id": str(t.id), "text": t.text, "author_id": str(t.author_id)})
        return tweets