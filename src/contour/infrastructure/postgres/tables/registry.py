"""Assembly of PostgreSQL table capabilities for migration comparison."""

from __future__ import annotations

import sqlalchemy as sa

from contour.infrastructure.postgres.tables import catalog as _catalog_tables
from contour.infrastructure.postgres.tables.metadata import metadata


def registered_metadata() -> sa.MetaData:
    """Return metadata after importing every implemented table capability."""
    if _catalog_tables.workspaces.metadata is not metadata:
        raise RuntimeError("PostgreSQL table capabilities must share one metadata registry")
    return metadata
