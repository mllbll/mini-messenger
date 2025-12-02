import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123456789")  # nosec B101 - default only for development
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize bcrypt - use direct bcrypt due to passlib/bcrypt version compatibility issues
import bcrypt
_use_direct_bcrypt = True
pwd_context = None

def hash_password(password: str) -> str:
    # Bcrypt has a maximum password length of 72 bytes
    # Truncate if necessary before hashing
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    
    if _use_direct_bcrypt:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        try:
            return pwd_context.hash(password)
        except ValueError as e:
            # If still too long, truncate more aggressively
            if "72 bytes" in str(e) or "longer than 72" in str(e):
                password = password[:72] if len(password) > 72 else password
                password_bytes = password.encode('utf-8')
                if len(password_bytes) > 72:
                    password_bytes = password_bytes[:72]
                    password = password_bytes.decode('utf-8', errors='ignore')
                return pwd_context.hash(password)
            raise

def verify_password(plain: str, hashed: str) -> bool:
    # Bcrypt has a maximum password length of 72 bytes
    # Truncate if necessary before verification
    password_bytes = plain.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain = password_bytes.decode('utf-8', errors='ignore')
    
    if _use_direct_bcrypt:
        import bcrypt
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    else:
        return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
