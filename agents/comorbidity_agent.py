"""
Comorbidity Agent - Risk Factor and Comorbidity Analysis
Author: Vinod Yadav
Date: 7-25-2025
"""

from typing import Dict, Any, Optional, List
import re
from .base_agent import BaseAgent
from models.patient_models import Priority, ComorbidityRisk

class ComorbidityAgent(BaseAgent):
    """Agent responsible for analyzing comorbidities and risk factors"""
    
    def __init__(self):
        system_prompt = """You are a specialized medical AI assistant focused on comorbidity and risk factor analysis.
Your role is to:
1. Identify potential risk factors from patient information
2. Assess how existing conditions might interact with current symptoms
3. Evaluate increased risk levels due to comorbidities
4. Provide recommendations for additional precautions or specialist referrals

Key Risk Factors to Consider:
- Age (65+ high risk, 75+ very high risk)
- Cardiovascular conditions (hypertension, heart disease, diabetes)
- Respiratory conditions (asthma, COPD, lung disease)
- Immunocompromised status
- Pregnancy
- Obesity
- Chronic kidney disease
- Cancer history
- Autoimmune disorders

Assessment Guidelines:
- Consider drug interactions and contraindications
- Evaluate symptoms in context of existing conditions
- Identify when comorbidities require specialist care
- Recommend monitoring protocols for high-risk patients
- Flag conditions that may complicate treatment

Provide risk assessment with specific recommendations for monitoring and care coordination."""
        
        super().__init__("Comorbidity Agent", system_prompt)
        
        # Define risk factor categories
        self.high_risk_conditions = [
            "diabetes", "heart disease", "hypertension", "cancer", "kidney disease",
            "liver disease", "lung disease", "copd", "asthma", "stroke history"
        ]
        
        self.immunocompromising_conditions = [
            "hiv", "aids", "chemotherapy", "immunosuppressant", "organ transplant",
            "autoimmune", "lupus", "rheumatoid arthritis", "crohns", "ulcerative colitis"
        ]
        
        self.cardiovascular_risks = [
            "high blood pressure", "hypertension", "heart attack", "cardiac",
            "coronary artery disease", "atrial fibrillation", "heart failure"
        ]
        
        self.respiratory_risks = [
            "asthma", "copd", "emphysema", "lung disease", "pulmonary",
            "breathing problems", "oxygen", "inhaler"
        ]
        
        # Drug interaction categories
        self.high_interaction_drugs = [
            "warfarin", "blood thinner", "insulin", "metformin", "lithium",
            "digoxin", "phenytoin", "theophylline"
        ]
    
    async def process_response(self, llm_response: str, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process comorbidity analysis and return risk assessment"""
        
        # Extract risk factors from message and context
        risk_factors = self._extract_risk_factors(user_message, context)
        
        # Assess overall risk level
        risk_level = self._assess_risk_level(risk_factors, user_message)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, risk_level, context)
        
        # Check for drug interactions
        interaction_risks = self._check_drug_interactions(user_message, risk_factors)
        
        # Calculate confidence in assessment
        confidence = self._calculate_comorbidity_confidence(risk_factors, risk_level)
        
        # Create comorbidity risk object
        comorbidity_risk = ComorbidityRisk(
            risk_factors=risk_factors,
            risk_level=risk_level,
            recommendations=recommendations
        )
        
        # Determine action based on risk assessment
        action_taken = self._determine_comorbidity_action(risk_level, risk_factors)
        
        return {
            "message": self._generate_comorbidity_message(comorbidity_risk, llm_response),
            "confidence": confidence,
            "action_taken": action_taken,
            "data": {
                "comorbidity_risk": comorbidity_risk.dict(),
                "interaction_risks": interaction_risks,
                "monitoring_requirements": self._get_monitoring_requirements(risk_factors),
                "specialist_referrals": self._get_specialist_referrals(risk_factors)
            }
        }
    
    def _extract_risk_factors(self, message: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract risk factors from message and context"""
        risk_factors = []
        message_lower = message.lower()
        
        # Check for age indicators
        age_patterns = [
            r"(\d+)\s*years?\s*old",
            r"age\s*(\d+)",
            r"(\d+)\s*yr"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, message_lower)
            if match:
                age = int(match.group(1))
                if age >= 65:
                    risk_factors.append(f"elderly (age {age})")
                break
        
        # Check for high-risk conditions
        for condition in self.high_risk_conditions:
            if condition in message_lower:
                risk_factors.append(condition)
        
        # Check for immunocompromising conditions
        for condition in self.immunocompromising_conditions:
            if condition in message_lower:
                risk_factors.append(f"immunocompromised ({condition})")
        
        # Check for cardiovascular risks
        for condition in self.cardiovascular_risks:
            if condition in message_lower:
                risk_factors.append(f"cardiovascular ({condition})")
        
        # Check for respiratory risks
        for condition in self.respiratory_risks:
            if condition in message_lower:
                risk_factors.append(f"respiratory ({condition})")
        
        # Check for pregnancy
        if any(word in message_lower for word in ["pregnant", "pregnancy", "expecting"]):
            risk_factors.append("pregnancy")
        
        # Check for obesity indicators
        if any(word in message_lower for word in ["obese", "obesity", "overweight", "bmi"]):
            risk_factors.append("obesity")
        
        # Extract from context if available
        if context and "extracted_info" in context:
            medical_history = context["extracted_info"].get("medical_history", [])
            risk_factors.extend(medical_history)
        
        return list(set(risk_factors))  # Remove duplicates
    
    def _assess_risk_level(self, risk_factors: List[str], message: str) -> Priority:
        """Assess overall risk level based on identified factors"""
        risk_score = 0
        
        # Score risk factors
        for factor in risk_factors:
            if "elderly" in factor:
                risk_score += 2
            elif "immunocompromised" in factor:
                risk_score += 3
            elif "cardiovascular" in factor:
                risk_score += 2
            elif "respiratory" in factor:
                risk_score += 2
            elif factor in ["diabetes", "cancer", "kidney disease"]:
                risk_score += 2
            elif factor == "pregnancy":
                risk_score += 1
            else:
                risk_score += 1
        
        # Multiple comorbidities increase risk exponentially
        if len(risk_factors) >= 3:
            risk_score += 2
        
        # Assess based on score
        if risk_score >= 6:
            return Priority.HIGH
        elif risk_score >= 3:
            return Priority.MEDIUM
        elif risk_score >= 1:
            return Priority.LOW
        else:
            return Priority.LOW
    
    def _generate_recommendations(self, risk_factors: List[str], risk_level: Priority, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate specific recommendations based on risk assessment"""
        recommendations = []
        
        # General high-risk recommendations
        if risk_level in [Priority.HIGH, Priority.EMERGENCY]:
            recommendations.extend([
                "Close monitoring by healthcare provider recommended",
                "Consider expedited appointment scheduling",
                "Monitor for symptom progression closely"
            ])
        
        # Specific condition recommendations
        if any("cardiovascular" in factor for factor in risk_factors):
            recommendations.append("Monitor blood pressure and heart rate")
            recommendations.append("Consider cardiology consultation")
        
        if any("respiratory" in factor for factor in risk_factors):
            recommendations.append("Monitor oxygen saturation if available")
            recommendations.append("Have rescue medications readily available")
        
        if any("immunocompromised" in factor for factor in risk_factors):
            recommendations.append("Take extra precautions to prevent infections")
            recommendations.append("Consider infectious disease consultation if fever present")
        
        if any("diabetes" in factor for factor in risk_factors):
            recommendations.append("Monitor blood glucose levels closely")
            recommendations.append("Adjust medications as directed by physician")
        
        if "pregnancy" in risk_factors:
            recommendations.append("Consult with obstetrician regarding symptoms")
            recommendations.append("Avoid medications not approved for pregnancy")
        
        # Add medication management recommendations
        if len(risk_factors) >= 2:
            recommendations.append("Review all current medications with pharmacist")
            recommendations.append("Coordinate care between specialists")
        
        return recommendations
    
    def _check_drug_interactions(self, message: str, risk_factors: List[str]) -> List[Dict[str, str]]:
        """Check for potential drug interactions"""
        interactions = []
        message_lower = message.lower()
        
        # Check for high-interaction drugs mentioned
        mentioned_drugs = []
        for drug in self.high_interaction_drugs:
            if drug in message_lower:
                mentioned_drugs.append(drug)
        
        # Generate interaction warnings
        for drug in mentioned_drugs:
            if "warfarin" in drug and any("diabetes" in factor for factor in risk_factors):
                interactions.append({
                    "drug": drug,
                    "risk": "Blood sugar medications may affect warfarin effectiveness",
                    "recommendation": "Monitor INR levels closely"
                })
            
            if "insulin" in drug and any("kidney" in factor for factor in risk_factors):
                interactions.append({
                    "drug": drug,
                    "risk": "Kidney disease may affect insulin clearance",
                    "recommendation": "Adjust insulin dosing with physician guidance"
                })
        
        return interactions
    
    def _calculate_comorbidity_confidence(self, risk_factors: List[str], risk_level: Priority) -> float:
        """Calculate confidence in comorbidity assessment"""
        base_confidence = 0.8
        
        # Higher confidence with more identified risk factors
        if len(risk_factors) >= 2:
            base_confidence += 0.1
        
        # Higher confidence for clear high-risk cases
        if risk_level == Priority.HIGH:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _determine_comorbidity_action(self, risk_level: Priority, risk_factors: List[str]) -> str:
        """Determine action based on comorbidity assessment"""
        if risk_level == Priority.HIGH:
            return "escalate_to_specialist"
        elif len(risk_factors) >= 3:
            return "coordinate_multidisciplinary_care"
        elif risk_level == Priority.MEDIUM:
            return "enhanced_monitoring"
        else:
            return "standard_care_protocol"
    
    def _get_monitoring_requirements(self, risk_factors: List[str]) -> List[str]:
        """Get specific monitoring requirements based on risk factors"""
        monitoring = []
        
        if any("cardiovascular" in factor for factor in risk_factors):
            monitoring.extend(["Blood pressure", "Heart rate", "ECG if indicated"])
        
        if any("respiratory" in factor for factor in risk_factors):
            monitoring.extend(["Oxygen saturation", "Respiratory rate", "Peak flow if available"])
        
        if "diabetes" in risk_factors:
            monitoring.append("Blood glucose levels")
        
        if any("kidney" in factor for factor in risk_factors):
            monitoring.extend(["Fluid balance", "Electrolytes", "Creatinine levels"])
        
        return monitoring
    
    def _get_specialist_referrals(self, risk_factors: List[str]) -> List[str]:
        """Get recommended specialist referrals based on risk factors"""
        referrals = []
        
        if any("cardiovascular" in factor for factor in risk_factors):
            referrals.append("Cardiology")
        
        if any("respiratory" in factor for factor in risk_factors):
            referrals.append("Pulmonology")
        
        if "diabetes" in risk_factors:
            referrals.append("Endocrinology")
        
        if any("kidney" in factor for factor in risk_factors):
            referrals.append("Nephrology")
        
        if any("immunocompromised" in factor for factor in risk_factors):
            referrals.append("Infectious Disease")
        
        if "pregnancy" in risk_factors:
            referrals.append("Obstetrics")
        
        return referrals
    
    def _generate_comorbidity_message(self, comorbidity_risk: ComorbidityRisk, llm_response: str) -> str:
        """Generate comprehensive comorbidity assessment message"""
        risk_text = {
            Priority.HIGH: "🔴 HIGH RISK",
            Priority.MEDIUM: "🟡 MODERATE RISK",
            Priority.LOW: "🟢 LOW RISK"
        }
        
        message = f"{risk_text.get(comorbidity_risk.risk_level, '🟢 ASSESSED')}\n\n"
        message += f"Comorbidity Analysis: {llm_response}\n\n"
        
        if comorbidity_risk.risk_factors:
            message += f"Identified Risk Factors:\n"
            for factor in comorbidity_risk.risk_factors:
                message += f"• {factor.title()}\n"
            message += "\n"
        
        if comorbidity_risk.recommendations:
            message += f"Recommendations:\n"
            for rec in comorbidity_risk.recommendations:
                message += f"• {rec}\n"
        
        return message