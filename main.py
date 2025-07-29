"""
Patient Appointment Booking System - Simplified Version
Author: Vinod Yadav
Date: 7-25-2025
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import uvicorn

# Import our simple agent system
from agents.agent_graph import PatientAgentGraph
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

# Initialize the agent graph
try:
    agent_graph = PatientAgentGraph()
    print("✅ Agent system initialized successfully")
except Exception as e:
    print(f"❌ Error initializing agents: {e}")
    agent_graph = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Patient Appointment Booking System API", 
        "version": "1.0.0",
        "status": "running",
        "agents_loaded": agent_graph is not None
    }

@app.post("/chat", response_model=AppointmentResponse)
async def chat_with_agents(request: PatientRequest):
    """
    Main chat endpoint that processes patient requests through the agent graph
    """
    if not agent_graph:
        raise HTTPException(status_code=500, detail="Agent system not initialized")
    
    try:
        # Process the request through the agent graph
        result = await agent_graph.process_request(request)
        return result
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/agents/status")
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
        "system_status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": "2025-07-25",
        "agents_ready": agent_graph is not None,
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify everything works"""
    if not agent_graph:
        return {"error": "Agent system not available"}
    
    test_request = PatientRequest(
        message="Hello, I want to test the system",
        session_id="test_session"
    )
    
    try:
        result = await agent_graph.process_request(test_request)
        return {"test_result": "success", "response_received": True}
    except Exception as e:
        return {"test_result": "failed", "error": str(e)}

if __name__ == "__main__":
    print("🏥 Starting Patient Appointment Booking System...")
    print(f"📍 OpenAI API Key configured: {bool(os.getenv('OPENAI_API_KEY'))}")
    
    uvicorn.run(
        "main_simple:app",
        host=os.getenv("APP_HOST", "localhost"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )