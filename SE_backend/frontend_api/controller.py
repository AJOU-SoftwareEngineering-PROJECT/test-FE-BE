from datetime import datetime
from typing import Optional
import hashlib
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Session

from db.database import Base, engine, get_db
from db.model import Book, Sentence, User, Gender


router = APIRouter(prefix="/api", tags=["frontend-api"])


# =========================
# Extra frontend tables
# =========================

class FrontComment(Base):
    __tablename__ = "frontend_comments"

    id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(Integer, ForeignKey("sentences.id"), nullable=False)
    content = Column(Text, nullable=False)
    user_name = Column(String(100), nullable=False, default="Guest User")
    like_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FrontScrap(Base):
    __tablename__ = "frontend_scraps"

    id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(Integer, ForeignKey("sentences.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    sentence_content = Column(Text, nullable=False)
    book_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
class FrontPlaylist(Base):
    __tablename__ = "frontend_playlists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    creator_name = Column(String(100), nullable=False, default="Guest User")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FrontPlaylistSong(Base):
    __tablename__ = "frontend_playlist_songs"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("frontend_playlists.id"), nullable=False)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    url = Column(Text, nullable=True)
    like_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

def create_frontend_tables():
    Base.metadata.create_all(bind=engine)


# =========================
# Schemas
# =========================
class FrontMusicSearchItem(BaseModel):
    title: str
    artist: str
    album: Optional[str] = ""
    preview_url: Optional[str] = ""
    artwork_url: Optional[str] = ""
    track_url: Optional[str] = ""
class FrontLoginRequest(BaseModel):
    email: str
    password: str

class FrontPasswordUpdate(BaseModel):
    old_password: str
    new_password: str
class FrontRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    gender: str = "MALE"
    age: int = 20
    intro: Optional[str] = ""


class FrontLoginResponse(BaseModel):
    id: int
    name: str
    email: str
    gender: str
    age: int
    intro: Optional[str] = None


class FrontBookCreate(BaseModel):
    name: str
    intro: Optional[str] = ""
    author_name: str
    author_email: Optional[str] = None
    sentences: list[str] = Field(default_factory=list)


class FrontBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    intro: Optional[str] = None
    author_id: Optional[int] = None
    author_name: str
    like_count: int = 0


class FrontAuthorCreate(BaseModel):
    name: str
    gender: str = "MALE"
    age: int = 20
    intro: Optional[str] = ""
    email: str


class FrontAuthorUpdate(BaseModel):
    name: str
    gender: str = "MALE"
    age: int = 20
    intro: Optional[str] = ""
    email: str


class FrontAuthorResponse(BaseModel):
    id: int
    name: str
    gender: str
    age: int
    intro: Optional[str] = None
    email: str
    book_count: int = 0


class FrontAuthorDetailResponse(BaseModel):
    id: int
    name: str
    gender: str
    age: int
    intro: Optional[str] = None
    email: str
    books: list[FrontBookResponse] = Field(default_factory=list)


class FrontSentenceCreate(BaseModel):
    chapter: int = 1
    content: str
    after_id: Optional[int] = None


class FrontSentenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter: int
    content: str
    after_id: Optional[int] = None
    book_id: int


class FrontCommentCreate(BaseModel):
    content: str
    user_name: str = "Guest User"


class FrontCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sentence_id: int
    content: str
    user_name: str
    like_count: int
    created_at: datetime


class FrontScrapCreate(BaseModel):
    sentence_id: int


class FrontScrapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sentence_id: int
    book_id: int
    sentence_content: str
    book_name: str
    created_at: datetime


class DashboardStat(BaseModel):
    label: str
    value: int
    description: str


class DashboardOverviewItem(BaseModel):
    month: str
    value: int


class DashboardActivity(BaseModel):
    type: str
    title: str
    time: str


class DashboardResponse(BaseModel):
    stats: list[DashboardStat]
    readingOverview: list[DashboardOverviewItem]
    recentActivities: list[DashboardActivity]


class FrontMyPageUpdate(BaseModel):
    name: str
    gender: str = "MALE"
    age: int = 20
    intro: Optional[str] = ""
    email: str


class FrontMyPageProfile(BaseModel):
    id: int
    name: str
    gender: str
    age: int
    intro: Optional[str] = None
    email: str
    book_count: int = 0
    comment_count: int = 0
    scrap_count: int = 0


class FrontMyPageActivity(BaseModel):
    type: str
    title: str
    description: str
    time: str


class FrontMyPageResponse(BaseModel):
    profile: FrontMyPageProfile
    activities: list[FrontMyPageActivity]
    books: list[FrontBookResponse]
    scraps: list[FrontScrapResponse]
    comments: list[FrontCommentResponse]
class FrontPlaylistCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    creator_name: str = "Guest User"


class FrontPlaylistSongCreate(BaseModel):
    title: str
    artist: str
    url: Optional[str] = ""


class FrontPlaylistSongResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playlist_id: int
    title: str
    artist: str
    url: Optional[str] = None
    like_count: int
    created_at: datetime


class FrontPlaylistResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    creator_name: str
    song_count: int = 0
    total_likes: int = 0
    created_at: datetime
    songs: list[FrontPlaylistSongResponse] = Field(default_factory=list)

# =========================
# Helpers
# =========================

def gender_to_string(gender):
    if hasattr(gender, "value"):
        return gender.value
    return str(gender)


def parse_gender(value: str):
    if value and value.upper() == "FEMALE":
        return Gender.FEMALE
    return Gender.MALE


def hash_password(password: str):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: Optional[str]):
    if not password_hash:
        return False
    return hash_password(password) == password_hash


