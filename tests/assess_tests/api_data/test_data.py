# There is config for any linked information shared across the mock api queries
# General config
# ruff: noqa
from dataclasses import dataclass

from assess.services.models.flag import FlagType

test_fund_id = "test-fund"
test_round_id = "test-round"
test_user_id_lead_assessor = "lead"
test_user_id_assessor = "assessor"
test_user_id_commenter = "commenter"
test_funding_requested = 5000.0
fund_specific_claim_map = {
    "CYP": {
        "LEAD_ASSESSOR": {
            "accountId": "cyp-lead-assessor",
            "email": "cyp-lead-assessor@test.com",
            "fullName": "Lead Test User",
            "roles": ["CYP_LEAD_ASSESSOR", "CYP_ASSESSOR", "CYP_COMMENTER"],
        },
        "ASSESSOR": {
            "accountId": "cyp-assessor",
            "email": "cyp-assessor@test.com",
            "fullName": "Assessor Test User",
            "roles": ["CYP_ASSESSOR", "CYP_COMMENTER"],
        },
        "COMMENTER": {
            "accountId": "cyp-commenter",
            "email": "cyp-commenter@test.com",
            "fullName": "Commenter Test User",
            "roles": ["CYP_COMMENTER"],
        },
    },
    "NSTF": {
        "LEAD_ASSESSOR": {
            "accountId": "nstf-lead-assessor",
            "email": "nstf-lead-assessor@test.com",
            "fullName": "Lead Test User",
            "roles": ["NSTF_LEAD_ASSESSOR", "NSTF_ASSESSOR", "NSTF_COMMENTER"],
        },
        "ASSESSOR": {
            "accountId": "nstf-assessor",
            "email": "nstf-assessor@test.com",
            "fullName": "Assessor Test User",
            "roles": ["NSTF_ASSESSOR", "NSTF_COMMENTER"],
        },
        "COMMENTER": {
            "accountId": "nstf-commenter",
            "email": "nstf-commenter@test.com",
            "fullName": "Commenter Test User",
            "roles": ["NSTF_COMMENTER"],
        },
    },
    "COF": {
        "LEAD_ASSESSOR": {
            "accountId": "cof-lead-assessor",
            "email": "cof-lead-assessor@test.com",
            "fullName": "Lead Test User",
            "roles": ["COF_LEAD_ASSESSOR", "COF_ASSESSOR", "COF_COMMENTER"],
        },
        "ASSESSOR": {
            "accountId": "cof-assessor",
            "email": "cof-assessor@test.com",
            "fullName": "Assessor Test User",
            "roles": ["COF_ASSESSOR", "COF_COMMENTER"],
        },
        "COMMENTER": {
            "accountId": "cof-commenter",
            "email": "cof-commenter@test.com",
            "fullName": "Commenter Test User",
            "roles": ["COF_COMMENTER"],
        },
    },
    "DPIF": {
        "LEAD_ASSESSOR": {
            "accountId": "dpif-lead-assessor",
            "email": "dpif-lead-assessor@test.com",
            "fullName": "Lead Test User",
            "roles": ["DPIF_LEAD_ASSESSOR", "DPIF_ASSESSOR", "DPIF_COMMENTER"],
        },
        "ASSESSOR": {
            "accountId": "dpif-assessor",
            "email": "dpif-assessor@test.com",
            "fullName": "Assessor Test User",
            "roles": ["DPIF_ASSESSOR", "DPIF_COMMENTER"],
        },
        "COMMENTER": {
            "accountId": "dpif-commenter",
            "email": "dpif-commenter@test.com",
            "fullName": "Commenter Test User",
            "roles": ["DPIF_COMMENTER"],
        },
    },
    "HSRA": {
        "LEAD_ASSESSOR": {
            "accountId": "hsra-lead-assessor",
            "email": "hsra-lead-assessor@test.com",
            "fullName": "Lead Test User",
            "roles": ["HSRA_LEAD_ASSESSOR", "HSRA_ASSESSOR", "HSRA_COMMENTER"],
        },
        "ASSESSOR": {
            "accountId": "hsra-assessor",
            "email": "hsra-assessor@test.com",
            "fullName": "Assessor Test User",
            "roles": ["HSRA_ASSESSOR", "HSRA_COMMENTER"],
        },
        "COMMENTER": {
            "accountId": "hsra-commenter",
            "email": "hsra-commenter@test.com",
            "fullName": "Commenter Test User",
            "roles": ["HSRA_COMMENTER"],
        },
    },
}

