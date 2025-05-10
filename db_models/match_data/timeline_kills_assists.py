from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import INTEGER

from .base import Base


class TimelineKillsAssists(Base):
    __tablename__ = "timeline_kills_assists"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    timeline_id: Mapped[int] = mapped_column(INTEGER)
    kill_id: Mapped[int] = mapped_column(INTEGER)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
        ForeignKeyConstraint(['kill_id'], ['match_data.timeline_kills.id']),
        UniqueConstraint('timeline_id', 'kill_id'),
    )
