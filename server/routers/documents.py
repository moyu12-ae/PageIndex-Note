import os
import json
import asyncio
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from server.services.document_service import (
    generate_document_id, save_metadata, load_all_metadata, delete_metadata,
    progress_tracker, orchestrate_processing, RESULTS_DIR, UPLOADS_DIR,
)
from server.services.tree_service import load_tree, get_skeleton, get_node_by_id, count_all_nodes
from server.services.converter_service import get_file_type, SUPPORTED_EXTENSIONS

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and begin tree generation.
    Supports: PDF, Markdown, TXT, JSON, CSV, Word (docx).
    """
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    supported_exts = list(SUPPORTED_EXTENSIONS.keys())
    file_type = get_file_type(ext)
    if not file_type:
        supported_str = ", ".join(supported_exts)
        raise HTTPException(400, f"Unsupported file type: {ext}. Supported: {supported_str}")

    # Read file content
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(400, "File too large. Maximum size is 50MB.")

    # Generate ID and save file
    doc_id = generate_document_id(filename)
    file_path = UPLOADS_DIR / f"{doc_id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    # Save metadata
    meta = {
        "document_id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "status": "processing",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file_path": str(file_path),
    }
    save_metadata(doc_id, meta)

    # Create progress tracker and start background task
    progress_tracker.create(doc_id)
    asyncio.create_task(orchestrate_processing(doc_id, str(file_path), file_type))

    return {
        "document_id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "status": "processing",
        "created_at": meta["created_at"],
    }


@router.get("")
async def list_documents():
    """List all documents."""
    all_meta = load_all_metadata()
    documents = []
    for doc_id, meta in all_meta.items():
        status = meta.get("status", "unknown")

        # Auto-fix: if status says "processing" but tree file exists, mark as completed
        if status == "processing":
            tree_path = RESULTS_DIR / f"{doc_id}.json"
            if tree_path.exists():
                status = "completed"
                meta["status"] = "completed"
                save_metadata(doc_id, meta)

        doc_info = {
            "document_id": doc_id,
            "filename": meta.get("filename", "unknown"),
            "file_type": meta.get("file_type", "unknown"),
            "status": status,
            "created_at": meta.get("created_at", ""),
        }
        # If completed, count nodes
        if meta.get("status") == "completed":
            try:
                tree = load_tree(doc_id)
                doc_info["node_count"] = count_all_nodes(tree)
            except Exception:
                doc_info["node_count"] = 0
        documents.append(doc_info)

    # Sort by created_at descending
    documents.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return {"documents": documents}


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document metadata."""
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id)
    if not meta:
        raise HTTPException(404, f"Document not found: {document_id}")
    return meta


@router.get("/{document_id}/tree")
async def get_document_tree(document_id: str):
    """Get the full generated tree structure."""
    try:
        tree = load_tree(document_id)
        return tree
    except FileNotFoundError:
        raise HTTPException(404, f"Tree not found for document: {document_id}")


@router.get("/{document_id}/tree/skeleton")
async def get_document_tree_skeleton(document_id: str):
    """Get tree without text fields."""
    try:
        tree = load_tree(document_id)
        return get_skeleton(tree)
    except FileNotFoundError:
        raise HTTPException(404, f"Tree not found for document: {document_id}")


@router.get("/{document_id}/nodes/{node_id}")
async def get_node(document_id: str, node_id: str):
    """Get a single node's full data."""
    try:
        tree = load_tree(document_id)
        node = get_node_by_id(tree, node_id)
        if not node:
            raise HTTPException(404, f"Node not found: {node_id}")
        return node
    except FileNotFoundError:
        raise HTTPException(404, f"Tree not found for document: {document_id}")


@router.get("/{document_id}/progress")
async def get_progress(document_id: str):
    """SSE endpoint — streams processing progress events."""
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id)
    if not meta:
        raise HTTPException(404, f"Document not found: {document_id}")

    # If already completed, return immediately
    if meta.get("status") == "completed":
        async def done_stream():
            yield f'data: {json.dumps({"status": "completed", "percent": 100})}\n\n'
        return StreamingResponse(done_stream(), media_type="text/event-stream")

    # If failed, return the error
    if meta.get("status") == "failed":
        async def fail_stream():
            yield f'data: {json.dumps({"status": "failed", "message": meta.get("error", "Processing failed")})}\n\n'
        return StreamingResponse(fail_stream(), media_type="text/event-stream")

    # If "processing" but no active task (server restarted), re-trigger processing
    task = progress_tracker.get(document_id)
    if not task:
        file_path = meta.get("file_path", "")
        file_type = meta.get("file_type", "pdf")
        if file_path and Path(file_path).exists():
            progress_tracker.create(document_id)
            asyncio.create_task(orchestrate_processing(document_id, file_path, file_type))
        else:
            async def no_file_stream():
                yield f'data: {json.dumps({"status": "failed", "message": "Source file not found, please re-upload"})}\n\n'
            return StreamingResponse(no_file_stream(), media_type="text/event-stream")

    async def event_stream():
        async for update in progress_tracker.subscribe(document_id):
            yield f"data: {json.dumps(update, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its generated tree."""
    # Delete tree file
    tree_path = RESULTS_DIR / f"{document_id}.json"
    if tree_path.exists():
        tree_path.unlink()

    # Delete uploaded file
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id, {})
    file_path = meta.get("file_path")
    if file_path and Path(file_path).exists():
        Path(file_path).unlink()

    # Delete metadata
    delete_metadata(document_id)

    return {"status": "deleted"}
