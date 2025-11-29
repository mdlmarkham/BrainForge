from sqlalchemy import Column, String, Boolean
from src.models.orm.base import BaseEntity


class User(BaseEntity):
    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"