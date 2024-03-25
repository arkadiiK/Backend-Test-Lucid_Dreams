from sqlalchemy import Column, Integer, String, ForeignKey


from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
