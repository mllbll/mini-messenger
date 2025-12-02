// Global state
let currentUser = null;
let currentUserId = null;
let currentChat = null;
let chats = [];
let messages = {};
let isLoginMode = true;
let websocket = null;
let token = null;

// API Base URL
const API_BASE = 'http://localhost:8000';

// DOM Elements - will be initialized in DOMContentLoaded
let authScreen, appScreen, authForm, authBtn, switchMode, errorMessage, successMessage;
let userName, userAvatar, chatsList, messagesContainer, messageInput, sendBtn;
let chatName, chatAvatar, chatStatus;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM elements
    authScreen = document.getElementById('authScreen');
    appScreen = document.getElementById('appScreen');
    authForm = document.getElementById('authForm');
    authBtn = document.getElementById('authBtn');
    switchMode = document.getElementById('switchMode');
    errorMessage = document.getElementById('errorMessage');
    successMessage = document.getElementById('successMessage');
    userName = document.getElementById('userName');
    userAvatar = document.getElementById('userAvatar');
    chatsList = document.getElementById('chatsList');
    messagesContainer = document.getElementById('messagesContainer');
    messageInput = document.getElementById('messageInput');
    sendBtn = document.getElementById('sendBtn');
    chatName = document.getElementById('chatName');
    chatAvatar = document.getElementById('chatAvatar');
    chatStatus = document.getElementById('chatStatus');
    
    // Ensure modals are closed on page load
    const createChatModal = document.getElementById('createChatModal');
    const userSearchModal = document.getElementById('userSearchModal');
    if (createChatModal) {
        createChatModal.classList.remove('show');
        createChatModal.style.display = 'none';
    }
    if (userSearchModal) {
        userSearchModal.classList.remove('show');
        userSearchModal.style.display = 'none';
    }
    
    // Check if user is already logged in
    token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('currentUser');
    
    console.log('Initializing app...');
    console.log('Token:', token);
    console.log('Saved user:', savedUser);
    
    if (token && savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            console.log('Restored user:', currentUser);
            showApp();
            loadChats();
        } catch (error) {
            console.error('Error parsing saved user:', error);
            localStorage.removeItem('token');
            localStorage.removeItem('currentUser');
            token = null;
            showAuth();
        }
    } else {
        console.log('No saved session, showing auth');
        showAuth();
    }

    // Event listeners
    if (authForm) {
        authForm.addEventListener('submit', handleAuth);
    }
    if (switchMode) {
        switchMode.addEventListener('click', toggleAuthMode);
    }
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Add logout button to user info
    const userInfo = document.querySelector('.user-info');
    if (userInfo) {
        const logoutBtn = document.createElement('button');
        logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i>';
        logoutBtn.className = 'action-btn';
        logoutBtn.title = 'Logout';
        logoutBtn.style.marginLeft = 'auto';
        logoutBtn.addEventListener('click', logout);
        userInfo.appendChild(logoutBtn);
    }
});

// Auth functions
function showAuth() {
    if (authScreen) {
        authScreen.style.display = 'flex';
    }
    if (appScreen) {
        appScreen.style.display = 'none';
    }
}

async function showApp() {
    if (authScreen) {
        authScreen.style.display = 'none';
    }
    if (appScreen) {
        appScreen.style.display = 'flex';
    }
    if (userName && currentUser) {
        userName.textContent = currentUser.username;
    }
    if (userAvatar && currentUser) {
        userAvatar.textContent = currentUser.username.charAt(0).toUpperCase();
    }
    
    // Get current user info to get the user ID
    await getCurrentUserInfo();
}

function toggleAuthMode(e) {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    authBtn.textContent = isLoginMode ? 'Sign In' : 'Sign Up';
    switchMode.textContent = isLoginMode 
        ? "Don't have an account? Sign up" 
        : "Already have an account? Sign in";
    hideMessages();
}

