
# agents/__init__.py
"""
Patient Appointment Booking System Agents
Author: Vinod Yadav
Date: 7-25-2025
"""

# Import only what we need for the simple version
from .base_agent import BaseAgent
from .assisting_agent import AssistingAgent
from .jailbreak_agent import JailbreakAgent
from .triage_agent import TriageAgent
from .comorbidity_agent import ComorbidityAgent
from .appointment_booker import AppointmentBookerAgent

try:
    from .agent_graph_simple import PatientAgentGraph
except ImportError:
    # Fallback if the file doesn't exist
    PatientAgentGraph = None

__all__ = [
    "BaseAgent",
    "AssistingAgent",
    "JailbreakAgent", 
    "TriageAgent",
    "ComorbidityAgent",
    "AppointmentBookerAgent",
    "PatientAgentGraph"
]