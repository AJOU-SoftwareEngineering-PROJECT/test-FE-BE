"""
seed_test_data.py
─────────────────────────────────────────────────────────────
프론트엔드-백엔드 연동 테스트용 초기 데이터 주입 스크립트

실행 방법 (SE_backend 디렉터리에서):
    python seed_test_data.py

동작:
  1. 모든 테이블 DROP → 재생성 (깔끔한 초기화)
  2. User / Book / Sentence (linked-list after_id 구조) 생성
  3. FrontComment / FrontScrap / FrontPlaylist / FrontPlaylistSong 생성
"""

# ── Windows 한글 로케일 CP949 오류 메시지 해결 ──────────────────────
# psycopg2 가 libpq 오류 메시지를 CP949 로 반환할 때
# Python 의 UTF-8 디코딩이 실패하는 문제를 방지한다.
import sys, os, locale

# 1) PostgreSQL 클라이언트 메시지 언어를 영어(ASCII)로 강제
os.environ.setdefault("PGCLIENTENCODING", "UTF8")
os.environ.setdefault("LC_MESSAGES", "C")
os.environ.setdefault("LANG", "en_US.UTF-8")

# 2) Python 표준 스트림을 UTF-8 로 재구성
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 3) psycopg2 가 UnicodeDecodeError 를 던질 때 CP949 로 재시도하는 패치
import psycopg2 as _psycopg2
_original_connect = _psycopg2.connect

def _patched_connect(*args, **kwargs):
    try:
        return _original_connect(*args, **kwargs)
    except UnicodeDecodeError:
        # libpq 가 CP949 메시지를 보낸 경우 — 연결 자체를 재시도하고
        # 오류 메시지를 ASCII safe 로 표시
        try:
            return _original_connect(*args, **kwargs)
        except UnicodeDecodeError as ude:
            raw = ude.object  # bytes
            decoded = raw.decode("cp949", errors="replace")
            raise _psycopg2.OperationalError(
                f"[psycopg2 connection error – decoded as CP949]\n{decoded}"
            ) from None

_psycopg2.connect = _patched_connect

from datetime import datetime


# ── DB 세션 & 엔진 ─────────────────────────────────────────
from db.database import Base, engine, SessionLocal

# ── ORM 모델 (db.model) ────────────────────────────────────
import db.model  # noqa: F401 – Base 에 모든 모델 등록
from db.model import Book, Gender, Sentence, User

# ── Frontend 전용 테이블: controller import 는 나중에 lazy import
#    (controller.py 마지막 줄의 create_frontend_tables() 가 import 시
#     DB 연결을 시도하므로, drop_all/create_all 이후에 import 해야 함)

# ═══════════════════════════════════════════════════════════
# 헬퍼
# ═══════════════════════════════════════════════════════════

def now() -> datetime:
    return datetime.utcnow()


def _build_linked_sentences(db, book_id: int, chapter: int, contents: list) -> list:
    """
    contents 순서대로 Sentence를 생성하고 after_id를 이용한
    단방향 연결 리스트 구조로 이어 붙인다.

    연결 방향 (앞 문장 ← 뒤 문장):
        s1(after_id=None)  ←  s2(after_id=s1.id)  ←  s3(after_id=s2.id)  ←  …
    """
    # 1) 첫 문장을 head 로 삽입 (after_id=None → 리스트 선두)
    head = Sentence(chapter=chapter, content=contents[0], after_id=None, book_id=book_id)
    db.add(head)
    db.flush()  # id 확보

    sentences = [head]
    prev_id = head.id

    # 2) 나머지 문장들을 순서대로 연결
    for content in contents[1:]:
        s = Sentence(chapter=chapter, content=content, after_id=prev_id, book_id=book_id)
        db.add(s)
        db.flush()
        sentences.append(s)
        prev_id = s.id

    return sentences


# ═══════════════════════════════════════════════════════════
# 메인 시드 함수
# ═══════════════════════════════════════════════════════════

