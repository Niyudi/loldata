from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BOOLEAN, INTEGER, SMALLINT

from .base import Base


class TimelineItems(Base):
    __tablename__ = "timeline_items"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    timeline_id: Mapped[int] = mapped_column(INTEGER)
    timestamp: Mapped[int] = mapped_column(INTEGER, nullable=False)
    item_id: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    is_purchase: Mapped[bool] = mapped_column(BOOLEAN, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
    )
