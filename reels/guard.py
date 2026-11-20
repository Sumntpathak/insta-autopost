"""Posting guard: enforce the standard posting plan in code, for every publisher that uses it.

The 30-day export showed reels posted in bursts (median gap 2 minutes, ten in ten minutes),
which makes them compete with each other for Instagram's first test audience. Rules:
  - at least MIN_GAP_MINUTES since the previous publish attempt (any pipeline in state.json)
  - at most DAILY_CAP posts per IST calendar day
The month calendar (reels/shipstack/calendar.json) uses 6 slots/day >= 2.5 h apart; the cap
leaves room for the news agent's posts.
"""
import datetime as dt

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
MIN_GAP_MINUTES = 60
DAILY_CAP = 12


def _time(post):
    stamp = post.get('published_at') or post.get('attempted_at')
    return dt.datetime.fromisoformat(stamp) if stamp else None


def blocked(posts, now, min_gap=MIN_GAP_MINUTES, cap=DAILY_CAP):
    """Return a human-readable reason if posting now would break the plan, else None."""
    times = [t for t in (_time(p) for p in posts.values()) if t]
    if times:
        last = max(times)
        gap = (now - last).total_seconds() / 60
        if gap < min_gap:
            return f'last post was {gap:.0f} min ago; the plan needs {min_gap} min between reels'
    today = now.astimezone(IST).date()
    count = sum(1 for t in times if t.astimezone(IST).date() == today)
    if count >= cap:
        return f'{count} posts already today (IST); the daily cap is {cap}'
    return None
