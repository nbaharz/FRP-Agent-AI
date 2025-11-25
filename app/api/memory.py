# api/memory.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.database.db_session import get_db
from agent_core.core.memory.long_term import add_long_term_memory, search_long_term_memory
from app.services.token_service import get_current_user

router = APIRouter()

class AddMemoryRequest(BaseModel):
    npc_id: Optional[str] = Field(
    default=None), 
    description="Optional NPC ID (for future NPC support)"
    text: str = Field(..., description="Text to be saved")
    tags: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AddMemoryResponse(BaseModel):
    memory_id: str

class SearchMemoryResponseItem(BaseModel):
    id: str
    user_id: str
    npc_id: Optional[str] = None,
    text: str
    tags: Optional[Dict[str, Any]]
    created_at: Optional[str]
    score: float

@router.post("/add", response_model=AddMemoryResponse)
def add_memory(
    req: AddMemoryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)):

    try:
        memory_id = add_long_term_memory(
            db,
            user_id=current_user.id,
            npc_id=req.npc_id,
            text=req.text,
            tags=req.tags,
            source_role = "gm",
        )
        return AddMemoryResponse(memory_id=memory_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[SearchMemoryResponseItem])
def search_memory(
    query: str = Query(...),
    npc_id: Optional[str]= Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) 
):
    
    results = search_long_term_memory(
        db=db,
        user_id=current_user.id,
        npc_id=npc_id,  # None -> GM-only memory
        query=query,
        k=10,
    )

    return results
