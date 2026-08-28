"""认证服务单元测试。"""

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.modules.auth.service import AuthService


class AuthServiceTest(unittest.TestCase):
    """验证登录成功和失败场景。"""

    def setUp(self) -> None:
        self.repository = MagicMock()
        self.service = AuthService(
            self.repository, "test-secret-with-at-least-32-bytes"
        )
        self.repository.find_user_by_username.return_value = {
            "user_id": 1,
            "username": "admin",
            "password_hash": "stored-hash",
            "user_status": "ACTIVE",
            "role_code": "SYSTEM_ADMIN",
        }

    @patch("src.modules.auth.service.bcrypt.checkpw", return_value=True)
    def test_login_returns_token_and_user(self, checkpw: MagicMock) -> None:
        result = self.service.login("admin", "password")

        self.assertTrue(result["token"])
        self.assertEqual(result["user"]["id"], "U001")
        self.assertEqual(result["user"]["role"], "system_admin")
        checkpw.assert_called_once()

    @patch("src.modules.auth.service.bcrypt.checkpw", return_value=False)
    def test_login_rejects_wrong_password(self, checkpw: MagicMock) -> None:
        with self.assertRaises(HTTPException) as context:
            self.service.login("admin", "wrong")

        self.assertEqual(context.exception.status_code, 401)