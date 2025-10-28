import React from 'react';
import { ChatWidget } from './components/ChatWidget';
import chatService from './services/chatService';
import './App.css';

function App() {
  const handleSendMessage = async (message: string): Promise<string> => {
    return await chatService.sendMessage(message);
  };

  return (
<div className="App min-h-screen bg-gray-50">
  <header className="bg-white shadow-sm">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1">
          <img
            src="/logo-huddleup.png"
            alt="HuddleUp"
            className="w-90 h-12  object-contain"
          />
        </div>
      </div>
    </div>
  </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-6">
            Welcome to HuddleUp
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            The community platform that transforms how your organization shares knowledge,
            collaborates, and grows together. More than an LMS - it's where connection meets learning.
          </p>

          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="bg-white p-8 rounded-lg shadow-sm border">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🤝</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Community First</h3>
              <p className="text-gray-600">
                Built around member engagement and peer-to-peer collaboration,
                not just content consumption.
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-sm border">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📚</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Knowledge Sharing</h3>
              <p className="text-gray-600">
                Turn tribal knowledge into searchable, shareable resources
                that grow with your community.
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-sm border">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Process Integration</h3>
              <p className="text-gray-600">
                Enhance your current workflows with collaboration layers
                and automation capabilities.
              </p>
            </div>
          </div>

          <div className="mt-16 bg-blue-50 rounded-xl p-8">
            <h3 className="text-2xl font-semibold mb-4">Have Questions?</h3>
            <p className="text-gray-600 mb-6">
              Our FAQ assistant is here to help! Click the chat icon in the bottom right
              to ask about pricing, features, use cases, or how HuddleUp can improve your current processes.
            </p>
          </div>
        </div>
      </main>

      <ChatWidget />
    </div>
  );
}

export default App;
