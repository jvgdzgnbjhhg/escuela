import secrets
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Institution, LoginSession, Membership, User
from app.services.security import COOKIE_NAME, csrf_for, digest, now


def get_db(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine, expire_on_commit=False) as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


Database = Annotated[Session, Depends(get_db, scope="function")]


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin not in request.app.state.settings.allowed_origins:
        raise HTTPException(403, "Origen de solicitud no permitido")


@dataclass
class Identity:
    user: User
    session: LoginSession
    token: str


def current_identity(request: Request, db: Database) -> Identity:
    token = request.cookies.get(COOKIE_NAME, "")
    session = db.get(LoginSession, digest(token)) if token else None
    clock = now()
    if (
        session is None
        or session.expires_at <= clock
        or session.last_seen_at < clock - timedelta(minutes=30)
    ):
        raise HTTPException(401, "Inicia sesión para continuar")
    user = db.get(User, session.user_id)
    if user is None or not user.active:
        raise HTTPException(401, "La sesión ya no está disponible")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_origin(request)
        if not secrets.compare_digest(
            request.headers.get("x-csrf-token", "").encode("utf-8"), csrf_for(token).encode("ascii")
        ):
            raise HTTPException(403, "No se pudo verificar la solicitud; vuelve a iniciar sesión")
    session.last_seen_at = clock
    return Identity(user, session, token)


Authenticated = Annotated[Identity, Depends(current_identity)]


@dataclass
class Tenant:
    institution: Institution
    membership: Membership
    identity: Identity


def current_tenant(request: Request, identity: Authenticated, db: Database) -> Tenant:
    try:
        institution_id = UUID(request.headers.get("x-institution-id", ""))
    except ValueError:
        raise HTTPException(400, "Selecciona una institución válida") from None
    institution_query = select(Institution).where(Institution.id == institution_id)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        # Orden único de bloqueo: institución antes de membresías y entidades.
        # Evita crear relaciones mientras otro administrador archiva sus padres.
        institution_query = institution_query.with_for_update()
    institution = db.scalar(institution_query)
    membership = db.scalar(
        select(Membership).where(
            Membership.institution_id == institution_id,
            Membership.user_id == identity.user.id,
            Membership.status == "ACTIVE",
        )
    )
    if institution is None or institution.status != "ACTIVE" or membership is None:
        raise HTTPException(403, "No tienes acceso a esta institución")
    if membership.role == "TECHNICAL":
        raise HTTPException(403, "El rol técnico no permite consultar contenido académico")
    return Tenant(institution, membership, identity)


Context = Annotated[Tenant, Depends(current_tenant)]


def require_admin(context: Tenant) -> None:
    if context.membership.role != "ADMIN":
        raise HTTPException(403, "Esta operación requiere administración institucional")
