#!/usr/bin/env python3
"""
Cleanup script to remove ChatMember records that were incorrectly added by migration.
This script removes members from chats they didn't create and aren't part of private chats with.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import Chat, User, ChatMember, Message

def cleanup_chat_members():
    """Remove ChatMember records for users who shouldn't be in chats."""
    db = SessionLocal()
    
    try:
        # Get all chats
        chats = db.query(Chat).all()
        
        print(f"Found {len(chats)} chats")
        
        removed_count = 0
        for chat in chats:
            # Get all members of this chat
            members = db.query(ChatMember).filter(ChatMember.chat_id == chat.id).all()
            member_ids = [m.user_id for m in members]
            
            # Get users who sent messages in this chat
            message_senders = db.query(Message.user_id).filter(
                Message.chat_id == chat.id
            ).distinct().all()
            sender_ids = [m[0] for m in message_senders]
            
            # Determine valid members:
            # 1. Users who sent messages in the chat
            # 2. For private chats (2 members), keep both members
            # 3. For public chats, keep message senders
            
            valid_member_ids = set()
            
            if len(member_ids) == 2:
                # Private chat - keep both members
                valid_member_ids = set(member_ids)
            else:
                # Public chat - keep only message senders
                valid_member_ids = set(sender_ids)
            
            # Remove invalid members
            for member in members:
                if member.user_id not in valid_member_ids:
                    user = db.query(User).filter(User.id == member.user_id).first()
                    print(f"Removing user {user.username if user else member.user_id} (ID: {member.user_id}) from chat '{chat.name}' (ID: {chat.id})")
                    db.delete(member)
                    removed_count += 1
        
        db.commit()
        print(f"\nCleanup complete! Removed {removed_count} invalid ChatMember records.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting ChatMember cleanup...")
    cleanup_chat_members()

