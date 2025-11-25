import traceback
from datetime import datetime
from sqlalchemy.orm import Session
from agent_core.agent_setup import setup_agent
from agent_core.core.memory.long_term import add_long_term_memory
from app.repositories.chat_repository import ChatRepository


class AgentOrchestrator:
    """
    Handles user-NPC conversation sessions, in-memory session tracking, and
    long-term memory summarization.
    """

    def __init__(self, db: Session):
        self.db = db
        # 🔹 user_id -> {"messages": [(user, npc), ...], "session_start": datetime}
        self.active_sessions = {}

    def get_or_create_session(self, user_id: str):
        """Create or get the user's current active session"""
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = {
                "messages": [],
                "session_start": datetime.utcnow()
            }
        return self.active_sessions[user_id]

    async def generate_response(self, agent, user_input: str):
        """Generate LLM response asynchronously"""
        try:
            response = await agent.ainvoke({"input": user_input})
            if isinstance(response, dict):
                return response.get("output", "")
            return str(response)
        except Exception as e:
            print(f"[Response Error] {e}")
            return "I’m having trouble processing that right now."

    async def handle_interaction(self, user_id: str, user_input: str, context=None):
        try:
            repo = ChatRepository(self.db)

            # 1) Save user message
            repo.add_message(
                user_id=user_id,
                content=user_input,
                role="user"
            )

            # 2) GM agent & response
            agent, memory = setup_agent(user_id=user_id, db=self.db)
            gm_response = await self.generate_response(agent, user_input)

            # 3) Save GM response
            repo.add_message(
                user_id=user_id,
                content=gm_response,
                role="gm"
            )

            return gm_response

        except Exception as e:
            print(f"[Agent Error] {e}")
            traceback.print_exc()
            return "Something went wrong during the interaction."


    async def end_session(self, user_id: str):
        """
        Summarize the active chat session and store the conversation + summary
        in the LongTermMemory table.
        """
        try:
            if user_id not in self.active_sessions:
                return "No active session to summarize."

            session_data = self.active_sessions.pop(user_id)
            messages = session_data["messages"]

            if not messages:
                return "No messages to summarize."

            conversation_text = "\n".join(
                [f"USER: {u}\nGM: {n}" for u, n in messages]
            )

            agent, _ = setup_agent(user_id=user_id, db=self.db)
            summary_prompt = (
            "Summarize the following conversation between USER and GM "
            "in 3–4 sentences. Focus on main events, player actions, and "
            "important narrative developments.\n\n"
            f"{conversation_text}\n\n"
            "Produce a concise summary of what happened during this session."
            )

            summary_resp = await agent.ainvoke({"input": summary_prompt})
            summary_text = (
                summary_resp.get("output", "").strip()
                if isinstance(summary_resp, dict)
                else str(summary_resp).strip()
            )
            if not summary_text:
                summary_text = "[Session Summary Unavailable]"

            # Store conversation summary in long-term memory
            add_long_term_memory(
                db=self.db,
                user_id=user_id,
                npc_id=None,
                text=summary_text,
                tags={"type": "session_summary"},
                source_role="gm",
            )

            print(f"[Memory] Session summary stored for user {user_id}")
            return summary_text

        except Exception as e:
            print(f"[Session End Error] {e}")
            traceback.print_exc()
            return "Failed to summarize session."
