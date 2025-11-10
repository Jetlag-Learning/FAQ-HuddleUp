import axios from 'axios';
import { FAQResponse, DiscoveryResponse } from '../types/chat';

const API_BASE_URL =
  process.env.REACT_APP_API_URL ||
  (window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://faq-huddleup.onrender.com'); 


const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatService = {
  async sendDiscoveryMessage(message: string, sessionId?: string, conversationContext?: any[]): Promise<DiscoveryResponse> {
    try {
      const response = await api.post<DiscoveryResponse>('/api/faq/discovery', {
        question: message,
        session_id: sessionId,
        conversation_context: conversationContext
      });

      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.error || 'Failed to get response');
      }
    } catch (error: any) {
      console.error('Error sending discovery message:', error);
      console.error('Error details:', error);
      console.error('Error type:', typeof error);
      
      // Log more details about the error
      if (error.isAxiosError || error.response) {
        console.error('Axios error - Status:', error.response?.status);
        console.error('Axios error - Data:', error.response?.data);
        console.error('Axios error - Message:', error.message);
        console.error('Request URL:', error.config?.url);
        console.error('Request baseURL:', error.config?.baseURL);
      }
      
      // Check if it's a CORS or connection error
      const errorMessage = error.message || '';
      const isNetworkError = errorMessage.includes('Network Error') || 
                           errorMessage.includes('ERR_NETWORK') ||
                           errorMessage.includes('Failed to fetch') ||
                           error.code === 'ERR_NETWORK';
      
      console.log('Is network error?', isNetworkError);
      console.log('Error message:', errorMessage);
      
      // Use fallback only for actual network errors
      if (isNetworkError) {
        console.log('Using fallback response due to network connectivity issue');
        return this.getFallbackDiscoveryResponse(message);
      }
      
      // For other errors, try to return the actual error response or re-throw
      console.log('Not a network error - checking for API response');
      throw new Error(`API Error: ${errorMessage}`);
    }
  },

  async sendMessage(message: string): Promise<string> {
    try {
      const response = await api.post<FAQResponse>('/api/faq/ask', {
        question: message,
      });

      if (response.data.success) {
        return response.data.answer;
      } else {
        throw new Error(response.data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Fallback responses for demo purposes
      if (error instanceof Error && error.message.includes('Network Error')) {
        return this.getFallbackResponse(message);
      }
      
      throw new Error('Failed to send message. Please try again.');
    }
  },

  // Enhanced fallback for discovery responses
  getFallbackDiscoveryResponse(message: string): DiscoveryResponse {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('cost') || lowerMessage.includes('price') || lowerMessage.includes('pricing')) {
      return {
        response: `HuddleUp offers flexible pricing starting at $29/month for up to 100 members. Our Professional plan is $79/month for up to 500 members, and we have Enterprise options for larger organizations.\n\nTo give you the most relevant pricing information, what size team are you working with, and what's your primary use case - training, collaboration, or community building?`,
        actions: [
          { type: 'questions', label: 'Ask more questions', description: 'Continue exploring HuddleUp' },
          { type: 'calendar', label: 'Find a time to meet with Derek', description: 'Get personalized pricing recommendations' }
        ],
        success: true
      };
    }
    
    if (lowerMessage.includes('train') || lowerMessage.includes('course') || lowerMessage.includes('learn')) {
      return {
        response: `HuddleUp enhances training programs by making them more interactive and collaborative. Unlike traditional LMS platforms, we focus on peer-to-peer learning and community-driven knowledge sharing.\n\nWhat challenges are you currently facing with your training programs? Are you looking to improve engagement, delivery efficiency, or knowledge retention?`,
        actions: [
          { type: 'process_analysis', label: 'See how your processes could work in HuddleUp', description: 'Discover improvements for your training workflows' },
          { type: 'research', label: 'Receive research on HuddleUp benefits', description: 'Get data on training effectiveness improvements' },
          { type: 'questions', label: 'Ask more questions', description: 'Continue exploring HuddleUp' }
        ],
        success: true
      };
    }
    
    return {
      response: `I'm here to help you discover how HuddleUp can transform your team's learning and collaboration! We specialize in creating interactive learning communities that boost engagement and knowledge sharing.\n\nTo better understand how HuddleUp can help you, what's your role and what are your biggest challenges with current learning or collaboration processes?`,
      actions: [
        { type: 'solution_preview', label: 'Explore HuddleUp Solution Preview', description: 'See how HuddleUp works for your specific needs' },
        { type: 'questions', label: 'Ask more questions', description: 'Continue exploring HuddleUp features' },
        { type: 'process_analysis', label: 'See benefits in HuddleUp', description: 'Discover how we can improve your workflows' }
      ],
      success: true
    };
  },

  // Fallback responses when backend is not available
  getFallbackResponse(message: string): string {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('cost') || lowerMessage.includes('price') || lowerMessage.includes('pricing')) {
      return `HuddleUp offers flexible pricing plans:
      
• **Starter Plan**: $29/month for up to 100 members
• **Professional Plan**: $79/month for up to 500 members  
• **Enterprise Plan**: Custom pricing for larger organizations

All plans include core features like community management, content sharing, and basic analytics. Higher tiers include advanced integrations and priority support.

Would you like to know more about any specific plan?`;
    }
    
    if (lowerMessage.includes('lms') || lowerMessage.includes('community') || lowerMessage.includes('platform')) {
      return `HuddleUp is primarily a **community platform** with learning management features, rather than a traditional LMS.

Key differences:
• **Community-first**: Built around member engagement and collaboration
• **Social Learning**: Emphasizes peer-to-peer knowledge sharing
• **Flexible Content**: Supports various content types beyond courses
• **Member-driven**: Communities can be self-organizing and member-led

Think of it as a blend of community platform and learning environment, perfect for organizations wanting to foster both connection and knowledge sharing.`;
    }
    
    if (lowerMessage.includes('different') || lowerMessage.includes('current') || lowerMessage.includes('process')) {
      return `HuddleUp can enhance your current processes in several ways:

🔄 **Process Integration**: Rather than replacing what works, HuddleUp adds collaboration layers
📚 **Knowledge Capture**: Turn tribal knowledge into searchable, shareable resources  
🤝 **Cross-team Collaboration**: Break down silos between departments
📈 **Engagement Analytics**: See what content resonates and drives participation
⚡ **Automation**: Reduce manual tasks with workflow automation

To give you more specific recommendations, could you tell me about your current processes? For example:
- How do you currently share knowledge?
- What tools do you use for team collaboration?
- What challenges are you facing with your current setup?`;
    }
    
    return `I'm here to help with questions about HuddleUp! I can tell you about:

• **Pricing and plans**
• **Features and capabilities** 
• **How HuddleUp compares to other platforms**
• **Implementation and use cases**
• **How it can improve your current processes**

What would you like to know more about?`;
  }
};

export default chatService;