from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert

from app.api.dependencies import Authenticated, Database, check_origin
from app.models import Institution, LoginBudget, LoginSession, Membership, User
from app.schemas.identity import ChangePassword, Login, SessionOut
from app.services.security import (
    COOKIE_NAME,
    csrf_for,
    digest,
    hash_password,
    hasher,
    new_token,
    now,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["identidad"])


def session_view(identity, db):
    rows = db.execute(
        select(Institution, Membership)
        .join(Membership, Membership.institution_id == Institution.id)
        .where(
            Membership.user_id == identity.user.id,
            Membership.status == "ACTIVE",
            Institution.status == "ACTIVE",
        )
        .order_by(Institution.name)
    ).all()
    return {
        "user": {
            "id": identity.user.id,
            "email": identity.user.email,
            "full_name": identity.user.full_name,
        },
        "institutions": [{"id": i.id, "name": i.name, "role": m.role} for i, m in rows],
        "csrf_token": csrf_for(identity.token),
    }


def login_budget(request, db, email):
    clock = now().timestamp()
    window = int(clock // 900)
    remote = request.client.host if request.client else "unknown"
    exceeded = False
    for key, limit in [("email:" + email, 8), ("remote:" + remote, 120)]:
        hashed = digest(key)
        statement = insert(LoginBudget).values(key=hashed, window=window, attempts=1)
        statement = statement.on_conflict_do_update(
            index_elements=[LoginBudget.key],
            set_={
                "window": window,
                "attempts": case((LoginBudget.window == window, LoginBudget.attempts + 1), else_=1),
            },
        ).returning(LoginBudget.attempts)
        exceeded |= db.scalar(statement) > limit
    db.commit()  # Los intentos fallidos también consumen presupuesto durable.
    if exceeded:
        raise HTTPException(
            429,
            "Demasiados intentos; espera antes de volver a intentar",
            headers={"Retry-After": str(900 - int(clock % 900))},
        )


@router.post("/login")
def login(payload: Login, request: Request, response: Response, db: Database):
    check_origin(request)
    email = str(payload.email).lower()
    login_budget(request, db, email)
    user = db.scalar(select(User).where(User.email == email))
    encoded = user.password_hash if user else request.app.state.dummy_password_hash
    valid = verify_password(encoded, payload.password.get_secret_value())
    if not valid or user is None or not user.active:
        raise HTTPException(401, "Correo o contraseña incorrectos")
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password.get_secret_value())
    previous = request.cookies.get(COOKIE_NAME)
    if previous:
        db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(previous)))
    token = new_token()
    clock = now()
    db.add(
        LoginSession(
            token_hash=digest(token),
            user_id=user.id,
            expires_at=clock + timedelta(hours=8),
            last_seen_at=clock,
        )
    )
    db.flush()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=8 * 3600,
        httponly=True,
        secure=request.app.state.settings.app_env == "production",
        samesite="lax",
        path="/",
    )
    return {"status": "authenticated"}


@router.get("/me", response_model=SessionOut)
def me(identity: Authenticated, db: Database):
    return session_view(identity, db)


@router.post("/logout", status_code=204)
def logout(identity: Authenticated, db: Database, response: Response):
    db.delete(identity.session)
    response.delete_cookie(COOKIE_NAME, path="/")


@router.post("/password", status_code=204)
def change_password(
    payload: ChangePassword,
    identity: Authenticated,
    db: Database,
    response: Response,
    request: Request,
):
    login_budget(request, db, "password:" + identity.user.email)
    if not verify_password(
        identity.user.password_hash, payload.current_password.get_secret_value()
    ):
        raise HTTPException(400, "La contraseña actual no es correcta")
    if payload.current_password.get_secret_value() == payload.new_password.get_secret_value():
        raise HTTPException(400, "Elige una contraseña diferente")
    identity.user.password_hash = hash_password(payload.new_password.get_secret_value())
    db.execute(delete(LoginSession).where(LoginSession.user_id == identity.user.id))
    response.delete_cookie(COOKIE_NAME, path="/")
