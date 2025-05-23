from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import ENUM, INTEGER

from .base import Base
from ..static import Roles


class TimelineKills(Base):
    __tablename__ = "timeline_kills"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    timeline_id: Mapped[int] = mapped_column(INTEGER)
    timestamp: Mapped[int] = mapped_column(INTEGER, nullable=False)
    target_role: Mapped[Roles] = mapped_column(ENUM(Roles, create_type=False), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
        UniqueConstraint('timeline_id', 'timestamp', 'target_role'),
    )
