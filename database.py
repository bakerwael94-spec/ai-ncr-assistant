from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./ncr.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class NCR(Base):
    __tablename__ = "ncrs"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String)
    project = Column(String)
    location = Column(String)
    discipline = Column(String)
    description = Column(Text)
    status = Column(String)
    image_path = Column(String)
    created_by = Column(String)
    approver = Column(String, nullable=True)
    approval_comment = Column(Text, nullable=True)


# IMPORTANT
Base.metadata.create_all(bind=engine)