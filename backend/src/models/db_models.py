from sqlalchemy import Column, String, Integer, Text
from database import Base


class ParseTask(Base):
    __tablename__ = "parse_tasks"

    id = Column(String, primary_key=True, index=True)
    batch_id = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    file_size = Column(Integer, nullable=True)
    parser_type = Column(String, nullable=False, default="mineru", index=True)
    file_type = Column(String, nullable=False, default="document", index=True)
    state = Column(String, nullable=False, index=True)
    error_msg = Column(Text, nullable=True)
    markdown_content = Column(Text, nullable=True)
    task_metadata = Column(Text, nullable=True)
    result_file_path = Column(String, nullable=True)
    result_file_format = Column(String, nullable=True, default="zip")
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