async function handleAuth(e) {
    e.preventDefault();
    hideMessages();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showError('Please fill in all fields');
        return;
    }

    try {
        authBtn.textContent = 'Loading...';
        authBtn.disabled = true;

        const endpoint = isLoginMode ? '/api/users/login' : '/api/users/register';
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            // If response is not JSON, try to get text
            const text = await response.text();
            showError(text || 'Authentication failed');
            return;
        }

        if (response.ok) {
            if (isLoginMode) {
                token = data.access_token;
                console.log('Token received and set:', token);
                localStorage.setItem('token', token);
                currentUser = { username };
                localStorage.setItem('currentUser', JSON.stringify(currentUser));
                console.log('User data saved:', currentUser);
                showApp();
                loadChats();
            } else {
                showSuccess('Account created successfully! Please sign in.');
                toggleAuthMode({ preventDefault: () => {} });
            }
        } else {
            // Handle different error formats from FastAPI
            let errorMsg = 'Authentication failed';
            if (data.detail) {
                if (Array.isArray(data.detail)) {
                    // Pydantic validation errors - extract first error message
                    const firstError = data.detail[0];
                    if (firstError) {
                        errorMsg = firstError.msg || firstError.message || 'Validation error';
                        // Remove "Value error, " prefix from Pydantic messages
                        errorMsg = errorMsg.replace(/^Value error,\s*/i, '');
                    }
                } else if (typeof data.detail === 'string') {
                    // Simple string error
                    errorMsg = data.detail;
                } else {
                    // Object error - try to extract message
                    errorMsg = data.detail.message || data.detail.msg || 'Authentication failed';
                }
            } else if (data.message) {
                errorMsg = data.message;
            }
            showError(errorMsg);
        }
    } catch (error) {
        console.error('Auth error:', error);
        showError('Network error. Please try again.');
    } finally {
        authBtn.textContent = isLoginMode ? 'Sign In' : 'Sign Up';
        authBtn.disabled = false;
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}

function hideMessages() {
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';
}

// Get current user info
async function getCurrentUserInfo() {
    if (!token) {
        console.error('No token available');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/users/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const userInfo = await response.json();
            currentUserId = userInfo.id;
            console.log('Current user ID:', currentUserId);
        } else {
            console.error('Failed to get current user info:', response.status);
        }
    } catch (error) {
        console.error('Failed to get current user info:', error);
    }
}

// Chat functions
async function loadChats() {
    console.log('loadChats called, token:', token);
    if (!token) {
        console.error('No token available');
        return;
    }

    try {
        console.log('Making request to:', `${API_BASE}/api/chats/`);
        console.log('Authorization header:', `Bearer ${token}`);
        
        const response = await fetch(`${API_BASE}/api/chats/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            chats = await response.json();
            console.log('Chats loaded:', chats);
            renderChats();
        } else {
            console.error('Failed to load chats:', response.status);
            if (response.status === 401) {
                // Token expired or invalid
                token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showAuth();
            } else {
                const errorText = await response.text().catch(() => 'Unknown error');
                console.error('Error response:', errorText);
            }
        }
    } catch (error) {
        console.error('Failed to load chats:', error);
    }
}

function renderChats() {
    chatsList.innerHTML = '';
    
    if (chats.length === 0) {
        chatsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comments"></i>
                <h3>No chats yet</h3>
                <p>Create your first chat to get started</p>
            </div>
        `;
        return;
    }

    chats.forEach(chat => {
        const chatElement = document.createElement('div');
        chatElement.className = 'chat-item';
        chatElement.setAttribute('data-chat-id', chat.id);
        
        // Format last message time
        let timeDisplay = 'Now';
        if (chat.last_message_time) {
            const lastMessageTime = new Date(chat.last_message_time);
            const now = new Date();
            const diffInMinutes = Math.floor((now - lastMessageTime) / (1000 * 60));
            
            if (diffInMinutes < 1) {
                timeDisplay = 'Now';
            } else if (diffInMinutes < 60) {
                timeDisplay = `${diffInMinutes}m`;
            } else if (diffInMinutes < 1440) { // 24 hours
                timeDisplay = `${Math.floor(diffInMinutes / 60)}h`;
            } else {
                timeDisplay = lastMessageTime.toLocaleDateString();
            }
        }
        
        // Get last message preview - will be loaded asynchronously
        let lastMessagePreview = '';
        if (messages[chat.id] && messages[chat.id].length > 0) {
            const lastMessage = messages[chat.id][messages[chat.id].length - 1];
            lastMessagePreview = lastMessage.content.length > 50 
                ? lastMessage.content.substring(0, 50) + '...' 
                : lastMessage.content;
        }
        
        chatElement.innerHTML = `
            <div class="chat-avatar">${(chat.name || 'C').charAt(0).toUpperCase()}</div>
            <div class="chat-info">
                <div class="chat-name">${chat.name || `Chat ${chat.id}`}</div>
                <div class="chat-preview">${lastMessagePreview}</div>
            </div>
            <div class="chat-time">${timeDisplay}</div>
        `;
        
        chatElement.addEventListener('click', (event) => selectChat(chat, event));
        chatsList.appendChild(chatElement);
        
        // Load last message if not in cache
        if (!messages[chat.id] || messages[chat.id].length === 0) {
            loadLastMessage(chat.id).then(lastMsg => {
                if (lastMsg) {
                    const previewElement = chatElement.querySelector('.chat-preview');
                    if (previewElement) {
                        const preview = lastMsg.content.length > 50 
                            ? lastMsg.content.substring(0, 50) + '...' 
                            : lastMsg.content;
                        previewElement.textContent = preview;
                    }
                }
            });
        }
    });
}

// Update chat preview in the list
function updateChatPreview(chatId) {
    if (!messages[chatId] || messages[chatId].length === 0) return;
    
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        const lastMessage = messages[chatId][messages[chatId].length - 1];
        const previewElement = chatElement.querySelector('.chat-preview');
        if (previewElement) {
            const preview = lastMessage.content.length > 50 
                ? lastMessage.content.substring(0, 50) + '...' 
                : lastMessage.content;
            previewElement.textContent = preview;
        }
    }
}

