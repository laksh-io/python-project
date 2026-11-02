"""
Smoke test: checks the cleaning pipeline and opens every page of the Streamlit app.

    python tests/smoke_test.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

import analysis  # noqa: E402

PAGES = ["Project Overview", "Dataset", "Data Information", "Data Cleaning",
         "Data Visualisation", "Results & Conclusion"]


def test_pipeline():
    raw = analysis.load_raw()
    assert raw.shape == (2461, 8), raw.shape
    result = analysis.clean_data(raw)
    df = result.data
    assert df["timestamp"].notna().all() and (df["amount"] > 0).all()
    assert set(df["type"].astype(str)) <= set(analysis.VALID_TYPES)
    assert df["category"].notna().all() and df["subcategory"].notna().all() and df["note"].notna().all()
    assert len(analysis.clean_data(raw, drop_all_exact_duplicates=True).data) == len(df) - 9
    print(f"pipeline OK: {raw.shape} -> {df.shape}")


def test_app_pages():
    for page in PAGES:
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, f"{page}: {[e.value for e in at.exception]}"
        print(f"page OK: {page}")


if __name__ == "__main__":
    test_pipeline()
    test_app_pages()
    print("ALL TESTS PASSED")
