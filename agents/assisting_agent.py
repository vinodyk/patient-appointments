"""
Assisting Agent - First point of contact for patients
Author: Vinod Yadav
Date: 7-25-2025
"""

from typing import Dict, Any, Optional
import json
import re
from .base_agent import BaseAgent

class AssistingAgent(BaseAgent):
    """Agent responsible for initial patient interaction and information gathering"""
    
    def __init__(self):
        system_prompt = """You are a helpful medical assistant for a patient appointment booking system.
Your role is to:
1. Greet patients warmly and professionally
2. Gather initial information about their symptoms or concerns
3. Ask clarifying questions to better understand their needs
4. Provide general guidance and reassurance
5. Determine if the patient needs emergency care, specialist consultation, or general appointment

Guidelines:
- Be empathetic and professional
- Ask one question at a time to avoid overwhelming the patient
- Don't provide medical diagnoses
- If symptoms seem urgent, recommend immediate medical attention
- Collect: chief complaint, symptom duration, severity (1-10), relevant medical history

Respond in a conversational, caring tone while gathering necessary information."""
        
        super().__init__("Assisting Agent", system_prompt)
    
    async def process_response(self, llm_response: str, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process the assistant's response and extract relevant information"""
        
        # Check if this is a medical-related request
        is_medical_request = self._is_medical_request(user_message)
        
        if not is_medical_request:
            # Handle non-medical requests appropriately
            response_type = self._classify_non_medical_request(user_message)
            polite_response = self._generate_polite_redirect(user_message, response_type)
            
            return {
                "message": polite_response,
                "confidence": 0.9,
                "action_taken": "non_medical_redirect",
                "data": {
                    "is_medical": False,
                    "request_type": response_type,
                    "conversation_stage": "redirect_to_medical"
                }
            }
        
        # Handle suicidal ideation or mental health crisis
        crisis_indicators = self._detect_crisis_indicators(user_message)
        if crisis_indicators:
            crisis_response = self._generate_crisis_response(crisis_indicators)
            return {
                "message": crisis_response,
                "confidence": 1.0,
                "action_taken": "crisis_intervention",
                "data": {
                    "is_medical": True,
                    "crisis_type": crisis_indicators,
                    "conversation_stage": "crisis_support"
                }
            }
        
        # Continue with normal medical processing
        extracted_info = self._extract_patient_info(user_message, llm_response)
        confidence = self._calculate_confidence(extracted_info)
        action_taken = self._determine_action(extracted_info, llm_response)
        
        return {
            "message": llm_response,
            "confidence": confidence,
            "action_taken": action_taken,
            "data": {
                "is_medical": True,
                "extracted_info": extracted_info,
                "conversation_stage": self._get_conversation_stage(extracted_info),
                "urgency_indicators": self._detect_urgency_indicators(user_message)
            }
        }
    
    def _is_medical_request(self, message: str) -> bool:
        """Check if the request is medical-related"""
        message_lower = message.lower()
        
        # Medical keywords
        medical_keywords = [
            # Symptoms
            "pain", "ache", "hurt", "hurts", "fever", "sick", "ill", "symptom", "feel", "headache",
            "nausea", "dizzy", "tired", "fatigue", "cough", "cold", "flu", "infection",
            "bleeding", "swelling", "rash", "itch", "sore", "tender", "numb", "weak",
            
            # Injuries and conditions
            "broken", "broke", "injured", "injury", "sprained", "twisted", "fractured",
            "cut", "burn", "bruised", "swollen", "dislocated", "torn", "pulled",
            
            # Medical appointments
            "doctor", "appointment", "checkup", "consultation", "medical", "health",
            "physician", "specialist", "clinic", "hospital", "medicine", "medication",
            "prescription", "treatment", "therapy", "surgery", "procedure", "urgent care",
            
            # Body parts (when context suggests medical issue)
            "head", "chest", "stomach", "back", "neck", "arm", "leg", "knee", "ankle",
            "shoulder", "wrist", "finger", "toe", "eye", "ear", "throat", "heart", 
            "lung", "kidney", "liver", "brain", "bone", "muscle", "joint",
            
            # Medical conditions
            "diabetes", "hypertension", "asthma", "allergy", "depression", "anxiety",
            "cancer", "arthritis", "migraine", "chronic", "acute", "emergency"
        ]
        
        # Check for medical keywords
        for keyword in medical_keywords:
            if keyword in message_lower:
                return True
        
        # Check for injury patterns with regex
        import re
        injury_patterns = [
            r"my .* (hurts|is broken|is injured|broke|hurt)",
            r"(broke|hurt|injured|sprained|twisted) my",
            r"pain in (my )?",
            r"can't (move|feel|use) my",
            r"something wrong with my",
            r"problem with my"
        ]
        
        for pattern in injury_patterns:
            if re.search(pattern, message_lower):
                return True
        
        # Check for appointment-related phrases
        appointment_phrases = [
            "book appointment", "schedule appointment", "see a doctor", "medical help",
            "health issue", "not feeling well", "need to see", "medical concern",
            "need medical attention", "visit doctor", "consult doctor"
        ]
        
        for phrase in appointment_phrases:
            if phrase in message_lower:
                return True
        
        return False
    
    def _classify_non_medical_request(self, message: str) -> str:
        """Classify the type of non-medical request"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["movie", "ticket", "cinema", "theater", "film"]):
            return "entertainment"
        elif any(word in message_lower for word in ["restaurant", "food", "dinner", "lunch", "table"]):
            return "dining"
        elif any(word in message_lower for word in ["travel", "flight", "hotel", "vacation", "trip"]):
            return "travel"
        elif any(word in message_lower for word in ["shopping", "buy", "purchase", "store"]):
            return "shopping"
        elif any(word in message_lower for word in ["weather", "temperature", "forecast"]):
            return "weather"
        elif any(word in message_lower for word in ["time", "date", "calendar", "schedule"]):
            return "general_info"
        else:
            return "other"
    
    def _generate_polite_redirect(self, message: str, request_type: str) -> str:
        """Generate a polite response redirecting to medical services"""
        
        type_responses = {
            "entertainment": "I understand you're looking to book movie tickets, but I'm specifically designed to help with medical appointments and healthcare needs.",
            "dining": "I see you're interested in restaurant reservations, but I specialize in medical appointment booking and healthcare assistance.",
            "travel": "I notice you're asking about travel arrangements, but my expertise is in medical appointments and healthcare services.",
            "shopping": "I understand you're looking to make a purchase, but I'm designed specifically for medical appointment booking.",
            "weather": "I see you're asking about weather, but I focus on medical appointments and healthcare needs.",
            "general_info": "I understand you're looking for general information, but I specialize in medical appointments and healthcare.",
            "other": "I appreciate your question, but I'm specifically designed to help with medical appointments and healthcare needs."
        }
        
        base_response = type_responses.get(request_type, type_responses["other"])
        
        return f"""😊 {base_response}

I'm here to help you with:
• Scheduling medical appointments
• Discussing health symptoms and concerns
• Finding appropriate medical specialists
• Providing guidance on medical urgency
• Booking consultations with doctors

If you have any health concerns or need to see a healthcare provider, I'd be happy to assist you! Please let me know about any symptoms you're experiencing or what type of medical appointment you need."""
    
    def _detect_crisis_indicators(self, message: str) -> list:
        """Detect mental health crisis indicators"""
        message_lower = message.lower()
        crisis_indicators = []
        
        # Suicidal ideation
        suicide_keywords = [
            "kill myself", "end my life", "want to die", "suicide", "suicidal",
            "don't want to live", "life isn't worth", "better off dead",
            "thinking of ending", "hurt myself", "harm myself"
        ]
        
        for keyword in suicide_keywords:
            if keyword in message_lower:
                crisis_indicators.append("suicidal_ideation")
                break
        
        # Self-harm
        self_harm_keywords = [
            "cut myself", "hurt myself", "self harm", "self-harm", "cutting",
            "burning myself", "hitting myself"
        ]
        
        for keyword in self_harm_keywords:
            if keyword in message_lower:
                crisis_indicators.append("self_harm")
                break
        
        # Severe depression
        severe_depression_keywords = [
            "can't go on", "hopeless", "worthless", "no point", "give up",
            "can't take it", "everything is dark", "no way out"
        ]
        
        for keyword in severe_depression_keywords:
            if keyword in message_lower:
                crisis_indicators.append("severe_depression")
                break
        
        return crisis_indicators
    
    def _generate_crisis_response(self, crisis_indicators: list) -> str:
        """Generate empathetic crisis intervention response"""
        
        if "suicidal_ideation" in crisis_indicators:
            return """🤗 I'm really concerned about you and want you to know that you're not alone. Your life has value, and there are people who want to help.

**Immediate Support:**
• 🆘 **Crisis Text Line**: Text HOME to 741741
• 📞 **National Suicide Prevention Lifeline**: 988 or 1-800-273-8255
• 🚨 **Emergency Services**: Call 911 if you're in immediate danger

**Please consider:**
• Reaching out to a trusted friend, family member, or counselor
• Going to your nearest emergency room
• Calling a crisis helpline to talk with someone right now

I can also help you find mental health professionals in your area who specialize in crisis intervention and ongoing support. Would you like me to help you schedule an urgent appointment with a mental health provider?

You matter, and there is help available. Please don't hesitate to reach out for immediate support."""

        elif "self_harm" in crisis_indicators:
            return """💙 I'm concerned about what you're going through. Self-harm can be a way of coping with difficult emotions, but there are healthier alternatives and people who can help.

**Immediate Resources:**
• 📞 **Crisis Text Line**: Text HOME to 741741
• 🆘 **Self-Injury Outreach & Support**: sioutreach.org
• 📞 **National Suicide Prevention Lifeline**: 988

**Healthy Coping Alternatives:**
• Hold ice cubes in your hands
• Draw on your skin with a red marker
• Exercise intensely for a few minutes
• Talk to someone you trust

I can help you find a mental health professional who specializes in self-harm and can provide proper support. Would you like me to schedule an urgent appointment with a counselor or therapist?

Your feelings are valid, and you deserve support and care."""

        else:  # severe_depression
            return """🤗 I hear that you're going through a really difficult time, and I want you to know that what you're feeling is valid. Depression can make everything seem overwhelming, but you don't have to face this alone.

**Support Resources:**
• 📞 **National Suicide Prevention Lifeline**: 988
• 💬 **Crisis Text Line**: Text HOME to 741741
• 🧠 **NAMI HelpLine**: 1-800-950-6264

**Remember:**
• These feelings can change with proper support and treatment
• You are not a burden to others
• Help is available and recovery is possible

I can help you schedule an appointment with a mental health professional, such as a psychiatrist or therapist, who can provide proper assessment and treatment for depression. Would you like me to help you find mental health services in your area?

Taking the step to reach out shows incredible strength. Please consider speaking with a professional who can provide the support you deserve."""
    
    def _extract_patient_info(self, user_message: str, llm_response: str) -> Dict[str, Any]:
        """Extract patient information from the conversation"""
        info = {
            "symptoms": [],
            "duration": None,
            "severity": None,
            "medical_history": [],
            "concerns": []
        }
        
        # Extract symptoms using common medical terms
        symptom_keywords = [
            "pain", "ache", "fever", "headache", "nausea", "vomiting", "diarrhea",
            "constipation", "cough", "shortness of breath", "chest pain", "dizziness",
            "fatigue", "weakness", "rash", "swelling", "bleeding", "infection"
        ]
        
        user_lower = user_message.lower()
        for symptom in symptom_keywords:
            if symptom in user_lower:
                info["symptoms"].append(symptom)
        
        # Extract duration patterns
        duration_patterns = [
            r"(\d+)\s*(day|days|week|weeks|month|months)",
            r"since\s+(\w+)",
            r"for\s+(\d+)\s*(hour|hours|day|days)"
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, user_lower)
            if match:
                info["duration"] = match.group(0)
                break
        
        # Extract severity (1-10 scale or descriptive)
        severity_patterns = [
            r"(\d+)/10",
            r"(\d+)\s+out\s+of\s+10",
            r"(severe|mild|moderate|extreme|unbearable)"
        ]
        
        for pattern in severity_patterns:
            match = re.search(pattern, user_lower)
            if match:
                info["severity"] = match.group(1)
                break
        
        return info
    
    def _calculate_confidence(self, extracted_info: Dict[str, Any]) -> float:
        """Calculate confidence based on information completeness"""
        score = 0.5  # Base confidence
        
        if extracted_info["symptoms"]:
            score += 0.2
        if extracted_info["duration"]:
            score += 0.15
        if extracted_info["severity"]:
            score += 0.15
        
        return min(score, 1.0)
    
    def _determine_action(self, extracted_info: Dict[str, Any], llm_response: str) -> str:
        """Determine what action to take next"""
        if self._detect_emergency_keywords(llm_response):
            return "escalate_to_emergency"
        elif extracted_info["symptoms"]:
            return "forward_to_triage"
        elif "appointment" in llm_response.lower():
            return "initiate_booking"
        else:
            return "continue_conversation"
    
    def _get_conversation_stage(self, extracted_info: Dict[str, Any]) -> str:
        """Determine the current stage of conversation"""
        if not extracted_info["symptoms"]:
            return "initial_contact"
        elif not extracted_info["duration"] and not extracted_info["severity"]:
            return "gathering_details"
        else:
            return "information_complete"
    
    def _detect_urgency_indicators(self, message: str) -> list:
        """Detect urgency indicators in patient message"""
        urgent_keywords = [
            "emergency", "urgent", "severe", "can't breathe", "chest pain",
            "unconscious", "bleeding heavily", "suicide", "overdose",
            "heart attack", "stroke", "allergic reaction"
        ]
        
        detected = []
        message_lower = message.lower()
        
        for keyword in urgent_keywords:
            if keyword in message_lower:
                detected.append(keyword)
        
        return detected
    
    def _detect_emergency_keywords(self, response: str) -> bool:
        """Detect if the response indicates emergency situation"""
        emergency_phrases = [
            "emergency room", "call 911", "immediate medical attention",
            "urgent care", "seek immediate help"
        ]
        
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in emergency_phrases)