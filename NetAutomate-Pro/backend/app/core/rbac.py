"""Role-Based Access Control dependency factory."""
from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import RoleEnum, User

_ROLE_HIERARCHY = {
    RoleEnum.viewer: 0,
    RoleEnum.operator: 1,
    RoleEnum.admin: 2,
}


def require_role(*roles: RoleEnum):
    """Return a FastAPI dependency that enforces one of the given roles."""
    min_level = min(_ROLE_HIERARCHY[r] for r in roles)

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if _ROLE_HIERARCHY.get(current_user.role, -1) < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in roles]}",
            )
        return current_user

    return dependency


# Convenience shorthands
require_viewer = require_role(RoleEnum.viewer, RoleEnum.operator, RoleEnum.admin)
require_operator = require_role(RoleEnum.operator, RoleEnum.admin)
require_admin = require_role(RoleEnum.admin)
