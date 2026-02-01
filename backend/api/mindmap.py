"""\
Mindmap API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import hashlib

from database.connection import get_db
from utils.auth import get_current_user, TokenData
from services.vector_store import vector_store_service
from models.study_plan import TopicMindmap

router = APIRouter()


def _hash_kb_documents(docs):
    h = hashlib.sha256()
    for d in docs:
        text = (d.get("text") or "").strip()
        url = (d.get("url") or "").strip()
        meta = d.get("metadata") if isinstance(d.get("metadata"), dict) else {}
        chunk_type = str(meta.get("chunk_type") or "")
        h.update((chunk_type + "|" + url + "|" + text).encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _extract_formula_label(text: str) -> str:
    if not text:
        return "Formula"
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Prefer a line that looks like a formula
    for l in lines:
        if "=" in l or "^" in l or "∝" in l:
            return f"Formula: {l}"[:80]
    return ("Formula: " + lines[0])[:80]


def _truncate(label: str, max_len: int = 40) -> str:
    label = (label or "").strip()
    if len(label) <= max_len:
        return label
    return label[: max_len - 1].rstrip() + "…"


def _build_mindmap_from_chunks(topic: str, chunks: list, metadata: dict):
    nodes = [{"id": "central", "label": _truncate(topic, 50), "type": "center"}]
    edges = []

    next_id = 1

    def add_node(label: str, node_type: str, parent: str = "central"):
        nonlocal next_id
        node_id = f"n{next_id}"
        next_id += 1
        nodes.append({"id": node_id, "label": _truncate(label, 80), "type": node_type})
        edges.append({"source": parent, "target": node_id})
        return node_id

    # Group by section title where available
    section_nodes = {}

    for c in chunks:
        meta = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
        ctype = meta.get("chunk_type")
        text = (c.get("text") or "").strip()

        if ctype == "definition":
            term = meta.get("term")
            if term:
                add_node(f"Definition: {term}", "definition")
            elif text:
                add_node(text.split("\n")[0], "definition")

        elif ctype == "formula":
            add_node(_extract_formula_label(text), "formula")

        elif ctype == "example":
            # First line typically starts with 'Example:'
            first = (text.split("\n")[0] if text else "Example")
            add_node(first, "example")

        elif ctype == "section":
            sec_title = meta.get("section_title")
            if sec_title:
                if sec_title not in section_nodes:
                    section_nodes[sec_title] = add_node(f"{sec_title}", "section")
                parent = section_nodes[sec_title]
            else:
                parent = "central"

            # Extract key points if present in the chunk text
            if "Key points:" in text:
                lines = [l.strip() for l in text.splitlines()]
                for l in lines:
                    if l.startswith("-"):
                        add_node(l.lstrip("- ").strip(), "key_point", parent=parent)

    # Guardrail: require at least some meaningful structure
    if len(nodes) < 5:
        return None

    return {
        "topic": topic,
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "exam": metadata.get("exam"),
            "chapter": metadata.get("chapter"),
            "topic": metadata.get("topic") or topic,
        },
    }


@router.get("/topic/{topic_id}")
async def get_topic_mindmap(
    topic_id: str,
    exam: str | None = Query(default=None),
    chapter: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get (or generate) a cached mindmap for a specific topic_id (moduleId)."""
    try:
        # Get all chunks for this topic KB
        metadata_filters = {}
        if exam:
            metadata_filters["exam"] = exam
        if chapter:
            metadata_filters["chapter"] = chapter
        if topic:
            metadata_filters["topic"] = topic
        chunks = vector_store_service.get_documents(topic_id, metadata_filters=metadata_filters or None)
        
        # RAG PATH: If no chunks, index content from internet first
        if not chunks:
            logger.info(f"🔍 No indexed content for {topic_id}, triggering RAG for mindmap")
            
            # Extract topic name and chapter from topic_id (format: chapter_id_Topic_Name)
            parts = topic_id.split('_')
            topic_name = topic or ('_'.join(parts[1:]).replace('_', ' ') if len(parts) > 1 else topic_id)
            chapter_name = chapter or "General"
            exam_type = exam or "General"
            
            logger.info(f"📚 Indexing content for mindmap: topic={topic_name}, chapter={chapter_name}")
            
            # Use orchestrator to ensure content is indexed via RAG
            from agents.orchestrator import orchestrator
            
            try:
                # This will:
                # 1. Search internet for content (DuckDuckGo)
                # 2. Filter and clean the content
                # 3. Index into vector store
                indexed = await orchestrator.ensure_topic_indexed(
                    module_id=topic_id,
                    topic=topic_name,
                    exam_type=exam_type,
                    module_name=chapter_name
                )
                
                if not indexed:
                    logger.warning(f"RAG indexing failed for {topic_id}, falling back to LLM")
                    # Fallback to LLM-generated mindmap
                    from agents.content_agent import content_agent
                    mindmap_data = await content_agent.create_mindmap(topic_name)
                    
                    mindmap = {
                        "topic": topic_name,
                        "nodes": mindmap_data.get("main_branches", []),
                        "edges": [],
                        "metadata": {
                            "exam": exam,
                            "chapter": chapter,
                            "topic": topic_name,
                            "source": "llm_generated"
                        }
                    }
                    
                    # Cache it
                    kb_hash = hashlib.sha256(topic_id.encode()).hexdigest()
                    new_row = TopicMindmap(
                        user_id=current_user.user_id,
                        topic_id=topic_id,
                        kb_hash=kb_hash,
                        mindmap_json=mindmap,
                        mindmap_metadata=mindmap.get("metadata", {}),
                    )
                    db.add(new_row)
                    await db.commit()
                    
                    return mindmap
                
                # After indexing, fetch chunks again
                logger.info(f"✅ Content indexed successfully, fetching chunks for mindmap")
                chunks = vector_store_service.get_documents(topic_id, metadata_filters=metadata_filters or None)
                
                if not chunks:
                    logger.error(f"Still no chunks after indexing for {topic_id}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to index content for mindmap generation"
                    )
                    
            except Exception as e:
                logger.error(f"RAG indexing error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate mindmap: {str(e)}"
                )

        kb_hash = _hash_kb_documents(chunks)

        existing = await db.execute(
            select(TopicMindmap).where(
                TopicMindmap.user_id == current_user.user_id,
                TopicMindmap.topic_id == topic_id,
                TopicMindmap.kb_hash == kb_hash,
            )
        )
        cached = existing.scalar_one_or_none()
        if cached and cached.mindmap_json:
            return cached.mindmap_json

        # Infer topic/chapter/exam from chunk metadata
        inferred_meta = {}
        for c in chunks:
            m = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
            if m:
                inferred_meta = m
                break

        inferred_topic = inferred_meta.get("topic") or topic_id
        mindmap = _build_mindmap_from_chunks(inferred_topic, chunks, inferred_meta)
        if mindmap is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mindmap will appear after sufficient content is indexed for this topic.",
            )

        # Upsert cache row (simple: insert a new row if hash changed)
        new_row = TopicMindmap(
            user_id=current_user.user_id,
            topic_id=topic_id,
            kb_hash=kb_hash,
            mindmap_json=mindmap,
            mindmap_metadata=mindmap.get("metadata", {}),
        )
        db.add(new_row)
        await db.commit()

        logger.info(f"Mindmap cached for user={current_user.user_id} topic_id={topic_id}")
        return mindmap

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating mindmap: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
