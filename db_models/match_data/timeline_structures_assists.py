from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import INTEGER

from .base import Base


class TimelineStructuresAssists(Base):
    __tablename__ = "timeline_structures_assists"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    timeline_id: Mapped[int] = mapped_column(INTEGER)
    structure_id: Mapped[int] = mapped_column(INTEGER)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
        ForeignKeyConstraint(['structure_id'], ['match_data.timeline_structures.id']),
        UniqueConstraint('timeline_id', 'structure_id'),
    )
