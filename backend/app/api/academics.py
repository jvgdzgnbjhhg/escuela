from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import Context, Database, require_admin
from app.models import (
    AcademicYear,
    AuditEvent,
    Course,
    Enrollment,
    Section,
    Student,
    TeachingAssignment,
)
from app.schemas.identity import (
    AcademicYearInput,
    AcademicYearOut,
    AcademicYearUpdate,
    AssignmentInput,
    AssignmentOut,
    AssignmentUpdate,
    CourseInput,
    CourseOut,
    CourseUpdate,
    EnrollmentInput,
    EnrollmentOut,
    EnrollmentUpdate,
    Page,
    SectionInput,
    SectionOut,
    SectionUpdate,
    StudentInput,
    StudentOut,
    StudentUpdate,
    TransferInput,
)
from app.services.academics import record_view, scoped_query, validate_record
from app.services.audit import audit

router = APIRouter(tags=["estructura académica"])


def register_resource(path, model, create_type, update_type):
    output = {
        AcademicYear: AcademicYearOut,
        Course: CourseOut,
        Section: SectionOut,
        Student: StudentOut,
        Enrollment: EnrollmentOut,
        TeachingAssignment: AssignmentOut,
    }[model]

    def list_records(
        context: Context,
        db: Database,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        q: str = Query(default="", max_length=100),
        status: str | None = Query(default=None, pattern="^(ACTIVE|ARCHIVED)$"),
        section_id: UUID | None = None,
    ):
        statement = scoped_query(model, context)
        if status:
            statement = statement.where(model.status == status)
        if q:
            search_column = getattr(model, "full_name", None)
            if search_column is None:
                search_column = getattr(model, "name", None)
            if search_column is not None:
                statement = statement.where(search_column.icontains(q, autoescape=True))
        if section_id and model is Student:
            # El subquery sigue limitado al tenant; no amplía el alcance docente.
            statement = statement.where(
                Student.id.in_(
                    select(Enrollment.student_id).where(
                        Enrollment.institution_id == context.institution.id,
                        Enrollment.section_id == section_id,
                        Enrollment.status == "ACTIVE",
                    )
                )
            )
        total = db.scalar(select(func.count()).select_from(statement.subquery()))
        items = db.scalars(
            statement.order_by(model.created_at.desc(), model.id).limit(limit).offset(offset)
        )
        return {
            "items": [record_view(item) for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_record(record_id: UUID, context: Context, db: Database):
        item = db.scalar(scoped_query(model, context).where(model.id == record_id))
        if item is None:
            raise HTTPException(404, "Registro no disponible")
        return record_view(item)

    def create_record(payload: create_type, context: Context, db: Database):
        require_admin(context)
        values = payload.model_dump()
        validate_record(db, model, values, context.institution.id)
        item = model(institution_id=context.institution.id, **values)
        db.add(item)
        db.flush()
        result = record_view(item)
        audit(db, context, item, "CREATE", after=result)
        return result

    def update_record(record_id: UUID, payload: update_type, context: Context, db: Database):
        require_admin(context)
        item = db.scalar(
            scoped_query(model, context).where(model.id == record_id).with_for_update()
        )
        if item is None:
            raise HTTPException(404, "Registro no disponible")
        values = payload.model_dump()
        if item.version != values.pop("version"):
            raise HTTPException(409, "El registro cambió; recarga antes de guardar")
        before = record_view(item)
        validate_record(db, model, values, context.institution.id, existing=item)
        for key, value in values.items():
            setattr(item, key, value)
        item.version += 1
        db.flush()
        result = record_view(item)
        audit(db, context, item, "UPDATE", before, result)
        return result

    for method, suffix, endpoint, code in [
        ("GET", "", list_records, 200),
        ("GET", "/{record_id}", get_record, 200),
        ("POST", "", create_record, 201),
        ("PATCH", "/{record_id}", update_record, 200),
    ]:
        router.add_api_route(
            path + suffix,
            endpoint,
            methods=[method],
            status_code=code,
            response_model=Page[output] if endpoint is list_records else output,
            name=method.lower() + "_" + model.__tablename__ + suffix.replace("/", "_"),
        )


for spec in [
    ("/academic-years", AcademicYear, AcademicYearInput, AcademicYearUpdate),
    ("/courses", Course, CourseInput, CourseUpdate),
    ("/sections", Section, SectionInput, SectionUpdate),
    ("/students", Student, StudentInput, StudentUpdate),
    ("/enrollments", Enrollment, EnrollmentInput, EnrollmentUpdate),
    ("/teaching-assignments", TeachingAssignment, AssignmentInput, AssignmentUpdate),
]:
    register_resource(*spec)


@router.post("/enrollments/{record_id}/transfer", status_code=201, response_model=EnrollmentOut)
def transfer(record_id: UUID, payload: TransferInput, context: Context, db: Database):
    require_admin(context)
    enrollment = db.scalar(
        scoped_query(Enrollment, context).where(Enrollment.id == record_id).with_for_update()
    )
    if enrollment is None:
        raise HTTPException(404, "Matrícula no disponible")
    if enrollment.status != "ACTIVE" or enrollment.version != payload.version:
        raise HTTPException(409, "La matrícula cambió o ya está archivada")
    if payload.start_date <= enrollment.start_date or payload.section_id == enrollment.section_id:
        raise HTTPException(
            422, "El traslado debe cambiar de sección y comenzar después de la matrícula"
        )
    section = db.get(Section, enrollment.section_id)
    year = db.get(AcademicYear, section.academic_year_id)
    original_end = enrollment.end_date
    if payload.start_date > (original_end or year.end_date):
        raise HTTPException(422, "La matrícula ya había terminado en la fecha del traslado")
    before = record_view(enrollment)
    enrollment.end_date = payload.start_date - timedelta(days=1)
    enrollment.status = "ARCHIVED" if enrollment.end_date < date.today() else "ACTIVE"
    enrollment.version += 1
    db.flush()
    values = {
        "student_id": enrollment.student_id,
        "section_id": payload.section_id,
        "start_date": payload.start_date,
        "end_date": original_end,
        "status": "ACTIVE",
    }
    validate_record(db, Enrollment, values, context.institution.id)
    new = Enrollment(institution_id=context.institution.id, **values)
    db.add(new)
    db.flush()
    audit(db, context, enrollment, "TRANSFER_OUT", before, record_view(enrollment))
    audit(db, context, new, "TRANSFER_IN", after=record_view(new))
    return record_view(new)


@router.get("/audit-events")
def audit_events(
    context: Context,
    db: Database,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    if context.membership.role not in {"ADMIN", "COORDINATOR", "VIEWER"}:
        raise HTTPException(403, "No tienes permiso para consultar auditoría")
    items = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.institution_id == context.institution.id)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id)
        .limit(limit)
        .offset(offset)
    )
    return {
        "items": [
            {
                key: getattr(item, key)
                for key in (
                    "id",
                    "actor_id",
                    "entity_type",
                    "entity_id",
                    "action",
                    "details",
                    "created_at",
                )
            }
            for item in items
        ]
    }
