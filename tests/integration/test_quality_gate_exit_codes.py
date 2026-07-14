from __future__ import annotations

import pytest
from typer.testing import CliRunner

from apps.cli import main as cli


runner = CliRunner()


@pytest.mark.parametrize(
    ("command", "function_name", "arguments"),
    [
        (
            "validate-platform-readiness",
            "_run_validate_platform_readiness",
            ["--workspace", "w.json", "--bundle", "b.json", "--checklist", "c.json", "--out", "o.json"],
        ),
        ("run-evals", "_run_evals", ["--case", "case.json", "--out", "out"]),
        ("validate-datasets", "_run_validate_datasets", ["--registry", "r.json", "--out", "o.json"]),
        ("validate-adapters", "_run_validate_adapters", ["--registry", "r.json", "--out", "o.json"]),
        ("validate-approvals", "_run_validate_approvals", ["--packet", "p.json", "--out", "o.json"]),
        ("validate-handoff-package", "_run_validate_handoff_package", ["--package", "p.json", "--out", "o.json"]),
    ],
)
def test_review_required_quality_gates_exit_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    function_name: str,
    arguments: list[str],
) -> None:
    payload = {
        "status": "REVIEW_REQUIRED",
        "score": 0.0,
        "counts": {
            "adapters": 1,
            "approvals": 1,
            "artifacts": 1,
            "cases": 1,
            "findings": 1,
        },
    }
    monkeypatch.setattr(cli, function_name, lambda *_args, **_kwargs: payload)

    result = runner.invoke(cli.app, [command, *arguments])

    assert result.exit_code == 1
    assert "requires review" in result.output or "REVIEW_REQUIRED" in result.output
