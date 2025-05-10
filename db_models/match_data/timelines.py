from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, ENUM, INTEGER

from .base import Base
from ..static import Regions, Roles


class Timelines(Base):
    __tablename__ = "timelines"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(BIGINT)
    role: Mapped[Roles] = mapped_column(ENUM(Roles, create_type=False))
    is_blue_team: Mapped[bool] = mapped_column(BOOLEAN, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['match_id'], ['registry.matches.id']),
        UniqueConstraint('match_id', 'role', 'is_blue_team'),
    )