function selectChat(chat, event = null) {
    if (!chat || !chat.id) {
        console.error('selectChat: Invalid chat object', chat);
        return;
    }
    currentChat = chat;
    
    // Update UI
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Only add active class if we have an event (clicked by user)
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    } else {
        // Find the chat element and make it active
        const chatElements = document.querySelectorAll('.chat-item');
        chatElements.forEach(element => {
            const chatId = element.getAttribute('data-chat-id');
            if (chatId && parseInt(chatId) === chat.id) {
                element.classList.add('active');
            }
        });
    }
    
    chatName.textContent = chat.name || `Chat ${chat.id}`;
    chatAvatar.textContent = (chat.name || 'C').charAt(0).toUpperCase();
    
    // Load messages and update status with last message
    if (chat && chat.id) {
        loadMessages(chat.id);
        connectWebSocket(chat.id);
        // Update chatStatus with last message
        updateChatStatus(chat.id);
    } else {
        console.error('selectChat: chat or chat.id is missing', chat);
    }
}

// Load last message for a chat
async function loadLastMessage(chatId) {
    if (!token) return null;
    
    try {
        const response = await fetch(`${API_BASE}/api/messages/${chatId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            const messagesList = await response.json();
            if (messagesList && messagesList.length > 0) {
                // Sort and return last message
                messagesList.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                return messagesList[messagesList.length - 1];
            }
        }
    } catch (error) {
        console.error('Failed to load last message:', error);
    }
    return null;
}

// Update chat status with last message
async function updateChatStatus(chatId) {
    if (!chatId || !chatStatus) return;
    
    // Check if we have messages in cache
    if (messages[chatId] && messages[chatId].length > 0) {
        const lastMessage = messages[chatId][messages[chatId].length - 1];
        chatStatus.textContent = lastMessage.content.length > 100 
            ? lastMessage.content.substring(0, 100) + '...' 
            : lastMessage.content;
    } else {
        // Load last message from API
        const lastMsg = await loadLastMessage(chatId);
        if (lastMsg) {
            chatStatus.textContent = lastMsg.content.length > 100 
                ? lastMsg.content.substring(0, 100) + '...' 
                : lastMsg.content;
        } else {
            chatStatus.textContent = '';
        }
    }
}

async function loadMessages(chatId) {
    if (!token) {
        console.error('No token available');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/messages/${chatId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            const messagesList = await response.json();
            // Sort messages by timestamp
            messagesList.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            messages[chatId] = messagesList;
            renderMessages();
            // Update chat status with last message
            if (currentChat && currentChat.id === chatId) {
                updateChatStatus(chatId);
            }
            // Update chat preview in list
            updateChatPreview(chatId);
        } else {
            console.error('Failed to load messages:', response.status);
            if (response.status === 401) {
                token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showAuth();
            }
        }
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

function renderMessages() {
    if (!currentChat || !messages[currentChat.id]) {
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comments"></i>
                <h3>Select a chat</h3>
                <p>Choose a chat from the sidebar to start messaging</p>
            </div>
        `;
        return;
    }

    const chatMessages = messages[currentChat.id];
    messagesContainer.innerHTML = '';

    if (chatMessages.length === 0) {
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comments"></i>
                <h3></h3>
                <p>Start the conversation!</p>
            </div>
        `;
        return;
    }

    chatMessages.forEach(message => {
        const messageElement = document.createElement('div');
        const isOwnMessage = message.user_id === currentUserId;
        messageElement.className = `message ${isOwnMessage ? 'sent' : 'received'}`;
        
        const time = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageElement.innerHTML = `
            <div class="message-bubble">
                <div class="message-text">${message.content}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
    });

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Send message function
async function sendMessage() {
    if (!currentChat || !messageInput.value.trim()) return;

    const content = messageInput.value.trim();
    messageInput.value = '';

    if (!token) {
        alert('Not authenticated');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/messages/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                chat_id: currentChat.id,
                content: content
            }),
        });

        if (response.ok) {
            const newMessage = await response.json();
            // Add message locally immediately for instant feedback
            // WebSocket will also send it, but we check for duplicates by ID
            if (!messages[currentChat.id]) {
                messages[currentChat.id] = [];
            }
            // Check if message already exists (in case WebSocket was faster)
            const messageExists = messages[currentChat.id].some(m => m.id === newMessage.id);
            if (!messageExists) {
                messages[currentChat.id].push(newMessage);
                // Sort messages by timestamp
                messages[currentChat.id].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                renderMessages();
                // Update chat status with new last message
                updateChatStatus(currentChat.id);
                // Update chat preview in list
                updateChatPreview(currentChat.id);
            }
            
            // Reload chats to update the order based on last message time
            loadChats();
        } else {
            if (response.status === 401) {
                token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showAuth();
                alert('Session expired. Please login again.');
            } else {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to send message' }));
                alert(errorData.detail || 'Failed to send message');
            }
        }
    } catch (error) {
        console.error('Failed to send message:', error);
        alert('Failed to send message');
    }
}

