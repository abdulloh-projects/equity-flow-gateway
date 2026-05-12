from datetime import datetime, timezone

from apps.api.deps import get_current_user
from apps.db import get_conn
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/startup", tags=["media"])


class VideoRequest(BaseModel):
    youtube_url: str = Field(...)


@router.get("/{startup_id}/video")
def get_video(startup_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT youtube_url FROM startup_videos WHERE startup_id = ?",
            (startup_id,),
        ).fetchone()
    if not row:
        return {"success": False, "youtube_url": None}
    return {"success": True, "youtube_url": row["youtube_url"]}


@router.post("/{startup_id}/video")
def set_video(
    startup_id: int,
    body: VideoRequest,
    user_id: str = Depends(get_current_user),
):
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO startup_videos (startup_id, youtube_url, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(startup_id) DO UPDATE SET youtube_url = excluded.youtube_url,
                                                   updated_at = excluded.updated_at
            """,
            (startup_id, body.youtube_url, now),
        )
    return {"success": True, "youtube_url": body.youtube_url}


@router.delete("/{startup_id}/video")
def delete_video(startup_id: int, user_id: str = Depends(get_current_user)):
    with get_conn() as conn:
        conn.execute("DELETE FROM startup_videos WHERE startup_id = ?", (startup_id,))
    return {"success": True}


DOC_TYPES = {
    "pitch_deck",
    "financial_report",
    "business_plan",
    "legal_document",
    "other",
}


class DocumentRequest(BaseModel):
    title: str = Field(...)
    doc_type: str = Field(...)
    file_url: str = Field(...)


@router.get("/{startup_id}/documents")
def list_documents(startup_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, doc_type, file_url, created_at FROM startup_documents WHERE startup_id = ? ORDER BY created_at DESC",
            (startup_id,),
        ).fetchall()
    return {
        "success": True,
        "documents": [dict(r) for r in rows],
    }


@router.post("/{startup_id}/documents")
def add_document(
    startup_id: int,
    body: DocumentRequest,
    user_id: str = Depends(get_current_user),
):
    if body.doc_type not in DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"doc_type must be one of: {', '.join(sorted(DOC_TYPES))}",
        )
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO startup_documents (startup_id, title, doc_type, file_url, created_at) VALUES (?, ?, ?, ?, ?)",
            (startup_id, body.title, body.doc_type, body.file_url, now),
        )
        doc_id = cursor.lastrowid
    return {"success": True, "id": doc_id}


@router.delete("/{startup_id}/documents/{doc_id}")
def delete_document(
    startup_id: int,
    doc_id: int,
    user_id: str = Depends(get_current_user),
):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM startup_documents WHERE id = ? AND startup_id = ?",
            (doc_id, startup_id),
        )
    return {"success": True}
