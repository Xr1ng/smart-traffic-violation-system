# app/api/v1/roles.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import Role, User

router = APIRouter(prefix="/admin/roles", tags=["roles"])


class RoleCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    permissions: list[str] | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


def _to_dict(r: Role) -> dict:
    import json
    perms = None
    if r.permissions:
        try:
            perms = json.loads(r.permissions)
        except (json.JSONDecodeError, TypeError):
            perms = []
    return {
        "id": r.id, "code": r.code, "name": r.name,
        "description": r.description,
        "permissions": perms or [],
    }


@router.get("")
def list_roles(db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> list[dict]:
    roles = db.query(Role).all()
    return [_to_dict(r) for r in roles]


@router.post("", status_code=201)
def create_role(body: RoleCreate, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> dict:
    if db.query(Role).filter(Role.code == body.code).first():
        raise HTTPException(status_code=409, detail="角色编码已存在")
    import json
    r = Role(
        name=body.name, code=body.code, description=body.description,
        permissions=json.dumps(body.permissions, ensure_ascii=False) if body.permissions else None,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _to_dict(r)


@router.patch("/{role_id}")
def update_role(role_id: int, body: RoleUpdate, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> dict:
    r = db.get(Role, role_id)
    if r is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    import json
    if body.name is not None:
        r.name = body.name
    if body.code is not None:
        existing = db.query(Role).filter(Role.code == body.code, Role.id != role_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="角色编码已存在")
        r.code = body.code
    if body.description is not None:
        r.description = body.description
    if body.permissions is not None:
        r.permissions = json.dumps(body.permissions, ensure_ascii=False)
    db.commit()
    db.refresh(r)
    return _to_dict(r)


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))):
    r = db.get(Role, role_id)
    if r is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.delete(r)
    db.commit()
    return None
