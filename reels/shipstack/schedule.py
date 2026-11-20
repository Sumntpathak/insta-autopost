"""Month calendar for unattended posting.

    python -m reels.shipstack.schedule make --start 2026-11-19 --days 30   # writes calendar.json
    python -m reels.shipstack.schedule plan                               # prints the due slot (or nothing)

calendar.json is the content plan: one entry per post with id, IST date/time, format and
episode. Each episode is a different race (Arena) or setup (Lab), so nothing repeats.
`plan` picks the earliest unposted slot that is due. A slot missed by more than 2 h is skipped (it never
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
STALE = dt.timedelta(hours=2)   # a slot missed by more than this is skipped, never posted late or allowed to block the queue
# Daily rhythm (IST). Balloon Pop is the proven performer, so it runs twice; the 1-2 news slots
# per hour in between are left free for the news agent.
DAY = [('08:10', 'physics'), ('10:40', 'balloon'), ('13:10', 'strings'),
       ('16:10', 'ring'), ('19:10', 'balloon'), ('21:40', 'strings')]


def make(start, days):
    episode = {'lab01': 0, 'lab02': 0, 'balloon': 10, 'strings': 10, 'ring': 10}   # 1-9 used for samples/tests
    slots = []
    for d in range(days):
        date = start + dt.timedelta(days=d)
        for time, kind in DAY:
            fmt = ('lab01' if d % 2 == 0 else 'lab02') if kind == 'physics' else kind
            episode[fmt] += 1
            slots.append({'id': f'CAL-{date.isoformat()}-{time.replace(":", "")}-{fmt}', 'date': date.isoformat(),
                          'time': time, 'format': fmt, 'episode': episode[fmt]})
    return {'paused': False, 'timezone': 'Asia/Kolkata', 'start': start.isoformat(), 'days': days,
            'note': 'Edit freely: change format/episode/time per slot, or set paused=true to stop.',
            'slots': slots}


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
    sub.add_parser('plan')
    a = ap.parse_args()
    if a.cmd == 'make':
        cal = make(dt.date.fromisoformat(a.start), a.days)
        CALENDAR.write_text(json.dumps(cal, indent=1) + '\n')
        print(f"Wrote {len(cal['slots'])} slots from {a.start} to {cal['slots'][-1]['date']}")
        return
    slot = due(json.loads(CALENDAR.read_text()), json.loads(STATE.read_text())['posts'], dt.datetime.now(IST))
    print(json.dumps(slot))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            out.write(f"due={'true' if slot else 'false'}\n")
            if slot:
                out.write(f"id={slot['id']}\nformat={slot['format']}\nepisode={slot['episode']}\n")


if __name__ == '__main__':
    sys.exit(main())
