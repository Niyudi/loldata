from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import SMALLINT, VARCHAR

from .base import Base


class Champions(Base):
    __tablename__ = "champions"

    id: Mapped[int] = mapped_column(SMALLINT, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)

    __table_args__ = (
        UniqueConstraint('name'),
    )
