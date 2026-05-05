from pydantic import BaseModel, EmailStr
from sqlmodel import JSON, SQLModel, Field, create_engine,Column
from sqlalchemy.ext.mutable import MutableList
from typing import Optional
from datetime import datetime, timezone
from typing import Dict,Any,List

class User(BaseModel):
    email: EmailStr
    password: str

class ConversationHistory(SQLModel,table=True):
    id: Optional[int]=Field(default=None,primary_key=True)
    user_id: int=Field(foreign_key="userentity.id")
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(MutableList.as_mutable(JSON)))


class UserEntity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserDopamineAndSurvival(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: int = Field(foreign_key="userentity.id")
    dopamine_user: float
    survival_user: float
    dopamine_ai: float
    survival_ai: float
    timestamp: datetime = Field(default_factory=datetime.now(timezone.utc), index=True)


class UserDopamineAndSurvivalHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: int = Field(foreign_key="userentity.id")
    dopamine_user: float
    survival_user: float
    dopamine_ai: float
    survival_ai: float
    timestamp: datetime = Field(default_factory=datetime.now(timezone.utc), index=True)

sqlite_file_name = "savaan_users.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}", echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

