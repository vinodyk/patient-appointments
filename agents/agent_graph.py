"""
Patient Agent Graph - LangGraph Implementation
Author: Vinod Yadav
Date: 7-25-2025
"""

from typing import Dict, Any, List
import asyncio
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from .assisting_agent import AssistingAgent
from .jailbreak_agent import JailbreakAgent
from .triage_agent import TriageAgent
from .comorbidity_agent import ComorbidityAgent
from .appointment_booker import AppointmentBookerAgent
from models.patient_models import PatientRequest, AppointmentResponse, AgentResponse

class PatientGraphState:
    """State management for the patient agent graph"""
    
    def __init__(self):
        self.patient_request: PatientRequest = None
        self.conversation_context: Dict[str, Any] = {}
        self.agent_responses: List[AgentResponse] = []
        self.security_status: str = "unknown"
        self.symptom_analysis: Dict[str, Any] = {}
        self.comorbidity_risk: Dict[str, Any] = {}
        self.appointment_data: Dict[str, Any] = {}
        self.requires_emergency: bool = False
        self.next_steps: List[str] = []
        self.final_message: str = ""

class PatientAgentGraph:
    """Main agent graph orchestrating patient appointment workflow"""
    
    def __init__(self):
        self.assisting_agent = AssistingAgent()
        self.jailbreak_agent = JailbreakAgent()
        self.triage_agent = TriageAgent()
        self.comorbidity_agent = ComorbidityAgent()
        self.appointment_booker = AppointmentBookerAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> CompiledStateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("security_check", self._security_check_node)
        workflow.add_node("initial_assistance", self._initial_assistance_node)
        workflow.add_node("triage_assessment", self._triage_assessment_node)
        workflow.add_node("comorbidity_analysis", self._comorbidity_analysis_node)
        workflow.add_node("appointment_booking", self._appointment_booking_node)
        workflow.add_node("emergency_route", self._emergency_route_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # Define the flow
        workflow.set_entry_point("security_check")
        
        # Security check routing
        workflow.add_conditional_edges(
            "security_check",
            self._route_after_security,
            {
                "block": END,
                "continue": "initial_assistance"
            }
        )
        
        # Initial assistance routing
        workflow.add_conditional_edges(
            "initial_assistance",
            self._route_after_assistance,
            {
                "emergency": "emergency_route",
                "triage": "triage_assessment",
                "booking": "appointment_booking",
                "continue": "finalize_response"
            }
        )
        
        # Triage routing
        workflow.add_conditional_edges(
            "triage_assessment",
            self._route_after_triage,
            {
                "emergency": "emergency_route",
                "comorbidity": "comorbidity_analysis",
                "booking": "appointment_booking"
            }
        )
        
        # Comorbidity routing
        workflow.add_edge("comorbidity_analysis", "appointment_booking")
        
        # Final routing
        workflow.add_edge("appointment_booking", "finalize_response")
        workflow.add_edge("emergency_route", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        return workflow.compile()
    
    async def process_request(self, request: PatientRequest) -> AppointmentResponse:
        """Process patient request through the agent graph"""
        
        # Initialize state
        initial_state = {
            "patient_request": request,
            "conversation_context": {},
            "agent_responses": [],
            "security_status": "unknown",
            "symptom_analysis": {},
            "comorbidity_risk": {},
            "appointment_data": {},
            "requires_emergency": False,
            "next_steps": [],
            "final_message": ""
        }
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state)
        
        # Convert to response model
        return self._create_response(result)
    
    async def _security_check_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Security and safety check node"""
        request = state["patient_request"]
        
        security_response = await self.jailbreak_agent.invoke(
            request.message,
            state["conversation_context"]
        )
        
        state["agent_responses"].append(AgentResponse(**security_response))
        state["security_status"] = security_response["data"]["safety_level"]
        
        return state
    
    async def _initial_assistance_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Initial assistance and information gathering node"""
        request = state["patient_request"]
        
        assistance_response = await self.assisting_agent.invoke(
            request.message,
            state["conversation_context"]
        )
        
        state["agent_responses"].append(AgentResponse(**assistance_response))
        state["conversation_context"].update(assistance_response["data"])
        
        return state
    
    async def _triage_assessment_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Medical triage assessment node"""
        request = state["patient_request"]
        
        triage_response = await self.triage_agent.invoke(
            request.message,
            state["conversation_context"]
        )
        
        state["agent_responses"].append(AgentResponse(**triage_response))
        state["symptom_analysis"] = triage_response["data"]["symptom_analysis"]
        state["requires_emergency"] = triage_response["data"].get("emergency_indicators", False)
        
        return state
    
    async def _comorbidity_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Comorbidity and risk factor analysis node"""
        request = state["patient_request"]
        
        # Combine context with symptom analysis
        enhanced_context = {**state["conversation_context"], **state["symptom_analysis"]}
        
        comorbidity_response = await self.comorbidity_agent.invoke(
            request.message,
            enhanced_context
        )
        
        state["agent_responses"].append(AgentResponse(**comorbidity_response))
        state["comorbidity_risk"] = comorbidity_response["data"]["comorbidity_risk"]
        
        return state
    
    async def _appointment_booking_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Appointment booking and scheduling node"""
        request = state["patient_request"]
        
        # Combine all context
        full_context = {
            **state["conversation_context"],
            "symptom_analysis": state["symptom_analysis"],
            "comorbidity_risk": state["comorbidity_risk"]
        }
        
        booking_response = await self.appointment_booker.invoke(
            request.message,
            full_context
        )
        
        state["agent_responses"].append(AgentResponse(**booking_response))
        state["appointment_data"] = booking_response["data"]
        
        return state
    
    async def _emergency_route_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Emergency routing node"""
        emergency_message = """🚨 EMERGENCY PROTOCOL ACTIVATED 🚨

Based on your symptoms, you may require immediate medical attention.

IMMEDIATE ACTIONS:
• Call 911 if experiencing severe symptoms
• Go to the nearest Emergency Room
• Do not drive yourself - call an ambulance or have someone drive you
• Bring a list of current medications
• Have your insurance information ready

If this is not a life-threatening emergency, consider:
• Urgent Care Center for same-day treatment
• Telehealth consultation with a physician
• Contact your primary care provider's emergency line

Your safety is our top priority. When in doubt, seek immediate medical care."""

        emergency_response = AgentResponse(
            agent_name="Emergency Protocol",
            message=emergency_message,
            confidence=1.0,
            action_taken="emergency_routing"
        )
        
        state["agent_responses"].append(emergency_response)
        state["requires_emergency"] = True
        state["next_steps"] = [
            "Call 911 if experiencing severe symptoms",
            "Go to nearest Emergency Room",
            "Contact emergency services",
            "Do not delay seeking immediate care"
        ]
        
        return state
    
    async def _finalize_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the response and generate summary"""
        
        # Generate next steps if not emergency
        if not state["requires_emergency"]:
            state["next_steps"] = self._generate_next_steps(state)
        
        # Generate final summary message
        state["final_message"] = self._generate_final_message(state)
        
        return state
    
    def _route_after_security(self, state: Dict[str, Any]) -> str:
        """Route after security check"""
        if state["security_status"] == "BLOCK":
            return "block"
        return "continue"
    
    def _route_after_assistance(self, state: Dict[str, Any]) -> str:
        """Route after initial assistance"""
        context = state["conversation_context"]
        
        if context.get("urgency_indicators"):
            return "emergency"
        elif context.get("extracted_info", {}).get("symptoms"):
            return "triage"
        elif "appointment" in state["patient_request"].message.lower():
            return "booking"
        return "continue"
    
    def _route_after_triage(self, state: Dict[str, Any]) -> str:
        """Route after triage assessment"""
        if state["requires_emergency"]:
            return "emergency"
        elif state["symptom_analysis"].get("risk_factors"):
            return "comorbidity"
        return "booking"
    
    def _generate_next_steps(self, state: Dict[str, Any]) -> List[str]:
        """Generate next steps based on assessment"""
        steps = []
        
        symptom_analysis = state["symptom_analysis"]
        appointment_data = state["appointment_data"]
        
        if symptom_analysis.get("severity") == "HIGH":
            steps.append("Schedule appointment within 24-48 hours")
            steps.append("Monitor symptoms closely")
        elif symptom_analysis.get("severity") == "MEDIUM":
            steps.append("Schedule appointment within 1 week")
            steps.append("Track symptom progression")
        else:
            steps.append("Schedule routine appointment")
            steps.append("Continue monitoring symptoms")
        
        if appointment_data.get("available_slots"):
            steps.append("Choose preferred appointment slot")
            steps.append("Confirm appointment booking")
        
        if state["comorbidity_risk"]:
            steps.extend(state["comorbidity_risk"].get("recommendations", []))
        
        return steps
    
    def _generate_final_message(self, state: Dict[str, Any]) -> str:
        """Generate final summary message"""
        if state["requires_emergency"]:
            return "Emergency care recommended. Please seek immediate medical attention."
        
        # Find the most relevant agent response
        booking_response = next(
            (r for r in state["agent_responses"] if r.agent_name == "Appointment Booker"),
            None
        )
        
        if booking_response:
            return booking_response.message
        
        # Default message
        return "Thank you for using our appointment booking system. Our agents have assessed your request and provided recommendations above."
    
    def _create_response(self, result: Dict[str, Any]) -> AppointmentResponse:
        """Create the final appointment response"""
        return AppointmentResponse(
            message=result["final_message"],
            agent_responses=result["agent_responses"],
            symptom_analysis=result["symptom_analysis"] if result["symptom_analysis"] else None,
            comorbidity_risk=result["comorbidity_risk"] if result["comorbidity_risk"] else None,
            available_slots=result["appointment_data"].get("available_slots", []),
            booking=result["appointment_data"].get("booking"),
            next_steps=result["next_steps"],
            requires_emergency=result["requires_emergency"],
            session_id=result["patient_request"].session_id
        )