all_fund_user_ids = [user_info["accountId"] for fund in fund_specific_claim_map.values() for user_info in fund.values()]

# application specific config
flagged_app_id = "flagged_app"
flagged_app = {
    "id": flagged_app_id,
    "workflow_status": "IN_PROGRESS",
    "project_name": "Project In prog and Res",
    "short_id": "INP",
    "flags": [
        {
            "id": "1c5e8bea-f5ed-4b74-8823-e64fec27a7db",
            "latest_status": FlagType.RAISED.value,
            "latest_allocation": "test_team",
            "application_id": flagged_app_id,
            "sections_to_flag": ["Test section"],
            "updates": [
                {
                    "id": "316f607a-03b7-4592-b927-5021a28b7d6a",
                    "user_id": test_user_id_lead_assessor,
                    "date_created": "2023-02-19 12:00:00",
                    "justification": "Test",
                    "status": FlagType.RAISED.value,
                    "allocation": None,
                }
            ],
        },
    ],
    "tag_associations": [
        {
            "associated": True,
            "id": "e908512a-25ef-4ec8-9850-b5a9c867992f",
            "user_id": test_user_id_lead_assessor,
            "tag": {
                "active": True,
                "creator_user_id": test_user_id_lead_assessor,
                "id": "52ea161d-8593-4943-8676-baae283cd979",
                "value": "Tag one red",
                "tag_type": {
                    "id": "5e7ecf78-9239-498a-9086-008043230a69",
                    "purpose": "NEGATIVE",
                },
            },
        }
    ],
    "qa_complete": [],
    "is_qa_complete": False,
    "criteria_sub_criteria_name": "test_sub_criteria",
    "criteria_sub_criteria_id": "test_sub_criteria_id",
    "theme_id": "test_theme_id",
    "theme_name": "test_theme_name",
    "mock_field": {
        "answer": "Yes",
        "field_id": "JCACTy",
        "field_type": "yesNoField",
        "form_name": "community-engagement",
        "presentation_type": "text",
        "question": "Have you done any fundraising in the community?",
    },
}

resolved_app_id = "resolved_app"
resolved_app = {
    "id": resolved_app_id,
    "workflow_status": "IN_PROGRESS",
    "project_name": "Project In prog and Res",
    "short_id": "INP",
    "flags": [
        {
            "id": "1c5e8bea-f5ed-4b74-8823-e64fec27a7dc",
            "latest_status": FlagType.RESOLVED.value,
            "latest_allocation": "test_team",
            "application_id": resolved_app_id,
            "sections_to_flag": ["Test section"],
            "updates": [
                {
                    "id": "316f607a-03b7-4592-b927-5021a28b7d6a",
                    "user_id": test_user_id_lead_assessor,
                    "date_created": "2023-02-20 12:00:00",
                    "justification": "Test",
                    "status": FlagType.RAISED.value,
                    "allocation": None,
                },
                {
                    "id": "316f607a-03b7-4592-b927-5021a28b7d6a",
                    "user_id": test_user_id_lead_assessor,
                    "date_created": "2023-02-20 12:00:00",
                    "justification": "Test",
                    "status": FlagType.RESOLVED.value,
                    "allocation": None,
                },
            ],
        },
    ],
    "tag_associations": [
        {
            "associated": True,
            "id": "f908512a-25ef-4ec8-9850-b5a9c867992f",
            "user_id": test_user_id_lead_assessor,
            "tag": {
                "active": True,
                "creator_user_id": test_user_id_lead_assessor,
                "id": "62ea161d-8593-4943-8676-baae283cd979",
                "value": "Tag one red",
                "tag_type": {
                    "id": "7e7ecf78-9239-498a-9086-008043230a69",
                    "purpose": "NEGATIVE",
                },
            },
        }
    ],
    "user_associations": [],
    "qa_complete": [],
    "is_qa_complete": False,
    "criteria_sub_criteria_name": "test_sub_criteria",
    "criteria_sub_criteria_id": "test_sub_criteria_id",
    "theme_id": "test_theme_id",
    "theme_name": "test_theme_name",
    "mock_field": {
        "answer": "Yes",
        "field_id": "JCACTy",
        "field_type": "yesNoField",
        "form_name": "community-engagement",
        "presentation_type": "text",
        "question": "Have you done any fundraising in the community?",
    },
}

