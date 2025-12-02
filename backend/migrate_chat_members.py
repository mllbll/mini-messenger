#!/usr/bin/env python3
"""
Migration script to add ChatMember records for existing chats.
This script adds all users as members of all existing chats.
Run this once to migrate existing data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, engine
from app.models import Chat, User, ChatMember, Base

def migrate_chat_members():
    """Add ChatMember records for all existing chats and users."""
    db = SessionLocal()
    
    try:
        # Get all chats
        chats = db.query(Chat).all()
        # Get all users
        users = db.query(User).all()
        
        print(f"Found {len(chats)} chats and {len(users)} users")
        
        added_count = 0
        for chat in chats:
            for user in users:
                # Check if ChatMember already exists
                existing = db.query(ChatMember).filter(
                    ChatMember.chat_id == chat.id,
                    ChatMember.user_id == user.id
                ).first()
                
                if not existing:
                    member = ChatMember(chat_id=chat.id, user_id=user.id)
                    db.add(member)
                    added_count += 1
                    print(f"Added user {user.username} (ID: {user.id}) to chat '{chat.name}' (ID: {chat.id})")
        
        db.commit()
        print(f"\nMigration complete! Added {added_count} ChatMember records.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting ChatMember migration...")
    migrate_chat_members()

