from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import CHAR, INTEGER

from .base import Base


class Players(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    riot_id: Mapped[str] = mapped_column(CHAR(78), nullable=False)

    __table_args__ = (
        UniqueConstraint('riot_id'),
    )
