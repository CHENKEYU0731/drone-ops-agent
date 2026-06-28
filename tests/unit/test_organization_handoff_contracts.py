from pathlib import Path

from packages.drone_schemas import OrganizationHandoffArtifact, OrganizationHandoffPackage, load_model


def test_organization_handoff_package_contract_collects_local_artifacts() -> None:
    artifact = OrganizationHandoffArtifact(
        artifact_id="workspace-project",
        artifact_type="workspace_project",
        path="data/sample_platform/workspace_project.json",
        required=True,
        description="Local workspace governance file.",
    )
    package = OrganizationHandoffPackage(
        package_id="org-handoff-demo",
        version="1.8.0",
        title="Offline organization handoff package",
        workspace_project_id="workspace-local-demo",
        artifact_refs=[artifact],
        reviewer_roles=["safety_reviewer", "maintenance_lead"],
        safety_boundary={"offline_only": True, "advisory_only": True},
    )

    assert package.artifact_count == 1
    assert package.human_review_required is True
    assert package.artifact_refs[0].human_review_required is True
    assert package.reviewer_roles == ["maintenance_lead", "safety_reviewer"]


def test_sample_organization_handoff_package_loads_with_stable_order() -> None:
    package = load_model(Path("data/sample_handoff/organization_handoff_package.json"), OrganizationHandoffPackage)

    assert package.package_id == "org-handoff-demo"
    assert package.version == "1.8.0"
    assert package.workspace_project_id == "workspace-local-demo"
    assert package.artifact_count >= 6
    assert [artifact.artifact_id for artifact in package.artifact_refs] == sorted(
        artifact.artifact_id for artifact in package.artifact_refs
    )
    assert package.safety_boundary["offline_only"] is True
    assert package.safety_boundary["advisory_only"] is True
