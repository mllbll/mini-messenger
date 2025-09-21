import React, { useState, useEffect } from 'react';
import { MessageCircle, Plus, Search, MoreVertical } from 'lucide-react';
import { chatsAPI } from '../api/client';

const ChatList = ({ selectedChat, onChatSelect, onCreateChat }) => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadChats();
  }, []);

  const loadChats = async () => {
    try {
      const response = await chatsAPI.getChats();
      setChats(response.data);
    } catch (error) {
      console.error('Failed to load chats:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredChats = chats.filter(chat =>
    chat.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="chat-sidebar flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Chats</h2>
          <button
            onClick={onCreateChat}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="New Chat"
          >
            <Plus className="w-5 h-5 text-gray-600" />
          </button>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search chats..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center text-gray-500">
            <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading chats...
          </div>
        ) : filteredChats.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p className="text-sm">
              {searchTerm ? 'No chats found' : 'No chats yet'}
            </p>
            {!searchTerm && (
              <button
                onClick={onCreateChat}
                className="mt-2 text-primary-600 hover:text-primary-700 text-sm font-medium"
              >
                Create your first chat
              </button>
            )}
          </div>
        ) : (
          <div className="p-2">
            {filteredChats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => onChatSelect(chat)}
                className={`p-3 rounded-lg cursor-pointer transition-colors mb-1 ${
                  selectedChat?.id === chat.id
                    ? 'bg-primary-50 border border-primary-200'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <MessageCircle className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {chat.name || `Chat ${chat.id}`}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {chat.lastMessage || 'No messages yet'}
                    </p>
                  </div>
                  <button className="p-1 hover:bg-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreVertical className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatList;