def seed():
    # ── 1. DROP ALL → CREATE ALL ────────────────────────────
    print("=" * 55)
    print("▶  모든 테이블 DROP 후 재생성 중...")

    # controller.py 를 미리 import 해서 FrontComment 등 모델을
    # Base 에 등록시켜야 drop_all / create_all 이 해당 테이블까지 포함함.
    # 단, controller.py 마지막 줄의 create_frontend_tables() 가
    # import 시점에 DB 연결을 시도하므로 아래 순서를 지켜야 함:
    #   (a) import 만 먼저 → 이 시점에 create_frontend_tables() 가 호출되지만
    #       DB 가 이미 연결 가능한 상태이면 문제없음
    #   (b) 이후 drop_all → create_all 로 깨끗하게 초기화
    from frontend_api.controller import (  # noqa: E402
        FrontComment,
        FrontPlaylist,
        FrontPlaylistSong,
        FrontScrap,
        hash_password,
    )

    # 모든 테이블 삭제 후 재생성
    # drop_all 은 외래 키 순서 문제로 실패할 수 있으므로
    # DROP SCHEMA ... CASCADE 로 한 번에 초기화한다.
    with engine.begin() as conn:
        conn.execute(__import__("sqlalchemy").text("DROP SCHEMA public CASCADE"))
        conn.execute(__import__("sqlalchemy").text("CREATE SCHEMA public"))
    Base.metadata.create_all(bind=engine)
    print("✔  테이블 초기화 완료\n")

    db = SessionLocal()

    try:
        # ── 2. User 생성 ────────────────────────────────────
        print("▶  User 생성 중...")

        author = User(
            name="Test Author",
            gender=Gender.MALE,
            age=30,
            intro="소프트웨어 공학 수업용 테스트 계정입니다. 소설 창작을 즐깁니다.",
            email="test@example.com",
            password_hash=hash_password("1234"),
        )
        db.add(author)
        db.flush()  # author.id 확보
        print(f"  + User id={author.id}  name='{author.name}'  email='{author.email}'")

        # 대시보드 댓글 user_name 매칭용 추가 독자 계정
        reader = User(
            name="Reader One",
            gender=Gender.FEMALE,
            age=25,
            intro="독서를 좋아하는 독자입니다.",
            email="reader@example.com",
            password_hash=hash_password("1234"),
        )
        db.add(reader)
        db.flush()
        print(f"  + User id={reader.id}  name='{reader.name}'  email='{reader.email}'")

        # ── 3. Book 생성 ────────────────────────────────────
        print("\n▶  Book 생성 중...")

        book1 = Book(
            name="별빛이 내리는 밤",
            intro=(
                "한 청년이 기억을 잃은 채 낯선 마을에 도착하면서 시작되는 미스터리 소설. "
                "마을 사람들의 비밀과 얽힌 과거가 하나씩 드러나며 독자를 몰입시킨다."
            ),
            author_id=author.id,
        )
        db.add(book1)
        db.flush()
        print(f"  + Book id={book1.id}  name='{book1.name}'")

        book2 = Book(
            name="유리 정원의 시계",
            intro=(
                "시간을 멈출 수 있는 능력을 가진 소녀와 그녀를 쫓는 비밀 결사의 이야기. "
                "판타지와 로맨스가 어우러진 청소년 소설."
            ),
            author_id=author.id,
        )
        db.add(book2)
        db.flush()
        print(f"  + Book id={book2.id}  name='{book2.name}'")

        # ── 4. Sentence 생성 (after_id 연결 리스트) ─────────
        print("\n▶  Sentence 생성 중 (after_id 연결 리스트)...")

        book1_contents = [
            "그가 눈을 떴을 때 주위는 온통 낯선 풍경이었다.",
            "머릿속에는 자신의 이름조차 떠오르지 않았고, 다만 별빛이 쏟아지는 하늘만이 선명했다.",
            "마을 입구에는 녹슨 간판이 하나 서 있었다. '환영합니다 — 잊혀진 마을, 별하.'",
            "낡은 여관 문을 두드리자 주름진 노인이 문을 열었다. 그의 눈빛에는 두려움이 담겨 있었다.",
            "\"당신이 드디어 돌아왔군요.\" 노인이 속삭였다. \"하지만 기억은 두고 온 모양이에요.\"",
        ]

        book2_contents = [
            "세상에서 가장 아름다운 정원은 유리로 만들어져 있다고 사람들은 말했다.",
            "하지만 그 정원에 들어간 사람은 아무도 돌아오지 않았다 — 루나가 나타나기 전까지는.",
            "루나는 손목의 시계를 두드렸다. 째깍째깍 소리가 멈추는 순간, 세상이 정지했다.",
            "그녀는 얼어붙은 빗방울 사이를 걸었다. 이 능력을 아는 사람은 아직 없었다.",
            "그날 밤, 처음으로 그림자가 그녀의 뒤를 따라왔다. 그것은 인간의 형상을 하고 있었다.",
        ]

        b1_sentences = _build_linked_sentences(db, book1.id, chapter=1, contents=book1_contents)
        print(f"  + Book1 Sentence ids={[s.id for s in b1_sentences]}")
        for s in b1_sentences:
            print(f"      Sentence id={s.id}  after_id={s.after_id}  '{s.content[:30]}...'")

        b2_sentences = _build_linked_sentences(db, book2.id, chapter=1, contents=book2_contents)
        print(f"  + Book2 Sentence ids={[s.id for s in b2_sentences]}")
        for s in b2_sentences:
            print(f"      Sentence id={s.id}  after_id={s.after_id}  '{s.content[:30]}...'")

        # ── 5. FrontComment 생성 ────────────────────────────
        print("\n▶  FrontComment 생성 중...")

        front_comments_data = [
            dict(
                sentence_id=b1_sentences[0].id,
                content="첫 문장부터 분위기가 압도적이에요. 계속 읽고 싶어집니다.",
                user_name=author.name,
                like_count=4,
            ),
            dict(
                sentence_id=b1_sentences[2].id,
                content="'잊혀진 마을'이라는 이름이 너무 인상적이에요. 복선 같기도 하고.",
                user_name=reader.name,
                like_count=7,
            ),
            dict(
                sentence_id=b2_sentences[1].id,
                content="루나가 유리 정원에서 살아 돌아온 이유가 궁금해요!",
                user_name=reader.name,
                like_count=3,
            ),
        ]

        for fc_data in front_comments_data:
            fc = FrontComment(
                sentence_id=fc_data["sentence_id"],
                content=fc_data["content"],
                user_name=fc_data["user_name"],
                like_count=fc_data["like_count"],
                created_at=now(),
            )
            db.add(fc)
            db.flush()
            print(f"  + FrontComment id={fc.id}  sentence_id={fc.sentence_id}  user='{fc.user_name}'")

        # ── 6. FrontScrap 생성 ──────────────────────────────
        print("\n▶  FrontScrap 생성 중...")

        front_scraps_data = [
            dict(
                sentence_id=b1_sentences[4].id,
                book_id=book1.id,
                sentence_content=b1_sentences[4].content,
                book_name=book1.name,
            ),
            dict(
                sentence_id=b2_sentences[2].id,
                book_id=book2.id,
                sentence_content=b2_sentences[2].content,
                book_name=book2.name,
            ),
            dict(
                sentence_id=b2_sentences[4].id,
                book_id=book2.id,
                sentence_content=b2_sentences[4].content,
                book_name=book2.name,
            ),
        ]

        for fs_data in front_scraps_data:
            fs = FrontScrap(
                sentence_id=fs_data["sentence_id"],
                book_id=fs_data["book_id"],
                sentence_content=fs_data["sentence_content"],
                book_name=fs_data["book_name"],
                created_at=now(),
            )
            db.add(fs)
            db.flush()
            print(f"  + FrontScrap id={fs.id}  book='{fs.book_name}'  sentence_id={fs.sentence_id}")

        # ── 7. FrontPlaylist & FrontPlaylistSong 생성 ────────
        print("\n▶  FrontPlaylist 생성 중...")

        playlist1 = FrontPlaylist(
            title="독서 집중 모드",
            description="소설을 읽을 때 집중력을 높여주는 Lo-fi & 어쿠스틱 플레이리스트.",
            creator_name=author.name,
            created_at=now(),
        )
        db.add(playlist1)
        db.flush()
        print(f"  + FrontPlaylist id={playlist1.id}  title='{playlist1.title}'")

        playlist2 = FrontPlaylist(
            title="밤하늘 감성 BGM",
            description="별빛 가득한 밤에 어울리는 잔잔한 피아노 음악 모음.",
            creator_name=reader.name,
            created_at=now(),
        )
        db.add(playlist2)
        db.flush()
        print(f"  + FrontPlaylist id={playlist2.id}  title='{playlist2.title}'")

        playlist3 = FrontPlaylist(
            title="판타지 독서 OST",
            description="유리 정원의 시계 같은 판타지 소설에 어울리는 영화 OST 모음.",
            creator_name=author.name,
            created_at=now(),
        )
        db.add(playlist3)
        db.flush()
        print(f"  + FrontPlaylist id={playlist3.id}  title='{playlist3.title}'")

        print("\n▶  FrontPlaylistSong 생성 중...")

        songs_data = [
            # playlist1 노래
            dict(
                playlist_id=playlist1.id,
                title="Lofi Hip Hop Study",
                artist="ChilledCow",
                url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                like_count=12,
            ),
            dict(
                playlist_id=playlist1.id,
                title="Calm Acoustic Guitar",
                artist="Peaceful Morning",
                url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
                like_count=8,
            ),
            # playlist2 노래
            dict(
                playlist_id=playlist2.id,
                title="Starlight Piano",
                artist="Nightfall Ensemble",
                url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
                like_count=15,
            ),
            dict(
                playlist_id=playlist2.id,
                title="Moonlit Waltz",
                artist="Clara Sola",
                url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
                like_count=9,
            ),
            # playlist3 노래
            dict(
                playlist_id=playlist3.id,
                title="Epic Fantasy Theme",
                artist="Two Steps From Hell",
                url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
                like_count=21,
            ),
        ]

        for song_data in songs_data:
            song = FrontPlaylistSong(
                playlist_id=song_data["playlist_id"],
                title=song_data["title"],
                artist=song_data["artist"],
                url=song_data["url"],
                like_count=song_data["like_count"],
                created_at=now(),
            )
            db.add(song)
            db.flush()
            print(f"  + FrontPlaylistSong id={song.id}  playlist_id={song.playlist_id}  title='{song.title}'")

        # ── 최종 커밋 ────────────────────────────────────────
        db.commit()

        print("\n" + "=" * 55)
        print("✅  시드 데이터 주입 완료!")
        print("-" * 55)
        print("📋 생성된 데이터 요약")
        print(f"  User       : {author.name} ({author.email})")
        print(f"             : {reader.name} ({reader.email})")
        print(f"  Book       : '{book1.name}' (id={book1.id})")
        print(f"             : '{book2.name}' (id={book2.id})")
        print(f"  Sentence   : Book1 {len(b1_sentences)}개, Book2 {len(b2_sentences)}개 (after_id 연결 리스트)")
        print(f"  FrontComment  : {len(front_comments_data)}개")
        print(f"  FrontScrap    : {len(front_scraps_data)}개")
        print(f"  FrontPlaylist : 3개 / FrontPlaylistSong : {len(songs_data)}개")
        print("-" * 55)
        print("🔑 로그인 계정 (비밀번호: 1234)")
        print(f"  {author.email}")
        print(f"  {reader.email}")
        print("=" * 55)

    except Exception as exc:
        db.rollback()
        print(f"\n❌  시드 실패: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()