"""
Unit tests for authentication module.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # bcrypt should produce different salts


class TestTokenCreation:
    """Test JWT token creation and validation."""
    
    def test_create_access_token_default_expiry(self):
        """Test token creation with default expiry."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Test token creation with custom expiry."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=5)
        token = create_access_token(data, expires_delta)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta
        
        # Allow 1 second tolerance
        assert abs((exp_time - expected_time).total_seconds()) < 1
    
    def test_token_expiry(self):
        """Test that token expires correctly."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=1)
        token = create_access_token(data, expires_delta)
        
        # Token should be valid immediately
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        
        # After expiry, token should be invalid
        import time
        time.sleep(2)
        
        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    def test_token_with_invalid_secret(self):
        """Test token validation with invalid secret."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret", algorithms=[ALGORITHM])
    
    def test_token_with_wrong_algorithm(self):
        """Test token validation with wrong algorithm."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=["HS512"])
    
    def test_token_missing_subject(self):
        """Test token without subject field."""
        data = {"user_id": 123}
        token = create_access_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "sub" not in payload
        assert payload["user_id"] == 123


class TestSecurityConstants:
    """Test security-related constants."""
    
    def test_secret_key_not_default(self):
        """Test that secret key is not the default value."""
        assert SECRET_KEY != "your-secret-key"
        assert len(SECRET_KEY) >= 16
    
    def test_algorithm_is_secure(self):
        """Test that algorithm is secure."""
        assert ALGORITHM == "HS256"
    
    def test_token_expiry_reasonable(self):
        """Test that token expiry is reasonable."""
        assert 5 <= ACCESS_TOKEN_EXPIRE_MINUTES <= 60
