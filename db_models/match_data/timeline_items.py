from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, INTEGER, SMALLINT

from .base import Base


class TimelineItems(Base):
    __tablename__ = "timeline_items"

    timeline_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    timestamp: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    item_id: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    is_purchase: Mapped[bool] = mapped_column(BOOLEAN, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
    )
