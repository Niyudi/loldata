from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, ENUM, INTEGER

from .base import Base
from ..static import Roles


class TimelineKills(Base):
    __tablename__ = "timeline_kills"

    timeline_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    timestamp: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    target_role: Mapped[Roles] = mapped_column(ENUM(Roles, create_type=False), nullable=False)
    assist_roles: Mapped[list[Roles]] = mapped_column(ARRAY(ENUM(Roles, create_type=False)), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
    )
