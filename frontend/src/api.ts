/**
 * API Client for Patient Appointment System
 * Author: Vinod Yadav
 * Date: 7-25-2025
 */

import axios from 'axios';
import { PatientRequest, AppointmentResponse } from './types';

// Simple API base URL - will use relative path in production
const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), `${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const patientApi = {
  /**
   * Send a chat message to the patient appointment system
   */
  sendMessage: async (request: PatientRequest): Promise<AppointmentResponse> => {
    try {
      console.log('Sending message:', request);
      const response = await apiClient.post<AppointmentResponse>('/chat', request);
      console.log('Received response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error sending message:', error);
      
      // Provide more specific error messages
      if (error.code === 'ECONNREFUSED') {
        throw new Error('Cannot connect to server. Please check if the backend is running.');
      } else if (error.response?.status === 404) {
        throw new Error('API endpoint not found. Please check the backend configuration.');
      } else if (error.response?.status === 500) {
        throw new Error(`Server error: ${error.response.data?.detail || 'Internal server error'}`);
      } else {
        throw new Error(`Failed to send message: ${error.message}`);
      }
    }
  },

  /**
   * Get the status of all agents
   */
  getAgentsStatus: async () => {
    try {
      const response = await apiClient.get('/agents/status');
      return response.data;
    } catch (error) {
      console.error('Error getting agents status:', error);
      throw new Error('Failed to get agents status.');
    }
  },

  /**
   * Health check
   */
  healthCheck: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Error in health check:', error);
      throw new Error('Health check failed.');
    }
  }
};

export default apiClient;