stopped_app_id = "stopped_app"
stopped_app = {
    "id": stopped_app_id,
    "workflow_status": "IN_PROGRESS",
    "project_name": "Project In prog and Stop",
    "short_id": "FS",
    "asset_type": "gallery",
    "local_authority": "wokefield",
    "flags": [
        {
            "id": "1c5e8bea-f5ed-4b74-8823-e64fec27a7bd",
            "latest_status": FlagType.STOPPED.value,
            "latest_allocation": "test_team",
            "application_id": stopped_app_id,
            "sections_to_flag": ["Test section"],
            "updates": [
                {
                    "id": "316f607a-03b7-4592-b927-5021a28b7d6a",
                    "user_id": test_user_id_lead_assessor,
                    "date_created": "2023-02-20 12:00:00",
                    "justification": "Test",
                    "status": FlagType.STOPPED.value,
                    "allocation": None,
                }
            ],
        },
    ],
    "tag_associations": [
        {
            "associated": True,
            "id": "g908512a-25ef-4ec8-9850-b5a9c867992f",
            "user_id": test_user_id_lead_assessor,
            "tag": {
                "active": True,
                "creator_user_id": test_user_id_lead_assessor,
                "id": "72ea161d-8593-4943-8676-baae283cd979",
                "value": "Tag one red",
                "tag_type": {
                    "id": "7e7ecf78-9239-498a-9086-008043230a69",
                    "purpose": "NEGATIVE",
                },
            },
        }
    ],
    "qa_complete": [],
    "is_qa_complete": False,
}

assigned_app_id = "assigned_app"
assigned_app = {
    "id": assigned_app_id,
    "workflow_status": "IN_PROGRESS",
    "project_name": "Project In prog and assigned",
    "short_id": "ASAP",
    "asset_type": "gallery",
    "local_authority": "wokefield",
    "qa_complete": [],
    "tag_associations": [],
    "user_associations": [
        {
            "user_id": user_id,
            "log": "{'2024-06-21T15:00:50.978297+00:00': 'activated'}",
            "assigner_id": user_id,
            "created_at": "2024-06-21T15:00:50.990591+00:00",
            "application_id": assigned_app_id,
            "active": True,
        }
        for user_id in all_fund_user_ids
    ],
    "flags": [],
    "is_qa_complete": False,
}

flagged_qa_completed_app_id = "flagged_qa_completed_app"
flagged_qa_completed_app = {
    "id": flagged_qa_completed_app_id,
    "workflow_status": "COMPLETED",
    "project_name": "Project Completed Flag and QA",
    "short_id": "FQAC",
    "flags": [
        {
            "id": "1c5e8bea-f5ed-4b74-8823-e64fec27a7bd",
            "latest_status": FlagType.RAISED.value,
            "latest_allocation": "test_team",
            "application_id": flagged_qa_completed_app_id,
            "justification": "Test",
            "sections_to_flag": ["Test section"],
            "updates": [
                {
                    "id": "316f607a-03b7-4592-b927-5021a28b7d6b",
                    "user_id": test_user_id_lead_assessor,
                    "date_created": "2023-02-20 12:00:00",
                    "justification": "Test",
                    "status": FlagType.RAISED.value,
                    "allocation": None,
                }
            ],
        },
    ],
    "tag_associations": [
        {
            "associated": True,
            "id": "h908512a-25ef-4ec8-9850-b5a9c867992f",
            "user_id": test_user_id_lead_assessor,
            "tag": {
                "active": True,
                "creator_user_id": test_user_id_lead_assessor,
                "id": "82ea161d-8593-4943-8676-baae283cd979",
                "value": "Tag one red",
                "tag_type": {
                    "id": "8e7ecf78-9239-498a-9086-008043230a69",
                    "purpose": "NEGATIVE",
                },
            },
        }
    ],
    "qa_complete": [
        {
            "id": "416f607a-03b7-4592-b927-5021a28b7d6b",
            "application_id": flagged_qa_completed_app_id,
            "user_id": test_user_id_lead_assessor,
            "date_created": "2023-02-19 12:00:00",
        }
    ],
    "is_qa_complete": True,
}

