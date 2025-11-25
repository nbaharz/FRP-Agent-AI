# agent_setup.py – Agent oluşturma fonksiyonu
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationSummaryMemory
from agent_core.core.tools.lore_search import lore_search_tool
from agent_core.core.tools.world_state_tool import get_world_state_tool, set_world_state_tool, reputation_change_tool
from agent_core.core.tools.inventory_tool import inventory_add_tool, inventory_remove_tool
from agent_core.core.tools.quest_tool import get_quest_tool
from agent_core.core.prompts.gmPromptTemplate import gm_prompt 
from langchain.schema import SystemMessage
from sqlalchemy.orm import Session
from agent_core.core.memory.long_term import search_long_term_memory


load_dotenv()

def setup_agent(user_id: str = None, db: Session = None):
    # LLM model
    llm = ChatOpenAI(
        temperature=0.7,
        model_name="gpt-4",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Memory (per-user: load past messages if user_id/db provided)
    # konusmalari ozetleyerek tutan Langchain konusma hafizasi sistemlerindendir.
    memory = ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True
    )

    if user_id and db:
        try:
            relevant_memories = search_long_term_memory(
                db=db,
                user_id=user_id,
                npc_id= None,
                query="current context",
                k=5,
                score_threshold=0.75
            )
            if relevant_memories:
                memory_summaries = "\n".join([m["text"] for m in relevant_memories])
                memory.buffer = (
                    f"Relevant past memories:\n{memory_summaries}\n---\n" +
                    getattr(memory, "buffer", "")
                )
        except Exception as e:
            print(f"[LongTermMemory Recall Error] {e}")

    quest_tool = get_quest_tool(llm)

    tools = [
        lore_search_tool,
        get_world_state_tool, set_world_state_tool,
        inventory_add_tool, inventory_remove_tool,
        reputation_change_tool,
        quest_tool,
    ]

    # Initilaizing the agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        memory=memory,
        verbose=False,
        agent_kwargs={
        "system_message": SystemMessage(content=gm_prompt)
        }
    )

    return agent, memory
