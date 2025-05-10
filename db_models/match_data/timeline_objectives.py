from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import ENUM, INTEGER

from .base import Base
from ..static import ObjectiveTypes


class TimelineObjectives(Base):
    __tablename__ = "timeline_objectives"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    timeline_id: Mapped[int] = mapped_column(INTEGER)
    timestamp: Mapped[int] = mapped_column(INTEGER, nullable=False)
    type: Mapped[ObjectiveTypes] = mapped_column(ENUM(ObjectiveTypes, create_type=False), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
    )
