"""Contratos de identidad y aislamiento contra PostgreSQL, sin datos reales."""

import os
from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import make_url, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.database import make_engine, migration_config
from app.main import create_app
from app.manage import provision_runtime
from app.models import AuditEvent, Base, Institution, Membership, Section, User
from app.services.security import hash_password

pytestmark = pytest.mark.integration
PASSWORD = "Ficticia-solo-pruebas-2026"
ORIGIN = "http://testserver"


@pytest.fixture
def system():
    raw = os.environ.get("TEST_DATABASE_URL")
    if not raw:
        pytest.skip("Requiere TEST_DATABASE_URL dedicada")
    url = make_url(raw)
    assert url.drivername == "postgresql+psycopg" and url.database.endswith("_test")
    engine = make_engine(url)
    with engine.begin() as conn:
        config = migration_config()
        config.attributes["connection"] = conn
        command.upgrade(config, "head")
        names = ", ".join('"' + name + '"' for name in Base.metadata.tables)
        conn.execute(text("TRUNCATE " + names + " CASCADE"))
    settings = Settings(
        app_env="test",
        postgres_host=url.host,
        postgres_port=url.port or 5432,
        postgres_user=url.username,
        postgres_password=SecretStr(url.password),
        postgres_db=url.database,
        allowed_origins=[ORIGIN],
        _env_file=None,
    )
    with Session(engine) as db, db.begin():
        a, b = Institution(name="Centro A"), Institution(name="Centro B")
        users = {
            role: User(
                email=f"{role.lower()}@example.com",
                full_name=role,
                password_hash=hash_password(PASSWORD),
            )
            for role in ["ADMIN", "TEACHER", "VIEWER", "TECHNICAL"]
        }
        db.add_all([a, b, *users.values()])
        db.flush()
        members = {
            role: Membership(institution_id=a.id, user_id=u.id, role=role)
            for role, u in users.items()
        }
        db.add_all(members.values())
        db.flush()
        ids = {
            "a": str(a.id),
            "b": str(b.id),
            **{role: str(u.id) for role, u in users.items()},
            **{role + "_member": str(m.id) for role, m in members.items()},
        }
    with TestClient(create_app(settings)) as client:
        yield client, engine, ids, settings
    engine.dispose()


def login(client, ids, role="ADMIN"):
    result = client.post(
        "/api/v1/auth/login",
        json={"email": f"{role.lower()}@example.com", "password": PASSWORD},
        headers={"Origin": ORIGIN},
    )
    assert result.status_code == 200, result.text
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200, me.text
    return {"Origin": ORIGIN, "X-CSRF-Token": me.json()["csrf_token"], "X-Institution-ID": ids["a"]}


