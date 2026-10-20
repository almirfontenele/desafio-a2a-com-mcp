import unittest
import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
MCP_DIR = BASE_DIR / "servidor-mcp"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from mcp_config import SALAS_FILE, RESERVAS_FILE, POLITICA_FILE, get_request_state_secret
from mcp_repository import RoomRepository
from mcp_rules import BookingPolicyValidator
from mcp_security import HMACStateTokenService


class TestMCPServerDomainAndRules(unittest.TestCase):
    """Unit tests for MCP Server repository, business rules, and HMAC tokens."""

    def setUp(self):
        self.repository = RoomRepository()
        self.validator = BookingPolicyValidator(self.repository)
        self.token_service = HMACStateTokenService("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")

    def test_data_files_exist(self):
        """Verify that fixed data files exist and are non-empty."""
        self.assertTrue(SALAS_FILE.exists(), "dados/salas.json must exist")
        self.assertTrue(RESERVAS_FILE.exists(), "dados/reservas.json must exist")
        self.assertTrue(POLITICA_FILE.exists(), "dados/politica-de-uso.md must exist")

        with open(SALAS_FILE, "r", encoding="utf-8") as f:
            salas = json.load(f)
            self.assertIsInstance(salas, list)
            self.assertGreaterEqual(len(salas), 5, "Should have at least 5 rooms")

        with open(POLITICA_FILE, "r", encoding="utf-8") as f:
            politica_text = f.read()
            self.assertIn("versao: 2026-11-01", politica_text)

    def test_business_rules_validation(self):
        """Test business constraints in sequence: room existence, operating hours, duration, interval."""
        # 1. Inexistent room
        val = self.validator.validate("sala-delorean", "2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00")
        self.assertFalse(val.is_valid)
        self.assertIn("Sala inexistente: sala-delorean", val.error_message or "")

        # 2. Out of operating hours (07:00 is before 08:00)
        val = self.validator.validate("sala-aquario", "2026-11-03T07:00:00-03:00", "2026-11-03T08:00:00-03:00")
        self.assertFalse(val.is_valid)
        self.assertEqual(val.error_message, "Fora da janela de uso: a politica permite reservas entre 08:00 e 20:00")

        # 3. Duration exceeds 2 hours
        val = self.validator.validate("sala-aquario", "2026-11-03T09:00:00-03:00", "2026-11-03T12:00:00-03:00")
        self.assertFalse(val.is_valid)
        self.assertEqual(val.error_message, "Duracao acima do limite: a politica permite no maximo 2 horas")

        # 4. Inverted interval (fim <= inicio)
        val = self.validator.validate("sala-aquario", "2026-11-03T10:00:00-03:00", "2026-11-03T09:00:00-03:00")
        self.assertFalse(val.is_valid)
        self.assertEqual(val.error_message, "Intervalo invalido: fim deve ser posterior a inicio")

        # 5. Valid window
        val = self.validator.validate("sala-aquario", "2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00")
        self.assertTrue(val.is_valid)
        self.assertIsNone(val.error_message)

    def test_alternative_rooms_capacity_filter(self):
        """Test alternative room discovery filtered by capacity >= requested room, max 3."""
        alts = self.repository.find_alternative_rooms("sala-garagem", "2026-11-03T14:00:00-03:00", "2026-11-03T15:00:00-03:00")
        self.assertEqual(alts, ["sala-fusca", "sala-mirante"])

        alts_mirante = self.repository.find_alternative_rooms("sala-mirante", "2026-11-03T11:00:00-03:00", "2026-11-03T12:00:00-03:00")
        self.assertEqual(alts_mirante, [])

    def test_hmac_state_signing_and_verification(self):
        """Test HMAC-SHA256 signature creation, verification, tamper rejection, and expiry."""
        args = {
            "sala": "sala-garagem",
            "inicio": "2026-11-03T14:00:00-03:00",
            "fim": "2026-11-03T15:00:00-03:00",
            "responsavel": "Marty",
        }
        token = self.token_service.generate_token(args)
        self.assertIsInstance(token, str)
        self.assertIn(".", token)

        payload = self.token_service.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sala"], "sala-garagem")
        self.assertEqual(payload["responsavel"], "Marty")

        # Tamper check
        tampered_token = token[:-6] + ("AAAAAA" if not token.endswith("AAAAAA") else "BBBBBB")
        self.assertIsNone(self.token_service.verify_token(tampered_token))

        # Expired token check
        expired_token = self.token_service.generate_token(args, ttl_seconds=-10)
        self.assertIsNone(self.token_service.verify_token(expired_token))

    def test_secret_refusal_without_env_variable(self):
        """Verify that get_request_state_secret and HMACStateTokenService refuse missing or short secret."""
        old_val = os.environ.get("REQUEST_STATE_SECRET")
        try:
            if "REQUEST_STATE_SECRET" in os.environ:
                del os.environ["REQUEST_STATE_SECRET"]

            with self.assertRaises(RuntimeError):
                get_request_state_secret()

            with self.assertRaises(RuntimeError):
                HMACStateTokenService()

            os.environ["REQUEST_STATE_SECRET"] = "too_short_secret"
            with self.assertRaises(RuntimeError):
                get_request_state_secret()

            os.environ["REQUEST_STATE_SECRET"] = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            sec = get_request_state_secret()
            self.assertEqual(sec, "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
        finally:
            if old_val is not None:
                os.environ["REQUEST_STATE_SECRET"] = old_val
            elif "REQUEST_STATE_SECRET" in os.environ:
                del os.environ["REQUEST_STATE_SECRET"]

    def test_dynamic_politica_version_extraction(self):
        """Verify that repository dynamically extracts policy version from first line of markdown."""
        self.assertEqual(self.repository.get_politica_versao(), "2026-11-01")


if __name__ == "__main__":
    unittest.main()
