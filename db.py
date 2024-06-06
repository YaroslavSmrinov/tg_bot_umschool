from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    scores = relationship("Score", back_populates="student")


class Score(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    student = relationship("Student", back_populates="scores")


engine = create_engine('sqlite:///students.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

