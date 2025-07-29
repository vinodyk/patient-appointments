"""
Triage Agent - Medical Priority Assessment
Author: Vinod Yadav
Date: 7-25-2025
"""

from typing import Dict, Any, Optional, List
import re
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from models.patient_models import Priority, SymptomAnalysis

class TriageAgent(BaseAgent):
    """Agent responsible for medical triage and priority assessment"""
    
    def __init__(self):
        system_prompt = """You are a medical triage specialist AI assistant.
Your role is to assess patient symptoms and determine appropriate priority levels for medical care.

Priority Levels:
- EMERGENCY: Life-threatening conditions requiring immediate attention
- HIGH: Urgent conditions needing same-day care
- MEDIUM: Conditions requiring care within 1-3 days
- LOW: Routine conditions that can wait 1-2 weeks

Assessment Criteria:
1. Symptom severity and progression
2. Vital signs if mentioned
3. Duration of symptoms
4. Patient's age and risk factors
5. Associated symptoms

RED FLAGS (EMERGENCY):
- Chest pain with breathing difficulty
- Severe head injury or altered consciousness
- Signs of stroke (FAST)
- Severe allergic reactions
- Difficulty breathing
- Heavy bleeding
- Severe abdominal pain
- Signs of heart attack
- Suicidal ideation

Provide triage assessment with reasoning, recommended urgency, and suggested medical specialty."""
        
        super().__init__("Triage Agent", system_prompt)
        
        # Define symptom severity mappings
        self.emergency_symptoms = [
            "chest pain", "difficulty breathing", "can't breathe", "heart attack",
            "stroke", "unconscious", "severe bleeding", "allergic reaction",
            "suicide", "overdose", "severe head injury"
        ]
        
        self.high_priority_symptoms = [
            "severe pain", "high fever", "persistent vomiting", "severe headache",
            "vision loss", "difficulty swallowing", "severe dizziness"
        ]
        
        self.medium_priority_symptoms = [
            "moderate pain", "fever", "headache", "nausea", "diarrhea",
            "rash", "joint pain", "muscle ache"
        ]
        
        self.specialty_mapping = {
            "heart": "cardiology",
            "chest": "cardiology",
            "breathing": "pulmonology",
            "lung": "pulmonology",
            "skin": "dermatology",
            "rash": "dermatology",
            "bone": "orthopedics",
            "joint": "orthopedics",
            "headache": "neurology",
            "vision": "ophthalmology",
            "eye": "ophthalmology",
            "ear": "otolaryngology",
            "throat": "otolaryngology"
        }
    
    async def process_response(self, llm_response: str, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process triage assessment and return structured analysis"""
        
        # Extract symptoms from user message and context
        symptoms = self._extract_symptoms(user_message, context)
        
        # Assess severity and priority
        priority_assessment = self._assess_priority(symptoms, user_message)
        
        # Determine required specialty
        specialty = self._determine_specialty(symptoms, user_message)
        
        # Check for emergency indicators
        emergency_check = self._check_emergency_indicators(user_message, symptoms)
        
        # Calculate confidence in assessment
        confidence = self._calculate_triage_confidence(symptoms, priority_assessment)
        
        # Create symptom analysis object
        symptom_analysis = SymptomAnalysis(
            symptoms=symptoms,
            severity=priority_assessment,
            urgency=emergency_check,
            specialty_required=specialty
        )
        
        # Determine action based on priority
        action_taken = self._determine_triage_action(priority_assessment, emergency_check)
        
        return {
            "message": self._generate_triage_message(symptom_analysis, llm_response),
            "confidence": confidence,
            "action_taken": action_taken,
            "data": {
                "symptom_analysis": symptom_analysis.dict(),
                "emergency_indicators": emergency_check,
                "recommended_timeframe": self._get_timeframe_recommendation(priority_assessment),
                "care_instructions": self._generate_care_instructions(priority_assessment)
            }
        }
    
    def _extract_symptoms(self, message: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract symptoms from message and context"""
        symptoms = []
        message_lower = message.lower()
        
        # Common symptom keywords
        symptom_keywords = [
            "pain", "ache", "fever", "headache", "nausea", "vomiting", "diarrhea",
            "constipation", "cough", "shortness of breath", "chest pain", "dizziness",
            "fatigue", "weakness", "rash", "swelling", "bleeding", "infection",
            "sore throat", "runny nose", "congestion", "chills", "sweating"
        ]
        
        # Extract symptoms from message
        for symptom in symptom_keywords:
            if symptom in message_lower:
                symptoms.append(symptom)
        
        # Extract from context if available
        if context and "extracted_info" in context:
            context_symptoms = context["extracted_info"].get("symptoms", [])
            symptoms.extend(context_symptoms)
        
        # Remove duplicates
        return list(set(symptoms))
    
    def _assess_priority(self, symptoms: List[str], message: str) -> Priority:
        """Assess priority level based on symptoms and message content"""
        message_lower = message.lower()
        
        # Check for emergency symptoms
        for emergency_symptom in self.emergency_symptoms:
            if emergency_symptom in message_lower:
                return Priority.EMERGENCY
        
        # Check for high priority symptoms
        for high_symptom in self.high_priority_symptoms:
            if high_symptom in message_lower:
                return Priority.HIGH
        
        # Check for severity indicators
        severity_indicators = [
            "severe", "extreme", "unbearable", "worst", "excruciating",
            "can't", "unable", "impossible"
        ]
        
        if any(indicator in message_lower for indicator in severity_indicators):
            return Priority.HIGH
        
        # Check for medium priority symptoms
        for medium_symptom in self.medium_priority_symptoms:
            if medium_symptom in message_lower:
                return Priority.MEDIUM
        
        # Default to low priority
        return Priority.LOW
    
    def _determine_specialty(self, symptoms: List[str], message: str) -> Optional[str]:
        """Determine required medical specialty"""
        message_lower = message.lower()
        
        # Check specialty mapping
        for keyword, specialty in self.specialty_mapping.items():
            if keyword in message_lower:
                return specialty
        
        # Check symptoms for specialty hints
        if any(symptom in ["chest pain", "heart", "cardiac"] for symptom in symptoms):
            return "cardiology"
        
        if any(symptom in ["breathing", "lung", "respiratory"] for symptom in symptoms):
            return "pulmonology"
        
        if any(symptom in ["headache", "neurological", "seizure"] for symptom in symptoms):
            return "neurology"
        
        # Default to general practice
        return "general_practice"
    
    def _check_emergency_indicators(self, message: str, symptoms: List[str]) -> bool:
        """Check if symptoms indicate emergency situation"""
        message_lower = message.lower()
        
        # Direct emergency keywords
        emergency_keywords = [
            "emergency", "911", "ambulance", "life threatening",
            "can't breathe", "heart attack", "stroke", "unconscious",
            "severe bleeding", "overdose", "poisoning"
        ]
        
        if any(keyword in message_lower for keyword in emergency_keywords):
            return True
        
        # Emergency symptom combinations
        if "chest pain" in message_lower and any(word in message_lower for word in ["breathing", "shortness", "dizzy"]):
            return True
        
        return False
    
    def _calculate_triage_confidence(self, symptoms: List[str], priority: Priority) -> float:
        """Calculate confidence in triage assessment"""
        base_confidence = 0.7
        
        # Higher confidence with more symptoms
        if len(symptoms) >= 3:
            base_confidence += 0.1
        
        # Higher confidence for clear emergency cases
        if priority == Priority.EMERGENCY:
            base_confidence += 0.2
        
        # Higher confidence with specific symptoms
        if symptoms:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _determine_triage_action(self, priority: Priority, emergency: bool) -> str:
        """Determine action based on triage assessment"""
        if priority == Priority.EMERGENCY or emergency:
            return "escalate_to_emergency"
        elif priority == Priority.HIGH:
            return "schedule_urgent_appointment"
        elif priority == Priority.MEDIUM:
            return "schedule_routine_appointment"
        else:
            return "provide_self_care_guidance"
    
    def _get_timeframe_recommendation(self, priority: Priority) -> str:
        """Get recommended timeframe for care"""
        timeframe_map = {
            Priority.EMERGENCY: "Immediate - Call 911 or go to ER",
            Priority.HIGH: "Same day or within 24 hours",
            Priority.MEDIUM: "Within 1-3 days",
            Priority.LOW: "Within 1-2 weeks"
        }
        return timeframe_map.get(priority, "As needed")
    
    def _generate_care_instructions(self, priority: Priority) -> List[str]:
        """Generate care instructions based on priority"""
        if priority == Priority.EMERGENCY:
            return [
                "Seek immediate emergency medical attention",
                "Call 911 if symptoms are severe",
                "Do not drive yourself to the hospital",
                "Have someone stay with you if possible"
            ]
        elif priority == Priority.HIGH:
            return [
                "Contact your healthcare provider today",
                "Monitor symptoms closely",
                "Seek urgent care if symptoms worsen",
                "Keep a record of symptom changes"
            ]
        elif priority == Priority.MEDIUM:
            return [
                "Schedule an appointment with your doctor",
                "Monitor symptoms and note any changes",
                "Take over-the-counter medications as appropriate",
                "Rest and stay hydrated"
            ]
        else:
            return [
                "Monitor symptoms for a few days",
                "Schedule routine appointment if symptoms persist",
                "Practice self-care measures",
                "Contact doctor if symptoms worsen"
            ]
    
    def _generate_triage_message(self, symptom_analysis: SymptomAnalysis, llm_response: str) -> str:
        """Generate comprehensive triage message"""
        priority_text = {
            Priority.EMERGENCY: "🚨 EMERGENCY PRIORITY",
            Priority.HIGH: "⚠️ HIGH PRIORITY", 
            Priority.MEDIUM: "📋 MEDIUM PRIORITY",
            Priority.LOW: "📝 LOW PRIORITY"
        }
        
        message = f"{priority_text.get(symptom_analysis.severity, '📝 ASSESSED')}\n\n"
        message += f"Triage Assessment: {llm_response}\n\n"
        
        if symptom_analysis.symptoms:
            message += f"Identified Symptoms: {', '.join(symptom_analysis.symptoms)}\n"
        
        if symptom_analysis.specialty_required:
            message += f"Recommended Specialty: {symptom_analysis.specialty_required.title()}\n"
        
        if symptom_analysis.urgency:
            message += "\n⚠️ This appears to require urgent medical attention."
        
        return message