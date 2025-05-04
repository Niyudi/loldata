from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, ENUM, INTEGER

from .base import Base
from ..static import Roles, StructureTypes


class TimelineStructures(Base):
    __tablename__ = "timeline_structures"

    timeline_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    timestamp: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    type: Mapped[StructureTypes] = mapped_column(ENUM(StructureTypes, create_type=False), nullable=False)
    assist_roles: Mapped[list[Roles]] = mapped_column(ARRAY(ENUM(Roles, create_type=False)), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
    )
