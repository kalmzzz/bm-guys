from __future__ import annotations
from typing import List
import re
from collections import Counter


def build_style_profile_from_tweets(tweets: List[str]) -> str:
    """
    Build a lightweight style guide string from example tweets.
    Heuristic approach: common hashtags, emojis, average length, exclamation/emoji frequency.
    """
    if not tweets:
        return "Conversational, helpful, positive tone. Avoid jargon."

    all_text = " \n".join(tweets)

    hashtags = re.findall(r"#\w+", all_text)
    emojis = re.findall(r"[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\u2600-\u26FF]", all_text)
    exclamations = sum(t.count("!") for t in tweets)
    avg_len = sum(len(t) for t in tweets) / max(1, len(tweets))

    top_hashtags = ", ".join([h for h, _ in Counter(hashtags).most_common(5)])
    top_emojis = "".join([e for e, _ in Counter(emojis).most_common(5)])

    guide = [
        "Tone: conversational, confident, helpful.",
        f"Average length target: ~{int(avg_len):d} chars.",
        f"Common hashtags to consider: {top_hashtags or 'n/a'}.",
        f"Preferred emojis: {top_emojis or 'n/a'}.",
        f"Exclamation usage frequency: {exclamations/max(1,len(tweets)):.2f} per tweet.",
        "Style tips: Use plain language, short sentences, avoid overuse of hashtags and emojis.",
    ]
    return "\n".join(guide)