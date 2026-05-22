from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Use psycopg2 driver to avoid requiring the separate psycopg package.
# The 'options' query parameter sets lc_messages=C so that PostgreSQL
# returns error messages in English (ASCII), preventing UnicodeDecodeError
# when the server locale is Korean (CP949) and psycopg2 tries to decode
# the message with Python's default UTF-8 codec.
DATABASE_URL = (
    "postgresql+psycopg2://postgres:1234@localhost:5432/ajou_se_db"
    "?options=-c%20lc_messages%3DC"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"client_encoding": "utf8"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Attach a listener to auto-create placeholder Books when Sentences are flushed
from sqlalchemy import event
from sqlalchemy.orm import Session as _Session


def _ensure_books_before_flush(session: _Session, flush_context, instances):
    # Local import to avoid circular dependencies during module import
    from db.model import Book, Sentence

    for obj in list(session.new):
        if isinstance(obj, Sentence):
            book_id = getattr(obj, "book_id", None)
            if book_id is not None:
                existing = session.get(Book, book_id)
                if existing is None:
                    placeholder = Book(id=book_id, name=f"AutoBook {book_id}", author_id=None)
                    session.add(placeholder)


# Listen on SessionLocal and the global Session class for before_flush events
event.listen(SessionLocal, "before_flush", _ensure_books_before_flush)
event.listen(_Session, "before_flush", _ensure_books_before_flush)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    import db.model  # noqa: F401  # ensures models are registered with Base

    Base.metadata.create_all(bind=engine)
