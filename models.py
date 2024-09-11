from databases import Database
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

DATABASE_URL = "sqlite:///./passwords.db"


database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column("hashed_password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
)


passwords = sqlalchemy.Table(
    "passwords",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("length", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("username", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
)


engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
