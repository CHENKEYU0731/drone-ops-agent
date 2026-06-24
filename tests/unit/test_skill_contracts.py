from pathlib import Path


SKILLS = [
    "preflight-check",
    "state-monitoring",
    "flight-log-analysis",
    "fault-diagnosis",
    "maintenance-advisor",
    "simulation-validation",
    "ops-report-generation",
]

REQUIRED_SECTIONS = [
    "# Skill:",
    "## Purpose",
    "## Inputs",
    "## Outputs",
    "## Hard Rules",
    "## Procedure",
    "## Evidence Requirements",
    "## Audit Requirements",
    "## Test Cases",
    "## Known Limitations",
    "## Future Extensions",
]


def test_skill_directories_have_contract_files() -> None:
    for skill in SKILLS:
        root = Path("skills") / skill
        assert (root / "SKILL.md").exists()
        assert (root / "schema.json").exists()
        assert (root / "examples").is_dir()
        assert (root / "tests").is_dir()


def test_skill_contract_sections_are_present() -> None:
    for skill in SKILLS:
        text = (Path("skills") / skill / "SKILL.md").read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{skill} missing {section}"


def test_mvp_skill_contracts_name_executable_entrypoints() -> None:
    expected = {
        "preflight-check": ["preflight-check", "run_preflight_check"],
        "flight-log-analysis": ["analyze-log", "parse_flight_log", "detect_anomalies"],
        "fault-diagnosis": ["diagnose", "generate_fault_hypotheses"],
        "maintenance-advisor": ["diagnose", "generate_maintenance_recommendations"],
        "ops-report-generation": ["generate-report", "render_ops_report"],
    }
    for skill, needles in expected.items():
        text = (Path("skills") / skill / "SKILL.md").read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{skill} should mention {needle}"