function connectWebSocket(chatId) {
    // Don't close existing connection if it's for the same chat
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        const currentChatId = websocket.url.match(/\/ws\/chat\/(\d+)/)?.[1];
        if (currentChatId && parseInt(currentChatId) === chatId) {
            console.log('WebSocket already connected for this chat, reusing connection');
            return;
        }
        console.log('Closing existing WebSocket connection for different chat');
        websocket.close();
    }

    try {
        // Add token to WebSocket URL as query parameter
        const wsUrl = `ws://localhost:8000/ws/chat/${chatId}?token=${encodeURIComponent(token)}`;
        console.log('Connecting WebSocket to:', wsUrl);
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function() {
            console.log('WebSocket connected successfully for chat', chatId);
            console.log('WebSocket readyState:', websocket.readyState, '(OPEN =', WebSocket.OPEN, ')');
        };
        
        websocket.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                console.log('WebSocket message received:', message);
                
                // Handle message for any chat, not just currentChat
                const chatId = message.chat_id;
                if (chatId) {
                    if (!messages[chatId]) {
                        messages[chatId] = [];
                    }
                    // Check if message already exists (avoid duplicates)
                    const messageExists = messages[chatId].some(m => m.id === message.id);
                    if (!messageExists) {
                        messages[chatId].push(message);
                        // Sort messages by timestamp
                        messages[chatId].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                        
                        console.log('Message added to chat', chatId, 'Total messages:', messages[chatId].length);
                        
                        // If this is the current chat, update UI immediately
                        if (currentChat && currentChat.id === chatId) {
                            console.log('Rendering messages for current chat');
                            renderMessages();
                            // Update chat status with new last message
                            updateChatStatus(chatId);
                        } else {
                            console.log('Message received for different chat:', chatId, 'Current chat:', currentChat?.id);
                        }
                        // Always update chat preview in list
                        updateChatPreview(chatId);
                    } else {
                        console.log('Duplicate message ignored:', message.id);
                    }
                } else {
                    console.warn('Received message without chat_id:', message);
                }
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error, event.data);
            }
        };
        
        websocket.onclose = function(event) {
            console.log('WebSocket disconnected for chat', chatId, 'Code:', event.code, 'Reason:', event.reason);
            // Try to reconnect after a short delay if connection was lost unexpectedly
            if (event.code !== 1000 && currentChat && currentChat.id === chatId) {
                console.log('Attempting to reconnect WebSocket in 2 seconds...');
                setTimeout(() => {
                    if (currentChat && currentChat.id === chatId) {
                        connectWebSocket(chatId);
                    }
                }, 2000);
            }
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            console.warn('WebSocket connection failed, messages will still work via HTTP');
            // Don't show error to user, as HTTP fallback works
        };
    } catch (error) {
        console.warn('WebSocket not available, using HTTP only:', error);
    }
}

