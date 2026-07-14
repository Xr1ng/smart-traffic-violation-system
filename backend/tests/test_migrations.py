from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory


def _script_directory() -> ScriptDirectory:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    return ScriptDirectory.from_config(config)


def test_alembic_has_single_head():
    assert _script_directory().get_heads() == ["20260714_120000"]


def test_email_verification_migration_rejects_missing_email(monkeypatch):
    script = _script_directory()
    revision = script.get_revision("20260714_120000")
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=True),
    )
    sa.Table(
        "notifications",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("violation_id", sa.Integer, nullable=False),
    )

    with engine.begin() as connection:
        metadata.create_all(connection)
        connection.execute(users.insert().values(id=1, email=None))
        operations = Operations(MigrationContext.configure(connection))
        monkeypatch.setattr(revision.module, "op", operations)

        with pytest.raises(RuntimeError, match="邮箱"):
            revision.module.upgrade()


def test_email_verification_migration_rejects_normalized_duplicates(monkeypatch):
    script = _script_directory()
    revision = script.get_revision("20260714_120000")
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=True),
    )
    sa.Table(
        "notifications",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("violation_id", sa.Integer, nullable=False),
    )

    with engine.begin() as connection:
        metadata.create_all(connection)
        connection.execute(users.insert(), [
            {"id": 1, "email": "User@Example.com"},
            {"id": 2, "email": " user@example.COM "},
        ])
        operations = Operations(MigrationContext.configure(connection))
        monkeypatch.setattr(revision.module, "op", operations)

        with pytest.raises(RuntimeError, match="重复邮箱"):
            revision.module.upgrade()


def test_email_verification_migration_upgrades_valid_legacy_schema(monkeypatch):
    script = _script_directory()
    revision = script.get_revision("20260714_120000")
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=True),
    )
    sa.Table(
        "notifications",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("violation_id", sa.Integer, nullable=False),
    )

    with engine.begin() as connection:
        metadata.create_all(connection)
        connection.execute(users.insert().values(id=1, email=" User@Example.COM "))
        operations = Operations(MigrationContext.configure(connection))
        monkeypatch.setattr(revision.module, "op", operations)

        revision.module.upgrade()

        inspector = sa.inspect(connection)
        assert "email_verification_codes" in inspector.get_table_names()
        user_columns = {column["name"]: column for column in inspector.get_columns("users")}
        assert user_columns["email"]["nullable"] is False
        assert "auth_version" in user_columns
        notification_columns = {
            column["name"]: column
            for column in inspector.get_columns("notifications")
        }
        assert notification_columns["violation_id"]["nullable"] is True
        assert "template_code" in notification_columns
        assert connection.scalar(sa.select(users.c.email)) == "user@example.com"


def test_merge_revision_owns_violation_rules_table(monkeypatch):
    script = _script_directory()
    engine = sa.create_engine("sqlite://")

    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        for revision_id in ("424e8489d6c7", "c98f93f77440"):
            revision = script.get_revision(revision_id)
            revision.module.upgrade()

        assert "violation_rules" not in sa.inspect(connection).get_table_names()

        merge = script.get_revision("7d4c9f1a2b3e")
        monkeypatch.setattr(merge.module, "op", operations)
        merge.module.upgrade()

        assert sa.inspect(connection).get_table_names().count("violation_rules") == 1

        merge.module.downgrade()

        assert "violation_rules" not in sa.inspect(connection).get_table_names()


def test_intake_description_and_vehicle_unbinding_migration(monkeypatch):
    script = _script_directory()
    revision = script.get_revision("8e5d0a2b4c6f")
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    users = sa.Table("users", metadata, sa.Column("id", sa.Integer, primary_key=True))
    vehicles = sa.Table(
        "vehicles",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    )
    violations = sa.Table(
        "violations",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vehicle_id", sa.Integer, sa.ForeignKey("vehicles.id"), nullable=True),
    )
    sa.Table("intake_events", metadata, sa.Column("id", sa.Integer, primary_key=True))

    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        metadata.create_all(connection)
        operations = Operations(MigrationContext.configure(connection))
        monkeypatch.setattr(revision.module, "op", operations)

        connection.execute(users.insert().values(id=1))
        connection.execute(vehicles.insert().values(id=1, owner_id=1))
        connection.execute(violations.insert().values(id=1, vehicle_id=1))
        connection.commit()

        # SQLite batch ALTER rebuilds the parent table, which requires FK checks
        # off during the upgrade. Enforcement is restored before the scenario.
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        revision.module.upgrade()
        connection.commit()
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1

        columns = {
            column["name"]: column
            for column in sa.inspect(connection).get_columns("intake_events")
        }
        assert columns["description"]["type"].length == 512
        owner_column = next(
            column
            for column in sa.inspect(connection).get_columns("vehicles")
            if column["name"] == "owner_id"
        )
        assert owner_column["nullable"] is True
        connection.execute(
            vehicles.update().where(vehicles.c.id == 1).values(owner_id=None)
        )
        connection.commit()

        revision.module.downgrade()

        assert connection.scalar(sa.select(sa.func.count()).select_from(vehicles)) == 0
        violation = connection.execute(
            sa.select(violations.c.id, violations.c.vehicle_id)
        ).one()
        assert violation.id == 1
        assert violation.vehicle_id is None
        assert "description" not in {
            column["name"]
            for column in sa.inspect(connection).get_columns("intake_events")
        }
        owner_column = next(
            column
            for column in sa.inspect(connection).get_columns("vehicles")
            if column["name"] == "owner_id"
        )
        assert owner_column["nullable"] is False
