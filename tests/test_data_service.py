from copy import deepcopy
import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile


def test_update_prospect_info_persists_and_refreshes_profile():
    prospect_id = "LEAD-12853"
    original_record = deepcopy(data_service.PROSPECTS[prospect_id])
    data_service._PROFILES.pop(prospect_id, None)

    try:
        data_service.update_prospect_info(prospect_id, "Terraform")

        assert "Terraform" in data_service.fetch_tech_stack(prospect_id)
        profile = build_prospect_profile.invoke({"prospect_id": prospect_id})
        assert "Terraform" in profile["prospect_profile"]["tech_stack"]
    finally:
        data_service.PROSPECTS[prospect_id] = original_record
        data_service._PROFILES.pop(prospect_id, None)
