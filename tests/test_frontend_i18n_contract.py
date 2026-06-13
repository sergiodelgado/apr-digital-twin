from __future__ import annotations

import re
from pathlib import Path

from apr_twin.twin.taxonomy import ENGINE_RECOMMENDATION_CATALOG


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
I18N_FILE = REPOSITORY_ROOT / "frontend" / "features" / "twin-state" / "lib" / "i18n.ts"


def test_frontend_translates_every_static_engine_recommendation() -> None:
    source = I18N_FILE.read_text(encoding="utf-8")
    recommendation_block = source.split(
        "export const RECOMMENDATION_ES: Record<string, string> = {",
        maxsplit=1,
    )[1].split("\n};", maxsplit=1)[0]
    translated_recommendations = set(
        re.findall(r"^  '([^']+)':", recommendation_block, flags=re.MULTILINE)
    )

    missing = set(ENGINE_RECOMMENDATION_CATALOG) - translated_recommendations

    assert not missing, f"Missing frontend recommendation translations: {sorted(missing)}"
