from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import INTEGER, VARCHAR

from .base import Base


class Patches(Base):
    __tablename__ = "patches"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(5), nullable=False)

    __table_args__ = (
        UniqueConstraint('name'),
    )
