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
    assert _script_directory().get_heads() == ["7d4c9f1a2b3e"]


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