# mock api call results
mock_api_results = {
    "fund_store/funds/{fund_id}": {
        "id": test_fund_id,
        "name": "Funding Service Design Unit Test Fund",
        "short_name": "TF",
        "description": "unit testing fund",
        # "assessment_start": None,
        # "assessment_deadline": "2124-01-01 12:00:00",
        # "deadline": "2024-01-01 12:00:00"
    },
    "fund_store/funds/NSTF": {
        "id": "NSTF",
        "name": "Night Shelter Test Fund",
        "short_name": "NSTF",
        "description": "unit testing fund",
    },
    "fund_store/funds/CYP": {
        "id": "CYP",
        "name": "The Children and Young People's Resettlement Fund",
        "short_name": "CYP",
        "description": "unit testing fund",
    },
    "fund_store/funds/COF": {
        "id": "COF",
        "name": "Community Ownership Fund",
        "short_name": "COF",
        "description": "unit testing fund",
    },
    "fund_store/funds/DPIF": {
        "id": "DPIF",
        "name": "Digital Planning Innovation Fund",
        "short_name": "DPIF",
        "description": "unit testing fund",
    },
    "fund_store/funds/{fund_id}/rounds/{round_id}": {
        "id": test_round_id,
        "fund_id": test_fund_id,
        "short_name": "TR",
        "title": "Test round",
        "assessment_criteria_weighting": [{"id": "crit1", "name": "Test criteria", "value": 1.0}],
        "assessment_deadline": "2023-03-01T12:00:00",
        "assessment_start": None,
        "deadline": "2022-12-01T12:00:00",
        "opens": "2022-10-01T12:00:00",
        "all_uploaded_documents_section_available": True,
        "application_fields_download_available": True,
    },
    "assessment_store/user/{user_id}/applications": [
        {
            "assigner_id": test_user_id_lead_assessor,
            "user_id": test_user_id_assessor,
            "log": "{'2024-06-21T11:13:51.964291+00:00': 'activated'}",
            "application_id": assigned_app_id,
            "active": "true",
            "created_at": "2024-06-21T11:13:52.011951+00:00",
        }
    ],
    "assessment_store/application_overviews/{fund_id}/{round_id}?": [
        {
            "fund_id": test_fund_id,
            "round_id": test_round_id,
            "application_id": flagged_qa_completed_app_id,
            "asset_type": "gallery",
            "local_authority": "wokefield",
            "tag_associations": flagged_qa_completed_app["tag_associations"],
            "user_associations": [],
            "flags": flagged_qa_completed_app["flags"],
            "qa_complete": flagged_qa_completed_app["qa_complete"],
            "funding_amount_requested": test_funding_requested + 2000,
            "is_qa_complete": True,
            "language": "en",
            "location_json_blob": {
                "constituency": "test-constituency",
                "country": "England",
                "county": "test-county",
                "error": False,
                "postcode": "QQ12QQ",
                "region": "England",
            },
            "project_name": flagged_qa_completed_app["project_name"],
            "short_id": flagged_qa_completed_app["short_id"],
            "type_of_application": "COF",
            "workflow_status": flagged_qa_completed_app["workflow_status"],
            "date_submitted": "2024-01-04T15:54:30.373564",
        },
        {
            "fund_id": test_fund_id,
            "round_id": test_round_id,
            "application_id": assigned_app_id,
            "asset_type": "gallery",
            "local_authority": "wokefield",
            "tag_associations": assigned_app["tag_associations"],
            "user_associations": assigned_app["user_associations"],
            "flags": assigned_app["flags"],
            "qa_complete": assigned_app["qa_complete"],
            "funding_amount_requested": test_funding_requested + 8000,
            "is_qa_complete": True,
            "language": "en",
            "location_json_blob": {
                "constituency": "test-constituency",
                "country": "England",
                "county": "test-county",
                "error": False,
                "postcode": "QQ12QQ",
                "region": "England",
            },
            "project_name": assigned_app["project_name"],
            "short_id": assigned_app["short_id"],
            "type_of_application": "COF",
            "workflow_status": assigned_app["workflow_status"],
            "date_submitted": "2024-01-04T15:54:30.373564",
        },
        {
            "fund_id": test_fund_id,
            "round_id": test_round_id,
            "application_id": stopped_app_id,
            "asset_type": stopped_app["asset_type"],
            "local_authority": stopped_app["local_authority"],
            "tag_associations": stopped_app["tag_associations"],
            "user_associations": [],
            "flags": stopped_app["flags"],
            "qa_complete": stopped_app["qa_complete"],
            "funding_amount_requested": test_funding_requested + 1000,
            "is_qa_complete": False,
            "language": "en",
            "location_json_blob": {
                "constituency": "test-constituency",
                "country": "Wales",
                "county": "test-county",
                "error": False,
                "postcode": "QQ12QQ",
                "region": "Wales",
            },
            "project_name": stopped_app["project_name"],
            "short_id": stopped_app["short_id"],
            "type_of_application": "COF",
            "workflow_status": stopped_app["workflow_status"],
            "date_submitted": "2024-01-04T15:54:30.373564",
        },
        {
            "fund_id": test_fund_id,
            "round_id": test_round_id,
            "application_id": resolved_app_id,
            "asset_type": "gallery",
            "local_authority": "wokefield",
            "tag_associations": resolved_app["tag_associations"],
            "user_associations": resolved_app["user_associations"],
            "flags": resolved_app["flags"],
            "qa_complete": resolved_app["qa_complete"],
            "funding_amount_requested": test_funding_requested,
            "is_qa_complete": False,
            "language": "en",
            "location_json_blob": {
                "constituency": "test-constituency",
                "country": "Scotland",
                "county": "test-county",
                "error": False,
                "postcode": "QQ12QQ",
                "region": "Scotland",
            },
            "project_name": resolved_app["project_name"],
            "short_id": resolved_app["short_id"],
            "type_of_application": "COF",
            "workflow_status": resolved_app["workflow_status"],
            "date_submitted": "2024-01-04T15:54:30.373564",
        },
    ],
    "assessment_store/application_overviews/{fund_id}/{round_id}?search_term=Project+S&search_in=project_name%2Cshort_id&asset_type=gallery&local_authority=wokefield&status=STOPPED": [
        {
            "fund_id": test_fund_id,
            "round_id": test_round_id,
            "application_id": stopped_app_id,
            "asset_type": stopped_app["asset_type"],
            "local_authority": stopped_app["local_authority"],
            "tag_associations": stopped_app["tag_associations"],
            "flags": stopped_app["flags"],
            "qa_complete": stopped_app["qa_complete"],
            "funding_amount_requested": test_funding_requested,
            "is_qa_complete": False,
            "language": "en",
            "location_json_blob": {
                "constituency": "test-constituency",
                "country": "England",
                "county": "test-county",
                "error": False,
                "postcode": "QQ12QQ",
                "region": "England",
            },
            "project_name": stopped_app["project_name"],
            "short_id": stopped_app["short_id"],
            "type_of_application": "COF",
            "workflow_status": stopped_app["workflow_status"],
            "date_submitted": "2024-01-04T15:54:30.373564",
        }
    ],
    "assessment_store/assessments/get-stats/{fund_id}": {
        test_round_id: {
            "completed": 1,
            "assessing": 1,
            "not_started": 1,
            "qa_completed": 1,
            "stopped": 1,
            "flagged": 1,
            "total": 3,
        }
    },
    "assessment_store/progress": [],
    "assessment_store/application_overviews/stopped_app": {
        "criterias": [
            {
                "name": "string",
                "sub_criterias": [
                    {
                        "id": "string",
                        "name": "string",
                        "theme_count": 0,
                        "score": 0,
                        "status": "string",
                    }
                ],
                "total_criteria_score": 0,
                "number_of_scored_sub_criteria": 0,
                "weighting": 0,
            }
        ],
        "sections": [
            {
                "name": "string",
                "sub_criterias": [{"id": "string", "name": "string"}],
            }
        ],
        "project_name": stopped_app["project_name"],
        "short_id": stopped_app["short_id"],
        "workflow_status": stopped_app["workflow_status"],
        "fund_id": test_fund_id,
        "round_id": test_round_id,
        "qa_complete": stopped_app["qa_complete"],
    },
    "assessment_store/application_overviews/resolved_app": {
        "criterias": [
            {
                "name": "string",
                "sub_criterias": [
                    {
                        "id": resolved_app["criteria_sub_criteria_id"],
                        "name": resolved_app["criteria_sub_criteria_name"],
                        "theme_count": 1,
                        "score": 4,
                        "status": "string",
                    }
                ],
                "total_criteria_score": 4,
                "number_of_scored_sub_criteria": 5,
                "weighting": 0,
            }
        ],
        "sections": [
            {
                "name": "string",
                "sub_criterias": [{"id": "string", "name": "A fixed sub criteria"}],
            }
        ],
        "project_name": resolved_app["project_name"],
        "short_id": resolved_app["short_id"],
        "workflow_status": resolved_app["workflow_status"],
        "fund_id": test_fund_id,
        "round_id": test_round_id,
        "qa_complete": resolved_app["qa_complete"],
    },
    "assessment_store/application_overviews/flagged_app": {
        "criterias": [
            {
                "name": "string",
                "sub_criterias": [
                    {
                        "id": flagged_app["criteria_sub_criteria_id"],
                        "name": flagged_app["criteria_sub_criteria_name"],
                        "theme_count": 1,
                        "score": 4,
                        "status": "string",
                    }
                ],
                "total_criteria_score": 4,
                "number_of_scored_sub_criteria": 5,
                "weighting": 0,
            }
        ],
        "sections": [
            {
                "name": "string",
                "sub_criterias": [{"id": "string", "name": "string"}],
            }
        ],
        "project_name": flagged_app["project_name"],
        "short_id": flagged_app["short_id"],
        "workflow_status": flagged_app["workflow_status"],
        "fund_id": test_fund_id,
        "round_id": test_round_id,
        "qa_complete": flagged_app["qa_complete"],
    },
    "assessment_store/application_overviews/flagged_qa_completed_app": {
        "criterias": [],
        "sections": [],
        "fund_id": test_fund_id,
        "round_id": test_round_id,
        "project_name": flagged_qa_completed_app["project_name"],
        "short_id": flagged_qa_completed_app["short_id"],
        "workflow_status": flagged_qa_completed_app["workflow_status"],
        "qa_complete": flagged_qa_completed_app["qa_complete"],
    },
    "assessment_store/sub_criteria_overview/banner_state/resolved_app": {
        "short_id": resolved_app["short_id"],
        "project_name": resolved_app["project_name"],
        "funding_amount_requested": test_funding_requested,
        "workflow_status": resolved_app["workflow_status"],
        "fund_id": test_fund_id,
    },
    "assessment_store/sub_criteria_overview/banner_state/stopped_app": {
        "short_id": stopped_app["short_id"],
        "project_name": stopped_app["project_name"],
        "funding_amount_requested": test_funding_requested,
        "workflow_status": stopped_app["workflow_status"],
        "fund_id": test_fund_id,
    },
    "assessment_store/sub_criteria_overview/banner_state/flagged_qa_completed_app": {
        "short_id": flagged_qa_completed_app["short_id"],
        "project_name": flagged_qa_completed_app["project_name"],
        "funding_amount_requested": test_funding_requested,
        "workflow_status": flagged_qa_completed_app["workflow_status"],
        "fund_id": test_fund_id,
    },
    "assessment_store/flag_data?flag_id=flagged_app": flagged_app["flags"][-1],
    "assessment_store/flag_data?flag_id=resolved_app": resolved_app["flags"][-1],
    "assessment_store/flag_data?flag_id=stopped_app": stopped_app["flags"][-1],
    "assessment_store/flag_data?flag_id=flagged_qa_completed_app": flagged_qa_completed_app["flags"][-1],
    "assessment_store/flags?application_id=flagged_app": flagged_app["flags"],
    "assessment_store/flags?application_id=resolved_app": resolved_app["flags"],
    "assessment_store/flags?application_id=stopped_app": stopped_app["flags"],
    "assessment_store/flags?application_id=flagged_qa_completed_app": flagged_qa_completed_app["flags"],
    "assessment_store/qa_complete/flagged_app": {},
    "assessment_store/qa_complete/resolved_app": {},
    "assessment_store/qa_complete/stopped_app": {},
    "assessment_store/qa_complete/flagged_qa_completed_app": flagged_qa_completed_app["qa_complete"][0],
    "account_store/bulk-accounts": {
        test_user_id_lead_assessor: {
            "user_id": test_user_id_lead_assessor,
            "full_name": "Lead User",
            "highest_role": "LEAD_ASSESSOR",
            "email_address": "lead@test.com",
        },
        test_user_id_commenter: {
            "user_id": test_user_id_commenter,
            "full_name": "Commenter User",
            "highest_role": "COMMENTER",
            "email_address": "commenter@test.com",
        },
        test_user_id_assessor: {
            "user_id": test_user_id_assessor,
            "full_name": "Assessor User",
            "highest_role": "ASSESSOR",
            "email_address": "assessor@test.com",
        },
    },
    f"assessment_store/sub_criteria_overview/{resolved_app_id}/{resolved_app['criteria_sub_criteria_id']}": {
        "id": resolved_app["criteria_sub_criteria_id"],
        "name": resolved_app["criteria_sub_criteria_name"],
        "is_scored": True,
        "fund_id": test_fund_id,
        "funding_amount_requested": test_funding_requested,
        "project_name": resolved_app["project_name"],
        "short_id": resolved_app["short_id"],
        "workflow_status": resolved_app["workflow_status"],
        "themes": [
            {
                "answers": [resolved_app["mock_field"]],
                "id": resolved_app["theme_id"],
                "name": resolved_app["theme_name"],
            }
        ],
    },
    f"assessment_store/sub_criteria_themes/{resolved_app_id}/{resolved_app['theme_id']}": [resolved_app["mock_field"]],
    "assessment_store/comment?": [
        {
            "id": "test_id_1",
            "user_id": test_user_id_lead_assessor,
            "date_created": "2022-12-08T08:00:01.748170",
            "theme_id": resolved_app["theme_id"],
            "sub_criteria_id": "test_sub_criteria_id",
            "application_id": resolved_app["id"],
            "comment_type": "WHOLE_APPLICATION",
            "updates": [
                {
                    "comment": "This is a comment",
                    "comment_id": "test_id_1",
                    "date_created": "2022-12-08T08:00:01.748170",
                }
            ],
        },
        {
            "id": "test_id_2",
            "user_id": test_user_id_lead_assessor,
            "date_created": "2022-10-27T08:00:02.748170",
            "theme_id": resolved_app["theme_id"],
            "sub_criteria_id": "test_sub_criteria_id",
            "application_id": resolved_app["id"],
            "comment_type": "WHOLE_APPLICATION",
            "updates": [
                {
                    "comment": "You're missing some details",
                    "comment_id": "test_id_2",
                    "date_created": "2022-10-27T08:00:02.748170",
                }
            ],
        },
        {
            "id": "test_id_3",
            "user_id": test_user_id_lead_assessor,
            "date_created": "2022-10-27T08:00:03.748170",
            "theme_id": resolved_app["theme_id"],
            "sub_criteria_id": "test_sub_criteria_id",
            "application_id": resolved_app["id"],
            "comment_type": "WHOLE_APPLICATION",
            "updates": [
                {
                    "comment": "You're missing some details",
                    "comment_id": "test_id_3",
                    "date_created": "2022-10-27T08:00:03.748170",
                }
            ],
        },
        {
            "id": "test_id_4",
            "user_id": test_user_id_assessor,
            "date_created": "2022-10-27T08:00:04.748170",
            "theme_id": resolved_app["theme_id"],
            "sub_criteria_id": "test_sub_criteria_id",
            "application_id": resolved_app["id"],
            "comment_type": "WHOLE_APPLICATION",
            "updates": [
                {
                    "comment": "Im an assessor",
                    "comment_id": "test_id_4",
                    "date_created": "2022-10-27T08:00:04.748170",
                }
            ],
        },
        {
            "id": "test_id_5",
            "user_id": test_user_id_commenter,
            "date_created": "2022-10-27T08:00:05.748170",
            "theme_id": resolved_app["theme_id"],
            "sub_criteria_id": "test_sub_criteria_id",
            "application_id": resolved_app["id"],
            "comment_type": "WHOLE_APPLICATION",
            "updates": [
                {
                    "comment": "Im a commenter",
                    "comment_id": "test_id_5",
                    "date_created": "2022-10-27T08:00:05.748170",
                }
            ],
        },
    ],
    "assessment_store/score?": [
        {
            "application_id": resolved_app_id,
            "date_created": "2022-12-08T15:45:54.664955",
            "id": "ba4ce3fb-6819-4f33-94ae-b830dc4c662b",
            "justification": "good",
            "score": 3,
            "sub_criteria_id": resolved_app["criteria_sub_criteria_id"],
            "user_id": test_user_id_lead_assessor,
        },
        {
            "application_id": resolved_app_id,
            "date_created": "2022-12-08T15:45:15.802821",
            "id": "a96513cd-b1f8-435d-81e9-d8b760c8bb7d",
            "justification": "better",
            "score": 4,
            "sub_criteria_id": resolved_app["criteria_sub_criteria_id"],
            "user_id": test_user_id_lead_assessor,
        },
    ],
    "assessment_store/applications/{application_id}": {
        "fund_id": "TF",
        "round_id": "TR",
    },
    "/application/stopped_app/metadata": {
        "fund_id": test_fund_id,
        "round_id": test_round_id,
        "application_id": stopped_app_id,
        "asset_type": stopped_app["asset_type"],
        "local_authority": stopped_app["local_authority"],
        "tag_associations": stopped_app["tag_associations"],
        "flags": stopped_app["flags"],
        "qa_complete": stopped_app["qa_complete"],
        "funding_amount_requested": test_funding_requested + 1000,
        "is_qa_complete": False,
        "language": "en",
        "location_json_blob": {
            "constituency": "test-constituency",
            "country": "Wales",
            "county": "test-county",
            "error": False,
            "postcode": "QQ12QQ",
            "region": "Wales",
        },
        "project_name": stopped_app["project_name"],
        "short_id": stopped_app["short_id"],
        "type_of_application": "COF",
        "workflow_status": stopped_app["workflow_status"],
    },
}