// Logout function
function logout() {
    token = null;
    localStorage.removeItem('token');
    localStorage.removeItem('currentUser');
    currentUser = null;
    currentUserId = null;
    currentChat = null;
    chats = [];
    messages = {};
    if (websocket) {
        websocket.close();
        websocket = null;
    }
    showAuth();
}

// Create chat modal
function showCreateChatModal() {
    const modal = document.getElementById('createChatModal');
    if (!modal) return;
    
    modal.classList.add('show');
    modal.style.display = 'flex';
    
    // Reset forms
    hideAllChatForms();
    const chatOptions = document.querySelector('.chat-options');
    if (chatOptions) {
        chatOptions.style.display = 'block';
    }
}

// User search modal functions
function showUserSearchModal() {
    const modal = document.getElementById('userSearchModal');
    if (!modal) return;
    
    modal.classList.add('show');
    modal.style.display = 'flex';
    const input = document.getElementById('userSearchInput');
    if (input) {
        input.focus();
    }
}

function closeUserSearchModal() {
    const modal = document.getElementById('userSearchModal');
    if (!modal) return;
    
    modal.classList.remove('show');
    modal.style.animation = 'modalFadeOut 0.2s ease-in';
    setTimeout(() => {
        modal.style.display = 'none';
        modal.style.animation = '';
    }, 200);
    
    const userSearchInput = document.getElementById('userSearchInput');
    if (userSearchInput) {
        userSearchInput.value = '';
    }
    
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.style.display = 'none';
    }
    
    const usersList = document.getElementById('usersList');
    if (usersList) {
        usersList.innerHTML = '';
    }
}

async function searchUsers() {
    const userSearchInput = document.getElementById('userSearchInput');
    if (!userSearchInput) return;
    
    const username = userSearchInput.value.trim();
    if (!username) {
        alert('Please enter a username to search');
        return;
    }

    if (!token) {
        alert('Not authenticated');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/users/search/${encodeURIComponent(username)}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const users = await response.json();
            displaySearchResults(users);
        } else {
            if (response.status === 401) {
                token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showAuth();
                alert('Session expired. Please login again.');
            } else {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to search users' }));
                alert(errorData.detail || 'Failed to search users');
            }
        }
    } catch (error) {
        console.error('Failed to search users:', error);
        alert('Failed to search users');
    }
}

