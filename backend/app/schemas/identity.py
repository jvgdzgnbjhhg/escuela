from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

Name = Annotated[str, Field(min_length=1, max_length=160)]
Role = Literal["ADMIN", "COORDINATOR", "TEACHER", "VIEWER", "TECHNICAL"]
Status = Literal["ACTIVE", "ARCHIVED"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)


class ChangePassword(Input):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


class InstitutionInput(Input):
    name: Name


class MemberInput(Input):
    email: EmailStr
    full_name: Name
    role: Role
    initial_password: SecretStr | None = Field(default=None, min_length=12, max_length=128)


class MemberUpdate(Input):
    role: Role
    status: Literal["ACTIVE", "REVOKED"]
    version: int = Field(ge=1)


class AcademicYearInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    start_date: date
    end_date: date
    status: Status = "ACTIVE"

    @model_validator(mode="after")
    def valid_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("La fecha final no puede ser anterior a la inicial")
        return self


class CourseInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    grade_level: Annotated[str, Field(min_length=1, max_length=50)]
    status: Status = "ACTIVE"


class SectionInput(Input):
    course_id: UUID
    academic_year_id: UUID
    name: Annotated[str, Field(min_length=1, max_length=80)]
    status: Status = "ACTIVE"


class StudentInput(Input):
    full_name: Name
    student_code: Annotated[str, Field(max_length=50)] | None = None
    status: Status = "ACTIVE"

    @field_validator("student_code")
    @classmethod
    def empty_code(cls, value):
        return value or None


class EnrollmentInput(Input):
    student_id: UUID
    section_id: UUID
    start_date: date
    end_date: date | None = None
    status: Status = "ACTIVE"

    @model_validator(mode="after")
    def valid_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("La fecha final no puede ser anterior a la inicial")
        return self


class AssignmentInput(Input):
    teacher_id: UUID
    section_id: UUID
    academic_year_id: UUID
    subject: Annotated[str, Field(min_length=1, max_length=100)]
    status: Status = "ACTIVE"


class AcademicYearUpdate(AcademicYearInput):
    version: int = Field(ge=1)


class CourseUpdate(CourseInput):
    version: int = Field(ge=1)


class SectionUpdate(SectionInput):
    version: int = Field(ge=1)


class StudentUpdate(StudentInput):
    version: int = Field(ge=1)


class EnrollmentUpdate(EnrollmentInput):
    version: int = Field(ge=1)


class AssignmentUpdate(AssignmentInput):
    version: int = Field(ge=1)


class TransferInput(Input):
    section_id: UUID
    start_date: date
    version: int = Field(ge=1)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class RecordMetadata(BaseModel):
    id: UUID
    institution_id: UUID
    version: int
    created_at: datetime
    updated_at: datetime


class AcademicYearOut(AcademicYearInput, RecordMetadata):
    pass


class CourseOut(CourseInput, RecordMetadata):
    pass


class SectionOut(SectionInput, RecordMetadata):
    pass


class StudentOut(StudentInput, RecordMetadata):
    pass


class EnrollmentOut(EnrollmentInput, RecordMetadata):
    pass


class AssignmentOut(AssignmentInput, RecordMetadata):
    pass


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str


class InstitutionOut(BaseModel):
    id: UUID
    name: str
    role: Role


class SessionOut(BaseModel):
    user: UserOut
    institutions: list[InstitutionOut]
    csrf_token: str


class MemberOut(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: Role
    status: Literal["ACTIVE", "REVOKED"]
    version: int