@dataclass
class TestSanitiseData:
    tag: str = None
    style: str = None

    @property
    def input(self):
        if self.style:
            return {
                "answer": (
                    f"<{self.tag} style='list-style-type:{self.style};'>Example"
                    f" text <li>One</li>\n<li>Two</li></{self.tag}>"
                )
            }
        else:
            return {"answer": f"<{self.tag}>Example text <li>One</li>\n<li>Two</li></{self.tag}>"}

    @property
    def response(self):
        if self.style:
            return {
                "answer": (
                    f"<{self.tag} class='list-type-{self.style}'"
                    f" style='list-style-type:{self.style};'>Example text"
                    f" <li>One</li>\n<li>Two</li></{self.tag}>"
                )
            }

        else:
            if self.tag == "p":
                return {
                    "answer": f"<{self.tag} class='govuk-body'>Example text <li>One</li>\n<li>Two</li></{self.tag}>"
                }
            if self.tag == "ul":
                return {
                    "answer": (
                        f"<{self.tag} class='govuk-list"
                        " govuk-list--bullet'>Example text"
                        f" <li>One</li>\n<li>Two</li></{self.tag}>"
                    )
                }
            if self.tag == "ol":
                return {
                    "answer": (
                        f"<{self.tag} class='govuk-list"
                        " govuk-list--number'>Example text"
                        f" <li>One</li>\n<li>Two</li></{self.tag}>"
                    )
                }
