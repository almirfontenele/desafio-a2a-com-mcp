import unittest
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AGENTE_DIR = BASE_DIR / "agente"
if str(AGENTE_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTE_DIR))

from agent_config import AGENT_CARD
from agent_models import TaskRecord, TaskState
from agent_parser import BookingMessageParser
from agent_task_manager import TaskManager


class TestA2AAgentUnit(unittest.TestCase):
    """Unit tests for A2A Agent state machine logic, card schema, and message parsing."""

    def test_agent_card_structure(self):
        """Verify that the agent card matches required A2A v1.0 specifications."""
        self.assertEqual(AGENT_CARD["name"], "Central de Salas")
        self.assertEqual(AGENT_CARD["version"], "1.0.0")
        self.assertIn("supportedInterfaces", AGENT_CARD)
        self.assertIn("skills", AGENT_CARD)

        interfaces = AGENT_CARD["supportedInterfaces"]
        self.assertTrue(any(i.get("protocolBinding") == "JSONRPC" and i.get("protocolVersion") == "1.0" for i in interfaces))

        skills = [s["id"] for s in AGENT_CARD.get("skills", [])]
        self.assertIn("reservar-sala", skills)

    def test_booking_message_argument_parsing(self):
        """Test parsing booking text into structured arguments."""
        text = "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 fim=2026-11-03T15:00:00-03:00 responsavel=Marty"
        args = BookingMessageParser.parse_booking_arguments(text)

        self.assertEqual(args.get("sala"), "sala-garagem")
        self.assertEqual(args.get("inicio"), "2026-11-03T14:00:00-03:00")
        self.assertEqual(args.get("fim"), "2026-11-03T15:00:00-03:00")
        self.assertEqual(args.get("responsavel"), "Marty")

    def test_continuation_message_parsing(self):
        """Test parsing user selection vs refusal in continuation messages."""
        msg_choice = "escolha=sala-fusca"
        msg_decline = "escolha=recusar"
        msg_invalid = "texto qualquer sem comando"

        action1, room1 = BookingMessageParser.parse_choice(msg_choice)
        self.assertEqual(action1, "accept")
        self.assertEqual(room1, "sala-fusca")

        action2, room2 = BookingMessageParser.parse_choice(msg_decline)
        self.assertEqual(action2, "decline")
        self.assertEqual(room2, "recusar")

        action3, room3 = BookingMessageParser.parse_choice(msg_invalid)
        self.assertEqual(action3, "none")
        self.assertEqual(room3, "")

    def test_pause_message_formatting(self):
        """Test pause message formatting standard alternatives: <id1>, <id2>."""
        alternatives = ["sala-fusca", "sala-mirante"]
        pause_text = f"alternativas: {', '.join(sorted(alternatives))}"

        self.assertEqual(pause_text, "alternativas: sala-fusca, sala-mirante")
        self.assertFalse(pause_text.startswith("Erro"))
        self.assertFalse(pause_text.endswith("."))

    def test_task_state_transitions_and_manager(self):
        """Test TaskManager lifecycle state management and serialization."""
        manager = TaskManager()
        task = manager.create_task(traceparent="00-test-01")
        self.assertEqual(task.state, TaskState.SUBMITTED)
        self.assertEqual(task.traceparent, "00-test-01")

        task.add_user_message("reservar sala=sala-garagem ...")
        task.state = TaskState.WORKING
        self.assertEqual(task.state, TaskState.WORKING)

        # Pause
        task.state = TaskState.INPUT_REQUIRED
        task.set_agent_message("alternativas: sala-fusca, sala-mirante")
        task_dict = task.to_dict()

        self.assertEqual(task_dict["status"]["state"], "TASK_STATE_INPUT_REQUIRED")
        self.assertIn("alternativas: sala-fusca, sala-mirante", task_dict["status"]["message"]["parts"][0]["text"])

        # Completion
        task.state = TaskState.COMPLETED
        task.set_artifact("reserva", {"sala": "sala-fusca"})
        task_dict = task.to_dict()
        self.assertEqual(task_dict["status"]["state"], "TASK_STATE_COMPLETED")
        self.assertEqual(len(task_dict["artifacts"]), 1)
        self.assertTrue(task.state.is_terminal)


if __name__ == "__main__":
    unittest.main()
