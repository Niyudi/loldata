from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, ENUM, INTEGER

from .base import Base
from ..static import Regions


class Matches(Base):
    __tablename__ = "matches"

    region: Mapped[Regions] = mapped_column(ENUM(Regions, create_type=False), primary_key=True)
    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    patch_id: Mapped[int] = mapped_column(INTEGER, nullable=False)
    time: Mapped[int] = mapped_column(BIGINT, nullable=False)
    duration: Mapped[int] = mapped_column(BIGINT, nullable=False)
    is_blue_win: Mapped[bool] = mapped_column(BOOLEAN)

    __table_args__ = (
        ForeignKeyConstraint(['patch_id'], ['static.patches.id']),
    )
