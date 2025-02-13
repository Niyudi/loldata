from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import CHAR, SMALLINT, VARCHAR

from .base import Base


class Players(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(SMALLINT, primary_key=True)
    riot_id: Mapped[str] = mapped_column(CHAR(78), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    tag: Mapped[str] = mapped_column(VARCHAR(5), nullable=False)

    __table_args__ = (
        UniqueConstraint('riot_id'),
    )
