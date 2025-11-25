from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator
from .db_session import Base
import json, enum, os, uuid


class JSONType(TypeDecorator):
    impl = Text
    def process_bind_param(self, value, dialect):
        return json.dumps(value, ensure_ascii=False) if value is not None else None
    def process_result_value(self, value, dialect):
        return json.loads(value) if value is not None else None

def json_column():
    if os.getenv("DATABASE_URL", "").startswith("postgres"):
        return Column(JSONB)
    return Column(JSONType)

# USER
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    inventory = relationship("Inventory", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("LongTermMemory", back_populates="user", cascade="all, delete-orphan")
    reputation = relationship("Reputation", back_populates="user", cascade="all, delete-orphan")
    quests = relationship("Quest", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


# MEMORY
# Chromdb vektor halini tutarken sqllite databasede ham text halini gormek iyi olur.
class LongTermMemory(Base):
    __tablename__ = "long_term_memory"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    npc_id  = Column(String, index=True, nullable=True) #ileride eklenebilir.

    source_role = Column(
        Enum("gm", "npc", name="memory_role"),
        nullable=False,
        server_default="gm"
    )

    text = Column(Text, nullable=False)
    tags = json_column()
    user = relationship("User", back_populates="memories")

# WORLD STATE (global)
class WorldState(Base):
    __tablename__ = "world_state"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    key = Column(String, unique=True, index=True)
    value = json_column()
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



# INVENTORY
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    item_name = Column(String, index=True)
    qty = Column(Integer, default=1)
    meta = json_column()
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="inventory")


# REPUTATION
class Reputation(Base):
    __tablename__ = "reputation"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    faction_id = Column(String, index=True)
    score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="reputation")

# QUEST SYSTEM

class QuestStatus(str, enum.Enum):
    locked = "locked"
    active = "active"
    completed = "completed"
    failed = "failed"

class Quest(Base):
    __tablename__ = "quests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    status = Column(Enum(QuestStatus), default=QuestStatus.locked, nullable=False)
    meta_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("User", back_populates="quests")

#CHAT MESSAGES
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    npc_id = Column(String, index=True, nullable=True) #ileride npc eklenebilir.
    
    # "user" or "gm"
    role = Column(String, nullable=False)

    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_messages")
