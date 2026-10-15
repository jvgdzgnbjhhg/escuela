from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TenantRecord(Identity):
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Institution(Identity, Base):
    __tablename__ = "institutions"
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE")
    __table_args__ = (CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')"),)


class User(Identity, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(512))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    __table_args__ = (CheckConstraint("email = lower(email)"),)


class Membership(Identity, Base):
    __tablename__ = "institution_memberships"
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    __table_args__ = (
        UniqueConstraint("institution_id", "user_id"),
        CheckConstraint("role IN ('ADMIN', 'COORDINATOR', 'TEACHER', 'VIEWER', 'TECHNICAL')"),
        CheckConstraint("status IN ('ACTIVE', 'REVOKED')"),
    )


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LoginBudget(Base):
    __tablename__ = "login_budgets"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window: Mapped[int] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer)


class AcademicYear(TenantRecord, Base):
    __tablename__ = "academic_years"
    name: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    __table_args__ = (
        UniqueConstraint("institution_id", "id"),
        UniqueConstraint("institution_id", "name"),
        CheckConstraint("end_date >= start_date"),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')"),
    )


class Course(TenantRecord, Base):
    __tablename__ = "courses"
    name: Mapped[str] = mapped_column(String(100))
    grade_level: Mapped[str] = mapped_column(String(50))
    __table_args__ = (
        UniqueConstraint("institution_id", "id"),
        UniqueConstraint("institution_id", "name"),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')"),
    )


class Section(TenantRecord, Base):
    __tablename__ = "sections"
    course_id: Mapped[UUID] = mapped_column()
    academic_year_id: Mapped[UUID] = mapped_column()
    name: Mapped[str] = mapped_column(String(80))
    __table_args__ = (
        UniqueConstraint("institution_id", "id"),
        UniqueConstraint("institution_id", "id", "academic_year_id"),
        UniqueConstraint("course_id", "academic_year_id", "name"),
        ForeignKeyConstraint(
            ["institution_id", "course_id"], ["courses.institution_id", "courses.id"]
        ),
        ForeignKeyConstraint(
            ["institution_id", "academic_year_id"],
            ["academic_years.institution_id", "academic_years.id"],
        ),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')"),
    )


class Student(TenantRecord, Base):
    __tablename__ = "students"
    student_code: Mapped[str | None] = mapped_column(String(50))
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    __table_args__ = (
        UniqueConstraint("institution_id", "id"),
        UniqueConstraint("institution_id", "student_code"),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')"),
    )


class Enrollment(TenantRecord, Base):
    __tablename__ = "enrollments"
    student_id: Mapped[UUID] = mapped_column()
    section_id: Mapped[UUID] = mapped_column()
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    __table_args__ = (
        ForeignKeyConstraint(
            ["institution_id", "student_id"], ["students.institution_id", "students.id"]
        ),
        ForeignKeyConstraint(
            ["institution_id", "section_id"], ["sections.institution_id", "sections.id"]
        ),
        CheckConstraint("end_date IS NULL OR end_date >= start_date"),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')"),
        UniqueConstraint("institution_id", "student_id", "section_id", "start_date"),
        Index("ix_enrollment_student", "institution_id", "student_id"),
        Index("ix_enrollment_section", "institution_id", "section_id"),
    )


class TeachingAssignment(TenantRecord, Base):
    __tablename__ = "teaching_assignments"
    teacher_id: Mapped[UUID] = mapped_column()
    section_id: Mapped[UUID] = mapped_column()
    academic_year_id: Mapped[UUID] = mapped_column()
    subject: Mapped[str] = mapped_column(String(100))
    __table_args__ = (
        ForeignKeyConstraint(
            ["institution_id", "teacher_id"],
            ["institution_memberships.institution_id", "institution_memberships.user_id"],
        ),
        ForeignKeyConstraint(
            ["institution_id", "section_id", "academic_year_id"],
            ["sections.institution_id", "sections.id", "sections.academic_year_id"],
        ),
        UniqueConstraint("institution_id", "teacher_id", "section_id", "subject"),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')"),
        Index("ix_assignment_teacher", "institution_id", "teacher_id", "status"),
    )


class AuditEvent(Identity, Base):
    __tablename__ = "audit_events"
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[UUID] = mapped_column()
    action: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
