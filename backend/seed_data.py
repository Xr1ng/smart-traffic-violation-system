# backend/seed_data.py
"""运行时演示 seed：角色 + 管理员 + 通知模板 + 车辆/车主。运行：uv run python -m seed_data"""
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.user import Role, User
from app.models.violation import NotificationTemplate, Vehicle

ROLES = [("citizen", "市民"), ("reviewer", "审核员"), ("admin", "管理员"), ("camera", "摄像头")]
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"
ADMIN_EMAIL = "admin@example.com"

AUTH_EMAIL_TEMPLATES = {
    "register_email_code": (
        "【交通违章智能管理平台】注册验证码",
        "您的注册验证码是 {code}，{expires_minutes} 分钟内有效。请勿向他人泄露。",
    ),
    "password_reset_email_code": (
        "【交通违章智能管理平台】密码重置验证码",
        "您的密码重置验证码是 {code}，{expires_minutes} 分钟内有效。若非本人操作，请忽略。",
    ),
}


def seed_roles_and_admin(db: Session) -> None:
    """幂等：建 4 个角色 + 默认管理员。已有则跳过。"""
    for code, name in ROLES:
        if not db.query(Role).filter_by(code=code).first():
            db.add(Role(code=code, name=name))
    db.commit()
    admin_role = db.query(Role).filter_by(code="admin").first()
    if admin_role and not db.query(User).filter_by(username=ADMIN_USERNAME).first():
        db.add(User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            email=ADMIN_EMAIL,
            role_id=admin_role.id,
        ))
    db.commit()


def seed_demo_data(db: Session) -> None:
    """幂等：通知模板 + 演示车辆/车主（依赖 citizen 角色已存在）。"""
    if not db.query(NotificationTemplate).filter_by(code="violation_notice").first():
        db.add(NotificationTemplate(
            code="violation_notice", channel="email",
            subject_template="【交通违章通知】{violation_type}",
            body_template=("车牌 {plate_no} 于 {occurred_at} 在 {location_text} 发生 {violation_type}，"
                           "罚款 {fine_amount} 元，扣 {points} 分。违章编号 {violation_no}。"),
        ))
    for code, (subject_template, body_template) in AUTH_EMAIL_TEMPLATES.items():
        if not db.query(NotificationTemplate).filter_by(code=code).first():
            db.add(NotificationTemplate(
                code=code,
                channel="email",
                subject_template=subject_template,
                body_template=body_template,
            ))
    role = db.query(Role).filter_by(code="citizen").first()
    if role and not db.query(User).filter_by(username="owner1").first():
        owner = User(username="owner1", password_hash=hash_password("pass1234"),
                     email="owner1@example.com", role_id=role.id)
        db.add(owner)
        db.flush()
        db.add(Vehicle(plate_no="粤A12345", owner_id=owner.id, vehicle_type="小汽车", color="白"))
        db.add(Vehicle(plate_no="粤B67890", owner_id=owner.id, vehicle_type="小汽车", color="黑"))
    # 演示审核员
    reviewer_role = db.query(Role).filter_by(code="reviewer").first()
    if reviewer_role and not db.query(User).filter_by(username="reviewer").first():
        db.add(User(username="reviewer", password_hash=hash_password("reviewer123"),
                    email="reviewer@example.com", role_id=reviewer_role.id))
    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        seed_roles_and_admin(db)
        seed_demo_data(db)
        print("seed done (admin/admin1234)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
