"""Private dated flow service with shared token coordination and read-only transport."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone, timedelta


class FlowService:
    @staticmethod
    def _checked(operation, stage):
        try:
            return operation()
        except Exception:
            # Fixed stage names only: never log provider exceptions or private values.
            print('NH flow unavailable: ' + stage)
            raise RuntimeError('private flow unavailable') from None

    def __init__(self, token_manager, transport, sanitize_rows, monotonic=time.monotonic, utcnow=None, archive=None, session_provider=None):
        self.token_manager, self.transport, self.sanitize_rows = token_manager, transport, sanitize_rows
        self.monotonic = monotonic
        self.utcnow = utcnow or (lambda: datetime.now(timezone.utc))
        self.lock = threading.Lock()
        self.cached, self.cached_at = None, 0.0
        self.archive, self.session_provider = archive, session_provider

    def get(self, trade_date=None):
        with self.lock:
            now = self.utcnow()
            today = now.astimezone(timezone(timedelta(hours=9))).date().isoformat()
            if trade_date and (datetime.strptime(trade_date, '%Y-%m-%d').date().isoformat() != trade_date or trade_date > today):
                raise ValueError('invalid requested date')
            if self.archive and trade_date and trade_date < today:
                saved = self.archive.read(trade_date)
                if not saved: raise ValueError('no saved flow for date')
                return saved
            if self.cached is not None and self.monotonic() - self.cached_at < 30 and (not trade_date or self.cached.get('tradeDate') == trade_date):
                return self.cached
            session = None
            if self.archive:
                try:
                    session = self._checked(self.session_provider, 'market-date')
                except Exception:
                    saved = self.archive.read(trade_date or today) or (self.archive.latest() if not trade_date else None)
                    if saved: return saved
                    raise
                if session['date'] != today:
                    saved = self.archive.read(trade_date or session['date'])
                    if saved: return saved
                    raise ValueError('no verified current trading day')
                saved = self._checked(lambda: self.archive.read(today), 'archive-read')
                if saved and saved.get('sessionStatus') == 'closed': return saved
            token = self._checked(self.token_manager.get_token, 'shared-token')
            series = {}
            for name in ("amount", "quantity"):
                payload = self._checked(lambda: self.transport.read_flow(token, name), 'quote-' + name)
                series[name] = self.sanitize_rows(payload)
            fetched = self.utcnow()
            self.cached = {"source": "NH PLUG", "market": "UNT", "fetchedAt": fetched.isoformat(),
                           "tradeDate": None, "unitsVerified": False, **series}
            if self.archive:
                after = self._checked(self.session_provider, 'market-date-after')
                if after['date'] != session['date'] or fetched.astimezone(timezone(timedelta(hours=9))).date().isoformat() != today:
                    self.cached = None
                    raise ValueError('trading day changed during collection')
                # Keep regular-session values only; never attach night/next-day rows.
                import re
                for mode in ('amount', 'quantity'):
                    self.cached[mode] = [r for r in series[mode] if re.fullmatch(r'\d{2}:\d{2}:\d{2}', str(r.get('bsop_hour', '')))
                        and '09:00:00' <= r['bsop_hour'] <= '15:30:00'
                        and re.fullmatch(r'\d{12}', str(r.get('timez12', '')))
                        and r['timez12'][-6:] == r['bsop_hour'].replace(':', '')]
                if not all(self.cached[m] for m in ('amount', 'quantity')):
                    self.cached = None
                    print('NH flow unavailable: regular-session-rows')
                    raise ValueError('no regular session flow')
                closed = after['closed'] and all(max(r['bsop_hour'] for r in self.cached[m]) >= '15:30:00' for m in ('amount', 'quantity'))
                self.cached.update(tradeDate=today, dateVerified=True, persisted=True,
                    sessionStatus='closed' if closed else 'partial')
                self._checked(lambda: self.archive.save(self.cached), 'archive-save')
            self.cached_at = self.monotonic()
            return self.cached
