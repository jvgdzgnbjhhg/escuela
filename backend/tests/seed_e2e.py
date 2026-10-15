"""Datos ficticios para el proyecto Compose aislado escuelagestion-e2e."""

import os

from sqlalchemy import make_url, select
from sqlalchemy.orm import Session

from app.core.database import make_engine
from app.models import Institution, Membership, User
from app.services.security import hash_password


def main():
    url = make_url(os.environ["TEST_DATABASE_URL"])
    if url.database != "evaluacion_e2e_test":
        raise ValueError("El fixture requiere exactamente evaluacion_e2e_test")
    engine = make_engine(url)
    with Session(engine) as db, db.begin():
        for profile in ("desktop", "mobile"):
            email = f"{profile}@example.com"
            if db.scalar(select(User.id).where(User.email == email)):
                continue
            institution = Institution(name=f"Centro ficticio {profile}")
            second = Institution(name=f"Segundo centro {profile}")
            user = User(
                email=email,
                full_name=f"Administrador {profile}",
                password_hash=hash_password("Ficticia-E2E-2026"),
            )
            db.add_all([institution, second, user])
            db.flush()
            db.add_all(
                [
                    Membership(institution_id=i.id, user_id=user.id, role="ADMIN")
                    for i in (institution, second)
                ]
            )
    engine.dispose()
    print("Cuentas ficticias preparadas en evaluacion_e2e_test.")


if __name__ == "__main__":
    main()
