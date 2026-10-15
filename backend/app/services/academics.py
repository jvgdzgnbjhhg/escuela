from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import (
    AcademicYear,
    Course,
    Enrollment,
    Membership,
    Section,
    Student,
    TeachingAssignment,
)

RESOURCE_FIELDS = {
    AcademicYear: ("name", "start_date", "end_date"),
    Course: ("name", "grade_level"),
    Section: ("course_id", "academic_year_id", "name"),
    Student: ("full_name", "student_code"),
    Enrollment: ("student_id", "section_id", "start_date", "end_date"),
    TeachingAssignment: ("teacher_id", "section_id", "academic_year_id", "subject"),
}


def record_view(record):
    fields = ("id", "institution_id", "status", "version", "created_at", "updated_at")
    return {key: getattr(record, key) for key in fields + RESOURCE_FIELDS[type(record)]}


def scoped_query(model, context):
    tenant = context.institution.id
    statement = select(model).where(model.institution_id == tenant)
    if context.membership.role != "TEACHER":
        return statement
    sections = select(TeachingAssignment.section_id).where(
        TeachingAssignment.institution_id == tenant,
        TeachingAssignment.teacher_id == context.identity.user.id,
        TeachingAssignment.status == "ACTIVE",
    )
    if model is TeachingAssignment:
        return statement.where(model.teacher_id == context.identity.user.id)
    if model is Section:
        return statement.where(model.id.in_(sections))
    if model is Enrollment:
        return statement.where(model.section_id.in_(sections))
    if model is Student:
        students = (
            select(Enrollment.student_id)
            .join(Section, Section.id == Enrollment.section_id)
            .join(AcademicYear, AcademicYear.id == Section.academic_year_id)
            .where(
                Enrollment.institution_id == tenant,
                Enrollment.section_id.in_(sections),
                Enrollment.status == "ACTIVE",
                Enrollment.start_date <= date.today(),
                func.coalesce(Enrollment.end_date, AcademicYear.end_date) >= date.today(),
            )
        )
        return statement.where(model.id.in_(students))
    column = Section.course_id if model is Course else Section.academic_year_id
    return statement.where(
        model.id.in_(
            select(column).where(Section.institution_id == tenant, Section.id.in_(sections))
        )
    )


def related(db, model, record_id, institution_id, active=True):
    result = db.scalar(
        select(model).where(model.id == record_id, model.institution_id == institution_id)
    )
    if result is None:
        raise HTTPException(404, "Registro relacionado no disponible en esta institución")
    if active and result.status != "ACTIVE":
        raise HTTPException(409, "No puedes utilizar un registro archivado")
    return result


def validate_record(db, model, payload, tenant, existing=None):
    if (
        existing
        and model is AcademicYear
        and (
            existing.start_date != payload["start_date"] or existing.end_date != payload["end_date"]
        )
        and db.scalar(select(Section.id).where(Section.academic_year_id == existing.id).limit(1))
    ):
        raise HTTPException(409, "El año ya tiene secciones; conserva sus fechas históricas")
    if model is Section:
        related(db, Course, payload["course_id"], tenant, payload["status"] == "ACTIVE")
        related(
            db, AcademicYear, payload["academic_year_id"], tenant, payload["status"] == "ACTIVE"
        )
    if model in (Enrollment, TeachingAssignment):
        section = related(db, Section, payload["section_id"], tenant, payload["status"] == "ACTIVE")
        year = related(
            db, AcademicYear, section.academic_year_id, tenant, payload["status"] == "ACTIVE"
        )
        if model is TeachingAssignment:
            membership = db.scalar(
                select(Membership).where(
                    Membership.institution_id == tenant,
                    Membership.user_id == payload["teacher_id"],
                )
            )
            if membership is None:
                raise HTTPException(404, "Docente no disponible en esta institución")
            if payload["status"] == "ACTIVE" and (
                membership.role != "TEACHER" or membership.status != "ACTIVE"
            ):
                raise HTTPException(409, "La asignación requiere una membresía docente activa")
            if payload["academic_year_id"] != section.academic_year_id:
                raise HTTPException(
                    422, "La sección y la asignación deben usar el mismo año escolar"
                )
        else:
            # Serializa matrículas del mismo estudiante, incluyendo creaciones concurrentes.
            student = db.scalar(
                select(Student)
                .where(Student.id == payload["student_id"], Student.institution_id == tenant)
                .with_for_update()
            )
            if student is None:
                raise HTTPException(404, "Estudiante no disponible en esta institución")
            if student.status != "ACTIVE" and payload["status"] == "ACTIVE":
                raise HTTPException(409, "El estudiante está archivado")
            if payload["start_date"] < year.start_date or payload["start_date"] > year.end_date:
                raise HTTPException(422, "La matrícula debe comenzar dentro del año escolar")
            if payload.get("end_date") and payload["end_date"] > year.end_date:
                raise HTTPException(422, "La matrícula no puede finalizar después del año escolar")
            if payload["status"] == "ACTIVE":
                overlaps = (
                    select(Enrollment.id)
                    .join(Section, Section.id == Enrollment.section_id)
                    .join(AcademicYear, AcademicYear.id == Section.academic_year_id)
                    .where(
                        Enrollment.institution_id == tenant,
                        Enrollment.student_id == payload["student_id"],
                        Enrollment.status == "ACTIVE",
                        func.coalesce(Enrollment.end_date, AcademicYear.end_date)
                        >= payload["start_date"],
                        Enrollment.start_date <= (payload.get("end_date") or year.end_date),
                    )
                )
                if existing:
                    overlaps = overlaps.where(Enrollment.id != existing.id)
                if db.scalar(overlaps.limit(1)):
                    raise HTTPException(
                        409, "Existe una matrícula vigente para esas fechas; utiliza traslado"
                    )
    if existing and model in (Enrollment, TeachingAssignment, Section):
        # Cambiar relaciones históricas convertiría un registro en otro distinto.
        keys = {
            Section: ("course_id", "academic_year_id"),
            Enrollment: ("student_id", "section_id"),
            TeachingAssignment: ("teacher_id", "section_id", "academic_year_id"),
        }[model]
        if any(getattr(existing, key) != payload[key] for key in keys):
            raise HTTPException(409, "Conserva las relaciones del registro; archívalo y crea otro")
    if existing and payload["status"] == "ARCHIVED":
        dependencies = {
            AcademicYear: [(Section, Section.academic_year_id)],
            Course: [(Section, Section.course_id)],
            Section: [
                (Enrollment, Enrollment.section_id),
                (TeachingAssignment, TeachingAssignment.section_id),
            ],
            Student: [(Enrollment, Enrollment.student_id)],
        }
        for child, column in dependencies.get(model, []):
            if db.scalar(
                select(child.id)
                .where(
                    child.institution_id == tenant, column == existing.id, child.status == "ACTIVE"
                )
                .limit(1)
            ):
                raise HTTPException(409, "Archiva primero los registros activos relacionados")
