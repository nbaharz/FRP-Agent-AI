import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.db_session import Base
from app.database.models import Inventory
from agent_core.agent_setup import setup_agent


@pytest.fixture(scope="function")
def test_db(monkeypatch):
    """Create a temporary SQLite file-based database shared between the agent and the test."""
    # Use a file-based DB so both agent and test can access the same data
    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Patch SessionLocal references so that tools and the agent use this test DB
    monkeypatch.setattr("tools.inventory_tool.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("database.db_session.SessionLocal", TestingSessionLocal)

    yield TestingSessionLocal

    # Clean up safely
    Base.metadata.drop_all(bind=engine)
    engine.dispose()  # ✅ release SQLite file lock
    if os.path.exists("test.db"):
        os.remove("test.db")

def test_agent_inventory_add(test_db):
    """Verify that the agent can trigger the inventory_add tool using a natural language prompt."""
    # Initialize the agent
    agent_executor, memory = setup_agent()

    # User prompt
    prompt = "Add 1 sword to my inventory"
    result = agent_executor.run(prompt)

    # Verify the database entry
    db = test_db()
    row = db.query(Inventory).first()
    assert row is not None, "❌ No inventory record found in the database."
    assert row.id.lower() in ["sword", "kılıç"]
    assert row.qty == 1

    db.close()
    print("✅ Agent successfully executed inventory_add_tool via natural language.")
