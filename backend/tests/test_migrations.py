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
    assert _script_directory().get_heads() == ["8e5d0a2b4c6f"]


@pytest.mark.parametrize(
    "revision_order",
    [
        ("424e8489d6c7", "c98f93f77440"),
        ("c98f93f77440", "424e8489d6c7"),
    ],
)
def test_duplicate_violation_rule_upgrades_are_idempotent(revision_order, monkeypatch):
    script = _script_directory()
    engine = sa.create_engine("sqlite://")

    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        for revision_id in revision_order:
            revision = script.get_revision(revision_id)
            monkeypatch.setattr(revision.module, "op", operations)
            revision.module.upgrade()

        assert sa.inspect(connection).get_table_names().count("violation_rules") == 1


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
    sa.Table("intake_events", metadata, sa.Column("id", sa.Integer, primary_key=True))

    with engine.begin() as connection:
        metadata.create_all(connection)
        operations = Operations(MigrationContext.configure(connection))
        monkeypatch.setattr(revision.module, "op", operations)

        revision.module.upgrade()

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
        connection.execute(vehicles.insert().values(id=1, owner_id=None))

        revision.module.downgrade()

        assert connection.scalar(sa.select(sa.func.count()).select_from(vehicles)) == 0
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
