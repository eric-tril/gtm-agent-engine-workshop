import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent.gtm_agent import send_prospect_email


class SendProspectEmailTest(unittest.TestCase):
    def setUp(self):
        self.runtime = SimpleNamespace(config={"metadata": {}})

    def test_blocks_disqualified_prospects(self):
        for prospect_id in (
            "LEAD-50001",
            "LEAD-50002",
            "LEAD-50003",
            "LEAD-50004",
            "LEAD-50005",
        ):
            with self.subTest(prospect_id=prospect_id):
                result = send_prospect_email.func(
                    {"prospect_id": prospect_id, "email": "prospect@example.com"},
                    "Subject",
                    "Body",
                    self.runtime,
                    from_rep={},
                )

                self.assertEqual(result["status"], "blocked")
                self.assertEqual(
                    result["reason"],
                    "Prospect is marked disqualified; confirm with the rep before contacting.",
                )

    def test_sends_to_non_disqualified_prospect(self):
        result = send_prospect_email.func(
            {"prospect_id": "LEAD-12853", "email": "prospect@example.com"},
            "Subject",
            "Body",
            self.runtime,
            from_rep={},
        )

        self.assertEqual(result["status"], "sent")
