from auth_service import database, security
from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr

app = FastAPI()
router = APIRouter()

# Pydantic models define the shape of your request data
class UserCredentials(BaseModel):
    email: EmailStr
    password: str


@router.post("/new_user", status_code=status.HTTP_201_CREATED)
def register_new_user(user: UserCredentials):
    # 1. Gera um hash de senha seguro para o usuário
    hashed_password = security.hash_password(user.password)

    # 2. Cria o usuário e trata os erros que vêm da camada do banco de dados.
    try:
        database.create_user(user.email, hashed_password)
    except ValueError as e:
        # Captura o erro de e-mail duplicado levantado por `database.create_user`
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        # Captura outros erros inesperados do banco de dados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return {"message": f"User {user.email} registered successfully!"}


@router.post("/login")
def login_user(user: UserCredentials):
    stored_hash = database.get_password_hash_for_user(user.email)

    if not stored_hash or not security.verify_password(stored_hash, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"message": "Login successful!"}


app.include_router(router)
