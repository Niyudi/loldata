from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import CHAR, VARCHAR

from .base import Base


class Players(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(CHAR(78), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    tag: Mapped[str] = mapped_column(VARCHAR(5), nullable=False)
