/**
 * TypeScript Types for Patient Appointment System
 * Author: Vinod Yadav
 * Date: 7-25-2025
 */

export enum Priority {
  LOW = "low",
  MEDIUM = "medium", 
  HIGH = "high",
  EMERGENCY = "emergency"
}

export enum AppointmentType {
  GENERAL = "general",
  SPECIALIST = "specialist",
  EMERGENCY = "emergency", 
  FOLLOWUP = "followup"
}

export interface PatientRequest {
  message: string;
  patient_id?: string;
  session_id?: string;
}

export interface SymptomAnalysis {
  symptoms: string[];
  severity: Priority;
  urgency: boolean;
  specialty_required?: string;
}

export interface ComorbidityRisk {
  risk_factors: string[];
  risk_level: Priority;
  recommendations: string[];
}

export interface AppointmentSlot {
  date: string;
  time: string;
  doctor: string;
  specialty: string;
  available: boolean;
}

export interface AppointmentBooking {
  appointment_id: string;
  patient_id: string;
  date: string;
  time: string;
  doctor: string;
  specialty: string;
  appointment_type: AppointmentType;
  confirmed: boolean;
}

export interface AgentResponse {
  agent_name: string;
  message: string;
  confidence: number;
  action_taken?: string;
  data?: Record<string, any>;
}

export interface AppointmentResponse {
  message: string;
  agent_responses: AgentResponse[];
  symptom_analysis?: SymptomAnalysis;
  comorbidity_risk?: ComorbidityRisk;
  available_slots: AppointmentSlot[];
  booking?: AppointmentBooking;
  next_steps: string[];
  requires_emergency: boolean;
  session_id?: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  response?: AppointmentResponse;
}