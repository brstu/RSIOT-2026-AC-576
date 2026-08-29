"""Circuit breaker для клиента devices → alerts — эталон лабы 3 (вариант 0).

Конечный автомат (лекция 09):

    CLOSED    → OPEN       в окне последних window_size вызовов набралось
                           fail_threshold ошибок — хватит мучить зависимость;
    OPEN      → HALF_OPEN  прошло recovery_timeout секунд с открытия
                           (до этого allow() отвечает False — fail fast);
    HALF_OPEN → CLOSED     пробный вызов удался — зависимость ожила;
    HALF_OPEN → OPEN       пробный вызов провалился — ждём заново.

Что считать ошибкой, решает вызывающий код (record_failure): здесь это
сетевая ошибка, таймаут или 5xx. Медленные-но-успешные ответы breaker
НЕ учитывает — это бонусное задание лабы.
"""

import logging
import time
from collections import deque
from enum import Enum

log = logging.getLogger("devices.breaker")


class BreakerState(str, Enum):
    CLOSED = "closed"        # вызовы идут, ошибки считаются в окне
    OPEN = "open"            # вызовы запрещены: мгновенный отказ (fail fast)
    HALF_OPEN = "half-open"  # пропускаем до half_open_max пробных вызовов


class CircuitBreaker:
    """Свой breaker на КАЖДУЮ зависимость. У примера она одна — alerts."""

    def __init__(
        self,
        *,
        fail_threshold: int = 3,     # сколько ошибок в окне открывает breaker
        window_size: int = 10,       # окно: сколько последних вызовов помним
        recovery_timeout: float = 8.0,  # сколько секунд OPEN «остывает»
        half_open_max: int = 1,      # сколько проб пускаем в HALF_OPEN
        name: str = "alerts",
    ) -> None:
        self.fail_threshold = fail_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max
        self.name = name
        self._window: deque[bool] = deque(maxlen=window_size)  # True = успех
        self._state = BreakerState.CLOSED
        self._opened_at = 0.0
        self._probes = 0
        self.transitions: list[str] = []
        self.counters = {"allowed": 0, "rejected": 0, "success": 0, "failure": 0}

    @property
    def state(self) -> str:
        return self._state.value

    def _set_state(self, new: BreakerState, reason: str) -> None:
        old, self._state = self._state, new
        # Причины переходов — латиницей: Invoke-RestMethod в Windows
        # PowerShell 5.1 декодирует JSON как Latin-1 и портит кириллицу.
        event = f"{old.value} -> {new.value} ({reason})"
        self.transitions.append(f"{time.strftime('%H:%M:%S')} {event}")
        log.warning("breaker[%s]: %s", self.name, event)

    def allow(self) -> bool:
        """Можно ли делать вызов прямо сейчас. Вызывать ПЕРЕД каждым вызовом."""
        if self._state is BreakerState.OPEN:
            if time.monotonic() - self._opened_at < self.recovery_timeout:
                self.counters["rejected"] += 1
                return False
            self._probes = 0
            self._set_state(BreakerState.HALF_OPEN, "recovery timeout elapsed, probing")
        if self._state is BreakerState.HALF_OPEN:
            if self._probes >= self.half_open_max:
                self.counters["rejected"] += 1  # проба уже в полёте — не толпимся
                return False
            self._probes += 1
        self.counters["allowed"] += 1
        return True

    def record_success(self) -> None:
        """Вызов удался (2xx). Вызывать ПОСЛЕ каждого разрешённого вызова."""
        self.counters["success"] += 1
        self._window.append(True)
        if self._state is BreakerState.HALF_OPEN:
            self._window.clear()
            self._set_state(BreakerState.CLOSED, "probe succeeded")

    def record_failure(self) -> None:
        """Вызов провалился (сеть/таймаут/5xx после всех ретраев)."""
        self.counters["failure"] += 1
        self._window.append(False)
        if self._state is BreakerState.HALF_OPEN:
            self._opened_at = time.monotonic()
            self._set_state(BreakerState.OPEN, "probe failed")
        elif self._state is BreakerState.CLOSED:
            fails = sum(1 for ok in self._window if not ok)
            if fails >= self.fail_threshold:
                self._opened_at = time.monotonic()
                self._set_state(
                    BreakerState.OPEN,
                    f"{fails} failures in window of {len(self._window)}",
                )

    def snapshot(self) -> dict:
        """Состояние для /health — простейшие метрики breaker'а."""
        return {
            "state": self.state,
            "counters": dict(self.counters),
            "recent_transitions": self.transitions[-10:],
        }
