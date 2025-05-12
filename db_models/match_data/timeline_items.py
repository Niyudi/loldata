from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import ENUM, INTEGER, SMALLINT

from .base import Base
from ..static import ItemOperationType


class TimelineItems(Base):
    __tablename__ = "timeline_items"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    timeline_id: Mapped[int] = mapped_column(INTEGER)
    timestamp: Mapped[int] = mapped_column(INTEGER, nullable=False)
    item_id: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    operation_type: Mapped[ItemOperationType] = mapped_column(ENUM(ItemOperationType, create_type=False), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['timeline_id'], ['match_data.timelines.id']),
    )
