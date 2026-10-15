from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.auth import session_view
from app.api.dependencies import Authenticated, Context, Database, require_admin
from app.models import Institution, Membership, TeachingAssignment, User
from app.schemas.identity import InstitutionInput, MemberInput, MemberOut, MemberUpdate, Page
from app.services.audit import audit
from app.services.security import hash_password

router = APIRouter(prefix="/institutions", tags=["instituciones"])


def member_view(member, user):
    return {
        "id": member.id,
        "user_id": member.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": member.role,
        "status": member.status,
        "version": member.version,
    }


@router.get("")
def institutions(identity: Authenticated, db: Database):
    return {"items": session_view(identity, db)["institutions"]}


@router.post("", status_code=201)
def create_institution(payload: InstitutionInput, context: Context, db: Database):
    require_admin(context)
    institution = Institution(name=payload.name)
    db.add(institution)
    db.flush()
    membership = Membership(
        institution_id=institution.id, user_id=context.identity.user.id, role="ADMIN"
    )
    db.add(membership)
    db.flush()
    from app.api.dependencies import Tenant

    audit(
        db,
        Tenant(institution, membership, context.identity),
        institution,
        "CREATE",
        after={"name": institution.name},
    )
    return {"id": institution.id, "name": institution.name, "role": "ADMIN"}


def same_context(institution_id, context):
    if institution_id != context.institution.id:
        raise HTTPException(404, "Institución no disponible en el contexto actual")


@router.patch("/{institution_id}")
def rename_institution(
    institution_id: UUID, payload: InstitutionInput, context: Context, db: Database
):
    same_context(institution_id, context)
    require_admin(context)
    before = {"name": context.institution.name}
    context.institution.name = payload.name
    audit(db, context, context.institution, "RENAME", before, {"name": payload.name})
    return {"id": institution_id, "name": payload.name}


@router.get("/{institution_id}/members", response_model=Page[MemberOut])
def list_members(
    institution_id: UUID,
    context: Context,
    db: Database,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    same_context(institution_id, context)
    require_admin(context)
    query = (
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.institution_id == institution_id)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(User.full_name, Membership.id).limit(limit).offset(offset))
    return {
        "items": [member_view(m, u) for m, u in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{institution_id}/members", status_code=201, response_model=MemberOut)
def create_member(institution_id: UUID, payload: MemberInput, context: Context, db: Database):
    same_context(institution_id, context)
    require_admin(context)
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        if payload.initial_password is None:
            raise HTTPException(
                422, "Una cuenta nueva requiere una contraseña inicial de 12 caracteres o más"
            )
        user = User(
            email=email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.initial_password.get_secret_value()),
        )
        db.add(user)
        db.flush()
    else:
        if payload.initial_password is not None:
            raise HTTPException(409, "La cuenta ya existe; vincúlala sin cambiar su contraseña")
        if not user.active:
            raise HTTPException(409, "La cuenta no está disponible")
    if db.scalar(
        select(Membership.id).where(
            Membership.institution_id == institution_id, Membership.user_id == user.id
        )
    ):
        raise HTTPException(409, "La cuenta ya tiene una membresía; edita su estado")
    membership = Membership(institution_id=institution_id, user_id=user.id, role=payload.role)
    db.add(membership)
    db.flush()
    result = member_view(membership, user)
    audit(db, context, membership, "CREATE", after=result)
    return result


@router.patch("/{institution_id}/members/{member_id}", response_model=MemberOut)
def update_member(
    institution_id: UUID, member_id: UUID, payload: MemberUpdate, context: Context, db: Database
):
    same_context(institution_id, context)
    require_admin(context)
    # Serializa cambios de rol y evita dos revocaciones del último administrador.
    db.scalar(select(Institution).where(Institution.id == institution_id).with_for_update())
    member = db.scalar(
        select(Membership)
        .where(Membership.id == member_id, Membership.institution_id == institution_id)
        .with_for_update()
    )
    if member is None:
        raise HTTPException(404, "Membresía no disponible")
    if member.version != payload.version:
        raise HTTPException(409, "La membresía cambió; recarga antes de guardar")
    if (
        member.role == "ADMIN"
        and member.status == "ACTIVE"
        and (payload.role != "ADMIN" or payload.status != "ACTIVE")
    ):
        other = db.scalar(
            select(Membership.id)
            .where(
                Membership.institution_id == institution_id,
                Membership.id != member.id,
                Membership.role == "ADMIN",
                Membership.status == "ACTIVE",
            )
            .limit(1)
        )
        if other is None:
            raise HTTPException(409, "La institución debe conservar al menos un administrador")
    user = db.get(User, member.user_id)
    before = member_view(member, user)
    member.role, member.status = payload.role, payload.status
    member.version += 1
    if payload.role != "TEACHER" or payload.status != "ACTIVE":
        assignments = db.scalars(
            select(TeachingAssignment).where(
                TeachingAssignment.institution_id == institution_id,
                TeachingAssignment.teacher_id == member.user_id,
                TeachingAssignment.status == "ACTIVE",
            )
        )
        for assignment in assignments:
            assignment.status = "ARCHIVED"
            assignment.version += 1
            audit(db, context, assignment, "ACCESS_REVOKED")
    db.flush()
    result = member_view(member, user)
    audit(db, context, member, "UPDATE", before, result)
    return result
