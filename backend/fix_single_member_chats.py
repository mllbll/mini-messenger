#!/usr/bin/env python3
"""
Fix chats with only one member - either add the creator or remove invalid memberships.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import Chat, User, ChatMember, Message

def fix_single_member_chats():
    """Fix chats that have only one member."""
    db = SessionLocal()
    
    try:
        chats = db.query(Chat).all()
        fixed_count = 0
        removed_count = 0
        
        for chat in chats:
            members = db.query(ChatMember).filter(ChatMember.chat_id == chat.id).all()
            member_ids = [m.user_id for m in members]
            
            if len(member_ids) == 1:
                # Chat with only one member - check if there are messages
                messages = db.query(Message).filter(Message.chat_id == chat.id).all()
                
                if messages:
                    # Has messages - find message senders and add them
                    sender_ids = set([m.user_id for m in messages])
                    current_member = member_ids[0]
                    
                    # Add all message senders who aren't already members
                    for sender_id in sender_ids:
                        if sender_id != current_member:
                            existing = db.query(ChatMember).filter(
                                ChatMember.chat_id == chat.id,
                                ChatMember.user_id == sender_id
                            ).first()
                            if not existing:
                                member = ChatMember(chat_id=chat.id, user_id=sender_id)
                                db.add(member)
                                user = db.query(User).filter(User.id == sender_id).first()
                                print(f"Added user {user.username if user else sender_id} to chat {chat.id} ({chat.name})")
                                fixed_count += 1
                else:
                    # No messages - remove the single member (orphaned chat)
                    member = members[0]
                    user = db.query(User).filter(User.id == member.user_id).first()
                    print(f"Removing orphaned membership: user {user.username if user else member.user_id} from chat {chat.id} ({chat.name})")
                    db.delete(member)
                    removed_count += 1
        
        db.commit()
        print(f"\nFixed {fixed_count} memberships, removed {removed_count} orphaned memberships.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Fixing single-member chats...")
    fix_single_member_chats()

