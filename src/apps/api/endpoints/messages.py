import logging
import uuid
from datetime import datetime
from typing import List

from apps.api.deps import get_current_user
from apps.db import get_conn
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/messages", tags=["messages"])


class SendMessageRequest(BaseModel):
    receiver_id: str = Field(...)
    text: str = Field(..., min_length=1, max_length=5000)


class SendMessageResponse(BaseModel):
    success: bool
    message: str


class ConversationResponse(BaseModel):
    success: bool
    conversations: List[dict] = []


class MessagesResponse(BaseModel):
    success: bool
    messages: List[dict] = []


def _get_or_create_conv(user_a: str, user_b: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT id FROM conversations
               WHERE (participant_a = ? AND participant_b = ?)
                  OR (participant_a = ? AND participant_b = ?)""",
            (user_a, user_b, user_b, user_a),
        ).fetchone()
        if row:
            return row["id"]
        cid = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO conversations (id, participant_a, participant_b, created_at)
               VALUES (?, ?, ?, ?)""",
            (cid, user_a, user_b, datetime.utcnow().isoformat()),
        )
        return cid


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        conv_id = _get_or_create_conv(user_id, request.receiver_id)
        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO messages (id, conversation_id, sender_id, text, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), conv_id, user_id, request.text, now),
            )
            conn.execute(
                """UPDATE conversations
                   SET last_message = ?, last_sender = ?, updated_at = ?
                   WHERE id = ?""",
                (request.text, user_id, now, conv_id),
            )
        logger.info("Message sent: conv=%s sender=%s", conv_id, user_id)
        return SendMessageResponse(success=True, message="Message sent.")
    except Exception as exc:
        logger.exception("Send message error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/conversations", response_model=ConversationResponse)
async def list_conversations(user_id: str = Depends(get_current_user)):
    try:
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT c.id, c.participant_a, c.participant_b,
                          c.last_message, c.last_sender, c.created_at, c.updated_at,
                          COUNT(m.id) AS messages_count
                   FROM conversations c
                   LEFT JOIN messages m ON m.conversation_id = c.id
                   WHERE c.participant_a = ? OR c.participant_b = ?
                   GROUP BY c.id
                   ORDER BY COALESCE(c.updated_at, c.created_at) DESC""",
                (user_id, user_id),
            ).fetchall()
        conversations = [
            {
                "id": r["id"],
                "participants": [r["participant_a"], r["participant_b"]],
                "last_message": r["last_message"],
                "last_sender": r["last_sender"],
                "messages_count": r["messages_count"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
        return ConversationResponse(success=True, conversations=conversations)
    except Exception as exc:
        logger.exception("List conversations error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{conversation_id}", response_model=MessagesResponse)
async def get_messages(
    conversation_id: str,
    user_id: str = Depends(get_current_user),
):
    try:
        with get_conn() as conn:
            conv = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found.")
            if user_id not in (conv["participant_a"], conv["participant_b"]):
                raise HTTPException(status_code=403, detail="Not a participant.")
            rows = conn.execute(
                """SELECT id, conversation_id, sender_id, text, created_at
                   FROM messages WHERE conversation_id = ?
                   ORDER BY created_at ASC""",
                (conversation_id,),
            ).fetchall()
        messages = [dict(r) for r in rows]
        return MessagesResponse(success=True, messages=messages)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Get messages error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
