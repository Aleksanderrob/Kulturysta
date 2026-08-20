from analysis.comparisons import compare_metric_series


def test_changes_are_neutral_and_percentage_safe():
    records = [{"session_id": "A", "metrics": {"x": 0}}, {"session_id": "B", "metrics": {"x": 2}}]
    rows = compare_metric_series(records, ["x"])
    assert rows[1]["absolute_change"] == 2
    assert rows[1]["percent_change"] is None
    assert rows[1]["direction"] == "wzrost"