def get_current_front_user(db: Session, user_id: Optional[int] = None):
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user

    user = db.query(User).order_by(User.id.asc()).first()

    if not user:
        user = User(
            name="Guest User",
            gender=Gender.MALE,
            age=20,
            intro="This is a default user profile.",
            email="guest@frontend.local",
            password_hash=hash_password("1234"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def make_login_response(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "gender": gender_to_string(user.gender),
        "age": user.age,
        "intro": user.intro,
    }


def make_author_response(author: User, db: Session):
    book_count = db.query(Book).filter(Book.author_id == author.id).count()

    return {
        "id": author.id,
        "name": author.name,
        "gender": gender_to_string(author.gender),
        "age": author.age,
        "intro": author.intro,
        "email": author.email,
        "book_count": book_count,
    }


def make_book_response(book: Book, author_name: str = "Unknown Author"):
    return {
        "id": book.id,
        "name": book.name,
        "intro": getattr(book, "intro", None),
        "author_id": getattr(book, "author_id", None),
        "author_name": author_name or "Unknown Author",
        "like_count": 0,
    }


# =========================
# Auth / Login
# =========================

@router.get("/auth/users", response_model=list[FrontLoginResponse])
def get_login_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).all()
    return [make_login_response(user) for user in users]


@router.post("/auth/login", response_model=FrontLoginResponse)
def login(dto: FrontLoginRequest, db: Session = Depends(get_db)):
    email = dto.email.strip()
    password = dto.password.strip()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    return make_login_response(user)


@router.post(
    "/auth/register",
    response_model=FrontLoginResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(dto: FrontRegisterRequest, db: Session = Depends(get_db)):
    name = dto.name.strip()
    email = dto.email.strip()
    password = dto.password.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    existing = db.query(User).filter(User.email == email).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        gender=parse_gender(dto.gender),
        age=dto.age,
        intro=dto.intro or "",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return make_login_response(user)


# =========================
# My Page
# =========================

@router.get("/me", response_model=FrontMyPageResponse)
def get_my_page(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    user = get_current_front_user(db, user_id)

    books = (
        db.query(Book)
        .filter(Book.author_id == user.id)
        .order_by(Book.id.desc())
        .all()
    )

    comments = (
        db.query(FrontComment)
        .filter(FrontComment.user_name == user.name)
        .order_by(FrontComment.created_at.desc())
        .limit(20)
        .all()
    )

    scraps = (
        db.query(FrontScrap)
        .order_by(FrontScrap.created_at.desc())
        .limit(20)
        .all()
    )

    book_items = [make_book_response(book, user.name) for book in books]

    activities = []

    for book in books[:3]:
        activities.append(
            {
                "type": "book",
                "title": "Book created",
                "description": book.name,
                "time": "Recently",
            }
        )

    for comment in comments[:3]:
        preview = comment.content[:70] + "..." if len(comment.content) > 70 else comment.content
        activities.append(
            {
                "type": "comment",
                "title": "Comment written",
                "description": preview,
                "time": "Recently",
            }
        )

    for scrap in scraps[:3]:
        preview = scrap.sentence_content[:70] + "..." if len(scrap.sentence_content) > 70 else scrap.sentence_content
        activities.append(
            {
                "type": "scrap",
                "title": f"Sentence saved from {scrap.book_name}",
                "description": preview,
                "time": "Recently",
            }
        )

    if not activities:
        activities.append(
            {
                "type": "system",
                "title": "No activity yet",
                "description": "Start reading, commenting, or bookmarking sentences.",
                "time": "Now",
            }
        )

    return {
        "profile": {
            "id": user.id,
            "name": user.name,
            "gender": gender_to_string(user.gender),
            "age": user.age,
            "intro": user.intro,
            "email": user.email,
            "book_count": len(books),
            "comment_count": len(comments),
            "scrap_count": len(scraps),
        },
        "activities": activities[:8],
        "books": book_items,
        "scraps": scraps,
        "comments": comments,
    }


@router.put("/me", response_model=FrontMyPageProfile)
def update_my_page(
    dto: FrontMyPageUpdate,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    user = get_current_front_user(db, user_id)

    name = dto.name.strip()
    email = dto.email.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    existing = (
        db.query(User)
        .filter(User.email == email, User.id != user.id)
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    old_name = user.name

    user.name = name
    user.email = email
    user.gender = parse_gender(dto.gender)
    user.age = dto.age
    user.intro = dto.intro or ""

    db.query(FrontComment).filter(FrontComment.user_name == old_name).update(
        {"user_name": name}
    )

    db.commit()
    db.refresh(user)

    book_count = db.query(Book).filter(Book.author_id == user.id).count()
    comment_count = db.query(FrontComment).filter(FrontComment.user_name == user.name).count()
    scrap_count = db.query(FrontScrap).count()

    return {
        "id": user.id,
        "name": user.name,
        "gender": gender_to_string(user.gender),
        "age": user.age,
        "intro": user.intro,
        "email": user.email,
        "book_count": book_count,
        "comment_count": comment_count,
        "scrap_count": scrap_count,
    }
@router.put("/me/password")
def update_my_password(
    dto: FrontPasswordUpdate,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    user = get_current_front_user(db, user_id)

    old_password = dto.old_password.strip()
    new_password = dto.new_password.strip()

    if not old_password:
        raise HTTPException(status_code=400, detail="Old password is required")

    if not new_password:
        raise HTTPException(status_code=400, detail="New password is required")

    if len(new_password) < 4:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 4 characters",
        )

    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    user.password_hash = hash_password(new_password)

    db.commit()

    return {"message": "Password updated successfully"}

# =========================
# Authors
# =========================

@router.get("/authors", response_model=list[FrontAuthorResponse])
def get_authors(db: Session = Depends(get_db)):
    authors = db.query(User).order_by(User.id.desc()).all()
    return [make_author_response(author, db) for author in authors]


@router.post(
    "/authors",
    response_model=FrontAuthorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_author(dto: FrontAuthorCreate, db: Session = Depends(get_db)):
    name = dto.name.strip()
    email = dto.email.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Author name is required")

    if not email:
        raise HTTPException(status_code=400, detail="Author email is required")

    existing = db.query(User).filter(User.email == email).first()

    if existing:
        raise HTTPException(status_code=400, detail="Author email already exists")

    author = User(
        name=name,
        gender=parse_gender(dto.gender),
        age=dto.age,
        intro=dto.intro or "",
        email=email,
        password_hash=hash_password("1234"),
    )

    db.add(author)
    db.commit()
    db.refresh(author)

    return make_author_response(author, db)


@router.get("/authors/{author_id}", response_model=FrontAuthorDetailResponse)
def get_author_detail(author_id: int, db: Session = Depends(get_db)):
    author = db.query(User).filter(User.id == author_id).first()

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    books = (
        db.query(Book)
        .filter(Book.author_id == author_id)
        .order_by(Book.id.desc())
        .all()
    )

    book_items = [make_book_response(book, author.name) for book in books]

    return {
        "id": author.id,
        "name": author.name,
        "gender": gender_to_string(author.gender),
        "age": author.age,
        "intro": author.intro,
        "email": author.email,
        "books": book_items,
    }


@router.put("/authors/{author_id}", response_model=FrontAuthorResponse)
def update_author(author_id: int, dto: FrontAuthorUpdate, db: Session = Depends(get_db)):
    author = db.query(User).filter(User.id == author_id).first()

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    name = dto.name.strip()
    email = dto.email.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Author name is required")

    if not email:
        raise HTTPException(status_code=400, detail="Author email is required")

    existing = (
        db.query(User)
        .filter(User.email == email, User.id != author_id)
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Author email already exists")

    author.name = name
    author.email = email
    author.gender = parse_gender(dto.gender)
    author.age = dto.age
    author.intro = dto.intro or ""

    db.commit()
    db.refresh(author)

    return make_author_response(author, db)


@router.delete("/authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(User).filter(User.id == author_id).first()

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    book_count = db.query(Book).filter(Book.author_id == author_id).count()

    if book_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete author because this author has books",
        )

    db.delete(author)
    db.commit()

    return {"message": "Author deleted"}


# =========================
# Books
# =========================

@router.post(
    "/books",
    response_model=FrontBookResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_book(dto: FrontBookCreate, db: Session = Depends(get_db)):
    book_name = dto.name.strip()
    author_name = dto.author_name.strip()

    if not book_name:
        raise HTTPException(status_code=400, detail="Book name is required")

    if not author_name:
        raise HTTPException(status_code=400, detail="Author name is required")

    email = dto.author_email or f"{author_name.lower().replace(' ', '.')}@frontend.local"

    author = db.query(User).filter(User.email == email).first()

    if not author:
        author = User(
            name=author_name,
            gender=Gender.MALE,
            age=20,
            intro=f"{author_name} is a frontend-created author.",
            email=email,
            password_hash=hash_password("1234"),
        )

        db.add(author)
        db.commit()
        db.refresh(author)

    book = Book(
        name=book_name,
        intro=dto.intro or "",
        author_id=author.id,
    )

    db.add(book)
    db.commit()
    db.refresh(book)

    for content in dto.sentences:
        clean_content = content.strip()

        if clean_content:
            sentence = Sentence(
                chapter=1,
                content=clean_content,
                after_id=None,
                book_id=book.id,
            )

            db.add(sentence)

    db.commit()

    return make_book_response(book, author.name)


@router.get("/books", response_model=list[FrontBookResponse])
def get_books(db: Session = Depends(get_db)):
    rows = (
        db.query(Book, User.name.label("author_name"))
        .join(User, Book.author_id == User.id, isouter=True)
        .order_by(Book.id.asc())
        .all()
    )

    return [make_book_response(book, author_name) for book, author_name in rows]


@router.get("/books/{book_id}", response_model=FrontBookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(Book, User.name.label("author_name"))
        .join(User, Book.author_id == User.id, isouter=True)
        .filter(Book.id == book_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Book not found")

    book, author_name = row

    return make_book_response(book, author_name)


# =========================
# Sentences
# =========================

@router.get("/books/{book_id}/sentences", response_model=list[FrontSentenceResponse])
def get_book_sentences(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return (
        db.query(Sentence)
        .filter(Sentence.book_id == book_id)
        .order_by(Sentence.chapter.asc(), Sentence.id.asc())
        .all()
    )


@router.post(
    "/books/{book_id}/sentences",
    response_model=FrontSentenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_book_sentence(
    book_id: int,
    dto: FrontSentenceCreate,
    db: Session = Depends(get_db),
):
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not dto.content.strip():
        raise HTTPException(status_code=400, detail="Sentence content is required")

    sentence = Sentence(
        chapter=dto.chapter,
        content=dto.content.strip(),
        after_id=dto.after_id,
        book_id=book_id,
    )

    db.add(sentence)
    db.commit()
    db.refresh(sentence)

    return sentence


# =========================
# Comments
# =========================

@router.get("/sentences/{sentence_id}/comments", response_model=list[FrontCommentResponse])
def get_sentence_comments(sentence_id: int, db: Session = Depends(get_db)):
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()

    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")

    return (
        db.query(FrontComment)
        .filter(FrontComment.sentence_id == sentence_id)
        .order_by(FrontComment.created_at.asc())
        .all()
    )


@router.post(
    "/sentences/{sentence_id}/comments",
    response_model=FrontCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sentence_comment(
    sentence_id: int,
    dto: FrontCommentCreate,
    db: Session = Depends(get_db),
):
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()

    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")

    if not dto.content.strip():
        raise HTTPException(status_code=400, detail="Comment content is required")

    comment = FrontComment(
        sentence_id=sentence_id,
        content=dto.content.strip(),
        user_name=dto.user_name or "Guest User",
        like_count=0,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


@router.post("/comments/{comment_id}/like", response_model=FrontCommentResponse)
def like_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(FrontComment).filter(FrontComment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.like_count += 1

    db.commit()
    db.refresh(comment)

    return comment


# =========================
# Scraps
# =========================

@router.get("/scraps", response_model=list[FrontScrapResponse])
def get_scraps(db: Session = Depends(get_db)):
    return (
        db.query(FrontScrap)
        .order_by(FrontScrap.created_at.desc())
        .all()
    )


@router.post(
    "/scraps",
    response_model=FrontScrapResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scrap(dto: FrontScrapCreate, db: Session = Depends(get_db)):
    sentence = db.query(Sentence).filter(Sentence.id == dto.sentence_id).first()

    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")

    book = db.query(Book).filter(Book.id == sentence.book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = (
        db.query(FrontScrap)
        .filter(FrontScrap.sentence_id == sentence.id)
        .first()
    )

    if existing:
        return existing

    scrap = FrontScrap(
        sentence_id=sentence.id,
        book_id=book.id,
        sentence_content=sentence.content,
        book_name=book.name,
    )

    db.add(scrap)
    db.commit()
    db.refresh(scrap)

    return scrap


@router.delete("/scraps/{scrap_id}")
def delete_scrap(scrap_id: int, db: Session = Depends(get_db)):
    scrap = db.query(FrontScrap).filter(FrontScrap.id == scrap_id).first()

    if not scrap:
        raise HTTPException(status_code=404, detail="Scrap not found")

    db.delete(scrap)
    db.commit()

    return {"message": "Scrap deleted"}
# =========================
# Music Search API - iTunes
# =========================

@router.get("/music/search", response_model=list[FrontMusicSearchItem])
def search_music(q: str, limit: int = 10):
    keyword = q.strip()

    if not keyword:
        return []

    params = urlencode(
        {
            "term": keyword,
            "country": "US",
            "media": "music",
            "entity": "song",
            "limit": max(1, min(limit, 20)),
        }
    )

    url = f"https://itunes.apple.com/search?{params}"

    try:
        request = Request(
            url,
            headers={
                "User-Agent": "InteractiveReader/1.0",
            },
        )

        with urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        results = data.get("results", [])

        items = []

        for item in results:
            preview_url = item.get("previewUrl") or ""

            if not preview_url:
                continue

            items.append(
                {
                    "title": item.get("trackName") or "Unknown Title",
                    "artist": item.get("artistName") or "Unknown Artist",
                    "album": item.get("collectionName") or "",
                    "preview_url": preview_url,
                    "artwork_url": item.get("artworkUrl100") or "",
                    "track_url": item.get("trackViewUrl") or "",
                }
            )

        return items

    except Exception as error:
        print("Music search failed:", error)
        raise HTTPException(
            status_code=500,
            detail="Music API search failed",
        )
# =========================
# Playlists
# =========================

def make_playlist_response(playlist: FrontPlaylist, db: Session):
    songs = (
        db.query(FrontPlaylistSong)
        .filter(FrontPlaylistSong.playlist_id == playlist.id)
        .order_by(FrontPlaylistSong.created_at.desc())
        .all()
    )

    total_likes = sum(song.like_count for song in songs)

    return {
        "id": playlist.id,
        "title": playlist.title,
        "description": playlist.description,
        "creator_name": playlist.creator_name,
        "song_count": len(songs),
        "total_likes": total_likes,
        "created_at": playlist.created_at,
        "songs": songs,
    }


@router.get("/playlists", response_model=list[FrontPlaylistResponse])
def get_playlists(db: Session = Depends(get_db)):
    playlists = (
        db.query(FrontPlaylist)
        .order_by(FrontPlaylist.created_at.desc())
        .all()
    )

    return [make_playlist_response(playlist, db) for playlist in playlists]


@router.post(
    "/playlists",
    response_model=FrontPlaylistResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_playlist(dto: FrontPlaylistCreate, db: Session = Depends(get_db)):
    title = dto.title.strip()

    if not title:
        raise HTTPException(status_code=400, detail="Playlist title is required")

    playlist = FrontPlaylist(
        title=title,
        description=dto.description or "",
        creator_name=dto.creator_name or "Guest User",
    )

    db.add(playlist)
    db.commit()
    db.refresh(playlist)

    return make_playlist_response(playlist, db)


@router.post(
    "/playlists/{playlist_id}/songs",
    response_model=FrontPlaylistSongResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_playlist_song(
    playlist_id: int,
    dto: FrontPlaylistSongCreate,
    db: Session = Depends(get_db),
):
    playlist = (
        db.query(FrontPlaylist)
        .filter(FrontPlaylist.id == playlist_id)
        .first()
    )

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    title = dto.title.strip()
    artist = dto.artist.strip()

    if not title:
        raise HTTPException(status_code=400, detail="Song title is required")

    if not artist:
        raise HTTPException(status_code=400, detail="Artist is required")

    song = FrontPlaylistSong(
        playlist_id=playlist_id,
        title=title,
        artist=artist,
        url=dto.url or "",
        like_count=0,
    )

    db.add(song)
    db.commit()
    db.refresh(song)

    return song


@router.post("/playlist-songs/{song_id}/like", response_model=FrontPlaylistSongResponse)
def like_playlist_song(song_id: int, db: Session = Depends(get_db)):
    song = (
        db.query(FrontPlaylistSong)
        .filter(FrontPlaylistSong.id == song_id)
        .first()
    )

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    song.like_count += 1

    db.commit()
    db.refresh(song)

    return song


@router.delete("/playlist-songs/{song_id}")
def delete_playlist_song(song_id: int, db: Session = Depends(get_db)):
    song = (
        db.query(FrontPlaylistSong)
        .filter(FrontPlaylistSong.id == song_id)
        .first()
    )

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    db.delete(song)
    db.commit()

    return {"message": "Song deleted"}


@router.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    playlist = (
        db.query(FrontPlaylist)
        .filter(FrontPlaylist.id == playlist_id)
        .first()
    )

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    db.query(FrontPlaylistSong).filter(
        FrontPlaylistSong.playlist_id == playlist_id
    ).delete()

    db.delete(playlist)
    db.commit()

    return {"message": "Playlist deleted"}
# =========================
# Dashboard
# =========================

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    books_count = db.query(Book).count()
    readers_count = db.query(User).count()
    comments_count = db.query(FrontComment).count()
    scraps_count = db.query(FrontScrap).count()

    chapters_count = (
        db.query(Sentence.book_id, Sentence.chapter)
        .distinct()
        .count()
    )

    stats = [
        {"label": "Books", "value": books_count, "description": "등록된 도서"},
        {"label": "Chapters", "value": chapters_count, "description": "전체 챕터"},
        {"label": "Comments", "value": comments_count, "description": "문장별 댓글"},
        {"label": "Completed", "value": scraps_count, "description": "저장된 문장"},
        {"label": "Readers", "value": readers_count, "description": "전체 사용자"},
        {"label": "Playlists", "value": 0, "description": "음악 API 준비 중"},
    ]

    chapter_rows = (
        db.query(
            Sentence.chapter.label("chapter"),
            func.count(Sentence.id).label("count"),
        )
        .group_by(Sentence.chapter)
        .order_by(Sentence.chapter.asc())
        .limit(6)
        .all()
    )

    reading_overview = [
        {"month": f"Ch {row.chapter}", "value": int(row.count)}
        for row in chapter_rows
    ]

    if not reading_overview:
        reading_overview = [
            {"month": "Ch 1", "value": 0},
            {"month": "Ch 2", "value": 0},
            {"month": "Ch 3", "value": 0},
            {"month": "Ch 4", "value": 0},
            {"month": "Ch 5", "value": 0},
            {"month": "Ch 6", "value": 0},
        ]

    recent_activities = []

    latest_comments = (
        db.query(FrontComment)
        .order_by(FrontComment.created_at.desc())
        .limit(3)
        .all()
    )

    for comment in latest_comments:
        preview = comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
        recent_activities.append(
            {
                "type": "comment",
                "title": f"New comment: {preview}",
                "time": "Recently",
            }
        )

    latest_scraps = (
        db.query(FrontScrap)
        .order_by(FrontScrap.created_at.desc())
        .limit(2)
        .all()
    )

    for scrap in latest_scraps:
        recent_activities.append(
            {
                "type": "scrap",
                "title": f"Sentence bookmarked from {scrap.book_name}",
                "time": "Recently",
            }
        )

    latest_books = db.query(Book).order_by(Book.id.desc()).limit(2).all()

    for book in latest_books:
        recent_activities.append(
            {
                "type": "book",
                "title": f"Book available: {book.name}",
                "time": "Recently",
            }
        )

    if not recent_activities:
        recent_activities = [
            {
                "type": "system",
                "title": "No activity yet. Start reading and commenting.",
                "time": "Now",
            }
        ]

    return {
        "stats": stats,
        "readingOverview": reading_overview,
        "recentActivities": recent_activities[:6],
    }


# Tables are created at application startup via main.py / lifespan hook.
# Do NOT call create_frontend_tables() here to avoid unintended DB connections
# when this module is imported by scripts (e.g. seed_test_data.py).
# create_frontend_tables()  ← intentionally commented out