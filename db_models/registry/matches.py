from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, ENUM, INTEGER, SMALLINT

from .base import Base
from ..static import Regions


class Matches(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    region: Mapped[Regions] = mapped_column(ENUM(Regions, create_type=False), nullable=False)
    riot_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    patch: Mapped[int] = mapped_column(SMALLINT)
    time: Mapped[int] = mapped_column(BIGINT)
    duration: Mapped[int] = mapped_column(SMALLINT)
    is_blue_win: Mapped[bool] = mapped_column(BOOLEAN)
    
    __table_args__ = (
        UniqueConstraint('region', 'riot_id'),
    )
