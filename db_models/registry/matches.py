from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, ENUM, SMALLINT

from .base import Base
from ..static import Regions


class Matches(Base):
    __tablename__ = "matches"

    region: Mapped[Regions] = mapped_column(ENUM(Regions, create_type=False), primary_key=True)
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    patch: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    time: Mapped[int] = mapped_column(BIGINT, nullable=False)
    duration: Mapped[int] = mapped_column(BIGINT, nullable=False)
    is_blue_win: Mapped[bool] = mapped_column(BOOLEAN)
