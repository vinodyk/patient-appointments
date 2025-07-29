/**
 * Main App Component - Patient Appointment Booking System
 * Author: Vinod Yadav
 * Date: 7-25-2025
 * Fixed Mobile Responsiveness
 */

import React, { useState, useRef, useEffect } from "react";
import {
  MessageCircle,
  Send,
  Bot,
  User,
  Calendar,
  AlertTriangle,
  Shield,
  Activity,
  Heart,
  Clock,
  CheckCircle,
  Eye,
  EyeOff,
  Brain,
  Cpu,
} from "lucide-react";
import { patientApi } from "./api";
import { ChatMessage, PatientRequest, Priority } from "./types";
import "./App.css";

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [showAgentPanel, setShowAgentPanel] = useState(true);
  const [currentAgentResponses, setCurrentAgentResponses] = useState<any[]>([]);
  const [processingStage, setProcessingStage] = useState<string>("");
  const [isMobile, setIsMobile] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Test backend connection on component mount
  useEffect(() => {
    const testConnection = async () => {
      try {
        const health = await patientApi.healthCheck();
        console.log("Backend health check:", health);
      } catch (error) {
        console.error("Backend connection failed:", error);
      }
    };

    testConnection();
  }, []);

  // Initial welcome message
  useEffect(() => {
    const welcomeMessage: ChatMessage = {
      id: "welcome",
      content: `👋 Welcome to our AI-powered Patient Appointment Booking System!

I'm here to help you:
• Discuss your symptoms and concerns
• Get medical triage assessment  
• Book appointments with appropriate specialists
• Provide health guidance and next steps

Please describe your symptoms or let me know how I can assist you today.`,
      sender: "assistant",
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, []);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: inputMessage,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);
    setProcessingStage("Initializing security check...");
    setCurrentAgentResponses([]);

    try {
      const request: PatientRequest = {
        message: inputMessage,
        session_id: sessionId,
      };

      const response = await patientApi.sendMessage(request);

      // Update agent responses for the panel
      setCurrentAgentResponses(response.agent_responses || []);
      setProcessingStage("Processing complete");

      const assistantMessage: ChatMessage = {
        id: `assistant_${Date.now()}`,
        content: response.message,
        sender: "assistant",
        timestamp: new Date(),
        response: response,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        content:
          "Sorry, I encountered an error processing your request. Please try again.",
        sender: "assistant",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setProcessingStage("Error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getPriorityColor = (priority: Priority) => {
    switch (priority) {
      case Priority.EMERGENCY:
        return "text-red-600";
      case Priority.HIGH:
        return "text-orange-600";
      case Priority.MEDIUM:
        return "text-yellow-600";
      case Priority.LOW:
        return "text-green-600";
      default:
        return "text-gray-600";
    }
  };

  const getAgentIcon = (agentName: string) => {
    switch (agentName.toLowerCase()) {
      case "jailbreak agent":
        return <Shield className="w-4 h-4 text-blue-600" />;
      case "assisting agent":
        return <Bot className="w-4 h-4 text-green-600" />;
      case "triage agent":
        return <Activity className="w-4 h-4 text-red-600" />;
      case "comorbidity agent":
        return <Heart className="w-4 h-4 text-purple-600" />;
      case "appointment booker":
        return <Calendar className="w-4 h-4 text-indigo-600" />;
      default:
        return <Brain className="w-4 h-4 text-gray-600" />;
    }
  };

  const getAgentBgColor = (agentName: string) => {
    switch (agentName.toLowerCase()) {
      case "jailbreak agent":
        return "bg-blue-50 border-blue-200";
      case "assisting agent":
        return "bg-green-50 border-green-200";
      case "triage agent":
        return "bg-red-50 border-red-200";
      case "comorbidity agent":
        return "bg-purple-50 border-purple-200";
      case "appointment booker":
        return "bg-indigo-50 border-indigo-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl lg:text-4xl md:text-3xl sm:text-2xl font-bold text-gray-800 mb-2">
            🏥 Patient Appointment Booking
          </h1>
          <p className="text-gray-600 text-lg lg:text-lg md:text-base sm:text-sm">
            AI-Powered Medical Assistance & Scheduling
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Created by{" "}
            <span className="font-bold text-blue-600">Vinod Yadav</span> • July
            25, 2025
          </p>
        </div>

        {/* Main Content Area - Responsive Layout */}
        <div className="max-w-7xl mx-auto main-container">
          {/* Chat Container */}
          <div className="chat-container bg-white rounded-lg shadow-xl overflow-hidden">
            {/* Chat Header */}
            <div className="chat-header bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MessageCircle className="w-6 h-6" />
                  <h2 className="text-xl lg:text-xl md:text-lg sm:text-base font-semibold">
                    Medical Assistant Chat
                  </h2>
                </div>
                <div className="flex items-center space-x-4">
                  {/* Hide toggle button on mobile since panels are stacked */}
                  {!isMobile && (
                    <button
                      onClick={() => setShowAgentPanel(!showAgentPanel)}
                      className="panel-toggle flex items-center space-x-2 px-3 py-1 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
                    >
                      {showAgentPanel ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                      <span className="text-sm hidden lg:inline">
                        {showAgentPanel ? "Hide" : "Show"} Agents
                      </span>
                    </button>
                  )}
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4" />
                    <span className="text-sm hidden md:inline">
                      Session: {sessionId.slice(-8)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Messages - Clean chat without agent responses */}
            <div className="chat-messages h-96 lg:h-96 md:h-80 overflow-y-auto p-4 space-y-4 bg-gray-50">
              {messages.map((message) => (
                <div key={message.id} className="space-y-2">
                  {/* Main Message Only */}
                  <div
                    className={`flex ${
                      message.sender === "user"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    <div
                      className={`message-content max-w-2xl lg:max-w-2xl md:max-w-xl sm:max-w-xs rounded-lg p-3 ${
                        message.sender === "user"
                          ? "bg-blue-600 text-white ml-12 lg:ml-12 md:ml-8 sm:ml-4"
                          : "bg-white border border-gray-200 mr-12 lg:mr-12 md:mr-8 sm:mr-4 shadow-sm"
                      }`}
                    >
                      <div className="flex items-start space-x-2">
                        <div className="flex-shrink-0 mt-1">
                          {message.sender === "user" ? (
                            <User className="w-5 h-5" />
                          ) : (
                            <Bot className="w-5 h-5 text-blue-600" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="whitespace-pre-wrap text-sm">
                            {message.content}
                          </div>
                          <div
                            className={`text-xs mt-1 ${
                              message.sender === "user"
                                ? "text-blue-100"
                                : "text-gray-500"
                            }`}
                          >
                            {message.timestamp.toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Clinical Information Cards - Clean presentation */}
                  {message.response && (
                    <div className="ml-8 lg:ml-8 md:ml-4 sm:ml-2 space-y-3">
                      {/* Symptom Analysis */}
                      {message.response.symptom_analysis && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 max-w-lg">
                          <h4 className="font-medium text-yellow-800 mb-2 flex items-center">
                            <Activity className="w-4 h-4 mr-2" />
                            Clinical Assessment
                          </h4>
                          <div className="text-sm space-y-1">
                            {message.response.symptom_analysis.symptoms.length >
                              0 && (
                              <div>
                                <strong>Symptoms:</strong>{" "}
                                {message.response.symptom_analysis.symptoms.join(
                                  ", "
                                )}
                              </div>
                            )}
                            <div className="flex items-center space-x-2">
                              <strong>Priority:</strong>
                              <span
                                className={`font-medium ${getPriorityColor(
                                  message.response.symptom_analysis.severity
                                )}`}
                              >
                                {message.response.symptom_analysis.severity.toUpperCase()}
                              </span>
                            </div>
                            {message.response.symptom_analysis
                              .specialty_required && (
                              <div>
                                <strong>Recommended Specialty:</strong>{" "}
                                {
                                  message.response.symptom_analysis
                                    .specialty_required
                                }
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Available Appointments */}
                      {message.response.available_slots &&
                        message.response.available_slots.length > 0 && (
                          <div className="bg-green-50 border border-green-200 rounded-lg p-3 max-w-lg">
                            <h4 className="font-medium text-green-800 mb-2 flex items-center">
                              <Calendar className="w-4 h-4 mr-2" />
                              Available Appointments
                            </h4>
                            <div className="space-y-2">
                              {message.response.available_slots
                                .slice(0, 3)
                                .map((slot, idx) => (
                                  <div
                                    key={idx}
                                    className="bg-white rounded p-2 text-sm border border-green-100"
                                  >
                                    <div className="font-medium text-green-800">
                                      {idx + 1}. {slot.date} at {slot.time}
                                    </div>
                                    <div className="text-green-600">
                                      {slot.doctor} - {slot.specialty}
                                    </div>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}

                      {/* Confirmed Booking */}
                      {message.response.booking && (
                        <div className="bg-green-100 border border-green-300 rounded-lg p-3 max-w-lg">
                          <h4 className="font-medium text-green-800 mb-2 flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Appointment Confirmed
                          </h4>
                          <div className="text-sm space-y-1">
                            <div>
                              <strong>ID:</strong>{" "}
                              {message.response.booking.appointment_id}
                            </div>
                            <div>
                              <strong>Date:</strong>{" "}
                              {message.response.booking.date}
                            </div>
                            <div>
                              <strong>Time:</strong>{" "}
                              {message.response.booking.time}
                            </div>
                            <div>
                              <strong>Doctor:</strong>{" "}
                              {message.response.booking.doctor}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Emergency Warning */}
                      {message.response.requires_emergency && (
                        <div className="bg-red-100 border border-red-300 rounded-lg p-3 max-w-lg">
                          <h4 className="font-medium text-red-800 mb-2 flex items-center">
                            <AlertTriangle className="w-4 h-4 mr-2" />
                            Emergency Alert
                          </h4>
                          <div className="text-sm text-red-700">
                            Immediate medical attention may be required. Please
                            contact emergency services if symptoms are severe.
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-lg p-3 mr-12 lg:mr-12 md:mr-8 sm:mr-4 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <Bot className="w-5 h-5 text-blue-600" />
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="chat-input-container border-t border-gray-200 p-4 bg-white">
              <div className="flex space-x-2">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Describe your symptoms or ask about booking an appointment..."
                  className="chat-input flex-1 border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={2}
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                Press Enter to send • Shift+Enter for new line
              </div>
            </div>
          </div>

          {/* Agent Orchestration Panel - Always visible on mobile, stacked below chat */}
          {(showAgentPanel || isMobile) && (
            <div className="agent-panel bg-white rounded-lg shadow-xl overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-5 h-5" />
                  <h3 className="font-semibold">Agent Orchestration</h3>
                </div>
                <p className="text-sm text-purple-100 mt-1">
                  Real-time AI agent workflow
                </p>
              </div>

              <div className="agent-content p-4 space-y-4 max-h-96 lg:max-h-96 md:max-h-80 sm:max-h-60 overflow-y-auto">
                {/* Processing Status */}
                {isLoading && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
                      <span className="font-medium text-blue-800">
                        Processing
                      </span>
                    </div>
                    <p className="text-sm text-blue-600">{processingStage}</p>
                  </div>
                )}

                {/* Agent Responses */}
                {currentAgentResponses.map((agent, idx) => (
                  <div
                    key={idx}
                    className={`border rounded-lg p-3 ${getAgentBgColor(
                      agent.agent_name
                    )}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getAgentIcon(agent.agent_name)}
                        <span className="font-medium text-sm">
                          {agent.agent_name}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-xs text-gray-600">
                          {Math.round(agent.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-700 line-clamp-3">
                      {agent.message.substring(0, 120)}...
                    </div>
                    {agent.action_taken && (
                      <div className="mt-2 px-2 py-1 bg-white/50 rounded text-xs font-medium">
                        Action: {agent.action_taken}
                      </div>
                    )}
                  </div>
                ))}

                {/* Default state when no agents are active */}
                {!isLoading && currentAgentResponses.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    <Cpu className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm">
                      Send a message to see agent workflow
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-8 space-y-3">
          {/* Demo Disclaimer */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-4xl mx-auto">
            <p className="text-yellow-800 font-medium mb-2">
              🚨 DEMO APPLICATION DISCLAIMER
            </p>
            <p className="text-yellow-700 text-sm">
              This is a <strong>demonstration application</strong> built by{" "}
              <strong className="text-yellow-900">Vinod Yadav</strong> to
              showcase AI-powered healthcare technology. This system is{" "}
              <strong>NOT</strong> intended for real medical use.
            </p>
          </div>

          {/* Emergency Warning */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-4xl mx-auto">
            <p className="text-red-800 font-bold mb-2">
              ⚠️ FOR REAL MEDICAL EMERGENCIES
            </p>
            <p className="text-red-700 text-sm">
              <strong>Call 911 immediately</strong> or visit your nearest
              emergency room. For non-emergency medical concerns, please consult
              with a licensed healthcare professional or your primary care
              physician.
            </p>
          </div>

          {/* Technical Info */}
          <div className="text-gray-600 text-sm">
            <p>
              🤖 Powered by Multi-Agent AI, OpenAI GPT-3.5, React & TypeScript
            </p>
            <p className="mt-1">
              Built by <strong className="text-blue-600">Vinod Yadav</strong> |
              <a
                href="https://github.com"
                className="text-blue-500 hover:text-blue-700 ml-1"
              >
                GitHub
              </a>{" "}
              |
              <a
                href="mailto:vinodyk@gmail.com"
                className="text-blue-500 hover:text-blue-700 ml-1"
              >
                Email
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
