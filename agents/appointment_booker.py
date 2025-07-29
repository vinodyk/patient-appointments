"""
Appointment Booker Agent - Schedule Management
Author: Vinod Yadav
Date: 7-25-2025
"""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from models.patient_models import AppointmentSlot, AppointmentBooking, AppointmentType, Priority

class AppointmentBookerAgent(BaseAgent):
    """Agent responsible for appointment scheduling and management"""
    
    def __init__(self):
        system_prompt = """You are an appointment booking specialist AI assistant.
Your role is to:
1. Find available appointment slots based on patient needs
2. Match appointments with appropriate specialists
3. Consider urgency and priority levels
4. Provide appointment confirmation and details
5. Offer alternative slots if preferred times unavailable

Booking Priorities:
- Emergency: Immediate or same-day slots
- High: Within 24-48 hours
- Medium: Within 1 week
- Low: Within 2-4 weeks

Available Specialties:
- General Practice
- Cardiology
- Pulmonology
- Neurology
- Dermatology
- Orthopedics
- Ophthalmology
- Otolaryngology
- Emergency Medicine
- Urgent Care

Consider patient preferences, insurance coverage, and medical urgency when scheduling."""
        
        super().__init__("Appointment Booker", system_prompt)
        
        # Hardcoded available slots for demonstration
        self.available_doctors = {
            "general_practice": [
                {"name": "Dr. Sarah Johnson", "availability": "Mon-Fri 9AM-5PM"},
                {"name": "Dr. Michael Chen", "availability": "Tue-Sat 10AM-6PM"},
                {"name": "Dr. Emily Rodriguez", "availability": "Mon-Wed-Fri 8AM-4PM"}
            ],
            "cardiology": [
                {"name": "Dr. Robert Heart", "availability": "Mon-Thu 9AM-3PM"},
                {"name": "Dr. Lisa Cardiac", "availability": "Tue-Fri 11AM-5PM"}
            ],
            "pulmonology": [
                {"name": "Dr. David Lung", "availability": "Mon-Wed-Fri 10AM-4PM"}
            ],
            "neurology": [
                {"name": "Dr. Amanda Brain", "availability": "Tue-Thu 9AM-3PM"}
            ],
            "emergency": [
                {"name": "Dr. Emergency Smith", "availability": "24/7"},
                {"name": "Dr. Urgent Care", "availability": "24/7"}
            ]
        }
    
    async def process_response(self, llm_response: str, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process appointment booking request and return available slots"""
        
        # First check if this is actually a medical appointment request
        if not self._is_valid_medical_request(user_message, context):
            return {
                "message": "I can only help with medical appointments. Please specify your health concerns or the type of medical specialist you need to see.",
                "confidence": 0.9,
                "action_taken": "invalid_medical_request",
                "data": {
                    "available_slots": [],
                    "booking_requirements": {},
                    "error": "non_medical_request"
                }
            }
        
        # Extract booking requirements from context
        booking_requirements = self._extract_booking_requirements(user_message, context)
        
        # Find available slots
        available_slots = self._find_available_slots(booking_requirements)
        
        # Generate booking if explicitly requested with medical context
        booking = self._generate_booking_if_requested(user_message, available_slots, booking_requirements)
        
        # Calculate confidence in booking suggestions
        confidence = self._calculate_booking_confidence(available_slots, booking_requirements)
        
        # Determine action taken
        action_taken = self._determine_booking_action(booking, available_slots)
        
        return {
            "message": self._generate_booking_message(available_slots, booking, llm_response),
            "confidence": confidence,
            "action_taken": action_taken,
            "data": {
                "available_slots": [slot.dict() for slot in available_slots],
                "booking": booking.dict() if booking else None,
                "booking_requirements": booking_requirements,
                "next_available": self._get_next_available_slot(booking_requirements)
            }
        }
    
    def _is_valid_medical_request(self, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if this is a legitimate medical appointment request"""
        
        # Check context for medical validation
        if context:
            # If context explicitly says it's not medical, reject
            if context.get("is_medical") == False:
                return False
            
            # If we have symptom analysis or medical info, it's valid
            if context.get("symptom_analysis") or context.get("extracted_info", {}).get("symptoms"):
                return True
            
            # If the assisting agent marked it as medical, trust that
            if context.get("is_medical") == True:
                return True
        
        # Check message content for medical indicators
        message_lower = message.lower()
        
        medical_appointment_keywords = [
            # Medical professionals
            "doctor", "physician", "medical", "health", "appointment", "consultation",
            "checkup", "specialist", "clinic", "hospital", "nurse", "therapist",
            
            # Symptoms and conditions
            "pain", "ache", "hurt", "sick", "ill", "broken", "broke", "injured", "injury",
            "symptom", "fever", "headache", "nausea", "dizzy", "tired", "fatigue",
            "cough", "cold", "flu", "infection", "bleeding", "swelling", "rash",
            
            # Body parts (when mentioned with issues)
            "leg", "arm", "back", "neck", "head", "chest", "stomach", "knee", "ankle",
            "shoulder", "wrist", "finger", "toe", "eye", "ear", "throat",
            
            # Medical terms
            "treatment", "medicine", "prescription", "therapy", "surgery", "procedure",
            "diagnosis", "emergency", "urgent", "chronic", "acute"
        ]
        
        # Must have at least one medical keyword
        has_medical_keyword = any(keyword in message_lower for keyword in medical_appointment_keywords)
        
        # Additional check for injury/pain patterns
        injury_patterns = [
            "my .* hurts", "my .* is broken", "my .* is injured", "broke my",
            "hurt my", "pain in", "injured my", "twisted my", "sprained my"
        ]
        
        import re
        has_injury_pattern = any(re.search(pattern, message_lower) for pattern in injury_patterns)
        
        # Exclude obvious non-medical requests
        non_medical_keywords = [
            "movie", "ticket", "cinema", "theater", "film", "restaurant", "food", "dinner",
            "travel", "flight", "hotel", "shopping", "weather", "entertainment", "concert",
            "show", "game", "sports", "vacation"
        ]
        
        has_non_medical_keyword = any(keyword in message_lower for keyword in non_medical_keywords)
        
        # Valid if: (has medical keyword OR injury pattern) AND NOT non-medical
        return (has_medical_keyword or has_injury_pattern) and not has_non_medical_keyword
    
    def _extract_booking_requirements(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract booking requirements from message and context"""
        requirements = {
            "specialty": "general_practice",
            "priority": Priority.LOW,
            "preferred_date": None,
            "preferred_time": None,
            "appointment_type": AppointmentType.GENERAL,
            "patient_id": str(uuid.uuid4())[:8]
        }
        
        message_lower = message.lower()
        
        # Extract specialty from context
        if context:
            symptom_analysis = context.get("symptom_analysis", {})
            if symptom_analysis.get("specialty_required"):
                requirements["specialty"] = symptom_analysis["specialty_required"]
            
            # Extract priority from triage
            if symptom_analysis.get("severity"):
                requirements["priority"] = Priority(symptom_analysis["severity"])
            
            # Check for emergency indicators
            if symptom_analysis.get("urgency"):
                requirements["appointment_type"] = AppointmentType.EMERGENCY
                requirements["priority"] = Priority.EMERGENCY
        
        # Extract date preferences
        date_keywords = [
            "today", "tomorrow", "this week", "next week",
            "monday", "tuesday", "wednesday", "thursday", "friday"
        ]
        
        for keyword in date_keywords:
            if keyword in message_lower:
                requirements["preferred_date"] = keyword
                break
        
        # Extract time preferences
        time_keywords = [
            "morning", "afternoon", "evening", "9am", "10am", "11am",
            "1pm", "2pm", "3pm", "4pm", "5pm"
        ]
        
        for keyword in time_keywords:
            if keyword in message_lower:
                requirements["preferred_time"] = keyword
                break
        
        # Check for appointment type indicators
        if any(word in message_lower for word in ["emergency", "urgent", "asap"]):
            requirements["appointment_type"] = AppointmentType.EMERGENCY
            requirements["priority"] = Priority.EMERGENCY
        elif any(word in message_lower for word in ["followup", "follow up", "check up"]):
            requirements["appointment_type"] = AppointmentType.FOLLOWUP
        elif any(word in message_lower for word in ["specialist", "referral"]):
            requirements["appointment_type"] = AppointmentType.SPECIALIST
        
        return requirements
    
    def _find_available_slots(self, requirements: Dict[str, Any]) -> List[AppointmentSlot]:
        """Find available appointment slots based on requirements"""
        slots = []
        specialty = requirements.get("specialty", "general_practice")
        priority = requirements.get("priority", Priority.LOW)
        
        # Get doctors for specialty
        doctors = self.available_doctors.get(specialty, self.available_doctors["general_practice"])
        
        # Generate slots based on priority
        base_date = datetime.now()
        
        if priority == Priority.EMERGENCY:
            # Emergency slots - today and tomorrow
            for i in range(2):
                date = base_date + timedelta(days=i)
                for doctor in doctors:
                    if "24/7" in doctor["availability"] or i == 0:
                        slots.extend(self._generate_slots_for_day(date, doctor, specialty, emergency=True))
        
        elif priority == Priority.HIGH:
            # High priority - next 3 days
            for i in range(3):
                date = base_date + timedelta(days=i)
                for doctor in doctors:
                    slots.extend(self._generate_slots_for_day(date, doctor, specialty))
        
        elif priority == Priority.MEDIUM:
            # Medium priority - next 7 days
            for i in range(7):
                date = base_date + timedelta(days=i)
                for doctor in doctors:
                    if date.weekday() < 5:  # Weekdays only for medium priority
                        slots.extend(self._generate_slots_for_day(date, doctor, specialty))
        
        else:
            # Low priority - next 14 days
            for i in range(14):
                date = base_date + timedelta(days=i)
                for doctor in doctors:
                    if date.weekday() < 5:  # Weekdays only
                        slots.extend(self._generate_slots_for_day(date, doctor, specialty))
        
        # Filter based on preferences
        if requirements.get("preferred_date"):
            slots = self._filter_by_date_preference(slots, requirements["preferred_date"])
        
        if requirements.get("preferred_time"):
            slots = self._filter_by_time_preference(slots, requirements["preferred_time"])
        
        # Sort by date and time
        slots.sort(key=lambda x: (x.date, x.time))
        
        # Return top 10 slots
        return slots[:10]
    
    def _generate_slots_for_day(self, date: datetime, doctor: Dict[str, str], specialty: str, emergency: bool = False) -> List[AppointmentSlot]:
        """Generate appointment slots for a specific day and doctor"""
        slots = []
        
        if emergency:
            # Emergency slots available every 30 minutes
            times = ["8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM", "10:00 AM", 
                    "10:30 AM", "11:00 AM", "11:30 AM", "2:00 PM", "2:30 PM"]
        else:
            # Regular slots every hour
            times = ["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"]
        
        for time in times:
            slot = AppointmentSlot(
                date=date.strftime("%Y-%m-%d"),
                time=time,
                doctor=doctor["name"],
                specialty=specialty.replace("_", " ").title(),
                available=True
            )
            slots.append(slot)
        
        return slots
    
    def _filter_by_date_preference(self, slots: List[AppointmentSlot], preference: str) -> List[AppointmentSlot]:
        """Filter slots by date preference"""
        if preference == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            return [slot for slot in slots if slot.date == today]
        elif preference == "tomorrow":
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            return [slot for slot in slots if slot.date == tomorrow]
        elif preference == "this week":
            week_end = datetime.now() + timedelta(days=7)
            return [slot for slot in slots if slot.date <= week_end.strftime("%Y-%m-%d")]
        
        return slots
    
    def _filter_by_time_preference(self, slots: List[AppointmentSlot], preference: str) -> List[AppointmentSlot]:
        """Filter slots by time preference"""
        if preference == "morning":
            return [slot for slot in slots if "AM" in slot.time]
        elif preference == "afternoon":
            return [slot for slot in slots if "PM" in slot.time and int(slot.time.split(":")[0]) < 5]
        elif preference == "evening":
            return [slot for slot in slots if "PM" in slot.time and int(slot.time.split(":")[0]) >= 5]
        
        return slots
    
    def _generate_booking_if_requested(self, message: str, available_slots: List[AppointmentSlot], requirements: Dict[str, Any]) -> Optional[AppointmentBooking]:
        """Generate booking if explicitly requested"""
        booking_keywords = ["book", "schedule", "confirm", "reserve", "appointment"]
        
        if any(keyword in message.lower() for keyword in booking_keywords) and available_slots:
            # Book the first available slot
            slot = available_slots[0]
            
            booking = AppointmentBooking(
                appointment_id=f"APT-{uuid.uuid4().hex[:8].upper()}",
                patient_id=requirements["patient_id"],
                date=slot.date,
                time=slot.time,
                doctor=slot.doctor,
                specialty=slot.specialty,
                appointment_type=requirements.get("appointment_type", AppointmentType.GENERAL),
                confirmed=True
            )
            
            return booking
        
        return None
    
    def _calculate_booking_confidence(self, available_slots: List[AppointmentSlot], requirements: Dict[str, Any]) -> float:
        """Calculate confidence in booking suggestions"""
        base_confidence = 0.8
        
        # Higher confidence with more available slots
        if len(available_slots) >= 5:
            base_confidence += 0.1
        
        # Higher confidence for emergency bookings
        if requirements.get("priority") == Priority.EMERGENCY:
            base_confidence += 0.1
        
        # Lower confidence if no specialty match
        if requirements.get("specialty") not in self.available_doctors:
            base_confidence -= 0.2
        
        return max(min(base_confidence, 1.0), 0.5)
    
    def _determine_booking_action(self, booking: Optional[AppointmentBooking], available_slots: List[AppointmentSlot]) -> str:
        """Determine action taken for booking"""
        if booking:
            return "appointment_booked"
        elif available_slots:
            return "slots_provided"
        else:
            return "no_slots_available"
    
    def _get_next_available_slot(self, requirements: Dict[str, Any]) -> Optional[str]:
        """Get the next available slot description"""
        slots = self._find_available_slots(requirements)
        if slots:
            slot = slots[0]
            return f"{slot.date} at {slot.time} with {slot.doctor}"
        return None
    
    def _generate_booking_message(self, available_slots: List[AppointmentSlot], booking: Optional[AppointmentBooking], llm_response: str) -> str:
        """Generate comprehensive booking message"""
        message = f"📅 APPOINTMENT SCHEDULING\n\n{llm_response}\n\n"
        
        if booking:
            message += f"✅ APPOINTMENT CONFIRMED\n"
            message += f"Appointment ID: {booking.appointment_id}\n"
            message += f"Date: {booking.date}\n"
            message += f"Time: {booking.time}\n"
            message += f"Doctor: {booking.doctor}\n"
            message += f"Specialty: {booking.specialty}\n"
            message += f"Type: {booking.appointment_type.value.title()}\n\n"
            message += "Please arrive 15 minutes early for check-in.\n"
        
        elif available_slots:
            message += f"📋 AVAILABLE APPOINTMENTS ({len(available_slots)} found):\n\n"
            for i, slot in enumerate(available_slots[:5], 1):
                message += f"{i}. {slot.date} at {slot.time}\n"
                message += f"   Doctor: {slot.doctor}\n"
                message += f"   Specialty: {slot.specialty}\n\n"
            
            if len(available_slots) > 5:
                message += f"...and {len(available_slots) - 5} more slots available.\n"
            
            message += "Please let me know which slot you'd prefer to book.\n"
        
        else:
            message += "❌ No available appointments found for your requirements.\n"
            message += "Please contact our office directly at (555) 123-4567 for assistance.\n"
        
        return message