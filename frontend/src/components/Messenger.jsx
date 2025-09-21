import React, { useState } from 'react';
import { LogOut, Settings, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ChatList from './ChatList';
import Chat from './Chat';
import { chatsAPI } from '../api/client';

const Messenger = () => {
  const { user, logout } = useAuth();
  const [selectedChat, setSelectedChat] = useState(null);
  const [showCreateChat, setShowCreateChat] = useState(false);
  const [newChatName, setNewChatName] = useState('');

  const handleChatSelect = (chat) => {
    setSelectedChat(chat);
  };

  const handleCreateChat = () => {
    setShowCreateChat(true);
  };

  const createChat = async (e) => {
    e.preventDefault();
    if (!newChatName.trim()) return;

    try {
      const response = await chatsAPI.createChat(newChatName.trim());
      setSelectedChat(response.data);
      setNewChatName('');
      setShowCreateChat(false);
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <span className="text-white font-medium text-sm">
                {user?.username?.charAt(0) || 'U'}
              </span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Mini Messenger</h1>
              <p className="text-sm text-gray-500">Welcome, {user?.username}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <User className="w-5 h-5 text-gray-600" />
            </button>
            <button
              onClick={logout}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 flex-shrink-0">
          <ChatList
            selectedChat={selectedChat}
            onChatSelect={handleChatSelect}
            onCreateChat={handleCreateChat}
          />
        </div>

        {/* Chat Area */}
        <div className="flex-1">
          <Chat chat={selectedChat} currentUser={user} />
        </div>
      </div>

      {/* Create Chat Modal */}
      {showCreateChat && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Chat</h3>
            <form onSubmit={createChat}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Chat Name
                </label>
                <input
                  type="text"
                  value={newChatName}
                  onChange={(e) => setNewChatName(e.target.value)}
                  className="input-field"
                  placeholder="Enter chat name..."
                  autoFocus
                />
              </div>
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateChat(false)}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newChatName.trim()}
                  className="flex-1 btn-primary disabled:opacity-50"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Messenger;