function displaySearchResults(users) {
    const searchResults = document.getElementById('searchResults');
    const usersList = document.getElementById('usersList');
    
    if (!searchResults || !usersList) return;
    
    if (users.length === 0) {
        usersList.innerHTML = '<p style="text-align: center; color: #718096; padding: 20px;">No users found</p>';
    } else {
        usersList.innerHTML = '';
        users.forEach(user => {
            const userElement = document.createElement('div');
            userElement.className = 'user-item';
            const safeUsername = user.username.replace(/'/g, "\\'");
            userElement.innerHTML = `
                <div class="user-avatar-small">${user.username.charAt(0).toUpperCase()}</div>
                <div class="user-info">
                    <div class="user-name">${user.username}</div>
                </div>
                <div class="user-actions">
                    <button class="btn btn-sm btn-primary" onclick="startChatWithUser(${user.id}, '${safeUsername}')">
                        <i class="fas fa-comment"></i> Чат
                    </button>
                </div>
            `;
            usersList.appendChild(userElement);
        });
    }
    
    searchResults.style.display = 'block';
}

async function startChatWithUser(userId, username) {
    if (!token) {
        alert('Not authenticated');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/chats/?user_id=${userId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            alert(errorData.detail || 'Failed to create chat');
            return;
        }

        const newChat = await response.json();
        if (!newChat || !newChat.id) {
            console.error('Invalid chat response:', newChat);
            alert('Failed to create chat: invalid response');
            return;
        }
        
        // Check if chat already exists in the list
        const existingChat = chats.find(c => c.id === newChat.id);
        if (!existingChat) {
            chats.push(newChat);
        }
        renderChats();
        selectChat(newChat);
        closeUserSearchModal();
    } catch (error) {
        console.error('Failed to create chat:', error);
        alert('Failed to create chat');
    }
}


// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const userSearchModal = document.getElementById('userSearchModal');
    const createChatModal = document.getElementById('createChatModal');
    
    if (userSearchModal && event.target === userSearchModal) {
        closeUserSearchModal();
    }
    if (createChatModal && event.target === createChatModal) {
        closeCreateChatModal();
    }
});

// Search on Enter key and close modals on Escape
document.addEventListener('DOMContentLoaded', function() {
    const userSearchInput = document.getElementById('userSearchInput');
    if (userSearchInput) {
        userSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchUsers();
            }
        });
    }
    
    // Close modals on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const userSearchModal = document.getElementById('userSearchModal');
            const createChatModal = document.getElementById('createChatModal');
            
            if (userSearchModal && userSearchModal.style.display === 'flex') {
                closeUserSearchModal();
            }
            if (createChatModal && createChatModal.style.display === 'flex') {
                closeCreateChatModal();
            }
        }
    });
});

// Create Chat Modal Functions
function closeCreateChatModal() {
    const modal = document.getElementById('createChatModal');
    if (!modal) return;
    
    modal.classList.remove('show');
    modal.style.animation = 'modalFadeOut 0.2s ease-in';
    setTimeout(() => {
        modal.style.display = 'none';
        modal.style.animation = '';
    }, 200);
    
    hideAllChatForms();
    
    const chatOptions = document.querySelector('.chat-options');
    if (chatOptions) {
        chatOptions.style.display = 'block';
    }
    
    // Reset modal title
    const modalTitle = document.querySelector('#createChatModal .modal-header h3');
    if (modalTitle) {
        modalTitle.textContent = 'Создать чат';
    }
    
    // Clear all form inputs
    const publicChatName = document.getElementById('publicChatName');
    if (publicChatName) publicChatName.value = '';
    
    const privateChatUsername = document.getElementById('privateChatUsername');
    if (privateChatUsername) privateChatUsername.value = '';
    
    const quickMessageUsername = document.getElementById('quickMessageUsername');
    if (quickMessageUsername) quickMessageUsername.value = '';
    
    const quickMessageText = document.getElementById('quickMessageText');
    if (quickMessageText) quickMessageText.value = '';
}

function hideAllChatForms() {
    const createPublicChatForm = document.getElementById('createPublicChatForm');
    if (createPublicChatForm) createPublicChatForm.style.display = 'none';
    
    const createPrivateChatForm = document.getElementById('createPrivateChatForm');
    if (createPrivateChatForm) createPrivateChatForm.style.display = 'none';
    
    const quickMessageForm = document.getElementById('quickMessageForm');
    if (quickMessageForm) quickMessageForm.style.display = 'none';
}

