import React, { useState, useEffect, useRef } from 'react';
import { Send, Smile, Paperclip, MoreVertical } from 'lucide-react';
import { format } from 'date-fns';
import { messagesAPI, createWebSocketConnection } from '../api/client';

const Chat = ({ chat, currentUser }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (chat) {
      loadMessages();
      connectWebSocket();
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [chat]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadMessages = async () => {
    if (!chat) return;
    
    setLoading(true);
    try {
      const response = await messagesAPI.getMessages(chat.id);
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    if (!chat) return;

    const websocket = createWebSocketConnection(chat.id);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setMessages(prev => [...prev, message]);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(websocket);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !chat) return;

    const messageData = {
      chat_id: chat.id,
      content: newMessage.trim(),
    };

    try {
      await messagesAPI.sendMessage(messageData);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  if (!chat) {
    return (
      <div className="chat-main flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Send className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium mb-2">Select a chat</h3>
          <p className="text-sm">Choose a chat from the sidebar to start messaging</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-main">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-primary-600 font-medium">
                {chat.name?.charAt(0) || 'C'}
              </span>
            </div>
            <div>
              <h3 className="font-medium text-gray-900">
                {chat.name || `Chat ${chat.id}`}
              </h3>
              <p className="text-sm text-gray-500">Online</p>
            </div>
          </div>
          <button className="p-2 hover:bg-gray-100 rounded-lg">
            <MoreVertical className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading ? (
          <div className="text-center text-gray-500">
            <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading messages...
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-gray-500">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.user_id === 1 ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`message-bubble ${
                  message.user_id === 1 ? 'message-sent' : 'message-received'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p className={`text-xs mt-1 ${
                  message.user_id === 1 ? 'text-primary-100' : 'text-gray-500'
                }`}>
                  {format(new Date(message.timestamp), 'HH:mm')}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={sendMessage} className="flex items-center space-x-2">
          <button
            type="button"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Paperclip className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1 relative">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type a message..."
              className="w-full px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
            >
              <Smile className="w-5 h-5 text-gray-600" />
            </button>
          </div>
          <button
            type="submit"
            disabled={!newMessage.trim()}
            className="p-2 bg-primary-600 text-white rounded-full hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat;
