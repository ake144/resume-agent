"""Deterministic checks for preference blockers in job matching."""

from app.agents.matcher import find_preference_conflicts


def test_remote_and_sponsorship_conflicts_are_explicit():
    conflicts = find_preference_conflicts(
        "Senior Frontend Engineer",
        "This is an onsite role. We do not provide visa sponsorship.",
        {"work_modes": ["remote"], "visa_sponsorship_required": True},
    )

    assert len(conflicts) == 2
    assert any("remote" in conflict.lower() for conflict in conflicts)
    assert any("sponsorship" in conflict.lower() for conflict in conflicts)


def test_missing_preference_details_do_not_create_false_blockers():
    assert find_preference_conflicts("Frontend Engineer", "Remote role", {}) == []