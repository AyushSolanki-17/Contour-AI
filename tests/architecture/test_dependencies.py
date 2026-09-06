"""Executable dependency rules for Contour's framework-independent core."""

from __future__ import annotations

import ast
from pathlib import Path

from contour.infrastructure.postgres.tables.catalog import (
    evidence,
    source_versions,
    sources,
    workspaces,
)
from contour.infrastructure.postgres.tables.execution import jobs, runs
from contour.infrastructure.postgres.tables.knowledge import (
    entities,
    entity_evidence,
    relationship_evidence,
    relationships,
)

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "contour"
_CAPABILITIES = frozenset(
    path.name
    for path in _PACKAGE_ROOT.iterdir()
    if (path / "domain").is_dir() and (path / "application").is_dir()
)
_CORE_EXTERNAL_FORBIDDEN = (
    "contour.api",
    "contour.composition",
    "contour.infrastructure",
    "contour.observability",
    "contour.settings",
    "fastapi",
    "psycopg",
    "pydantic",
    "sqlalchemy",
)


def _dependency_violation(relative: Path, imported: str) -> bool:
    """Evaluate capability boundaries without relying on obsolete global paths."""
    parts = relative.parts
    owner = parts[0]
    target = imported.split(".")
    capability = target[1] if len(target) > 1 and target[0] == "contour" else None
    domain = owner in _CAPABILITIES and len(parts) > 1 and parts[1] == "domain"
    application = owner in _CAPABILITIES and len(parts) > 1 and parts[1] == "application"
    if domain:
        if imported.startswith(
            _CORE_EXTERNAL_FORBIDDEN + ("contour.workflows", "contour.idempotency")
        ):
            return True
        return capability in _CAPABILITIES and (len(target) < 3 or target[2] != "domain")
    if application or owner == "workflows":
        if imported.startswith(_CORE_EXTERNAL_FORBIDDEN):
            return True
        if application and imported.startswith("contour.workflows"):
            return True
        if application and capability in _CAPABILITIES and capability != owner:
            return len(target) < 3 or target[2] != "domain"
        return False
    if owner == "api":
        return (
            imported.startswith(("contour.infrastructure", "contour.composition"))
            or (capability in _CAPABILITIES and ".application.ports" in imported)
            or imported.startswith("contour.idempotency.IdempotencyRepository")
        )
    if owner == "infrastructure":
        return imported.startswith(("contour.api", "contour.composition"))
    if owner == "observability" or relative.name == "settings.py":
        return capability in _CAPABILITIES or imported.startswith(
            ("contour.api", "contour.workflows", "contour.infrastructure", "contour.composition")
        )
    return False


_AMBIGUOUS_MODULE_NAMES = {
    "common",
    "core",
    "helpers",
    "models",
    "utils",
}


def test_layers_follow_the_capability_dependency_direction() -> None:
    """Check every capability and explicit cross-capability workflow."""
    violations = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(_PACKAGE_ROOT)
        for imported in _imported_names(path):
            if _dependency_violation(relative, imported):
                violations.append(f"{relative} imports {imported}")
    assert violations == []


def test_boundary_policy_rejects_realistic_bypasses() -> None:
    """Guard against the former vacuous checks of deleted global directories."""
    forbidden = (
        ("sources/domain/source.py", "contour.api.schemas.v1.sources"),
        ("sources/domain/source.py", "contour.jobs.JobPersistenceService"),
        ("sources/domain/source.py", "contour.sources.application.ports"),
        ("sources/application/registration.py", "sqlalchemy.select"),
        ("sources/application/registration.py", "contour.tenancy.application.collections"),
        ("sources/application/ports.py", "contour.workflows.source_admission"),
        ("api/routers/v1/sources.py", "contour.infrastructure.postgres.source_repository"),
        ("api/routers/v1/sources.py", "contour.sources.application.ports.SourceRepository"),
        ("infrastructure/postgres/source_repository.py", "contour.api.schemas.v1.sources"),
    )
    allowed = (
        ("sources/application/ports.py", "contour.workspaces.domain.workspace"),
        ("sources/domain/source.py", "contour.tenancy.domain.tenant"),
        ("workflows/source_admission.py", "contour.knowledge.application.ports"),
        ("composition/http.py", "contour.infrastructure.postgres.source_transaction"),
        ("api/routers/v1/sources.py", "contour.sources.application.registration"),
    )
    assert all(_dependency_violation(Path(path), name) for path, name in forbidden)
    assert not any(_dependency_violation(Path(path), name) for path, name in allowed)


def test_production_modules_do_not_use_ambiguous_catchall_names() -> None:
    """New behavior remains discoverable by capability or concrete concept."""
    ambiguous_paths = []
    for path in sorted(_PACKAGE_ROOT.rglob("*")):
        is_ambiguous_package = path.is_dir() and path.name in _AMBIGUOUS_MODULE_NAMES
        is_ambiguous_module = (
            path.is_file() and path.suffix == ".py" and (path.stem in _AMBIGUOUS_MODULE_NAMES)
        )
        if is_ambiguous_package or is_ambiguous_module:
            ambiguous_paths.append(str(path.relative_to(_PACKAGE_ROOT)))

    assert ambiguous_paths == []