def create(client, headers, path, payload):
    response = client.post("/api/v1/" + path, json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def structure(client, headers):
    today = date.today()
    year = create(
        client,
        headers,
        "academic-years",
        {
            "name": "Año de prueba",
            "start_date": str(today - timedelta(days=30)),
            "end_date": str(today + timedelta(days=300)),
        },
    )
    course = create(client, headers, "courses", {"name": "Primero", "grade_level": "1"})
    sections = [
        create(
            client,
            headers,
            "sections",
            {"name": name, "course_id": course["id"], "academic_year_id": year["id"]},
        )
        for name in ["A", "B"]
    ]
    student = create(client, headers, "students", {"full_name": "Estudiante ficticio"})
    enrollment = create(
        client,
        headers,
        "enrollments",
        {"student_id": student["id"], "section_id": sections[0]["id"], "start_date": str(today)},
    )
    return year, course, sections, student, enrollment


def test_session_csrf_origin_logout_and_secret_redaction(system):
    client, _, ids, _ = system
    assert client.get("/api/v1/students").status_code == 401
    assert client.post("/api/v1/auth/login", json={}).status_code == 403
    headers = login(client, ids)
    assert client.cookies.get("ea_session")
    no_csrf = {"Origin": ORIGIN, "X-Institution-ID": ids["a"]}
    assert (
        client.post("/api/v1/students", json={"full_name": "X"}, headers=no_csrf).status_code == 403
    )
    bad = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "bad", "password": "SECRET", "unexpected": "SECRET"},
    )
    assert bad.status_code == 422 and "SECRET" not in bad.text
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_tenant_scope_versions_audit_and_foreign_keys(system):
    client, engine, ids, _ = system
    headers = login(client, ids)
    year, course, sections, student, _ = structure(client, headers)
    foreign = {**headers, "X-Institution-ID": ids["b"]}
    assert client.get("/api/v1/students", headers=foreign).status_code == 403
    assert client.get(f"/api/v1/students/{uuid4()}", headers=headers).status_code == 404
    edit = {"full_name": "Nombre corregido", "version": student["version"]}
    assert (
        client.patch(f"/api/v1/students/{student['id']}", headers=headers, json=edit).status_code
        == 200
    )
    assert (
        client.patch(f"/api/v1/students/{student['id']}", headers=headers, json=edit).status_code
        == 409
    )
    with Session(engine) as db:
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "UPDATE")) is not None
        db.add(
            Section(
                institution_id=ids["b"],
                course_id=course["id"],
                academic_year_id=year["id"],
                name="Cruce inválido",
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
    archived = {"full_name": "Nombre corregido", "version": 2, "status": "ARCHIVED"}
    assert (
        client.patch(
            f"/api/v1/students/{student['id']}", headers=headers, json=archived
        ).status_code
        == 409
    )


def test_teacher_scope_transfer_and_revocation(system):
    client, _, ids, _ = system
    admin = login(client, ids)
    year, _, sections, student, enrollment = structure(client, admin)
    create(
        client,
        admin,
        "teaching-assignments",
        {
            "teacher_id": ids["TEACHER"],
            "section_id": sections[0]["id"],
            "academic_year_id": year["id"],
            "subject": "Lengua",
        },
    )
    teacher = login(client, ids, "TEACHER")
    assert client.get("/api/v1/students", headers=teacher).json()["total"] == 1
    assert client.get(f"/api/v1/sections/{sections[1]['id']}", headers=teacher).status_code == 404
    assert (
        client.post("/api/v1/students", headers=teacher, json={"full_name": "X"}).status_code == 403
    )
    admin = login(client, ids)
    duplicate = client.post(
        "/api/v1/enrollments",
        headers=admin,
        json={
            "student_id": student["id"],
            "section_id": sections[1]["id"],
            "start_date": str(date.today()),
        },
    )
    assert duplicate.status_code == 409
    moved = client.post(
        f"/api/v1/enrollments/{enrollment['id']}/transfer",
        headers=admin,
        json={
            "section_id": sections[1]["id"],
            "start_date": str(date.today() + timedelta(days=1)),
            "version": 1,
        },
    )
    assert moved.status_code == 201, moved.text
    old = client.get(f"/api/v1/enrollments/{enrollment['id']}", headers=admin).json()
    assert old["status"] == "ACTIVE" and old["end_date"] == str(date.today())
    response = client.patch(
        f"/api/v1/institutions/{ids['a']}/members/{ids['TEACHER_member']}",
        headers=admin,
        json={"role": "TEACHER", "status": "REVOKED", "version": 1},
    )
    assert response.status_code == 200, response.text
    teacher = login(client, ids, "TEACHER")
    assert client.get("/api/v1/students", headers=teacher).status_code == 403


def test_roles_last_admin_and_password_change(system):
    client, _, ids, _ = system
    viewer = login(client, ids, "VIEWER")
    assert client.get("/api/v1/students", headers=viewer).status_code == 200
    assert (
        client.post(
            "/api/v1/courses", headers=viewer, json={"name": "X", "grade_level": "1"}
        ).status_code
        == 403
    )
    technical = login(client, ids, "TECHNICAL")
    assert client.get("/api/v1/students", headers=technical).status_code == 403
    admin = login(client, ids)
    assert (
        client.patch(
            f"/api/v1/institutions/{ids['a']}/members/{ids['ADMIN_member']}",
            headers=admin,
            json={"role": "VIEWER", "status": "ACTIVE", "version": 1},
        ).status_code
        == 409
    )
    response = client.post(
        "/api/v1/auth/password",
        headers=admin,
        json={"current_password": PASSWORD, "new_password": PASSWORD + "-nueva"},
    )
    assert response.status_code == 204, response.text
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_rate_limit_and_body_limit(system):
    client, _, _, _ = system
    for _ in range(8):
        assert (
            client.post(
                "/api/v1/auth/login",
                headers={"Origin": ORIGIN},
                json={"email": "missing@example.com", "password": "incorrecta"},
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": "missing@example.com", "password": "incorrecta"},
        ).status_code
        == 429
    )
    assert (
        client.post(
            "/api/v1/auth/login", headers={"Origin": ORIGIN}, json={"password": "a" * 66000}
        ).status_code
        == 413
    )


def test_runtime_privileges(system):
    _, engine, _, settings = system
    settings.runtime_db_user = "identity_test_runtime"
    settings.runtime_db_password = SecretStr("test-runtime-only")
    provision_runtime(engine, settings)
    with engine.connect() as conn:
        for table, privilege, expected in [
            ("audit_events", "UPDATE", False),
            ("audit_events", "DELETE", False),
            ("audit_events", "INSERT", True),
            ("students", "DELETE", False),
            ("students", "UPDATE", True),
            ("login_sessions", "DELETE", True),
        ]:
            assert (
                conn.execute(
                    text("SELECT has_table_privilege(:role, :table, :privilege)"),
                    {"role": settings.runtime_db_user, "table": table, "privilege": privilege},
                ).scalar()
                is expected
            )


def test_next_year_enrollment_and_future_transfer_preserve_access(system):
    client, _, ids, _ = system
    admin = login(client, ids)
    year, course, sections, student, enrollment = structure(client, admin)
    create(
        client,
        admin,
        "teaching-assignments",
        {
            "teacher_id": ids["TEACHER"],
            "section_id": sections[0]["id"],
            "academic_year_id": year["id"],
            "subject": "Lengua",
        },
    )
    teacher = login(client, ids, "TEACHER")
    assert client.get("/api/v1/students", headers=teacher).json()["total"] == 1
    admin = login(client, ids)
    tomorrow = date.today() + timedelta(days=1)
    response = client.post(
        f"/api/v1/enrollments/{enrollment['id']}/transfer",
        headers=admin,
        json={"section_id": sections[1]["id"], "start_date": str(tomorrow), "version": 1},
    )
    assert response.status_code == 201
    teacher = login(client, ids, "TEACHER")
    assert client.get("/api/v1/students", headers=teacher).json()["total"] == 1
    admin = login(client, ids)
    start = date.fromisoformat(year["end_date"]) + timedelta(days=1)
    next_year = create(
        client,
        admin,
        "academic-years",
        {
            "name": "Siguiente año",
            "start_date": str(start),
            "end_date": str(start + timedelta(days=300)),
        },
    )
    section = create(
        client,
        admin,
        "sections",
        {"name": "A", "course_id": course["id"], "academic_year_id": next_year["id"]},
    )
    create(
        client,
        admin,
        "enrollments",
        {"student_id": student["id"], "section_id": section["id"], "start_date": str(start)},
    )
    changed = client.patch(
        f"/api/v1/academic-years/{year['id']}",
        headers=admin,
        json={
            "name": year["name"],
            "start_date": year["start_date"],
            "end_date": str(start + timedelta(days=10)),
            "version": 1,
        },
    )
    assert changed.status_code == 409


def test_concurrent_enrollment_rejects_second_writer(system):
    from concurrent.futures import ThreadPoolExecutor

    client, _, ids, settings = system
    headers = login(client, ids)
    _, _, sections, _, _ = structure(client, headers)
    student = create(client, headers, "students", {"full_name": "Prueba concurrente"})
    cookie = client.cookies.get("ea_session")

    def enroll(section):
        with TestClient(create_app(settings)) as other:
            other.cookies.set("ea_session", cookie)
            return other.post(
                "/api/v1/enrollments",
                headers=headers,
                json={
                    "student_id": student["id"],
                    "section_id": section["id"],
                    "start_date": str(date.today()),
                },
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(enroll, sections))
    assert sorted(results) == [201, 409]


def test_session_expiry_secure_cookie_and_revocation(system):
    from app.models import LoginSession
    from app.services.security import digest, now

    client, engine, ids, settings = system
    headers = login(client, ids)
    token = client.cookies.get("ea_session")
    with Session(engine) as db, db.begin():
        db.get(LoginSession, digest(token)).last_seen_at = now() - timedelta(minutes=31)
    assert client.get("/api/v1/auth/me").status_code == 401
    settings.app_env = "production"
    settings.allowed_origins = ["https://testserver"]
    with TestClient(create_app(settings), base_url="https://testserver") as secure:
        response = secure.post(
            "/api/v1/auth/login",
            headers={"Origin": "https://testserver"},
            json={"email": "admin@example.com", "password": PASSWORD},
        )
        assert response.status_code == 200
        cookie = response.headers["set-cookie"]
        assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
        assert secure.get("/api/v1/docs").status_code == 404
        assert secure.get("/api/v1/auth/me").status_code == 200
    settings.app_env = "test"
    settings.allowed_origins = [ORIGIN]
    # Una membresía revocada se vuelve a consultar sin invalidar toda la identidad.
    headers = login(client, ids, "VIEWER")
    with Session(engine) as db, db.begin():
        db.get(Membership, ids["VIEWER_member"]).status = "REVOKED"
    assert client.get("/api/v1/students", headers=headers).status_code == 403


def test_authorized_two_tenants_do_not_leak_objects_or_audit(system):
    client, _, ids, _ = system
    headers = login(client, ids)
    student = create(client, headers, "students", {"full_name": "Solo centro A"})
    second = create(client, headers, "institutions", {"name": "Centro nuevo"})
    other = {**headers, "X-Institution-ID": second["id"]}
    assert client.get("/api/v1/students", headers=other).json()["total"] == 0
    assert client.get(f"/api/v1/students/{student['id']}", headers=other).status_code == 404
    assert (
        client.patch(
            f"/api/v1/students/{student['id']}",
            headers=other,
            json={"full_name": "Cambio ajeno", "version": 1},
        ).status_code
        == 404
    )
    events = client.get("/api/v1/audit-events", headers=other).json()["items"]
    assert all(event["entity_id"] != student["id"] for event in events)
    assert client.get(f"/api/v1/institutions/{ids['a']}/members", headers=other).status_code == 404


def test_failed_transfer_is_atomic_and_existing_password_is_not_replaced(system):
    client, engine, ids, _ = system
    headers = login(client, ids)
    _, _, _, _, enrollment = structure(client, headers)
    with Session(engine) as db:
        before = len(db.scalars(select(AuditEvent)).all())
    invalid = client.post(
        f"/api/v1/enrollments/{enrollment['id']}/transfer",
        headers=headers,
        json={
            "section_id": str(uuid4()),
            "start_date": str(date.today() + timedelta(days=1)),
            "version": 1,
        },
    )
    assert invalid.status_code == 404
    old = client.get(f"/api/v1/enrollments/{enrollment['id']}", headers=headers).json()
    assert old["version"] == 1 and old["end_date"] is None and old["status"] == "ACTIVE"
    with Session(engine) as db:
        assert len(db.scalars(select(AuditEvent)).all()) == before
    second = create(client, headers, "institutions", {"name": "Otro centro"})
    other = {**headers, "X-Institution-ID": second["id"]}
    payload = {
        "email": "teacher@example.com",
        "full_name": "No cambia identidad global",
        "role": "VIEWER",
    }
    assert (
        client.post(
            f"/api/v1/institutions/{second['id']}/members",
            headers=other,
            json={**payload, "initial_password": "No-reemplazar-2026"},
        ).status_code
        == 409
    )
    create(client, other, f"institutions/{second['id']}/members", payload)
    login(client, ids, "TEACHER")


def test_interactive_bootstrap_creates_only_first_admin(system, monkeypatch):
    import app.manage as manage

    _, engine, _, _ = system
    with engine.begin() as conn:
        names = ", ".join('"' + name + '"' for name in Base.metadata.tables)
        conn.execute(text("TRUNCATE " + names + " CASCADE"))
    answers = iter(["Centro inicial", "first@example.com", "Primer administrador"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(manage, "getpass", lambda _: PASSWORD)
    manage.bootstrap(engine)
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == "first@example.com"))
        assert user is not None and user.password_hash.startswith("$argon2id$")
        assert db.scalar(select(Membership).where(Membership.user_id == user.id)).role == "ADMIN"
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "BOOTSTRAP")) is not None
    with pytest.raises(ValueError, match="Ya existen cuentas"):
        manage.bootstrap(engine)


def test_transfer_preserves_planned_end_and_cannot_extend_past_school_year(system):
    client, _, ids, _ = system
    headers = login(client, ids)
    year, _, sections, student, enrollment = structure(client, headers)
    invalid = client.post(
        f"/api/v1/enrollments/{enrollment['id']}/transfer",
        headers=headers,
        json={
            "section_id": sections[1]["id"],
            "version": 1,
            "start_date": str(date.fromisoformat(year["end_date"]) + timedelta(days=1)),
        },
    )
    assert invalid.status_code == 422
    planned_end = str(date.today() + timedelta(days=30))
    response = client.patch(
        f"/api/v1/enrollments/{enrollment['id']}",
        headers=headers,
        json={
            "student_id": student["id"],
            "section_id": sections[0]["id"],
            "start_date": enrollment["start_date"],
            "end_date": planned_end,
            "version": 1,
        },
    )
    assert response.status_code == 200
    moved = client.post(
        f"/api/v1/enrollments/{enrollment['id']}/transfer",
        headers=headers,
        json={
            "section_id": sections[1]["id"],
            "version": 2,
            "start_date": str(date.today() + timedelta(days=1)),
        },
    )
    assert moved.status_code == 201 and moved.json()["end_date"] == planned_end
