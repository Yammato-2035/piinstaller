from __future__ import annotations

import unittest

from app_bootstrap.app_factory import create_app
from app_bootstrap.middleware_registry import register_middlewares


class AppFactoryMiddlewareRegistryTests(unittest.TestCase):
    def test_create_app_works(self) -> None:
        app = create_app(title="t", description="d", version="1.0.0")
        self.assertEqual(app.title, "t")

    def test_register_middlewares_no_crash(self) -> None:
        app = create_app(title="t", description="d", version="1.0.0")

        async def mw1(request, call_next):  # noqa: ANN001
            return await call_next(request)

        async def mw2(request, call_next):  # noqa: ANN001
            return await call_next(request)

        count = register_middlewares(app, [mw1, mw2])
        self.assertEqual(count, 2)
        self.assertGreaterEqual(len(app.user_middleware), 2)


if __name__ == "__main__":
    unittest.main()

