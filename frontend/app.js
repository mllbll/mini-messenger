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

// DOM Elements
const authScreen = document.getElementById('authScreen');
const appScreen = document.getElementById('appScreen');
const authForm = document.getElementById('authForm');
const authBtn = document.getElementById('authBtn');
const switchMode = document.getElementById('switchMode');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const userName = document.getElementById('userName');
const userAvatar = document.getElementById('userAvatar');
const chatsList = document.getElementById('chatsList');
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatName = document.getElementById('chatName');
const chatAvatar = document.getElementById('chatAvatar');
const chatStatus = document.getElementById('chatStatus');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
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
    authForm.addEventListener('submit', handleAuth);
    switchMode.addEventListener('click', toggleAuthMode);
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});

// Auth functions
function showAuth() {
    authScreen.style.display = 'flex';
    appScreen.style.display = 'none';
}

async function showApp() {
    authScreen.style.display = 'none';
    appScreen.style.display = 'flex';
    userName.textContent = currentUser.username;
    userAvatar.textContent = currentUser.username.charAt(0).toUpperCase();
    
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

        const data = await response.json();

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
            showError(data.detail || 'Authentication failed');
        }
    } catch (error) {
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
            const errorText = await response.text();
            console.error('Error response:', errorText);
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
        
        chatElement.innerHTML = `
            <div class="chat-avatar">${(chat.name || 'C').charAt(0).toUpperCase()}</div>
            <div class="chat-info">
                <div class="chat-name">${chat.name || `Chat ${chat.id}`}</div>
                <div class="chat-preview">No messages yet</div>
            </div>
            <div class="chat-time">${timeDisplay}</div>
        `;
        
        chatElement.addEventListener('click', (event) => selectChat(chat, event));
        chatsList.appendChild(chatElement);
    });
}

function selectChat(chat, event = null) {
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
    chatStatus.textContent = 'Online';
    
    // Load messages
    loadMessages(chat.id);
    
    // Connect WebSocket
    connectWebSocket(chat.id);
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
            messages[chatId] = await response.json();
            renderMessages();
        } else {
            console.error('Failed to load messages:', response.status);
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
                <h3>No messages yet</h3>
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
            // Add message to local state immediately
            if (!messages[currentChat.id]) {
                messages[currentChat.id] = [];
            }
            messages[currentChat.id].push(newMessage);
            renderMessages();
            
            // Reload chats to update the order based on last message time
            loadChats();
        } else {
            alert('Failed to send message');
        }
    } catch (error) {
        console.error('Failed to send message:', error);
        alert('Failed to send message');
    }
}

