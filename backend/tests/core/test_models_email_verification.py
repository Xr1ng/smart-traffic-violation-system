from datetime import datetime, timedelta, timezone

from app.models.email_verification import EmailVerificationCode


def test_email_verification_model_defaults(db):
    code = EmailVerificationCode(
        email="person@example.com",
        purpose="register",
        code_hash="hash",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(code)
    db.commit()
    db.refresh(code)

    assert code.attempt_count == 0
    assert code.used_at is None