def test_catalog_collection_use_cases_remain_capability_named() -> None:
    """Tenant, workspace, and source collections do not regress to one mixed service."""
    expected_paths = {
        "tenancy/application/collections.py",
        "workspaces/application/collections.py",
        "sources/application/registration.py",
    }

    assert all((_PACKAGE_ROOT / path).is_file() for path in expected_paths)
    assert not (_PACKAGE_ROOT / "sources/application/catalog_collections.py").exists()


def test_record_transactions_remain_capability_scoped() -> None:
    """Knowledge and job units of work never regress to one mixed adapter."""
    expected_paths = {
        "infrastructure/postgres/job_transaction.py",
        "infrastructure/postgres/knowledge_transaction.py",
    }

    assert all((_PACKAGE_ROOT / path).is_file() for path in expected_paths)
    assert not (_PACKAGE_ROOT / "infrastructure/postgres/records_transaction.py").exists()


def test_superseded_global_layers_are_not_reintroduced() -> None:
    """Business capabilities must not regress to global domain/service/repository layers."""
    superseded = ("domain", "repositories", "services")
    assert [name for name in superseded if (_PACKAGE_ROOT / name).exists()] == []


def test_settings_remain_independent_of_runtime_frameworks_and_core_policy() -> None:
    """Process configuration stays reusable by migrations and composition roots."""
    forbidden_prefixes = (
        "contour.api",
        "contour.composition",
        "contour.domain",
        "contour.infrastructure",
        "contour.observability",
        "contour.repositories",
        "contour.services",
        "fastapi",
        "psycopg",
        "pydantic",
        "sqlalchemy",
    )
    imported_names = _imported_names(_PACKAGE_ROOT / "settings.py")

    assert [name for name in imported_names if name.startswith(forbidden_prefixes)] == []


def test_infrastructure_initializers_do_not_hide_implementation_imports() -> None:
    """Composition code names the concrete infrastructure module it constructs."""
    violations: list[str] = []
    for path in sorted((_PACKAGE_ROOT / "infrastructure").rglob("__init__.py")):
        for imported_name in _imported_names(path):
            if imported_name.startswith("contour.infrastructure"):
                violations.append(f"{path.relative_to(_PACKAGE_ROOT)} imports {imported_name}")

    assert violations == []


def test_only_infrastructure_and_composition_import_concrete_adapters() -> None:
    """Core and delivery code cannot bypass ports or executable composition."""
    violations: list[str] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(_PACKAGE_ROOT)
        if relative.parts[0] in {"composition", "infrastructure"}:
            continue
        for imported_name in _imported_names(path):
            if imported_name.startswith("contour.infrastructure"):
                violations.append(f"{relative} imports {imported_name}")

    assert violations == []


def test_capability_application_code_remains_source_neutral() -> None:
    """PEP policy stays in source infrastructure, not reusable core policy."""
    violations: list[str] = []
    for capability in ("tenancy", "workspaces", "sources", "knowledge", "jobs"):
        for layer in ("application", "domain"):
            for path in sorted((_PACKAGE_ROOT / capability / layer).rglob("*.py")):
                if "pep" in path.stem.lower():
                    violations.append(str(path.relative_to(_PACKAGE_ROOT)))
                source = path.read_text(encoding="utf-8")
                if "Pep" in source or "pep_" in source:
                    violations.append(str(path.relative_to(_PACKAGE_ROOT)))

    assert violations == []


def test_runtime_code_does_not_mutate_database_schema() -> None:
    """Alembic remains an explicit release tool rather than a runtime dependency."""
    violations: list[str] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(name.startswith("alembic") for name in _imported_names(path)):
            violations.append(f"{path.relative_to(_PACKAGE_ROOT)} imports alembic")
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"create_all", "drop_all"}
            ):
                violations.append(
                    f"{path.relative_to(_PACKAGE_ROOT)}:{node.lineno} calls {node.func.attr}"
                )

    assert violations == []


def test_durable_records_declare_nonoptional_tenant_workspace_ownership() -> None:
    """Every non-tenant durable record retains its owner tuple in Core metadata."""
    tenant_owned_tables = (
        workspaces,
        sources,
        source_versions,
        evidence,
        entities,
        entity_evidence,
        relationships,
        relationship_evidence,
        jobs,
        runs,
    )
    for table in tenant_owned_tables:
        assert not table.c.tenant_namespace.nullable
        assert not table.c.tenant_value.nullable

    workspace_owned_tables = (
        sources,
        source_versions,
        evidence,
        entities,
        entity_evidence,
        relationships,
        relationship_evidence,
        jobs,
        runs,
    )
    for table in workspace_owned_tables:
        assert not table.c.workspace_namespace.nullable
        assert not table.c.workspace_value.nullable


def test_source_registration_uniqueness_is_a_database_invariant() -> None:
    """Concurrent source registration cannot bypass an application pre-check."""
    assert "uq_sources_registration" in {constraint.name for constraint in sources.constraints}


def _imported_names(path: Path) -> tuple[str, ...]:
    """Resolve imports including from-package and relative-module bypasses."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    package = ("contour", *path.relative_to(_PACKAGE_ROOT).parent.parts)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = ".".join(package[: len(package) - node.level + 1]) if node.level else ""
            module = ".".join(part for part in (prefix, node.module) if part)
            names.extend(f"{module}.{alias.name}" for alias in node.names)
    return tuple(names)
