import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.user import User
from app.services.cache import cache_service

logger = logging.getLogger("ai_bos")

CACHE_PREFIX = "documents"


async def create_document(db: AsyncSession, payload, author_id: int):
    """Create a new document, setting the author and initial version."""
    data = payload.model_dump()
    data.pop("author_id", None)
    document = Document(**data, author_id=author_id, version=1)
    db.add(document)
    await db.commit()
    await db.refresh(document)

    await cache_service.delete_pattern(f"{CACHE_PREFIX}:list:*")
    await cache_service.delete(f"{CACHE_PREFIX}:stats")

    logger.info("Created document '%s' (id=%d) by author %d", document.title, document.id, author_id)
    return document


async def get_document(db: AsyncSession, document_id: int):
    """Get a single document by ID (with cache)."""
    cache_key = f"{CACHE_PREFIX}:{document_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document:
        await cache_service.set(cache_key, document.__dict__, ttl=600)

    return document


async def get_document_by_slug(db: AsyncSession, slug: str):
    """Get a single document by unique slug."""
    result = await db.execute(select(Document).where(Document.slug == slug))
    return result.scalar_one_or_none()


async def get_documents(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    company_id: Optional[int] = None,
    author_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "title",
    sort_order: str = "asc",
):
    """List documents with search, filtering, sorting, and pagination."""
    query = select(Document)

    if search:
        search_filter = or_(
            Document.title.ilike(f"%{search}%"),
            Document.summary.ilike(f"%{search}%"),
            Document.content.ilike(f"%{search}%"),
            Document.category.ilike(f"%{search}%"),
            Document.tags.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    if category is not None:
        query = query.where(Document.category == category)
    if status is not None:
        query = query.where(Document.status == status)
    if company_id is not None:
        query = query.where(Document.company_id == company_id)
    if author_id is not None:
        query = query.where(Document.author_id == author_id)
    if is_active is not None:
        query = query.where(Document.is_active == is_active)

    sort_column = getattr(Document, sort_by, Document.title)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    query = query.order_by(sort_column)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    return list(documents), total


async def update_document(db: AsyncSession, document_id: int, payload):
    """Update an existing document and increment its version."""
    document = await get_document(db, document_id)
    if not document:
        return None

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    # Increment the version when meaningful content fields change
    if any(field in update_data for field in ("title", "content", "summary", "slug")):
        update_data["version"] = (document.version or 1) + 1

    for field, value in update_data.items():
        setattr(document, field, value)

    await db.commit()
    await db.refresh(document)

    await cache_service.delete(f"{CACHE_PREFIX}:{document_id}")
    await cache_service.delete_pattern(f"{CACHE_PREFIX}:list:*")
    await cache_service.delete(f"{CACHE_PREFIX}:stats")

    logger.info("Updated document id=%d to version %d", document.id, document.version)
    return document


async def delete_document(db: AsyncSession, document_id: int) -> bool:
    """Delete a document permanently."""
    document = await get_document(db, document_id)
    if not document:
        return False

    await db.delete(document)
    await db.commit()

    await cache_service.delete(f"{CACHE_PREFIX}:{document_id}")
    await cache_service.delete_pattern(f"{CACHE_PREFIX}:list:*")
    await cache_service.delete(f"{CACHE_PREFIX}:stats")

    logger.info("Deleted document id=%d", document_id)
    return True


async def publish_document(db: AsyncSession, document_id: int):
    """Transition a document to published status."""
    document = await get_document(db, document_id)
    if not document:
        return None

    document.status = "published"
    await db.commit()
    await db.refresh(document)

    await cache_service.delete(f"{CACHE_PREFIX}:{document_id}")
    await cache_service.delete_pattern(f"{CACHE_PREFIX}:list:*")
    await cache_service.delete(f"{CACHE_PREFIX}:stats")

    logger.info("Published document id=%d", document_id)
    return document


async def get_document_stats(db: AsyncSession) -> Dict[str, Any]:
    """Compute aggregate documentation statistics (with cache)."""
    cache_key = f"{CACHE_PREFIX}:stats"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    total = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    published = (await db.execute(
        select(func.count(Document.id)).where(Document.status == "published")
    )).scalar() or 0
    draft = (await db.execute(
        select(func.count(Document.id)).where(Document.status == "draft")
    )).scalar() or 0
    archived = (await db.execute(
        select(func.count(Document.id)).where(Document.status == "archived")
    )).scalar() or 0

    companies_with_docs = (await db.execute(
        select(func.count(func.distinct(Document.company_id)))
    )).scalar() or 0

    if companies_with_docs > 0:
        avg_per_company = total / companies_with_docs
    else:
        avg_per_company = None

    # Documents by category
    by_category = {
        str(cat): count
        for cat, count in (await db.execute(
            select(Document.category, func.count(Document.id)).group_by(Document.category)
        )).all()
    }
    # Documents by status
    by_status = {
        str(st): count
        for st, count in (await db.execute(
            select(Document.status, func.count(Document.id)).group_by(Document.status)
        )).all()
    }

    stats = {
        "total_documents": total,
        "published_documents": published,
        "draft_documents": draft,
        "archived_documents": archived,
        "total_companies_with_documents": companies_with_docs,
        "avg_documents_per_company": float(avg_per_company) if avg_per_company else None,
        "documents_by_category": by_category,
        "documents_by_status": by_status,
    }

    await cache_service.set(cache_key, stats, ttl=300)
    return stats


async def get_document_with_details(db: AsyncSession, document_id: int):
    """Get a document enriched with author and company names."""
    document = await get_document(db, document_id)
    if not document:
        return None

    author_name = None
    if document.author_id:
        author_result = await db.execute(
            select(User.full_name, User.email).where(User.id == document.author_id)
        )
        author = author_result.first()
        if author:
            author_name = author.full_name or author.email

    company_name = None
    if document.company_id:
        from app.models.company import Company
        company_result = await db.execute(
            select(Company.name).where(Company.id == document.company_id)
        )
        company_name = company_result.scalar()

    doc_dict = document.__dict__.copy()
    doc_dict["author_name"] = author_name
    doc_dict["company_name"] = company_name

    return doc_dict