function showCreatePublicChatForm() {
    const modal = document.getElementById('createChatModal');
    if (!modal) return;
    
    modal.classList.add('show');
    modal.style.display = 'flex';
    hideAllChatForms();
    
    const chatOptions = document.querySelector('.chat-options');
    if (chatOptions) {
        chatOptions.style.display = 'none';
    }
    
    const createPublicChatForm = document.getElementById('createPublicChatForm');
    if (createPublicChatForm) {
        createPublicChatForm.style.display = 'block';
    }
    
    // Update modal title
    const modalTitle = document.querySelector('#createChatModal .modal-header h3');
    if (modalTitle) {
        modalTitle.textContent = 'Создать публичный чат';
    }
    
    // Focus on input field
    setTimeout(() => {
        const publicChatName = document.getElementById('publicChatName');
        if (publicChatName) {
            publicChatName.focus();
        }
    }, 100);
}

function showCreatePrivateChatForm() {
    const modal = document.getElementById('createChatModal');
    if (!modal) return;
    
    modal.classList.add('show');
    modal.style.display = 'flex';
    hideAllChatForms();
    
    const chatOptions = document.querySelector('.chat-options');
    if (chatOptions) {
        chatOptions.style.display = 'none';
    }
    
    const createPrivateChatForm = document.getElementById('createPrivateChatForm');
    if (createPrivateChatForm) {
        createPrivateChatForm.style.display = 'block';
    }
    
    // Update modal title
    const modalTitle = document.querySelector('#createChatModal .modal-header h3');
    if (modalTitle) {
        modalTitle.textContent = 'Создать приватный чат';
    }
    
    // Focus on input field
    setTimeout(() => {
        const privateChatUsername = document.getElementById('privateChatUsername');
        if (privateChatUsername) {
            privateChatUsername.focus();
        }
    }, 100);
}

function showQuickMessageForm() {
    const modal = document.getElementById('createChatModal');
    if (!modal) return;
    
    modal.classList.add('show');
    modal.style.display = 'flex';
    hideAllChatForms();
    
    const chatOptions = document.querySelector('.chat-options');
    if (chatOptions) {
        chatOptions.style.display = 'none';
    }
    
    const quickMessageForm = document.getElementById('quickMessageForm');
    if (quickMessageForm) {
        quickMessageForm.style.display = 'block';
    }
    
    // Update modal title
    const modalTitle = document.querySelector('#createChatModal .modal-header h3');
    if (modalTitle) {
        modalTitle.textContent = 'Быстрое сообщение';
    }
    
    // Focus on input field
    setTimeout(() => {
        const quickMessageUsername = document.getElementById('quickMessageUsername');
        if (quickMessageUsername) {
            quickMessageUsername.focus();
        }
    }, 100);
}

async function createPublicChat() {
    const publicChatName = document.getElementById('publicChatName');
    if (!publicChatName) return;
    
    const chatName = publicChatName.value.trim();
    if (!chatName) {
        alert('Пожалуйста, введите название чата');
        return;
    }

    if (!token) {
        alert('Not authenticated');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/chats/?name=${encodeURIComponent(chatName)}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const newChat = await response.json();
            // Check if chat already exists in the list
            const existingChat = chats.find(c => c.id === newChat.id);
            if (!existingChat) {
                chats.push(newChat);
            }
            renderChats();
            selectChat(newChat);
            closeCreateChatModal();
        } else {
            if (response.status === 401) {
                token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showAuth();
                alert('Session expired. Please login again.');
            } else {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to create chat' }));
                alert(errorData.detail || 'Failed to create chat');
            }
        }
    } catch (error) {
        console.error('Failed to create chat:', error);
        alert('Failed to create chat');
    }
}

