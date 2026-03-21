"""Persistence operations for users."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    """Encapsulates SQLAlchemy access patterns for users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        org_id: UUID,
        role: UserRole = UserRole.MEMBER,
        is_active: bool = True,
    ) -> User:
        """
        Insert a new user row.

        Args:
            email: Unique login email.
            hashed_password: Bcrypt hash of the password.
            org_id: Owning organization id.
            role: Authorization role.
            is_active: Whether the account can authenticate.

        Returns:
            Persisted User ORM instance.
        """
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            org_id=org_id,
            role=role,
            is_active=is_active,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """
        Fetch a user by email address (case-insensitive).

        Args:
            email: Email to look up.

        Returns:
            User when found, otherwise None.
        """
        normalized = email.lower()
        result = await self._session.execute(select(User).where(User.email == normalized))
        return result.scalar_one_or_none()

    async def list_for_org(self, org_id: UUID) -> list[User]:
        """
        List users belonging to an organization.

        Args:
            org_id: Organization identifier.

        Returns:
            Matching users ordered by creation time descending.
        """
        stmt = select(User).where(User.org_id == org_id).order_by(User.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Fetch a user by primary key.

        Args:
            user_id: User identifier.

        Returns:
            User when found, otherwise None.
        """
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
