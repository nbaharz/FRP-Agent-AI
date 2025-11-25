from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db_session import get_db
from app.services.token_service import get_current_user
from agent_core.core.orchestrator.agent_orchestrator import AgentOrchestrator

router = APIRouter()

# Global orchestrator (tek instance)
orchestrator_instance: AgentOrchestrator | None = None


def get_orchestrator(db: Session) -> AgentOrchestrator:
    """
    Returns a shared orchestrator instance.
    Ensures chat and end-session share the same active_sessions memory.
    """
    global orchestrator_instance
    if orchestrator_instance is None:
        orchestrator_instance = AgentOrchestrator(db)
    return orchestrator_instance


class ChatInput(BaseModel):
    message: str


@router.post("/chat")
async def chat(
    input: ChatInput,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Handles user input and returns NPC response."""
    try:
        orchestrator = get_orchestrator(db)
        response = await orchestrator.handle_interaction(
            user_id=current_user.id,
            user_input=input.message,
        )
        return {"npc_id": "elara", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end-session")
async def end_session(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Ends chat session and stores summary in long-term memory."""
    try:
        orchestrator = get_orchestrator(db)
        summary = await orchestrator.end_session(user_id=current_user.id)
        return {
            "message": "Session ended and summarized successfully.",
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {e}")
