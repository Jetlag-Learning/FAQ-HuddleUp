export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  actions?: ActionButton[];
  isSystemMessage?: boolean;
}

export interface ActionButton {
  type: 'calendar' | 'process_analysis' | 'research' | 'questions' | 'solution_preview';
  label: string;
  description: string;
}

export interface FAQResponse {
  answer: string;
  success: boolean;
  error?: string;
}

export interface DiscoveryResponse {
  response: string;
  actions: ActionButton[];
  success: boolean;
  error?: string;
}