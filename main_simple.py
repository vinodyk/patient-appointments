"""
Patient Appointment Booking System - Simplified Version
Author: Vinod Yadav
Date: 7-25-2025
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import uvicorn

# Import our simple agent system
from agents.agent_graph_simple import PatientAgentGraph
from models.patient_models import PatientRequest, AppointmentResponse

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Patient Appointment Booking System",
    description="AI-powered patient appointment booking with symptom analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the React app for all frontend routes
@app.get("/")
async def serve_frontend():
    """Serve the React app"""
    frontend_path = "frontend/dist/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Patient Appointment Booking System API", "frontend": "not_available", "path_checked": frontend_path}

# Serve static assets
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

# Session storage for conversation context
session_storage: Dict[str, Dict[str, Any]] = {}

# Initialize the agent graph
try:
    agent_graph = PatientAgentGraph()
    print("✅ Agent system initialized successfully")
except Exception as e:
    print(f"❌ Error initializing agents: {e}")
    agent_graph = None

def get_session_context(session_id: str) -> Dict[str, Any]:
    """Get conversation context for a session"""
    if session_id not in session_storage:
        session_storage[session_id] = {
            "conversation_history": [],
            "patient_info": {},
            "symptom_analysis": {},
            "comorbidity_risk": {},
            "available_slots": [],
            "last_booking_requirements": {},
            "conversation_stage": "initial"
        }
    return session_storage[session_id]

def update_session_context(session_id: str, response: AppointmentResponse, request: PatientRequest):
    """Update session context with new information"""
    context = get_session_context(session_id)
    
    # Add to conversation history
    context["conversation_history"].append({
        "user_message": request.message,
        "assistant_response": response.message,
        "timestamp": "now",
        "agent_responses": [agent.dict() for agent in response.agent_responses]
    })
    
    # Update persistent info
    if response.symptom_analysis:
        context["symptom_analysis"] = response.symptom_analysis.dict()
    
    if response.comorbidity_risk:
        context["comorbidity_risk"] = response.comorbidity_risk.dict()
    
    if response.available_slots:
        context["available_slots"] = [slot.dict() for slot in response.available_slots]
    
    # Update conversation stage
    if response.available_slots:
        context["conversation_stage"] = "slots_provided"
    elif response.booking:
        context["conversation_stage"] = "booking_confirmed"
    elif response.requires_emergency:
        context["conversation_stage"] = "emergency"
    
    # Keep only last 10 exchanges to prevent memory bloat
    if len(context["conversation_history"]) > 10:
        context["conversation_history"] = context["conversation_history"][-10:]

# Catch-all route for React Router (SPA)
@app.get("/{path:path}")
async def serve_frontend_routes(path: str):
    """Serve React app for all routes (SPA support)"""
    # API routes should not be caught here
    if path.startswith("api/") or path in ["docs", "redoc", "openapi.json", "health"]:
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    frontend_path = "frontend/dist/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Frontend not available", "path": path, "checked": frontend_path}

@app.get("/api/")
async def root():
    """Root API endpoint"""
    return {
        "message": "Patient Appointment Booking System API", 
        "version": "1.0.0",
        "status": "running",
        "agents_loaded": agent_graph is not None,
        "active_sessions": len(session_storage),
        "environment": os.getenv("APP_ENV", "development")
    }

@app.post("/api/chat", response_model=AppointmentResponse)
async def chat_with_agents(request: PatientRequest):
    """
    Main chat endpoint that processes patient requests through the agent graph
    """
    if not agent_graph:
        raise HTTPException(status_code=500, detail="Agent system not initialized")
    
    try:
        # Get session context
        session_id = request.session_id or "default_session"
        session_context = get_session_context(session_id)
        
        # Add session context to the request processing
        request_with_context = PatientRequest(
            message=request.message,
            session_id=session_id,
            patient_id=request.patient_id
        )
        
        # Process the request through the agent graph with context
        result = await agent_graph.process_request(request_with_context, session_context)
        
        # Update session with the results
        update_session_context(session_id, result, request)
        
        return result
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information for debugging"""
    if session_id in session_storage:
        context = session_storage[session_id]
        return {
            "session_id": session_id,
            "conversation_stage": context.get("conversation_stage"),
            "has_symptoms": bool(context.get("symptom_analysis")),
            "has_available_slots": bool(context.get("available_slots")),
            "conversation_length": len(context.get("conversation_history", []))
        }
    return {"error": "Session not found"}

@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session"""
    if session_id in session_storage:
        del session_storage[session_id]
        return {"message": f"Session {session_id} cleared"}
    return {"message": "Session not found"}

@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    if not agent_graph:
        return {"error": "Agent system not initialized"}
    
    return {
        "agents": [
            {"name": "Assisting Agent", "status": "active", "role": "Initial patient interaction"},
            {"name": "Jailbreak Agent", "status": "active", "role": "Security and safety checks"},
            {"name": "Triage Agent", "status": "active", "role": "Medical priority assessment"},
            {"name": "Comorbidity Agent", "status": "active", "role": "Risk factor analysis"},
            {"name": "Appointment Booker", "status": "active", "role": "Schedule management"}
        ],
        "system_status": "operational",
        "active_sessions": len(session_storage)
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": "2025-07-25",
        "agents_ready": agent_graph is not None,
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "active_sessions": len(session_storage),
        "environment": os.getenv("APP_ENV", "development")
    }

@app.get("/health")
async def health_check_simple():
    """Simple health check for load balancers"""
    return {"status": "ok"}

if __name__ == "__main__":
    print("🏥 Starting Patient Appointment Booking System...")
    print(f"📍 OpenAI API Key configured: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"🌍 Environment: {os.getenv('APP_ENV', 'development')}")
    
    # Use PORT environment variable for Cloud Run
    port = int(os.getenv("PORT", os.getenv("APP_PORT", 8080)))
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload in production
    )