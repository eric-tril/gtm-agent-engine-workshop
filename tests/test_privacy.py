import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"

from gtm_agent import gtm_agent, data_service


SENSITIVE_FIELDS = {"billing_qualification", "tax_id", "date_of_birth", "card_on_file", "credit_check_ref"}


class ProspectPrivacyTests(unittest.TestCase):
    def setUp(self):
        data_service._PROFILES.clear()

    def test_get_prospect_allows_only_contact_fields(self):
        result = gtm_agent.get_prospect.invoke({"prospect_id": "LEAD-12853"})

        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(result["prospect"]))
        self.assertEqual(set(result["prospect"]), {"prospect_id", "name", "email", "disqualified"})

    def test_build_profile_sanitizes_new_and_cached_profiles(self):
        built = gtm_agent.build_prospect_profile.invoke({"prospect_id": "LEAD-12853"})
        profile = built["prospect_profile"]

        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(profile))
        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(data_service._PROFILES["LEAD-12853"]))

        data_service._PROFILES["LEAD-12853"] = {
            **profile,
            "billing_qualification": {"tax_id": "secret"},
            "tax_id": "secret",
        }
        cached = gtm_agent.build_prospect_profile.invoke({"prospect_id": "LEAD-12853"})["prospect_profile"]

        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(cached))
        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(data_service._PROFILES["LEAD-12853"]))

    def test_score_payload_allows_only_scoring_fields(self):
        invoke = unittest.mock.Mock(return_value=SimpleNamespace(model_dump=lambda: {"score": 80}))
        profile = {
            "prospect_id": "LEAD-12853",
            "annual_revenue": 90000000,
            "tech_stack": ["Kafka"],
            "account_details": [{"industry": "Software"}],
            "billing_qualification": {"tax_id": "secret"},
            "tax_id": "secret",
        }
        offering = {
            "required_tech_stack": ["Kafka"],
            "min_annual_revenue": 1,
            "description": "Offer",
            "target_segment": "Enterprise",
            "internal_secret": "secret",
        }

        with patch.object(gtm_agent, "_scoring_llm", SimpleNamespace(invoke=invoke)):
            gtm_agent.score_prospect.invoke({"prospect_profile": profile, "offering": offering})
        payload = invoke.call_args.args[0][1]["content"]
        payload_data = json.loads(payload.split("\n\nProspect profile:\n", 1)[0].split("Offering:\n", 1)[1])
        profile_data = json.loads(payload.split("\n\nProspect profile:\n", 1)[1])

        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(payload))
        self.assertEqual(set(profile_data), {"annual_revenue", "tech_stack", "account_details"})
        self.assertEqual(set(payload_data), {"required_tech_stack", "min_annual_revenue", "description", "target_segment"})


if __name__ == "__main__":
    unittest.main()
