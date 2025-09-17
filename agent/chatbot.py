from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import database
from models import models
from util import schemas
from routes.auth import get_current_user
from tavily import TavilyClient
import google.generativeai as genai
from dotenv import load_dotenv
import os
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any

load_dotenv()
router = APIRouter(prefix="/chat", tags=["Chatbot"])

# 🔹 Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# 🔹 Setup Tavily
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# 🔹 LangGraph State
class ChatState(TypedDict):
    thread_id: int
    user_message: str
    search_results: List[Dict[str, Any]]
    assistant_response: str
    user_id: int

# 🔹 LangGraph Nodes
def save_user_message(state: ChatState, db: Session) -> ChatState:
    user_msg = models.Message(role="user", content=state["user_message"], thread_id=state["thread_id"])
    db.add(user_msg)
    db.commit()
    return state

def perform_search(state: ChatState) -> ChatState:
    search_results = tavily_client.search(state["user_message"])
    state["search_results"] = search_results["results"][:3]
    return state

def generate_response(state: ChatState) -> ChatState:
    context = "\n".join([res["title"] + ": " + res["url"] for res in state["search_results"]])
    response = model.generate_content(f"User asked: {state['user_message']}\n\nExtra context:\n{context}")
    state["assistant_response"] = response.text
    return state

def save_assistant_response(state: ChatState, db: Session) -> ChatState:
    ai_msg = models.Message(role="assistant", content=state["assistant_response"], thread_id=state["thread_id"])
    db.add(ai_msg)
    db.commit()
    return state

# 🔹 LangGraph Workflow
def create_workflow():
    workflow = StateGraph(ChatState)
    
    workflow.add_node("save_user_message", lambda state: save_user_message(state, state["db"]))
    workflow.add_node("perform_search", perform_search)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("save_assistant_response", lambda state: save_assistant_response(state, state["db"]))
    
    workflow.set_entry_point("save_user_message")
    workflow.add_edge("save_user_message", "perform_search")
    workflow.add_edge("perform_search", "generate_response")
    workflow.add_edge("generate_response", "save_assistant_response")
    workflow.add_edge("save_assistant_response", END)
    
    return workflow.compile()

# 🔹 Routes
@router.post("/start", response_model=schemas.ThreadResponse)
def start_thread(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    thread = models.Thread(user_id=current_user.id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread

@router.post("/{thread_id}/message", response_model=schemas.ThreadResponse)
def send_message(thread_id: int, msg: schemas.MessageCreate, db: Session = Depends(database.get_db), 
                current_user: models.User = Depends(get_current_user)):
    thread = db.query(models.Thread).filter(models.Thread.id == thread_id, models.Thread.user_id == current_user.id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Initialize LangGraph workflow
    workflow = create_workflow()
    
    # Run the workflow
    initial_state = ChatState(
        thread_id=thread_id,
        user_message=msg.content,
        search_results=[],
        assistant_response="",
        user_id=current_user.id,
        db=db
    )
    
    final_state = workflow.invoke(initial_state)
    
    db.refresh(thread)
    return thread

@router.get("/threads", response_model=list[schemas.ThreadResponse])
def get_threads(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Thread).filter(models.Thread.user_id == current_user.id).all()