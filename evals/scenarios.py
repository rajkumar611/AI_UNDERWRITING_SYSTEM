"""
Eval scenarios — one entry per sample document.

Each scenario defines:
  - doc:                   filename under samples/documents/
  - class_of_business/jurisdiction: submission parameters
  - expected_workflow_status:  what the pipeline must return
  - expected_decline_reason:   set only for DECLINED cases
  - expected_missing_fields:   fields that must appear in missing_critical_fields
  - expected_injection:        True if injection_snippets must be non-empty
  - must_have_pricing:         True if pricing_output must be present
  - must_have_governance:      True if governance_decision must be present
  - must_not_have_risk:        True if risk_assessment must be absent (early exit)
  - risk_decision:             expected risk_decision inside risk_assessment (if present)
  - description:               human-readable label for the score table
"""
from __future__ import annotations

SCENARIOS: list[dict] = [
    # ── File 1 — Clean auto-approve ───────────────────────────────────────────
    {
        "doc": "clean_auto_approve.txt",
        "class_of_business": "property",
        "jurisdiction": "NZ",
        "description": "Clean risk — auto-approve, full pipeline",
        "expected_workflow_status": "COMPLETED",
        "must_have_pricing": True,
        "must_have_governance": True,
        "must_not_have_risk": False,
        "risk_decision": "ACCEPT",
        "expected_decline_reason": None,
        "expected_missing_fields": [],
        "expected_injection": False,
    },

    # ── File 2 — Referral: sum insured > NZD 50M ─────────────────────────────
    {
        "doc": "referral_sum_insured.txt",
        "class_of_business": "property",
        "jurisdiction": "NZ",
        "description": "Referral — sum insured NZD 52M exceeds delegation threshold",
        "expected_workflow_status": "AWAITING_HUMAN",
        "must_have_pricing": False,
        "must_have_governance": False,
        "must_not_have_risk": False,
        "risk_decision": "REFER",
        "expected_decline_reason": None,
        "expected_missing_fields": [],
        "expected_injection": False,
    },

    # ── File 3 — Referral: high claim frequency ───────────────────────────────
    {
        "doc": "referral_more_claims.txt",
        "class_of_business": "property",
        "jurisdiction": "NZ",
        "description": "Referral — 4 claims in 3 years (elevated frequency)",
        "expected_workflow_status": "AWAITING_HUMAN",
        "must_have_pricing": False,
        "must_have_governance": False,
        "must_not_have_risk": False,
        "risk_decision": "REFER",
        "expected_decline_reason": None,
        "expected_missing_fields": [],
        "expected_injection": False,
    },

    # ── File 4 — Referral: single large loss ──────────────────────────────────
    {
        "doc": "referral_large_claim.txt",
        "class_of_business": "property",
        "jurisdiction": "NZ",
        "description": "Referral — single loss NZD 1,050,000 (severity trigger)",
        "expected_workflow_status": "AWAITING_HUMAN",
        "must_have_pricing": False,
        "must_have_governance": False,
        "must_not_have_risk": False,
        "risk_decision": "REFER",
        "expected_decline_reason": None,
        "expected_missing_fields": [],
        "expected_injection": False,
    },

    # ── File 5 — Referral: hazard zone ───────────────────────────────────────
    {
        "doc": "referral_hazard_zone.txt",
        "class_of_business": "property",
        "jurisdiction": "NZ",
        "description": "Referral — Category 2 flood zone, coastal exposure",
        "expected_workflow_status": "AWAITING_HUMAN",
        "must_have_pricing": False,
        "must_have_governance": False,
        "must_not_have_risk": False,
        "risk_decision": "REFER",
        "expected_decline_reason": None,
        "expected_missing_fields": [],
        "expected_injection": False,
    },

    # ── File 6 — Decline: missing mandatory fields ────────────────────────────
    {
        "doc": "decline_missing_fields.txt",
        "class_of_business": "property",
        "jurisdiction": "NZ",
        "description": "Decline — sum insured and other critical fields missing",
        "expected_workflow_status": "DECLINED",
        "must_have_pricing": False,
        "must_have_governance": False,
        "must_not_have_risk": True,
        "risk_decision": None,
        "expected_decline_reason": "MISSING_MANDATORY_FIELDS",
        "expected_missing_fields": ["sum_insured"],
        "expected_injection": False,
    },

    # ── File 7 — Decline: prompt injection ───────────────────────────────────
    {
        "doc": "decline_prompt_injection.txt",
        "class_of_business": "property",
        "jurisdiction": "NZ",
        "description": "Decline — document contains prompt injection attempts",
        "expected_workflow_status": "DECLINED",
        "must_have_pricing": False,
        "must_have_governance": False,
        "must_not_have_risk": True,
        "risk_decision": None,
        "expected_decline_reason": "PROMPT_INJECTION",
        "expected_missing_fields": [],
        "expected_injection": True,
    },
]
