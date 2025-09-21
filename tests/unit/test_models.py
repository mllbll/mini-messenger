"""
Unit tests for database models.
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from backend.app.models import User, Chat, ChatMember, Message
from backend.app.db import Base


class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, test_db_session):
        """Test creating a user."""
        user = User(
            username="testuser",
            password_hash="hashed_password"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
    
    def test_user_unique_username(self, test_db_session):
        """Test that usernames must be unique."""
        user1 = User(username="testuser", password_hash="hash1")
        user2 = User(username="testuser", password_hash="hash2")
        
        test_db_session.add(user1)
        test_db_session.commit()
        
        test_db_session.add(user2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_user_username_required(self, test_db_session):
        """Test that username is required."""
        user = User(password_hash="hashed_password")
        test_db_session.add(user)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_user_password_hash_required(self, test_db_session):
        """Test that password_hash is required."""
        user = User(username="testuser")
        test_db_session.add(user)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestChatModel:
    """Test Chat model functionality."""
    
    def test_create_chat(self, test_db_session):
        """Test creating a chat."""
        chat = Chat(name="Test Chat")
        test_db_session.add(chat)
        test_db_session.commit()
        
        assert chat.id is not None
        assert chat.name == "Test Chat"
        assert chat.last_message_time is not None
    
    def test_create_chat_without_name(self, test_db_session):
        """Test creating a chat without name."""
        chat = Chat()
        test_db_session.add(chat)
        test_db_session.commit()
        
        assert chat.id is not None
        assert chat.name is None
    
    def test_chat_last_message_time_default(self, test_db_session):
        """Test that last_message_time has default value."""
        chat = Chat(name="Test Chat")
        test_db_session.add(chat)
        test_db_session.commit()
        
        assert chat.last_message_time is not None
        assert isinstance(chat.last_message_time, datetime)


class TestChatMemberModel:
    """Test ChatMember model functionality."""
    
    def test_create_chat_member(self, test_db_session):
        """Test creating a chat member."""
        user = User(username="testuser", password_hash="hash")
        chat = Chat(name="Test Chat")
        test_db_session.add(user)
        test_db_session.add(chat)
        test_db_session.commit()
        
        member = ChatMember(chat_id=chat.id, user_id=user.id)
        test_db_session.add(member)
        test_db_session.commit()
        
        assert member.id is not None
        assert member.chat_id == chat.id
        assert member.user_id == user.id
    
    def test_chat_member_foreign_keys(self, test_db_session):
        """Test that foreign keys are required."""
        member = ChatMember()
        test_db_session.add(member)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestMessageModel:
    """Test Message model functionality."""
    
    def test_create_message(self, test_db_session):
        """Test creating a message."""
        user = User(username="testuser", password_hash="hash")
        chat = Chat(name="Test Chat")
        test_db_session.add(user)
        test_db_session.add(chat)
        test_db_session.commit()
        
        message = Message(
            chat_id=chat.id,
            user_id=user.id,
            content="Hello, world!"
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        assert message.id is not None
        assert message.chat_id == chat.id
        assert message.user_id == user.id
        assert message.content == "Hello, world!"
        assert message.timestamp is not None
    
    def test_message_timestamp_default(self, test_db_session):
        """Test that timestamp has default value."""
        user = User(username="testuser", password_hash="hash")
        chat = Chat(name="Test Chat")
        test_db_session.add(user)
        test_db_session.add(chat)
        test_db_session.commit()
        
        message = Message(
            chat_id=chat.id,
            user_id=user.id,
            content="Test message"
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        assert message.timestamp is not None
        assert isinstance(message.timestamp, datetime)
    
    def test_message_required_fields(self, test_db_session):
        """Test that required fields are enforced."""
        message = Message()
        test_db_session.add(message)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestModelRelationships:
    """Test model relationships."""
    
    def test_user_chat_relationship(self, test_db_session):
        """Test user-chat relationship through ChatMember."""
        user = User(username="testuser", password_hash="hash")
        chat = Chat(name="Test Chat")
        test_db_session.add(user)
        test_db_session.add(chat)
        test_db_session.commit()
        
        member = ChatMember(chat_id=chat.id, user_id=user.id)
        test_db_session.add(member)
        test_db_session.commit()
        
        # Test that we can query relationships
        user_chats = test_db_session.query(Chat).join(ChatMember).filter(
            ChatMember.user_id == user.id
        ).all()
        
        assert len(user_chats) == 1
        assert user_chats[0].id == chat.id
    
    def test_chat_messages_relationship(self, test_db_session):
        """Test chat-messages relationship."""
        user = User(username="testuser", password_hash="hash")
        chat = Chat(name="Test Chat")
        test_db_session.add(user)
        test_db_session.add(chat)
        test_db_session.commit()
        
        message1 = Message(chat_id=chat.id, user_id=user.id, content="Message 1")
        message2 = Message(chat_id=chat.id, user_id=user.id, content="Message 2")
        test_db_session.add(message1)
        test_db_session.add(message2)
        test_db_session.commit()
        
        # Test that we can query chat messages
        chat_messages = test_db_session.query(Message).filter(
            Message.chat_id == chat.id
        ).all()
        
        assert len(chat_messages) == 2
        assert chat_messages[0].content == "Message 1"
        assert chat_messages[1].content == "Message 2"
