import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    AppError,
    AuthenticationError,
    BattleNotFoundError,
    InvalidVoteError,
    ModelNotFoundError,
    ProviderQuotaExceededError,
    ProviderUnavailableError,
)
from app.core.exception_handlers import app_error_handler, global_exception_handler


class TestAppErrorArchitecture(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.add_exception_handler(AppError, app_error_handler)
        self.app.add_exception_handler(Exception, global_exception_handler)

        @self.app.get("/test/quota")
        def trigger_quota():
            raise ProviderQuotaExceededError(provider="groq", reset_in_seconds=3600)

        @self.app.get("/test/unavailable")
        def trigger_unavailable():
            raise ProviderUnavailableError(provider="google")

        @self.app.get("/test/model-not-found")
        def trigger_model_not_found():
            raise ModelNotFoundError(model_id="nonexistent-model-v1")

        @self.app.get("/test/battle-not-found")
        def trigger_battle_not_found():
            raise BattleNotFoundError(battle_id="b123")

        @self.app.get("/test/invalid-vote")
        def trigger_invalid_vote():
            raise InvalidVoteError(reason="Battle already voted")

        @self.app.get("/test/auth-error")
        def trigger_auth_error():
            raise AuthenticationError(message="Invalid token")

        @self.app.get("/test/unhandled")
        def trigger_unhandled():
            raise RuntimeError("Unexpected failure")

        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_provider_quota_exceeded_error(self):
        response = self.client.get("/test/quota")
        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "PROVIDER_QUOTA_EXHAUSTED")
        self.assertEqual(
            data["error"]["details"],
            {"provider": "groq", "reset_in_seconds": 3600},
        )
        self.assertIn("timestamp", data["error"])

    def test_provider_unavailable_error(self):
        response = self.client.get("/test/unavailable")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "PROVIDER_UNAVAILABLE")
        self.assertEqual(data["error"]["details"], {"provider": "google"})

    def test_model_not_found_error(self):
        response = self.client.get("/test/model-not-found")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "MODEL_NOT_FOUND")
        self.assertEqual(data["error"]["details"], {"model_id": "nonexistent-model-v1"})

    def test_battle_not_found_error(self):
        response = self.client.get("/test/battle-not-found")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "BATTLE_NOT_FOUND")
        self.assertEqual(data["error"]["details"], {"battle_id": "b123"})

    def test_invalid_vote_error(self):
        response = self.client.get("/test/invalid-vote")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "INVALID_VOTE")
        self.assertEqual(data["error"]["details"], {"reason": "Battle already voted"})

    def test_auth_error(self):
        response = self.client.get("/test/auth-error")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "UNAUTHORIZED")

    def test_unhandled_exception(self):
        response = self.client.get("/test/unhandled")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "INTERNAL_SERVER_ERROR")
        self.assertEqual(
            data["error"]["message"], "An unexpected internal server error occurred."
        )


if __name__ == "__main__":
    unittest.main()
