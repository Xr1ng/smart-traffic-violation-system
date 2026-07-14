"""seed_data 幂等性测试。"""
from app.core.security import verify_password
from app.models.user import Role, User
from app.models.violation import NotificationTemplate
from seed_data import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    seed_demo_data,
    seed_roles_and_admin,
)


def test_seed_roles_and_admin_creates(db):
    seed_roles_and_admin(db)
    assert db.query(Role).count() == 4
    for code in ("citizen", "reviewer", "admin", "camera"):
        assert db.query(Role).filter_by(code=code).first() is not None
    admin = db.query(User).filter_by(username=ADMIN_USERNAME).first()
    assert admin is not None
    assert admin.role.code == "admin"
    assert verify_password(ADMIN_PASSWORD, admin.password_hash) is True


def test_seed_roles_and_admin_idempotent(db):
    seed_roles_and_admin(db)
    seed_roles_and_admin(db)
    assert db.query(Role).count() == 4
    assert db.query(User).filter_by(username=ADMIN_USERNAME).count() == 1


def test_seed_roles_and_admin_skips_existing_password(db):
    seed_roles_and_admin(db)
    admin = db.query(User).filter_by(username=ADMIN_USERNAME).first()
    original_hash = admin.password_hash
    seed_roles_and_admin(db)
    db.refresh(admin)
    assert admin.password_hash == original_hash


def test_seed_demo_data_creates_auth_email_templates_idempotently(db):
    seed_roles_and_admin(db)
    seed_demo_data(db)
    seed_demo_data(db)

    templates = {
        template.code: template
        for template in db.query(NotificationTemplate).all()
    }
    assert set(templates) >= {
        "violation_notice",
        "register_email_code",
        "password_reset_email_code",
    }
    assert "{code}" in templates["register_email_code"].body_template
    assert "{code}" in templates["password_reset_email_code"].body_template
    assert "{expires_minutes}" in templates["register_email_code"].body_template
    assert "{expires_minutes}" in templates["password_reset_email_code"].body_template
