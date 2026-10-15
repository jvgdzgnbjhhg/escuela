"""Punto de partida de migraciones, sin anticipar modelos de la Fase 1."""

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic crea y mantiene alembic_version transaccionalmente.
    pass


def downgrade() -> None:
    pass
