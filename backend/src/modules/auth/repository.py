"""认证数据访问逻辑。"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


class AuthRepository:
    """负责查询用户和用户角色。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def find_user_by_username(self, username: str) -> dict | None:
        """按用户名查询用户及其角色。"""
        statement = text(
            "SELECT u.user_id, u.username, u.password_hash, u.user_status, "
            "r.role_code "
            "FROM users AS u "
            "LEFT JOIN user_roles AS ur ON ur.user_id = u.user_id "
            "AND ur.status = 'ACTIVE' "
            "LEFT JOIN roles AS r ON r.role_id = ur.role_id "
            "WHERE u.username = :username "
            "LIMIT 1"
        )
        with self._engine.connect() as connection:
            row = connection.execute(
                statement, {"username": username}
            ).mappings().first()
        return dict(row) if row is not None else None