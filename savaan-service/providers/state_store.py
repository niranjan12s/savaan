"""State store interface and adapters for per-user conversation and emotion state.

- SQLiteStateStore: the original SQLModel + SQLite storage. It delegates to the
  existing conversation_history and emotional_state functions, so the SQL and
  semantics are byte-for-byte the original behavior.
A Cloudflare D1 / Durable Object adapter lands with the Cloudflare adapter PR.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlmodel import Session

import conversation_history
import emotional_state
from model import models


class StateStore(ABC):
    @abstractmethod
    def get_conversation_history(self, user_id: int) -> Optional[List[Dict[str, Any]]]: ...

    @abstractmethod
    def update_conversation_history(
        self, user_id: int, role: str, message: str, continuity: bool
    ) -> None: ...

    @abstractmethod
    def reset_conversation(self, user_id: int) -> None: ...

    @abstractmethod
    def get_current_metrics(self, user_id: int) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def update_metrics(
        self,
        user_id: int,
        dopamine_user: float,
        survival_user: float,
        dopamine_ai: float,
        survival_ai: float,
    ) -> None: ...

    @abstractmethod
    def get_metrics_history(self, user_id: int) -> Optional[Dict[str, Any]]: ...


class SQLiteStateStore(StateStore):
    def _session(self) -> Session:
        return Session(models.engine)

    def get_conversation_history(self, user_id):
        with self._session() as session:
            return conversation_history.get_conversation_history(user_id, session)

    def update_conversation_history(self, user_id, role, message, continuity):
        with self._session() as session:
            conversation_history.update_conversation_history(
                user_id, role, message, continuity, session
            )

    def reset_conversation(self, user_id):
        with self._session() as session:
            conversation_history.reset_conversation(user_id, session)

    def get_current_metrics(self, user_id):
        with self._session() as session:
            return emotional_state.get_current_dopamine_and_survival(user_id, session)

    def update_metrics(self, user_id, dopamine_user, survival_user, dopamine_ai, survival_ai):
        with self._session() as session:
            emotional_state.update_dopamine_and_survival_data(
                user_id, dopamine_user, survival_user, dopamine_ai, survival_ai, session
            )

    def get_metrics_history(self, user_id):
        with self._session() as session:
            return emotional_state.get_dopamine_and_survival_history(user_id, session)
