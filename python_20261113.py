#pip install langgraph langchain-openai python-dotenv
import os
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Load environment variables from .env file if it exists
load_dotenv()

# ==========================================
# 1. DEFINE THE STATE
# ==========================================
class DebateState(TypedDict):
    # The messages annotation automatically appends new messages to the list
    messages: Annotated[Sequence[BaseMessage], add_messages]
    topic: str
    turn_count: int

# ==========================================
# 2. INITIALIZE THE MODEL (The "Copilot" Brain)
# ==========================================
# We use gpt-4o, which is the exact underlying model powering GitHub Copilot Chat
model = ChatOpenAI(model="gpt-4o", temperature=0.8)

# ==========================================
# 3. DEFINE THE AGENTS (NODES)
# ==========================================
def proposition_agent(state: DebateState):
    """The Proposition: Argues FOR the motion."""
    topic = state["topic"]
    messages = state["messages"]
    
    system_prompt = SystemMessage(content=f"""
    You are the PROPOSITION in a high-stakes Intelligence Squared debate. 
    The motion is: "{topic}"
    
    Your goal is to persuasively argue FOR this motion. 
    - Be brilliant, concise, and hard-hitting (max 2 paragraphs).
    - Use real-world examples, logic, and rhetoric.
    - If this is not your first turn, you MUST directly rebut the Opposition's previous argument before advancing your own point.
    - Do not break character. Do not say "As an AI...".
    """)
    
    # Combine system prompt with the debate history
    response = model.invoke([system_prompt] + messages)
    
    # We return the message to be added to the state
    return {"messages": [response]}

def opposition_agent(state: DebateState):
    """The Opposition: Argues AGAINST the motion."""
    topic = state["topic"]
    messages = state["messages"]
    
    system_prompt = SystemMessage(content=f"""
    You are the OPPOSITION in a high-stakes Intelligence Squared debate. 
    The motion is: "{topic}"
    
    Your goal is to persuasively argue AGAINST this motion. 
    - Be brilliant, concise, and hard-hitting (max 2 paragraphs).
    - Expose the flaws, risks, and unintended consequences of the Proposition's stance.
    - You MUST directly and aggressively rebut the Proposition's most recent argument.
    - Do not break character. Do not say "As an AI...".
    """)
    
    response = model.invoke([system_prompt] + messages)
    return {"messages": [response]}

# ==========================================
# 4. DEFINE THE GRAPH ROUTING (EDGES)
# ==========================================
def should_continue_debate(state: DebateState):
    """Conditional edge to determine if the debate should end."""
    max_turns = 6  # 3 rounds each (Prop, Opp, Prop, Opp, Prop, Opp)
    if state["turn_count"] >= max_turns:
        return "end"
    return "continue"

# ==========================================
# 5. BUILD AND COMPILE THE LANGGRAPH
# ==========================================
def create_debate_graph():
    # Initialize the StateGraph
    workflow = StateGraph(DebateState)

    # Add the nodes (agents)
    workflow.add_node("proposition", proposition_agent)
    workflow.add_node("opposition", opposition_agent)
    
    # Add a simple node just to increment the turn counter
    def increment_turn(state: DebateState):
        return {"turn_count": state["turn_count"] + 1}
    
    workflow.add_node("increment_turn", increment_turn)

    # Define the edges (the flow of the debate)
    workflow.add_edge(START, "proposition")
    workflow.add_edge("proposition", "opposition")
    workflow.add_edge("opposition", "increment_turn")
    
    # Add conditional edge: check if we should keep going or end
    workflow.add_conditional_edges(
        "increment_turn",
        should_continue_debate,
        {
            "continue": "proposition",
            "end": END
        }
    )

    # Compile the graph
    return workflow.compile()

# ==========================================
# 6. RUN THE DEBATE
# ==========================================
if __name__ == "__main__":
    TOPIC = "This House Would Mandate Memory-Safe Programming Languages for All Government and Critical Infrastructure Software."
    
    print(f"🏛️  INTELLIGENCE SQUARED DEBATE 🏛️")
    print(f"📜 MOTION: {TOPIC}\n")
    print("-" * 50)
    
    # Set up initial state
    initial_state = {
        "messages": [],
        "topic": TOPIC,
        "turn_count": 0
    }
    
    # Compile graph
    app = create_debate_graph()
    
    # Stream the debate in real-time to the VS Code terminal
    for event in app.stream(initial_state, stream_mode="updates"):
        for node_name, state_update in event.items():
            if "messages" in state_update:
                for msg in state_update["messages"]:
                    if isinstance(msg, BaseMessage) and msg.type != "system":
                        # Determine who is speaking based on the node
                        speaker = "🟢 PROPOSITION" if node_name == "proposition" else "🔴 OPPOSITION"
                        print(f"\n{speaker}:")
                        print(msg.content)
                        print("-" * 50)
                        
    print("\n🏁 DEBATE CONCLUDED. THE AUDIENCE WILL NOW VOTE. 🏁")