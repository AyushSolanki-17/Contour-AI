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
from contour.infrastructure.postgres.tables.knowledge import (
    entities,
    entity_evidence,
    jobs,
    relationship_evidence,
    relationships,
    runs,
)

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "contour"
_FORBIDDEN_IMPORTS_BY_LAYER = {
    "domain": (
        "contour.api",
        "contour.bootstrap",
        "contour.infrastructure",
        "contour.observability",
        "contour.repositories",
        "contour.services",
        "contour.settings",
        "fastapi",
        "psycopg",
        "pydantic",
        "sqlalchemy",
    ),
    "repositories": (
        "contour.api",
        "contour.bootstrap",
        "contour.infrastructure",
        "contour.observability",
        "contour.services",
        "contour.settings",
        "fastapi",
        "psycopg",
        "pydantic",
        "sqlalchemy",
    ),
    "services": (
        "contour.api",
        "contour.bootstrap",
        "contour.infrastructure",
        "contour.observability",
        "contour.settings",
        "fastapi",
        "psycopg",
        "pydantic",
        "sqlalchemy",
    ),
    "infrastructure": (
        "contour.api",
        "contour.bootstrap",
    ),
    "api": (
        "contour.bootstrap",
        "contour.infrastructure",
        "contour.repositories",
    ),
    "observability": (
        "contour.api",
        "contour.bootstrap",
        "contour.domain",
        "contour.infrastructure",
        "contour.repositories",
        "contour.services",
    ),
}

_AMBIGUOUS_MODULE_NAMES = {
    "common",
    "core",
    "helpers",
    "models",
    "utils",
}


def test_layers_follow_the_conventional_dependency_direction() -> None:
    """Domain, repository ports, and services stay reusable outside delivery and storage."""
    violations: list[str] = []
    for layer, forbidden_prefixes in _FORBIDDEN_IMPORTS_BY_LAYER.items():
        for path in sorted((_PACKAGE_ROOT / layer).rglob("*.py")):
            for imported_name in _imported_names(path):
                if imported_name.startswith(forbidden_prefixes):
                    violations.append(f"{path.relative_to(_PACKAGE_ROOT)} imports {imported_name}")

    assert violations == []


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


def test_settings_remain_independent_of_runtime_frameworks_and_core_policy() -> None:
    """Process configuration stays reusable by migrations and composition roots."""
    forbidden_prefixes = (
        "contour.api",
        "contour.bootstrap",
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


def test_only_infrastructure_and_bootstrap_import_concrete_adapters() -> None:
    """Core and delivery code cannot bypass ports or executable composition."""
    violations: list[str] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(_PACKAGE_ROOT)
        if relative.parts[0] in {"bootstrap", "infrastructure"}:
            continue
        for imported_name in _imported_names(path):
            if imported_name.startswith("contour.infrastructure"):
                violations.append(f"{relative} imports {imported_name}")

    assert violations == []


def test_application_services_remain_source_neutral() -> None:
    """PEP policy stays in source infrastructure, not reusable core policy."""
    violations: list[str] = []
    for layer in ("domain", "services"):
        for path in sorted((_PACKAGE_ROOT / layer).rglob("*.py")):
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
    """Return absolute names referenced by import statements in one module."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.append(node.module)
    return tuple(names)
