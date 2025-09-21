# backend/app/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Set, List
from . import database, models, schemas, utils
from sqlalchemy.orm import Session
import json

router = APIRouter()

# In-memory room management: group_id -> set of WebSocket
rooms: Dict[int, Set[WebSocket]] = {}
# Connected websockets -> username
connected: Dict[WebSocket, str] = {}

# REST endpoints for groups and messages
@router.get("/groups")
def list_groups(db: Session = Depends(database.get_db)):
    groups = db.query(models.Group).order_by(models.Group.id).all()
    return [{"id": g.id, "name": g.name} for g in groups]

@router.post("/groups")
def create_group(payload: schemas.GroupCreate, db: Session = Depends(database.get_db)):
    exists = db.query(models.Group).filter(models.Group.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Group already exists")
    g = models.Group(name=payload.name)
    db.add(g)
    db.commit()
    db.refresh(g)
    return {"id": g.id, "name": g.name}

@router.get("/groups/{group_id}/messages")
def get_group_messages(group_id: int, db: Session = Depends(database.get_db)):
    msgs = db.query(models.Message).filter(models.Message.group_id == group_id).order_by(models.Message.timestamp).all()
    out = []
    for m in msgs:
        out.append({
            "id": m.id,
            "from_user": m.from_user,
            "to_user": m.to_user,
            "group_id": m.group_id,
            "text": m.text,
            "timestamp": m.timestamp.isoformat()
        })
    return {"messages": out}

# WebSocket endpoint for a specific group
@router.websocket("/ws/{token}/{group_id}")
async def websocket_endpoint(websocket: WebSocket, token: str, group_id: int):
    payload = utils.decode_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    username = payload.get("sub")
    # accept connection
    await websocket.accept()
    # register
    connected[websocket] = username
    rooms.setdefault(group_id, set()).add(websocket)

    # notify room about join
    join_msg = {"system": True, "msg": f"{username} joined group {group_id}"}
    await broadcast_to_group(group_id, join_msg)

    try:
        while True:
            raw = await websocket.receive_text()
            # expect plain text message; could be JSON with more fields
            # We support JSON { "text": "...", "to_user": optional } or plain text
            try:
                data = json.loads(raw)
                text = data.get("text")
                to_user = data.get("to_user")
            except Exception:
                text = raw
                to_user = None

            if not text:
                continue

            # save message to DB
            db: Session = next(database.get_db())
            msg = models.Message(from_user=username, to_user=to_user, group_id=group_id, text=text)
            db.add(msg)
            db.commit()
            db.refresh(msg)
            payload_msg = {
                "id": msg.id,
                "from_user": msg.from_user,
                "to_user": msg.to_user,
                "group_id": msg.group_id,
                "text": msg.text,
                "timestamp": msg.timestamp.isoformat()
            }

            # broadcast to group
            await broadcast_to_group(group_id, payload_msg)
    except WebSocketDisconnect:
        # cleanup
        rooms.get(group_id, set()).discard(websocket)
        connected.pop(websocket, None)
        leave_msg = {"system": True, "msg": f"{username} left group {group_id}"}
        await broadcast_to_group(group_id, leave_msg)
    except Exception:
        # on other error, ensure cleanup
        rooms.get(group_id, set()).discard(websocket)
        connected.pop(websocket, None)

async def broadcast_to_group(group_id: int, message):
    conns = list(rooms.get(group_id, []))
    for ws in conns:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            # remove bad sockets
            rooms[group_id].discard(ws)
            connected.pop(ws, None)
