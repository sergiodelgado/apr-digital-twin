import pytest

from apr_twin.twin import taxonomy


def test_all_recommendation_texts_have_codes():
    missing = [
        text
        for text in taxonomy.ENGINE_RECOMMENDATION_CATALOG
        if text not in taxonomy.RECOMMENDATION_TEXT_TO_CODE
    ]
    assert not missing, f"Missing mapping for recommendation texts: {missing}"
