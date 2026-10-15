"""Operaciones locales con credenciales de propietario; nunca expuestas por HTTP."""

import argparse
from getpass import getpass

from psycopg import sql
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.database import make_engine, migration_config
from app.models import AuditEvent, Base, Institution, Membership, User
from app.schemas.identity import InstitutionInput, MemberInput
from app.services.security import hash_password


def provision_runtime(engine, settings):
    if settings.runtime_db_password is None:
        raise ValueError("Define RUNTIME_DB_PASSWORD para la cuenta de ejecución")
    role = settings.runtime_db_user
    if role == settings.postgres_user:
        raise ValueError("La cuenta de ejecución debe ser distinta del propietario")
    with engine.begin() as connection:
        cursor = connection.connection.driver_connection.cursor()
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))
        if not cursor.fetchone():
            cursor.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(role)))
        cursor.execute(
            sql.SQL(
                "ALTER ROLE {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION "
                "NOBYPASSRLS PASSWORD {}"
            ).format(
                sql.Identifier(role), sql.Literal(settings.runtime_db_password.get_secret_value())
            )
        )
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(settings.postgres_db), sql.Identifier(role)
            )
        )
        cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
        for table in [*Base.metadata.tables, "alembic_version"]:
            privileges = "SELECT"
            if table == "audit_events":
                privileges = "SELECT, INSERT"
            elif table != "alembic_version":
                privileges = "SELECT, INSERT, UPDATE"
                if table in {"login_sessions", "login_budgets"}:
                    privileges += ", DELETE"
            cursor.execute(
                sql.SQL("REVOKE ALL ON TABLE {} FROM {}").format(
                    sql.Identifier(table), sql.Identifier(role)
                )
            )
            cursor.execute(
                sql.SQL("GRANT {} ON TABLE {} TO {}").format(
                    sql.SQL(privileges), sql.Identifier(table), sql.Identifier(role)
                )
            )
        cursor.close()


def bootstrap(engine):
    """Sólo la primera cuenta; el resto se gestiona desde la institución."""
    with Session(engine) as db, db.begin():
        # Bloqueo transaccional para dos invocaciones simultáneas.
        from sqlalchemy import text

        db.execute(text("SELECT pg_advisory_xact_lock(48159301)"))
        if db.scalar(select(User.id).limit(1)):
            raise ValueError("Ya existen cuentas. Utiliza la administración institucional.")
        institution_data = InstitutionInput(name=input("Nombre de la institución: "))
        email = input("Correo del administrador: ")
        name = input("Nombre del administrador: ")
        password = getpass("Contraseña (mínimo 12 caracteres): ")
        if password != getpass("Repite la contraseña: "):
            raise ValueError("Las contraseñas no coinciden")
        data = MemberInput(email=email, full_name=name, role="ADMIN", initial_password=password)
        institution = Institution(name=institution_data.name)
        user = User(
            email=str(data.email).lower(),
            full_name=data.full_name,
            password_hash=hash_password(password),
        )
        db.add_all([institution, user])
        db.flush()
        db.add(Membership(institution_id=institution.id, user_id=user.id, role="ADMIN"))
        db.add(
            AuditEvent(
                institution_id=institution.id,
                actor_id=user.id,
                entity_type="institutions",
                entity_id=institution.id,
                action="BOOTSTRAP",
                details={"name": institution.name},
            )
        )
    print("Institución y administrador creados. Ya puedes iniciar sesión.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["migrate", "bootstrap"])
    args = parser.parse_args()
    settings = Settings()
    engine = make_engine(settings.database_url)
    try:
        if args.action == "migrate":
            if settings.runtime_db_password is None:
                raise ValueError("Define RUNTIME_DB_PASSWORD antes de migrar")
            with engine.begin() as connection:
                config = migration_config()
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
            provision_runtime(engine, settings)
            print("Migraciones y permisos de ejecución aplicados.")
        else:
            bootstrap(engine)
    except ValidationError:
        parser.exit(1, "Datos inválidos; revisa correo, longitud de nombres y contraseña.\n")
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