async function createPrivateChatFromModal() {
    const privateChatUsername = document.getElementById('privateChatUsername');
    if (!privateChatUsername) return;
    
    const username = privateChatUsername.value.trim();
    if (!username) {
        alert('Пожалуйста, введите username пользователя');
        return;
    }

    if (!token) {
        alert('Not authenticated');
        return;
    }

    try {
        // First, search for the user
        const searchResponse = await fetch(`${API_BASE}/api/users/search/${encodeURIComponent(username)}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!searchResponse.ok) {
            alert('Failed to search for user');
            return;
        }

        const users = await searchResponse.json();
        if (users.length === 0) {
            alert('User not found');
            return;
        }

        const user = users[0];
        
        // Create private chat with the user
        const response = await fetch(`${API_BASE}/api/chats/?user_id=${user.id}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const newChat = await response.json();
            // Check if chat already exists in the list
            const existingChat = chats.find(c => c.id === newChat.id);
            if (!existingChat) {
                chats.push(newChat);
            }
            renderChats();
            selectChat(newChat);
            closeCreateChatModal();
        } else {
            if (response.status === 401) {
                token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showAuth();
                alert('Session expired. Please login again.');
            } else {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to create private chat' }));
                alert(errorData.detail || 'Failed to create private chat');
            }
        }
    } catch (error) {
        console.error('Failed to create private chat:', error);
        alert('Failed to create private chat');
    }
}

async function sendQuickMessageFromModal() {
    const quickMessageUsername = document.getElementById('quickMessageUsername');
    const quickMessageText = document.getElementById('quickMessageText');
    
    if (!quickMessageUsername || !quickMessageText) return;
    
    const username = quickMessageUsername.value.trim();
    const message = quickMessageText.value.trim();
    
    if (!username) {
        alert('Пожалуйста, введите username пользователя');
        return;
    }
    
    if (!message) {
        alert('Пожалуйста, введите сообщение');
        return;
    }

    if (!token) {
        alert('Not authenticated');
        return;
    }

    try {
        // First, search for the user
        const searchResponse = await fetch(`${API_BASE}/api/users/search/${encodeURIComponent(username)}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!searchResponse.ok) {
            alert('Failed to search for user');
            return;
        }

        const users = await searchResponse.json();
        if (users.length === 0) {
            alert('User not found');
            return;
        }

        const user = users[0];
        
        // Create private chat with the user
        const chatResponse = await fetch(`${API_BASE}/api/chats/?user_id=${user.id}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (chatResponse.ok) {
            const newChat = await chatResponse.json();
            // Check if chat already exists in the list
            const existingChat = chats.find(c => c.id === newChat.id);
            if (!existingChat) {
                chats.push(newChat);
            }
            renderChats();
            selectChat(newChat);
            closeCreateChatModal();
            
            // Send the message immediately
            const messageResponse = await fetch(`${API_BASE}/api/messages/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    chat_id: newChat.id,
                    content: message
                }),
            });

            if (messageResponse.ok) {
                const newMessage = await messageResponse.json();
                if (!messages[newChat.id]) {
                    messages[newChat.id] = [];
                }
                messages[newChat.id].push(newMessage);
                // Sort messages by timestamp
                messages[newChat.id].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                renderMessages();
                // Reload chats to update order
                loadChats();
            } else {
                if (messageResponse.status === 401) {
                    token = null;
                    localStorage.removeItem('token');
                    localStorage.removeItem('currentUser');
                    showAuth();
                    alert('Session expired. Please login again.');
                } else {
                    const errorData = await messageResponse.json().catch(() => ({ detail: 'Failed to send message' }));
                    alert(errorData.detail || 'Failed to send message');
                }
            }
        } else {
            if (chatResponse.status === 401) {
                token = null;
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showAuth();
                alert('Session expired. Please login again.');
            } else {
                const errorData = await chatResponse.json().catch(() => ({ detail: 'Failed to create private chat' }));
                alert(errorData.detail || 'Failed to create private chat');
            }
        }
    } catch (error) {
        console.error('Failed to send quick message:', error);
        alert('Failed to send quick message');
    }
}

    // Close modals when clicking outside
    document.addEventListener('click', function(event) {
        const userSearchModal = document.getElementById('userSearchModal');
        const createChatModal = document.getElementById('createChatModal');
        
        if (event.target === userSearchModal) {
            closeUserSearchModal();
        }
        if (event.target === createChatModal) {
            closeCreateChatModal();
        }
    });
