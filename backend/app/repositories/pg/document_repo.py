"""Persistence operations for document sources."""

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_source import DocumentSource, DocumentSourceType


class DocumentRepository:
    """Encapsulates SQLAlchemy access patterns for document sources."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        org_id: UUID,
        name: str,
        source_type: DocumentSourceType,
        connection_config_encrypted: str,
        ingestion_status: str = "pending",
    ) -> DocumentSource:
        """
        Insert a document source row.

        Args:
            org_id: Owning organization.
            name: Display name.
            source_type: Source category.
            connection_config_encrypted: Encrypted configuration payload.
            ingestion_status: Pipeline status marker.

        Returns:
            Persisted DocumentSource ORM instance.
        """
        row = DocumentSource(
            org_id=org_id,
            name=name,
            source_type=source_type,
            connection_config_encrypted=connection_config_encrypted,
            ingestion_status=ingestion_status,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_for_org(self, org_id: UUID, document_id: UUID) -> DocumentSource | None:
        """
        Fetch a document source scoped to an organization.

        Args:
            org_id: Organization identifier.
            document_id: Document primary key.

        Returns:
            DocumentSource when found, otherwise None.
        """
        stmt: Select[tuple[DocumentSource]] = select(DocumentSource).where(
            DocumentSource.id == document_id,
            DocumentSource.org_id == org_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_org(
        self,
        org_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DocumentSource], int]:
        """
        List document sources for an organization with pagination.

        Args:
            org_id: Organization identifier.
            limit: Page size.
            offset: Page offset.

        Returns:
            Tuple of rows and total count.
        """
        count_stmt = select(func.count()).select_from(DocumentSource).where(DocumentSource.org_id == org_id)
        total = int((await self._session.execute(count_stmt)).scalar_one())
        stmt = (
            select(DocumentSource)
            .where(DocumentSource.org_id == org_id)
            .order_by(DocumentSource.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def delete(self, row: DocumentSource) -> None:
        """
        Remove a document source row.

        Args:
            row: ORM instance to delete.
        """
        self._session.delete(row)

    async def update_ingestion(
        self,
        document_id: UUID,
        *,
        status: str,
        last_error: str | None = None,
    ) -> None:
        """
        Update ingestion status fields for a document.

        Args:
            document_id: Document primary key.
            status: New ingestion status label.
            last_error: Optional error text when status reflects failure.
        """
        row = await self._session.get(DocumentSource, document_id)
        if row is None:
            return
        row.ingestion_status = status
        row.last_error = last_error
        await self._session.flush()
