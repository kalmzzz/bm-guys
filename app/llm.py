from __future__ import annotations
from typing import Optional, List
from openai import OpenAI
from .config import settings


DEFAULT_MODEL = "gpt-4o-mini"


def _get_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def generate_text(prompt: str, system: Optional[str] = None, model: str = DEFAULT_MODEL, max_tokens: int = 200) -> str:
    client = _get_client()
    if client is None:
        # Fallback: echo prompt for development
        return prompt[:max_tokens]

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.7, max_tokens=max_tokens)
    return (resp.choices[0].message.content or "").strip()


def build_style_system_prompt(style_profile: Optional[str]) -> str:
    base = (
        "You are a social media copywriter tasked with writing engaging X (Twitter) content. \n"
        "Stay within 240 characters unless instructed otherwise. Keep the style consistent."
    )
    if style_profile:
        base += "\nStyle guide to emulate:\n" + style_profile.strip()
    return base


def craft_tweet(style_profile: Optional[str], topic: str, cta_url: Optional[str] = None) -> str:
    system = build_style_system_prompt(style_profile)
    user_prompt = f"Write a single tweet about: {topic}."
    if cta_url:
        user_prompt += f" Include this link naturally once: {cta_url}"
    return generate_text(user_prompt, system=system, max_tokens=180)


def craft_reply(style_profile: Optional[str], original_tweet: str, cta_url: Optional[str] = None) -> str:
    system = build_style_system_prompt(style_profile)
    user_prompt = (
        "Write a single tweet-length reply to the following tweet. Be relevant and add value, avoid generic praise.\n"
        f"Tweet: {original_tweet}\n"
    )
    if cta_url:
        user_prompt += f" Optionally include this link in a natural, non-spammy way if appropriate: {cta_url}"
    return generate_text(user_prompt, system=system, max_tokens=180)


def rewrite_tweet(style_profile: Optional[str], source_tweet: str) -> str:
    system = build_style_system_prompt(style_profile)
    user_prompt = (
        "Rewrite the following tweet in the target style. Preserve the core idea but make it original and non-plagiarized.\n"
        f"Tweet: {source_tweet}"
    )
    return generate_text(user_prompt, system=system, max_tokens=180)