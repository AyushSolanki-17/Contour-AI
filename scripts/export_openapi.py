"""Generate or verify the checked-in frontend-facing OpenAPI contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from contour.api.app import create_app
from contour.infrastructure.authentication.static_credentials import StaticCredentialVerifier
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.catalog_collections import CatalogCollectionService
from contour.services.health_service import HealthService

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "openapi" / "contour.openapi.json"


class ContractReadinessProbe:
    """Provide a side-effect-free dependency for schema generation."""

    def check(self) -> None:
        """Satisfy the health-service contract without touching a database."""


def render_contract() -> str:
    """Render the current FastAPI contract as deterministic JSON.

    Returns:
        Canonical OpenAPI JSON with a trailing newline.
    """
    app = create_app(
        health_service=HealthService(ContractReadinessProbe()),
        catalog_service=CatalogCollectionService(
            cast(CatalogTransactionManager, object()), frozenset({"pep"})
        ),
        credential_verifier=StaticCredentialVerifier({}),
    )
    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for generation or drift checking.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="OpenAPI artifact to write or check.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail instead of writing when the artifact differs.",
    )
    return parser.parse_args()


def main() -> int:
    """Generate the artifact or report contract drift.

    Returns:
        Zero when generation or verification succeeds; otherwise one.
    """
    arguments = parse_arguments()
    expected = render_contract()

    if arguments.check:
        if not arguments.output.is_file():
            print(f"OpenAPI artifact is missing: {arguments.output}")
            return 1
        if arguments.output.read_text(encoding="utf-8") != expected:
            print(f"OpenAPI artifact is stale: {arguments.output}")
            print("Run `make openapi` after reviewing the contract change.")
            return 1
        print(f"OpenAPI artifact is current: {arguments.output}")
        return 0

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(expected, encoding="utf-8")
    print(f"Wrote OpenAPI artifact: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
