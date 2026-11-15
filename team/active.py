"""Shared handover guard for legacy and team schedulers."""
from datetime import datetime,timezone
from .storage import config,read


def active(at=None):
    cfg=config(); state=read()
    if not cfg['enabled'] or not state.get('start_at'):return False
    current=at or datetime.now(timezone.utc)
    elapsed=(current-datetime.fromisoformat(state['start_at'])).total_seconds()
    return 0<=elapsed<cfg['pilot_days']*86400