function connectWebSocket(chatId) {
    if (websocket) {
        websocket.close();
    }

    try {
        websocket = new WebSocket(`ws://localhost:8000/ws/chat/${chatId}`);
        
        websocket.onopen = function() {
            console.log('WebSocket connected for chat', chatId);
        };
        
        websocket.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                if (!messages[currentChat.id]) {
                    messages[currentChat.id] = [];
                }
                messages[currentChat.id].push(message);
                renderMessages();
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        websocket.onclose = function() {
            console.log('WebSocket disconnected for chat', chatId);
        };
        
        websocket.onerror = function(error) {
            console.warn('WebSocket connection failed, messages will still work via HTTP:', error);
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

        // Add logout button to user info
        document.addEventListener('DOMContentLoaded', function() {
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

        // Create chat modal
        function showCreateChatModal() {
            const modal = document.getElementById('createChatModal');
            modal.style.display = 'flex';
            
            // Reset forms
            hideAllChatForms();
            document.querySelector('.chat-options').style.display = 'block';
        }


    // User search modal functions
    function showUserSearchModal() {
        const modal = document.getElementById('userSearchModal');
        modal.style.display = 'flex';
        document.getElementById('userSearchInput').focus();
    }

    function closeUserSearchModal() {
        const modal = document.getElementById('userSearchModal');
        modal.style.animation = 'modalFadeOut 0.2s ease-in';
        setTimeout(() => {
            modal.style.display = 'none';
            modal.style.animation = '';
        }, 200);
        document.getElementById('userSearchInput').value = '';
        document.getElementById('searchResults').style.display = 'none';
        document.getElementById('usersList').innerHTML = '';
    }

    async function searchUsers() {
        const username = document.getElementById('userSearchInput').value.trim();
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
                alert('Failed to search users');
            }
        } catch (error) {
            console.error('Failed to search users:', error);
            alert('Failed to search users');
        }
    }

    function displaySearchResults(users) {
        const searchResults = document.getElementById('searchResults');
        const usersList = document.getElementById('usersList');
        
        if (users.length === 0) {
            usersList.innerHTML = '<p style="text-align: center; color: #718096; padding: 20px;">No users found</p>';
        } else {
            usersList.innerHTML = '';
            users.forEach(user => {
                const userElement = document.createElement('div');
                userElement.className = 'user-item';
                userElement.innerHTML = `
                    <div class="user-avatar-small">${user.username.charAt(0).toUpperCase()}</div>
                    <div class="user-info">
                        <div class="user-name">${user.username}</div>
                    </div>
                    <div class="user-actions">
                        <button class="btn btn-sm btn-primary" onclick="startChatWithUser(${user.id}, '${user.username}')">
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

            if (response.ok) {
                const newChat = await response.json();
                chats.push(newChat);
                renderChats();
                selectChat(newChat);
                closeUserSearchModal();
            } else {
                alert('Failed to create chat');
            }
        } catch (error) {
            console.error('Failed to create chat:', error);
            alert('Failed to create chat');
        }
    }


    // Close modal when clicking outside
    document.addEventListener('click', function(event) {
        const modal = document.getElementById('userSearchModal');
        if (event.target === modal) {
            closeUserSearchModal();
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
                
                if (userSearchModal.style.display === 'flex') {
                    closeUserSearchModal();
                }
                if (createChatModal.style.display === 'flex') {
                    closeCreateChatModal();
                }
            }
        });
    });

    // Create Chat Modal Functions
    function closeCreateChatModal() {
        const modal = document.getElementById('createChatModal');
        modal.style.animation = 'modalFadeOut 0.2s ease-in';
        setTimeout(() => {
            modal.style.display = 'none';
            modal.style.animation = '';
        }, 200);
        hideAllChatForms();
        document.querySelector('.chat-options').style.display = 'block';
        
        // Reset modal title
        document.querySelector('#createChatModal .modal-header h3').textContent = 'Создать чат';
        
        // Clear all form inputs
        document.getElementById('publicChatName').value = '';
        document.getElementById('privateChatUsername').value = '';
        document.getElementById('quickMessageUsername').value = '';
        document.getElementById('quickMessageText').value = '';
    }

    function hideAllChatForms() {
        document.getElementById('createPublicChatForm').style.display = 'none';
        document.getElementById('createPrivateChatForm').style.display = 'none';
        document.getElementById('quickMessageForm').style.display = 'none';
    }

    function showCreatePublicChatForm() {
        const modal = document.getElementById('createChatModal');
        modal.style.display = 'flex';
        hideAllChatForms();
        document.querySelector('.chat-options').style.display = 'none';
        document.getElementById('createPublicChatForm').style.display = 'block';
        
        // Update modal title
        document.querySelector('#createChatModal .modal-header h3').textContent = 'Создать публичный чат';
        
        // Focus on input field
        setTimeout(() => {
            document.getElementById('publicChatName').focus();
        }, 100);
    }

    function showCreatePrivateChatForm() {
        const modal = document.getElementById('createChatModal');
        modal.style.display = 'flex';
        hideAllChatForms();
        document.querySelector('.chat-options').style.display = 'none';
        document.getElementById('createPrivateChatForm').style.display = 'block';
        
        // Update modal title
        document.querySelector('#createChatModal .modal-header h3').textContent = 'Создать приватный чат';
        
        // Focus on input field
        setTimeout(() => {
            document.getElementById('privateChatUsername').focus();
        }, 100);
    }

    function showQuickMessageForm() {
        const modal = document.getElementById('createChatModal');
        modal.style.display = 'flex';
        hideAllChatForms();
        document.querySelector('.chat-options').style.display = 'none';
        document.getElementById('quickMessageForm').style.display = 'block';
        
        // Update modal title
        document.querySelector('#createChatModal .modal-header h3').textContent = 'Быстрое сообщение';
        
        // Focus on input field
        setTimeout(() => {
            document.getElementById('quickMessageUsername').focus();
        }, 100);
    }

    async function createPublicChat() {
        const chatName = document.getElementById('publicChatName').value.trim();
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
                chats.push(newChat);
                renderChats();
                selectChat(newChat);
                closeCreateChatModal();
            } else {
                alert('Failed to create chat');
            }
        } catch (error) {
            console.error('Failed to create chat:', error);
            alert('Failed to create chat');
        }
    }

    async function createPrivateChatFromModal() {
        const username = document.getElementById('privateChatUsername').value.trim();
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
                chats.push(newChat);
                renderChats();
                selectChat(newChat);
                closeCreateChatModal();
            } else {
                alert('Failed to create private chat');
            }
        } catch (error) {
            console.error('Failed to create private chat:', error);
            alert('Failed to create private chat');
        }
    }

    async function sendQuickMessageFromModal() {
        const username = document.getElementById('quickMessageUsername').value.trim();
        const message = document.getElementById('quickMessageText').value.trim();
        
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
                chats.push(newChat);
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
                    renderMessages();
                }
            } else {
                alert('Failed to create private chat');
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
