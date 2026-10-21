from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)

    # One driver can have many collection records.
    collections: Mapped[list["TransportCollection"]] = relationship(
        back_populates="driver" 
    )
