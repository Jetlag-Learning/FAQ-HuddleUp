import React, { useState, useRef, useEffect } from 'react';
// import { FC, ReactNode } from 'react';
import { Send, MessageCircle, X, Minus, Maximize2, Copy, ThumbsUp, ThumbsDown, Calendar, FileText, BookOpen, HelpCircle, Play } from 'lucide-react';
import { Message, ActionButton } from '../types/chat';
import { chatService } from '../services/chatService';

export const ChatWidget: React.FC<{}> = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hoveredMessage, setHoveredMessage] = useState<string | null>(null);
  const [sessionId] = useState(() => 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (inputMessage.trim() === '') return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Auto-resize textarea
    if (inputRef.current) {
      inputRef.current.style.height = '44px';
    }

    try {
      // Use discovery endpoint for enhanced conversation
      const discoveryResponse = await chatService.sendDiscoveryMessage(
        inputMessage,
        sessionId,
        messages.slice(-6).map(msg => ({ role: msg.sender === 'user' ? 'user' : 'assistant', content: msg.text }))
      );

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: discoveryResponse.response,
        sender: 'bot',
        timestamp: new Date(),
        actions: discoveryResponse.actions
      };

      setMessages(prev => [...prev, botMessage]);

      // Check if this is the transition to full engagement (5+ queries)
      const userQueries = [...messages, userMessage].filter(msg => msg.sender === 'user').length;
      if (userQueries === 5 && discoveryResponse.actions && discoveryResponse.actions.length > 2) {
        // Show a subtle celebration or acknowledgment after a delay
        setTimeout(() => {
          const celebrationMessage: Message = {
            id: (Date.now() + 2).toString(),
            text: "🎉 I can see you're genuinely interested in exploring HuddleUp! Since we've been chatting, I'd love to offer you some additional ways to dive deeper and get personalized insights about how HuddleUp can specifically help you.",
            sender: 'bot',
            timestamp: new Date(),
            actions: [],
            isSystemMessage: true
          };
          setMessages(prev => [...prev, celebrationMessage]);
        }, 1500);
      }

    } catch (error) {
      console.error('Discovery failed, trying fallback:', error);

      try {
        // Fallback to regular FAQ endpoint
        const response = await chatService.sendMessage(inputMessage);

        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response,
          sender: 'bot',
          timestamp: new Date()
        };

        setMessages(prev => [...prev, botMessage]);
      } catch (fallbackError) {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: 'I apologize, but I encountered an error processing your request. Please try again or contact our support team.',
          sender: 'bot',
          timestamp: new Date()
        };

        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
      focusInput();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);

    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = '44px';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };

  // Ensure input field is focused after certain actions
  const focusInput = () => {
    setTimeout(() => {
      if (inputRef.current && !isLoading) {
        inputRef.current.focus();
      }
    }, 100);
  };

  const copyMessage = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleActionClick = async (action: ActionButton) => {
    let actionMessage = '';

    switch (action.type) {
      case 'calendar':
        actionMessage = "I'd like to schedule a meeting with Derek to discuss how HuddleUp can help my organization.";
        // Open calendar booking link
        window.open('https://calendly.com/d/cq2w-3fm-krb/huddle-up-intro-call', '_blank');
        break;
      case 'solution_preview':
        actionMessage = "I'd like to explore a HuddleUp Solution Preview tailored to my specific needs.";
        break;
      case 'process_analysis':
        actionMessage = "Please show me how my current processes could work better in HuddleUp.";
        break;
      case 'research':
        actionMessage = "I'd like to receive research on the problems HuddleUp solves.";
        break;
      case 'questions':
        actionMessage = "I have more questions about HuddleUp features and capabilities.";
        break;
      default:
        actionMessage = action.label;
    }

    // Add user message for the action
    const userMessage: Message = {
      id: Date.now().toString(),
      text: actionMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Handle different action types
      if (action.type === 'calendar') {
        // Direct Google Calendar booking link
        const calendarBookingUrl = 'https://calendly.com/d/cq2w-3fm-krb/huddle-up-intro-call';
        window.open(calendarBookingUrl, '_blank');

        // Show confirmation message
        const confirmationMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `Perfect! I've opened Google Calendar for you to schedule a meeting with Derek.

**During your session, Derek will:**
• 🎯 Understand your specific challenges and goals
• 🚀 Show you HuddleUp features relevant to your needs
• 🔧 Discuss how our platform integrates with your workflows
• 💡 Answer all your questions about implementation
• 📊 Share case studies from similar organizations

Looking forward to the meeting! 🚀`,
          sender: 'bot',
          timestamp: new Date()
        };

        setTimeout(() => {
          setMessages(prev => [...prev, confirmationMessage]);
          setIsLoading(false);
          focusInput();
        }, 800);
        return;
      } else if (action.type === 'solution_preview') {
        // HuddleUp Solution Preview
        const previewMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `Excellent choice! Let me show you a tailored HuddleUp Solution Preview based on what I've learned about your needs.

🎯 **Your Personalized HuddleUp Solution Preview:**

**For Your Role & Challenges:**
• 📚 **Interactive Learning Modules** - Replace static training with engaging, collaborative sessions
• 👥 **Peer Learning Networks** - Connect team members for knowledge sharing and problem-solving
• 📊 **Progress Analytics** - Track engagement and learning outcomes in real-time
• 🔄 **Workflow Integration** - Seamlessly fits into your existing processes

**Key Features You'll Love:**
✅ **Smart Content Management** - Organize and update training materials effortlessly
✅ **Discussion Forums** - Foster ongoing conversations around learning topics
✅ **Mobile-First Design** - Learn and collaborate anywhere, anytime
✅ **Custom Branding** - Make it feel like your organization's platform

**What Makes This Different:**
🌟 Community-driven learning vs. traditional top-down training
🌟 Real-time collaboration vs. isolated learning experiences
🌟 Data-driven insights vs. guesswork about effectiveness

**Ready to See It in Action?**
The best way to understand how this works for your specific situation is through a personalized demo!`,
          sender: 'bot',
          timestamp: new Date(),
          actions: [
            { type: 'calendar', label: 'Schedule a live demo', description: 'See HuddleUp in action with your use case' },
            { type: 'process_analysis', label: 'Analyze my current processes', description: 'Deep dive into your specific workflows' },
            { type: 'questions', label: 'Ask more questions', description: 'Continue exploring features' }
          ]
        };

        setTimeout(() => {
          setMessages(prev => [...prev, previewMessage]);
          setIsLoading(false);
          focusInput();
        }, 1200);

      } else {
        // For other actions, use the discovery endpoint
        const discoveryResponse = await chatService.sendDiscoveryMessage(
          actionMessage,
          sessionId,
          messages.slice(-6).map(msg => ({ role: msg.sender === 'user' ? 'user' : 'assistant', content: msg.text }))
        );

        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: discoveryResponse.response,
          sender: 'bot',
          timestamp: new Date(),
          actions: discoveryResponse.actions
        };

        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
        focusInput();
      }
    } catch (error) {
      console.error('Error handling action:', error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'd be happy to help with that! Could you tell me more about what you're looking for?",
        sender: 'bot',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }

    // Restore focus to input after action completes
    focusInput();
  };

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'calendar': return <Calendar size={16} />;
      case 'solution_preview': return <Play size={16} />;
      case 'process_analysis': return <FileText size={16} />;
      case 'research': return <BookOpen size={16} />;
      case 'questions': return <HelpCircle size={16} />;
      default: return <HelpCircle size={16} />;
    }
  };

  const getActionColor = (type: string) => {
    switch (type) {
      case 'calendar': return 'border-[#182978] hover:border-[#14205F] hover:bg-[#18297810] text-[#182978]';
      case 'solution_preview': return 'border-blue-200 hover:border-blue-400 hover:bg-blue-50 text-blue-700';
      case 'process_analysis': return 'border-indigo-200 hover:border-indigo-400 hover:bg-indigo-50 text-indigo-700';
      case 'research': return 'border-purple-200 hover:border-purple-400 hover:bg-purple-50 text-purple-700';
      case 'questions': return 'border-gray-200 hover:border-gray-400 hover:bg-gray-50 text-gray-700';
      default: return 'border-gray-200 hover:border-gray-400 hover:bg-gray-50 text-gray-700';
    }
  };

  const handleChatOpen = () => {
    setIsOpen(true);
    setIsMinimized(true);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const formatMessage = (text: string) => {
    // Handle markdown-like formatting
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
      .replace(/\n/g, '<br>');
  };

  // Email Collection Modal - Removed (using inline collection instead)

  // Full-screen maximized view
  if (isMaximized) {
    return (
      <div className="fixed inset-0 bg-gray-50/95 z-50 flex items-center justify-center p-2 sm:p-8">
        <div className="bg-white rounded-xl border border-gray-200 hover:border-[#182978] transition-colors duration-200 flex flex-col min-h-[600px] max-h-[calc(100vh-64px)] w-full max-w-6xl overflow-hidden shadow-lg">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 p-4 sm:p-6">
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <h1 className="text-xl sm:text-2xl font-semibold text-gray-900 text-left truncate">
                  HuddleUp Agent
                </h1>

                <p className="text-xs sm:text-sm text-gray-600 mt-1 line-clamp-2">Connect with our AI assistant for personalized support on your HuddleUp journey.</p>
              </div>
              <button
                onClick={() => setIsMaximized(false)}
                className="hover:bg-gray-100 p-2 rounded-lg transition-colors flex-shrink-0"
                aria-label="Exit full screen"
              >
                <X size={20} className="text-gray-600" />
              </button>
            </div>
          </div>

          <div className="flex-1 flex w-full h-full overflow-hidden gap-4 p-2 sm:p-4">
            {/* Sidebar - Hidden on mobile */}
            <div className="hidden lg:flex bg-white rounded-xl border border-gray-200 hover:border-indigo-200 transition-colors duration-200 w-64 p-4 flex-col flex-shrink-0 overflow-y-auto [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-gray-50 [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-gray-400 shadow-sm">

              <div className="space-y-3 flex-shrink-0">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">AI ASSISTANCE</h3>

                <div className="space-y-2">
                  <div className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors">
                    <img
                      src="/favicon1.png"
                      alt="HuddleUp"
                      className="w-8 h-8 rounded-full object-cover"
                    />

                    <div>
                      <div className="font-medium text-gray-900">HuddleUp Assistant</div>
                      <div className="text-sm text-[#182978]">AI Agent</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col bg-gray-50 min-h-0 rounded-xl overflow-hidden">
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto min-h-0 scroll-smooth [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-gray-100 [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-gray-400">
                <div className="p-3 sm:p-6 space-y-4 sm:space-y-6 flex flex-col">
                  {/* Filter out initial greeting messages but show all user conversations */}
                  {messages.filter(msg =>
                    !(msg.sender === 'bot' && (
                      msg.text.includes('Hi there 👋') ||
                      msg.text.includes('Please introduce yourself')
                    ))
                  ).map((message) => (
                    <div
                      key={message.id}
                      className={`group flex gap-2 sm:gap-3 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                      onMouseEnter={() => setHoveredMessage(message.id)}
                      onMouseLeave={() => setHoveredMessage(null)}
                    >
                      {message.sender === 'bot' && (
                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-[#ffffff] rounded-full items-center justify-center flex-shrink-0 self-start hidden sm:flex">
                           <img
                              src="/favicon1.png"
                              alt="HuddleUp"
                              className="w-6 sm:w-8 h-6 sm:h-8 object-contain"
                            />
                        </div>
                      )}

                      <div className={`max-w-[85%] sm:max-w-[70%] ${message.sender === 'user' ? 'order-1' : ''}`}>
                        <div
                          className={`p-3 sm:p-4 rounded-2xl text-left text-xs sm:text-sm ${message.sender === 'user'
                              ? 'bg-[#182978] text-white rounded-br-md'
                              : message.isSystemMessage
                                ? 'bg-gradient-to-r from-[#18297810] to-[#14205F10] text-gray-800 rounded-bl-md border border-[#182978] shadow-sm'
                                : 'bg-white text-gray-800 rounded-bl-md border border-gray-200 shadow-sm'
                            }`}
                        >
                          <div
                            className="leading-relaxed"
                            dangerouslySetInnerHTML={{ __html: formatMessage(message.text) }}
                          />
                        </div>

                        {/* Action buttons for bot messages in maximized view */}
                        {message.sender === 'bot' && message.actions && message.actions.length > 0 && (
                          <div className="mt-3 sm:mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {message.actions.map((action, index) => (
                              <button
                                key={`${message.id}-action-${index}`}
                                onClick={() => handleActionClick(action)}
                                className={`flex items-center gap-2 sm:gap-3 text-left p-2 sm:p-4 rounded-lg border transition-all duration-200 text-xs sm:text-sm ${getActionColor(action.type)}`}
                                disabled={isLoading}
                              >
                                {getActionIcon(action.type)}
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium truncate">{action.label}</div>
                                  <div className="opacity-75 line-clamp-1">{action.description}</div>
                                </div>
                              </button>
                            ))}
                          </div>
                        )}

                        {/* Message actions */}
                        {hoveredMessage === message.id && (
                          <div className={`flex items-center gap-1 mt-2 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <button
                              onClick={() => copyMessage(message.text)}
                              className="text-gray-400 hover:text-gray-600 p-1 rounded transition-colors"
                              title="Copy message"
                            >
                              <Copy size={12} />
                            </button>
                            {message.sender === 'bot' && (
                              <>
                                <button
                                  className="text-gray-400 hover:text-[#182978] p-1 rounded transition-colors"
                                  title="Good response"
                                >
                                  <ThumbsUp size={12} />
                                </button>
                                <button
                                  className="text-gray-400 hover:text-red-600 p-1 rounded transition-colors"
                                  title="Poor response"
                                >
                                  <ThumbsDown size={12} />
                                </button>
                              </>
                            )}
                            <span className="text-xs text-gray-400">
                              {message.timestamp.toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        )}
                      </div>

                      {message.sender === 'user' && (
                        <div className="w-8 h-8 sm:w-10 sm:h-10 bg-indigo-300 rounded-full items-center justify-center flex-shrink-0 hidden sm:flex">
                          <svg
                            className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Typing indicator */}
                  {isLoading && (
                    <div className="flex justify-start gap-2 sm:gap-3">
                      <div className="w-10 h-10 sm:w-12 sm:h-12 bg-[#e2e2e2] rounded-full items-center justify-center flex-shrink-0 self-start hidden sm:flex">
                         <img
                        src="/favicon1.png"
                        alt="HuddleUp"
                        className="w-6 sm:w-8 h-6 sm:h-8 object-contain"
                      />
                      </div>
                      <div className="bg-white border border-gray-200 p-3 sm:p-4 rounded-2xl rounded-bl-md shadow-sm">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* Input Area */}
              <div className="border-t border-gray-200 bg-white p-2 sm:p-4 flex-shrink-0 shadow-lg relative z-20">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="flex-1 relative">
                    <textarea
                      ref={inputRef}
                      value={inputMessage}
                      onChange={handleInputChange}
                      onKeyPress={handleKeyPress}
                      onClick={() => inputRef.current?.focus()}
                      placeholder="Ask me anything..."
                      className="w-full border border-gray-300 rounded-lg px-2 sm:px-3 py-2 pr-8 sm:pr-10 focus:outline-none focus:ring-2 focus:ring-[#182978] focus:border-transparent text-xs sm:text-sm resize-none transition-all duration-200 bg-white shadow-sm"
                      disabled={isLoading}
                      rows={1}
                      style={{ minHeight: '36px', maxHeight: '100px' }}
                      tabIndex={0}
                      autoFocus={true}
                    />
                    <div className="absolute right-1 bottom-1 text-xs text-gray-400">
                      {inputMessage.length > 0 && `${inputMessage.length}/1000`}
                    </div>
                  </div>
                  <button
                    onClick={handleSendMessage}
                    disabled={isLoading || inputMessage.trim() === ''}
                    className="bg-[#182978] hover:bg-[#14205F] disabled:bg-gray-400 text-white p-2 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg disabled:cursor-not-allowed flex items-center justify-center flex-shrink-0 h-9 sm:h-10 w-9 sm:w-10"
                    aria-label="Send message"
                  >
                    <Send size={14} className={`sm:w-4 sm:h-4 ${isLoading ? 'animate-pulse' : ''}`} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={handleChatOpen}
          className="group bg-[#182978] hover:bg-[#14205F] text-white p-4 rounded-full shadow-xl transition-all duration-300 hover:scale-105 hover:shadow-2xl border-2 border-[#182978]"
          aria-label="Open FAQ Chat"
        >
          <MessageCircle size={24} className="group-hover:rotate-12 transition-transform duration-300" />
        </button>
        <div className="absolute -top-12 right-0 bg-gray-900 text-white text-sm px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap border border-gray-700">
          💬 Ask me anything about HuddleUp!
        </div>
      </div>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 bg-white rounded-2xl shadow-2xl z-50 transition-all duration-300 overflow-hidden ${isMinimized ? 'w-[360px] h-[580px]' : 'h-[600px] w-96'
      }`}>
      {/* Minimized View */}
      {isMinimized ? (
      
        <div className="relative w-[360px] h-[580px] rounded-2xl overflow-hidden shadow-2xl flex flex-col text-white">

          {/* PURPLE HEADER */}
          <div className="relative flex-none bg-gradient-to-br from-[#182978] via-[#182978] to-[#182978]">
            {/* top bar */}
            <div className="flex items-start justify-between p-4">
              {/* Logo circle */}
              <div className="w-10 h-10 bg-white/30 rounded-full flex items-center justify-center backdrop-blur overflow-hidden">
                <img
                  src="/favicon1.png"
                  alt="HuddleUp logo"
                  className="w-7 h-7 object-contain"
                  loading="lazy"
                />
              </div>

              <button
                onClick={() => setIsOpen(false)}
                className="text-white/90 hover:bg-white/10 p-2 rounded-lg transition"
                aria-label="Close chat"
              >
                <X size={20} />
              </button>
            </div>


            {/* welcome copy */}
            <div className="px-5 pb-24"> {/* pb-24 leaves space for the floating card */}
              <h2 className="text-2xl font-bold mb-1 flex items-center gap-1">
                Hi there <span className="text-3xl">👋</span>
              </h2>
              <p className="text-white/90">
                Welcome to our website. Ask us anything 🎉
              </p>
            </div>

            {/* floating chat preview (sits over purple + above white footer) */}
            <div className="absolute bottom-[-28px] left-1/2 -translate-x-1/2 w-[calc(100%-48px)] z-10">
              <div className="bg-white rounded-2xl shadow-lg p-3 border border-gray-100">
                <div
                  onClick={() => setIsMinimized(false)}
                  className="w-full flex items-center gap-3 text-left hover:bg-gray-50 p-2 rounded-lg transition cursor-pointer"
                >
                  <div className="flex-1">
                    <p className="text-gray-900 font-semibold text-sm">Chat with us</p>
                    <p className="text-gray-600 text-xs">
                      We typically reply within a few minutes.
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsMinimized(false);
                    }}
                    className="text-white p-2 rounded-lg transition-all flex items-center justify-center flex-shrink-0
                      bg-[#182978] hover:bg-[#14205F] focus:ring-2 focus:ring-offset-2 focus:ring-[#182978]"
                    aria-label="Open chat"
                  >
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        fillRule="evenodd"
                        d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>

                </div>
              </div>
            </div>
          </div>

          {/* WHITE FOOTER (tabs + powered by) */}
          <div className="mt-auto bg-white text-gray-700 pt-10 pb-4 px-4">
            {/* tabs */}
            <div className="flex gap-4 justify-center mb-3">
              <button
                className="flex flex-col items-center gap-2 flex-1 hover:opacity-80 transition"
                onClick={() => setIsMinimized(false)}
              >
                <div className="text-xl">🏠</div>
                <span className="text-xs font-medium">Home</span>
              </button>
              <button
                className="flex flex-col items-center gap-2 flex-1 hover:opacity-80 transition"
                onClick={() => setIsMinimized(false)}
              >
                <div className="text-xl">💬</div>
                <span className="text-xs font-medium">Chat</span>
              </button>
            </div>

            {/* powered by */}
            <div className="border-t pt-2">
              <p className="text-[11px] text-gray-500 text-center tracking-wide">
                POWERED BY <span className="font-semibold">HUDDLEUP AI AGENT</span>
              </p>
            </div>
          </div>
        </div>


      ) : (
        <>
          {/* Header */}
          <div className="bg-[#182978] border-b border-[#182978] p-4 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                 <img
    src="/favicon1.png"
    alt="HuddleUp"
    className="w-5 h-5 object-contain"
  />
              </div>
              <div>
                <span className="font-semibold text-white">HuddleUp Assistant</span>
                <div className="flex items-center space-x-1 text-xs text-blue-100">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>Online</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setIsMaximized(true)}
                className="hover:bg-[#14205F] p-2 rounded-lg transition-colors"
                aria-label="Maximize chat"
              >
                <Maximize2 size={16} className="text-white" />
              </button>
              <button
                onClick={() => setIsMinimized(true)}
                className="hover:bg-blue-700 p-2 rounded-lg transition-colors"
                aria-label="Minimize chat"
              >
                <Minus size={16} className="text-white" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-blue-700 p-2 rounded-lg transition-colors"
                aria-label="Close chat"
              >
                <X size={16} className="text-white" />
              </button>
            </div>
          </div>

          {/* Chat Content */}
          {/* Messages */}
          <div className="flex-1 overflow-y-auto" style={{ height: '440px' }}>
            <div className="p-4 space-y-4">
              {/* Show welcome message only if no real conversation has started */}
              {(messages.filter(msg =>
                !(msg.sender === 'bot' && (
                  msg.text.includes('Hi there 👋') ||
                  msg.text.includes('Please introduce yourself')
                ))
              ).length === 0) && (
                  <div className="text-center py-8">
              
                    <p className="text-gray-600 text-sm">
                      How can we assist you today? 
                    </p>
                  </div>
                )}

              {/* Show actual conversation messages */}
              {messages.filter(msg =>
                !(msg.sender === 'bot' && (
                  msg.text.includes('Hi there 👋') ||
                  msg.text.includes('Please introduce yourself')
                ))
              ).map((message) => (
                <div
                  key={message.id}
                  className={`group flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  onMouseEnter={() => setHoveredMessage(message.id)}
                  onMouseLeave={() => setHoveredMessage(null)}
                >
                  {message.sender === 'bot' && (
                    <div className="w-10 h-10 bg-[#f6f6f8] rounded-full flex items-center justify-center mr-4 mt-1 flex-shrink-0 self-start">
                       <img
                          src="/favicon1.png"
                          alt="HuddleUp"
                          className="w-5 h-5 object-contain"
                        />
                    </div>
                  )}

                  <div className={`max-w-[75%] ${message.sender === 'user' ? 'order-1' : ''}`}>
                    <div
                      className={`p-4 rounded-2xl shadow-sm text-left ${message.sender === 'user'
                          ? 'bg-blue-600 text-white rounded-br-md'
                          : message.isSystemMessage
                            ? 'bg-gradient-to-r from-emerald-50 to-blue-50 text-gray-800 rounded-bl-md border border-emerald-200'
                            : 'bg-gray-50 text-gray-800 rounded-bl-md border border-gray-100'
                        }`}
                    >
                      <div
                        className="text-sm leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: formatMessage(message.text) }}
                      />
                    </div>

                    {/* Action buttons for bot messages */}
                    {message.sender === 'bot' && message.actions && message.actions.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {message.actions.map((action, index) => (
                          <button
                            key={`${message.id}-action-${index}`}
                            onClick={() => handleActionClick(action)}
                            className={`flex items-center space-x-2 w-full text-left p-3 rounded-lg border transition-all duration-200 ${getActionColor(action.type)}`}
                            disabled={isLoading}
                          >
                            {getActionIcon(action.type)}
                            <div className="flex-1">
                              <div className="font-medium text-sm">{action.label}</div>
                              <div className="text-xs opacity-75">{action.description}</div>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Message actions */}
                    {hoveredMessage === message.id && (
                      <div className={`flex items-center space-x-2 mt-2 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <button
                          onClick={() => copyMessage(message.text)}
                          className="text-gray-400 hover:text-gray-600 p-1 rounded transition-colors"
                          title="Copy message"
                        >
                          <Copy size={14} />
                        </button>
                        {message.sender === 'bot' && (
                          <>
                            <button
                              className="text-gray-400 hover:text-green-600 p-1 rounded transition-colors"
                              title="Good response"
                            >
                              <ThumbsUp size={14} />
                            </button>
                            <button
                              className="text-gray-400 hover:text-red-600 p-1 rounded transition-colors"
                              title="Poor response"
                            >
                              <ThumbsDown size={14} />
                            </button>
                          </>
                        )}
                        <span className="text-xs text-gray-400">
                          {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      </div>
                    )}
                  </div>

                  {message.sender === 'user' && (
                    <div className="w-8 h-8 sm:w-10 sm:h-10 bg-indigo-300 rounded-full items-center justify-center flex-shrink-0 hidden mr-1 sm:flex">
                          <svg
                            className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                          </svg>
                        </div>
                  )}
                </div>
              ))}

              {/* Typing indicator */}
              {isLoading && (
                <div className="flex justify-start">
                 <div className="w-10 h-10 bg-[#f8f8fa] rounded-full flex items-center justify-center mr-4 mt-1 flex-shrink-0 self-start">
                     <img
                      src="/favicon1.png"
                      alt="HuddleUp"
                      className="w-5 h-5 object-contain"
                    />
                  </div>
                  <div className="bg-gray-50 border border-gray-100 p-4 rounded-2xl rounded-bl-md shadow-sm">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4 bg-gray-50 rounded-b-2xl">
            <div className="flex items-end space-x-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputMessage}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  onClick={() => inputRef.current?.focus()}
                  placeholder="Ask me anything about HuddleUp..."
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-[#182978] focus:border-transparent text-sm resize-none transition-all duration-200 bg-white shadow-sm"
                  disabled={isLoading}
                  rows={1}
                  style={{ minHeight: '44px', maxHeight: '120px' }}
                  tabIndex={0}
                  autoFocus={true}
                />
                <div className="absolute right-2 bottom-2 text-xs text-gray-400">
                  {inputMessage.length > 0 && `${inputMessage.length}/1000`}
                </div>
              </div>
              <button
                onClick={handleSendMessage}
                disabled={isLoading || inputMessage.trim() === ''}
                className="bg-[#182978] hover:bg-[#14205F] disabled:bg-gray-400 text-white p-3 rounded-xl transition-all duration-200 shadow-md hover:shadow-lg disabled:cursor-not-allowed flex items-center justify-center"
                aria-label="Send message"
              >
                <Send size={16} className={isLoading ? 'animate-pulse' : ''} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatWidget;