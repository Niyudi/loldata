from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, INTEGER, SMALLINT

from .base import Base


class TimelineSnapshots(Base):
    __tablename__ = "timeline_snapshots"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    timeline_id: Mapped[int] = mapped_column(BIGINT)
    timestamp: Mapped[int] = mapped_column(INTEGER, nullable=False)
    crowd_control_time: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_magic: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_magic_champions: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_magic_taken: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_physical: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_physical_champions: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_physical_taken: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_true: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_true_champions: Mapped[int] = mapped_column(INTEGER, nullable=False)
    damage_true_taken: Mapped[int] = mapped_column(INTEGER, nullable=False)
    experience: Mapped[int] = mapped_column(INTEGER, nullable=False)
    minions_killed: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    minions_killed_jungle: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    position_x: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    position_y: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    total_gold: Mapped[int] = mapped_column(INTEGER, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
        UniqueConstraint('timeline_id', 'timestamp')
    )
