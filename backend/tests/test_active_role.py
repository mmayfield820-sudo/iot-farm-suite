from __future__ import annotations

import unittest

from fastapi import HTTPException

from backend.app.auth import resolve_active_role


class ActiveRoleTests(unittest.TestCase):
    def test_frontend_farm_admin_role_is_resolved_for_multi_role_user(self) -> None:
        role = resolve_active_role(
            "farmAdmin",
            ["system_admin", "farm_admin", "farmer"],
            "system_admin",
        )

        self.assertEqual(role, "farm_admin")

    def test_unassigned_role_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            resolve_active_role("farmAdmin", ["farmer"], "farmer")

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(raised.exception.detail, "ROLE_NOT_ASSIGNED")

    def test_missing_header_keeps_existing_fallback(self) -> None:
        self.assertEqual(
            resolve_active_role(None, ["system_admin", "farm_admin"], "system_admin"),
            "system_admin",
        )


if __name__ == "__main__":
    unittest.main()
