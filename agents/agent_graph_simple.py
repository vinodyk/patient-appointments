"""
Patient Agent Graph - Simple Implementation (No LangGraph)
Author: Vinod Yadav
Date: 7-25-2025
"""

from typing import Dict, Any, List
import asyncio

from .assisting_agent import AssistingAgent
from .jailbreak_agent import JailbreakAgent
from .triage_agent import TriageAgent
from .comorbidity_agent import ComorbidityAgent
from .appointment_booker import AppointmentBookerAgent
from models.patient_models import PatientRequest, AppointmentResponse, AgentResponse

class PatientAgentGraph:
    """Main agent graph orchestrating patient appointment workflow"""
    
    def __init__(self):
        self.assisting_agent = AssistingAgent()
        self.jailbreak_agent = JailbreakAgent()
        self.triage_agent = TriageAgent()
        self.comorbidity_agent = ComorbidityAgent()
        self.appointment_booker = AppointmentBookerAgent()
    
    async def process_request(self, request: PatientRequest, session_context: Dict[str, Any] = None) -> AppointmentResponse:
        """Process patient request through the agent workflow with session context"""
        
        # Initialize workflow state with session context
        state = {
            "patient_request": request,
            "conversation_context": session_context or {},
            "agent_responses": [],
            "security_status": "unknown",
            "symptom_analysis": session_context.get("symptom_analysis", {}) if session_context else {},
            "comorbidity_risk": session_context.get("comorbidity_risk", {}) if session_context else {},
            "appointment_data": {},
            "requires_emergency": False,
            "next_steps": [],
            "final_message": ""
        }
        
        # Add conversation history to context for agents
        if session_context and session_context.get("conversation_history"):
            state["conversation_context"]["conversation_history"] = session_context["conversation_history"]
            state["conversation_context"]["conversation_stage"] = session_context.get("conversation_stage", "initial")
            state["conversation_context"]["available_slots"] = session_context.get("available_slots", [])
        
        try:
            # Check if user is trying to book from previously shown slots
            if self._is_booking_from_previous_slots(request, session_context):
                return await self._handle_slot_booking(request, session_context)
            
            # Step 1: Security Check
            await self._security_check(state)
            
            if state["security_status"] == "BLOCK":
                return self._create_blocked_response(state)
            
            # Step 2: Initial Assistance
            await self._initial_assistance(state)
            
            # Step 2.5: Check if this is a non-medical request
            if self._is_non_medical_request(state):
                # For non-medical requests, just return the polite redirect
                self._finalize_response(state)
                return self._create_response(state)
            
            # Step 2.6: Check if this is a direct booking request with context
            if self._is_booking_request_with_context(state):
                await self._appointment_booking(state)
                self._finalize_response(state)
                return self._create_response(state)
            
            # Step 3: Check for emergency routing
            if self._should_route_to_emergency(state):
                await self._emergency_route(state)
                return self._create_response(state)
            
            # Step 4: Triage Assessment (if symptoms present or new symptoms)
            if self._has_symptoms(state) or not state["symptom_analysis"]:
                await self._triage_assessment(state)
                
                # Step 5: Emergency check after triage
                if state.get("requires_emergency"):
                    await self._emergency_route(state)
                    return self._create_response(state)
                
                # Step 6: Comorbidity Analysis (if high risk)
                if self._needs_comorbidity_analysis(state):
                    await self._comorbidity_analysis(state)
            
            # Step 7: Appointment Booking
            await self._appointment_booking(state)
            
            # Step 8: Finalize Response
            self._finalize_response(state)
            
            return self._create_response(state)
            
        except Exception as e:
            return self._create_error_response(str(e))
    
    def _is_booking_from_previous_slots(self, request: PatientRequest, session_context: Dict[str, Any]) -> bool:
        """Check if user is trying to book from previously shown appointment slots"""
        if not session_context:
            return False
        
        available_slots = session_context.get("available_slots", [])
        if not available_slots:
            return False
        
        message_lower = request.message.lower()
        booking_keywords = ["book", "schedule", "confirm", "reserve", "choose", "select", "pick"]
        
        # Check if message contains booking intent
        has_booking_intent = any(keyword in message_lower for keyword in booking_keywords)
        
        # Check if message references specific doctors, times, or slot numbers
        slot_references = []
        for slot in available_slots:
            doctor_name = slot.get("doctor", "").lower()
            if any(part in message_lower for part in doctor_name.split()):
                slot_references.append(slot)
            if slot.get("time", "").lower() in message_lower:
                slot_references.append(slot)
            if slot.get("date", "") in message_lower:
                slot_references.append(slot)
        
        # Check for slot numbers (1, 2, 3, etc.)
        import re
        slot_numbers = re.findall(r'\b(\d+)\b', message_lower)
        if slot_numbers and has_booking_intent:
            return True
        
        # Check for doctor names specifically
        doctor_names = ["michael", "chen", "sarah", "johnson", "emily", "rodriguez"]
        has_doctor_reference = any(name in message_lower for name in doctor_names)
        
        return has_booking_intent and (slot_references or has_doctor_reference or "appointment" in message_lower)
    
    async def _handle_slot_booking(self, request: PatientRequest, session_context: Dict[str, Any]) -> AppointmentResponse:
        """Handle booking from previously shown slots"""
        available_slots = session_context.get("available_slots", [])
        message_lower = request.message.lower()
        
        # Try to identify which slot the user wants
        selected_slot = None
        
        # Check for doctor name reference (like "michael chen")
        for slot in available_slots:
            doctor_lower = slot.get("doctor", "").lower()
            # Split doctor name and check if any part is mentioned
            doctor_parts = doctor_lower.replace("dr. ", "").split()
            if any(part in message_lower for part in doctor_parts):
                selected_slot = slot
                break
        
        # Check for slot number (1, 2, 3, etc.)
        if not selected_slot:
            import re
            slot_numbers = re.findall(r'\b(\d+)\b', message_lower)
            if slot_numbers:
                try:
                    slot_index = int(slot_numbers[0]) - 1  # Convert to 0-based index
                    if 0 <= slot_index < len(available_slots):
                        selected_slot = available_slots[slot_index]
                except (ValueError, IndexError):
                    pass
        
        # Check for time reference
        if not selected_slot:
            for slot in available_slots:
                time_str = slot.get("time", "").lower().replace(" ", "")
                message_clean = message_lower.replace(" ", "")
                if time_str in message_clean:
                    selected_slot = slot
                    break
        
        # Default to first slot if no specific selection but booking intent is clear
        if not selected_slot and available_slots:
            if any(word in message_lower for word in ["book", "schedule", "confirm", "yes"]):
                selected_slot = available_slots[0]
        
        if selected_slot:
            # Create booking
            import uuid
            from models.patient_models import AppointmentBooking, AppointmentType, AgentResponse
            
            booking = AppointmentBooking(
                appointment_id=f"APT-{uuid.uuid4().hex[:8].upper()}",
                patient_id=request.patient_id or str(uuid.uuid4())[:8],
                date=selected_slot["date"],
                time=selected_slot["time"],
                doctor=selected_slot["doctor"],
                specialty=selected_slot["specialty"],
                appointment_type=AppointmentType.GENERAL,
                confirmed=True
            )
            
            booking_message = f"""✅ **APPOINTMENT CONFIRMED**

🎯 **Appointment Details:**
• **ID**: {booking.appointment_id}
• **Date**: {booking.date}
• **Time**: {booking.time}
• **Doctor**: {booking.doctor}
• **Specialty**: {booking.specialty}

📋 **Next Steps:**
• You'll receive a confirmation email shortly
• Please arrive 15 minutes early for check-in
• Bring your insurance card and ID
• Prepare any questions you'd like to discuss

Thank you for choosing our medical services! If you need to reschedule, please call us at least 24 hours in advance."""
            
            agent_response = AgentResponse(
                agent_name="Appointment Booker",
                message=f"Successfully booked appointment with {booking.doctor}",
                confidence=1.0,
                action_taken="slot_booking_confirmed"
            )
            
            return AppointmentResponse(
                message=booking_message,
                agent_responses=[agent_response],
                booking=booking,
                available_slots=[],
                next_steps=[
                    "Arrive 15 minutes early",
                    "Bring insurance card and ID",
                    "Prepare questions for your doctor"
                ],
                requires_emergency=False,
                session_id=request.session_id
            )
        
        # If we couldn't identify the slot, ask for clarification
        clarification_message = """🤔 I'd like to help you book an appointment, but I need clarification on which slot you'd prefer.

**Available options:**
"""
        for i, slot in enumerate(available_slots, 1):
            clarification_message += f"{i}. {slot['date']} at {slot['time']} with {slot['doctor']}\n"
        
        clarification_message += "\nPlease specify which option you'd like (e.g., 'Book option 1' or 'Schedule with Dr. Chen')."
        
        agent_response = AgentResponse(
            agent_name="Appointment Booker",
            message="Requesting clarification for slot selection",
            confidence=0.8,
            action_taken="clarification_requested"
        )
        
        return AppointmentResponse(
            message=clarification_message,
            agent_responses=[agent_response],
            available_slots=session_context.get("available_slots", []),
            next_steps=["Specify which appointment slot you prefer"],
            requires_emergency=False,
            session_id=request.session_id
        )
    
    async def _security_check(self, state: Dict[str, Any]):
        """Security and safety check"""
        request = state["patient_request"]
        
        security_response = await self.jailbreak_agent.invoke(
            request.message,
            state["conversation_context"]
        )
        
        state["agent_responses"].append(AgentResponse(**security_response))
        
        # Safely get safety_level with fallback
        security_data = security_response.get("data", {})
        safety_level = security_data.get("safety_level", "SAFE")
        state["security_status"] = safety_level
    
    async def _initial_assistance(self, state: Dict[str, Any]):
        """Initial assistance and information gathering"""
        request = state["patient_request"]
        
        assistance_response = await self.assisting_agent.invoke(
            request.message,
            state["conversation_context"]
        )
        
        state["agent_responses"].append(AgentResponse(**assistance_response))
        state["conversation_context"].update(assistance_response["data"])
    
    async def _triage_assessment(self, state: Dict[str, Any]):
        """Medical triage assessment"""
        request = state["patient_request"]
        
        triage_response = await self.triage_agent.invoke(
            request.message,
            state["conversation_context"]
        )
        
        state["agent_responses"].append(AgentResponse(**triage_response))
        
        # Safely get triage data with fallbacks
        triage_data = triage_response.get("data", {})
        state["symptom_analysis"] = triage_data.get("symptom_analysis", {})
        state["requires_emergency"] = triage_data.get("emergency_indicators", False)
    
    async def _comorbidity_analysis(self, state: Dict[str, Any]):
        """Comorbidity and risk factor analysis"""
        request = state["patient_request"]
        
        # Combine context with symptom analysis
        enhanced_context = {**state["conversation_context"], **state["symptom_analysis"]}
        
        comorbidity_response = await self.comorbidity_agent.invoke(
            request.message,
            enhanced_context
        )
        
        state["agent_responses"].append(AgentResponse(**comorbidity_response))
        
        # Safely get comorbidity data with fallback
        comorbidity_data = comorbidity_response.get("data", {})
        state["comorbidity_risk"] = comorbidity_data.get("comorbidity_risk", {})
    
    async def _appointment_booking(self, state: Dict[str, Any]):
        """Appointment booking and scheduling"""
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
        
        # Safely get appointment data with fallback
        appointment_data = booking_response.get("data", {})
        state["appointment_data"] = appointment_data
    
    async def _emergency_route(self, state: Dict[str, Any]):
        """Emergency routing"""
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
    
    def _finalize_response(self, state: Dict[str, Any]):
        """Finalize the response and generate summary"""
        
        # Generate next steps if not emergency
        if not state["requires_emergency"]:
            state["next_steps"] = self._generate_next_steps(state)
        
        # Generate final summary message
        state["final_message"] = self._generate_final_message(state)
    
    def _should_route_to_emergency(self, state: Dict[str, Any]) -> bool:
        """Check if should route to emergency immediately"""
        context = state["conversation_context"]
        urgency_indicators = context.get("urgency_indicators", [])
        crisis_type = context.get("crisis_type", [])
        return len(urgency_indicators) > 0 or len(crisis_type) > 0
    
    def _has_symptoms(self, state: Dict[str, Any]) -> bool:
        """Check if patient has reported symptoms"""
        context = state["conversation_context"]
        
        # Check if this is a medical request
        if not context.get("is_medical", True):
            return False
            
        extracted_info = context.get("extracted_info", {})
        symptoms = extracted_info.get("symptoms", [])
        return len(symptoms) > 0
    
    def _is_booking_request_with_context(self, state: Dict[str, Any]) -> bool:
        """Check if this is a booking request when we already have context"""
        context = state["conversation_context"]
        
        # Check if we have previous slots available
        has_previous_slots = bool(context.get("available_slots"))
        
        # Check if the assisting agent detected booking intent
        assistant_data = state["conversation_context"]
        booking_intent = assistant_data.get("booking_intent", False)
        
        # Check the action taken by assisting agent
        for response in state.get("agent_responses", []):
            if response.agent_name == "Assisting Agent" and response.action_taken == "initiate_booking":
                return True
        
        return has_previous_slots and booking_intent
    
    def _is_non_medical_request(self, state: Dict[str, Any]) -> bool:
        """Check if this is a non-medical request that should be redirected"""
        context = state["conversation_context"]
        return not context.get("is_medical", True)
    
    def _needs_comorbidity_analysis(self, state: Dict[str, Any]) -> bool:
        """Check if comorbidity analysis is needed"""
        symptom_analysis = state.get("symptom_analysis", {})
        severity = symptom_analysis.get("severity")
        return severity in ["HIGH", "MEDIUM"] or len(symptom_analysis.get("symptoms", [])) >= 2
    
    def _generate_next_steps(self, state: Dict[str, Any]) -> List[str]:
        """Generate next steps based on assessment"""
        steps = []
        
        symptom_analysis = state["symptom_analysis"]
        appointment_data = state["appointment_data"]
        
        severity = symptom_analysis.get("severity", "LOW")
        
        if severity == "HIGH":
            steps.append("Schedule appointment within 24-48 hours")
            steps.append("Monitor symptoms closely")
        elif severity == "MEDIUM":
            steps.append("Schedule appointment within 1 week")
            steps.append("Track symptom progression")
        else:
            steps.append("Schedule routine appointment")
            steps.append("Continue monitoring symptoms")
        
        if appointment_data.get("available_slots"):
            steps.append("Choose preferred appointment slot")
            steps.append("Confirm appointment booking")
        
        if state["comorbidity_risk"]:
            recommendations = state["comorbidity_risk"].get("recommendations", [])
            steps.extend(recommendations[:2])  # Add first 2 recommendations
        
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
    
    def _create_response(self, state: Dict[str, Any]) -> AppointmentResponse:
        """Create the final appointment response"""
        return AppointmentResponse(
            message=state["final_message"],
            agent_responses=state["agent_responses"],
            symptom_analysis=state["symptom_analysis"] if state["symptom_analysis"] else None,
            comorbidity_risk=state["comorbidity_risk"] if state["comorbidity_risk"] else None,
            available_slots=state["appointment_data"].get("available_slots", []),
            booking=state["appointment_data"].get("booking"),
            next_steps=state["next_steps"],
            requires_emergency=state["requires_emergency"],
            session_id=state["patient_request"].session_id
        )
    
    def _create_blocked_response(self, state: Dict[str, Any]) -> AppointmentResponse:
        """Create response for blocked requests"""
        return AppointmentResponse(
            message="Your request has been blocked for security reasons. Please contact support if you believe this is an error.",
            agent_responses=state["agent_responses"],
            available_slots=[],
            next_steps=["Contact support for assistance"],
            requires_emergency=False,
            session_id=state["patient_request"].session_id
        )
    
    def _create_error_response(self, error_message: str) -> AppointmentResponse:
        """Create response for errors"""
        return AppointmentResponse(
            message=f"An error occurred while processing your request: {error_message}",
            agent_responses=[],
            available_slots=[],
            next_steps=["Please try again or contact support"],
            requires_emergency=False
        )