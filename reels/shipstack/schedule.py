"""Month calendar for unattended posting.

    python -m reels.shipstack.schedule make --start 2026-11-19 --days 30   # writes calendar.json
    python -m reels.shipstack.schedule plan                               # prints the due slot (or nothing)

calendar.json is the content plan: one entry per post with id, IST date/time, format and
episode. Each episode is a different race (Arena) or setup (Lab), so nothing repeats.
`plan` picks the earliest unposted slot that is due. A slot missed by more than 3 h is skipped (it never
posts late and never blocks later slots). Set "paused": true
in calendar.json to stop everything.
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CALENDAR = HERE / 'calendar.json'
STATE = HERE.parent / 'state.json'
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
STALE = dt.timedelta(hours=3)   # a slot missed by more than this is skipped, never posted late or allowed to block the queue
# Daily rhythm (IST): 12 posts, 90 min apart (the guard needs 60): 4 news, 4 DSA debugger, 4 automation, interleaved.
DAY = [('06:30', 'news'), ('08:00', 'dsa'), ('09:30', 'automation'), ('11:00', 'news'), ('12:30', 'dsa'), ('14:00', 'automation'),
       ('15:30', 'news'), ('17:00', 'dsa'), ('18:30', 'automation'), ('20:00', 'news'), ('21:30', 'dsa'), ('23:00', 'automation')]
FIRST_DSA = 2      # DSA #1 (Two Sum) went out with the launch


def make(start, days, not_before=None):
    """Slots carry episode 'next': the episode is chosen when the slot fires (see resolve), so a skipped slot wastes no content."""
    slots = []
    for d in range(days):
        date = start + dt.timedelta(days=d)
        for time, fmt in DAY:
            if not_before and dt.datetime.fromisoformat(f'{date}T{time}:00').replace(tzinfo=IST) < not_before:
                continue
            slots.append({'id': f'CAL-{date.isoformat()}-{time.replace(":", "")}-{fmt}', 'date': date.isoformat(),
                          'time': time, 'format': fmt, 'episode': 'next'})
    return {'paused': False, 'timezone': 'Asia/Kolkata', 'start': start.isoformat(), 'days': days,
            'note': 'Edit freely: change format per slot, or set paused=true to stop. Episodes resolve when a slot fires.',
            'slots': slots}


def available(fmt):
    """Episode numbers that exist for a format (news is unlimited)."""
    if fmt == 'dsa':
        sys.path.insert(0, str(HERE.parents[1]))
        from reels.shipstack.studio.problems import PROBLEMS
        return [e for e in sorted(PROBLEMS) if e >= FIRST_DSA]
    if fmt == 'automation':
        n = len(json.loads((HERE.parents[1] / 'film' / 'src' / 'automations.json').read_text(encoding='utf-8')))
        return list(range(1, n + 1))
    return None


def resolve(slot, posts):
    """Turn a calendar slot into the (format, episode) to render now. Falls back to news when DSA/automation content runs out."""
    fmt, episode = slot['format'], slot.get('episode')
    if fmt != 'news' and episode != 'next':
        return fmt, episode
    if fmt != 'news':
        used = {p.get('episode') for p in posts.values() if p.get('scene') == fmt and p.get('status') in ('published', 'publishing')}
        free = [e for e in available(fmt) if e not in used]
        if free:
            return fmt, free[0]
    done = sum(1 for p in posts.values() if p.get('scene') == 'news')
    return 'news', done + 1


def due(calendar, posts, now):
    if calendar.get('paused'):
        return None
    for slot in calendar['slots']:
        at = dt.datetime.fromisoformat(f"{slot['date']}T{slot['time']}:00").replace(tzinfo=IST)
        if at <= now < at + STALE and slot['id'] not in posts:
            return slot
    return None


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('make')
    m.add_argument('--start', required=True)
    m.add_argument('--days', type=int, default=30)
    m.add_argument('--not-before', help='ISO IST time: drop earlier slots of the first day')
    sub.add_parser('plan')
    a = ap.parse_args()
    if a.cmd == 'make':
        nb = dt.datetime.fromisoformat(a.not_before).replace(tzinfo=IST) if a.not_before else None
        cal = make(dt.date.fromisoformat(a.start), a.days, nb)
        CALENDAR.write_text(json.dumps(cal, indent=1) + '\n')
        print(f"Wrote {len(cal['slots'])} slots from {a.start} to {cal['slots'][-1]['date']}")
        return
    posts = json.loads(STATE.read_text())['posts']
    slot = due(json.loads(CALENDAR.read_text()), posts, dt.datetime.now(IST))
    if slot:
        slot = dict(slot, **dict(zip(('format', 'episode'), resolve(slot, posts))))
    print(json.dumps(slot))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            out.write(f"due={'true' if slot else 'false'}\n")
            if slot:
                out.write(f"id={slot['id']}\nformat={slot['format']}\nepisode={slot['episode']}\n")


if __name__ == '__main__':
    sys.exit(main())
