from app.database.models import ChatMessage

class ChatRepository:
    def __init__(self, db):
        self.db = db


    def add_message(self, user_id: str, content: str, role: str, npc_id=None):
        """
        Unified method to add both user and GM messages.
        Role is ALWAYS decided by the backend.
        """
        if role not in ["user", "gm"]:
            raise ValueError(f"Backend attempted to save invalid role: {role}")

        message = ChatMessage(
            user_id=user_id,
            npc_id=npc_id,
            role=role,
            content=content,
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

