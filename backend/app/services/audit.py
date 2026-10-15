from fastapi.encoders import jsonable_encoder

from app.models import AuditEvent


def audit(db, context, entity, action, before=None, after=None):
    # Solo los contratos públicos del dominio: nunca hashes, contraseñas o sesiones.
    db.add(
        AuditEvent(
            institution_id=context.institution.id,
            actor_id=context.identity.user.id,
            entity_type=entity.__tablename__,
            entity_id=entity.id,
            action=action,
            details=jsonable_encoder({"before": before, "after": after}),
        )
    )
