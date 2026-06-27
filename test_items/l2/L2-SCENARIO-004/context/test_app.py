from app import get_report

def test_get_report_all():
    result = get_report()
    assert "total" in result
    assert "by_product" in result
    assert len(result["top_orders"]) == 5

def test_get_report_filtered():
    result = get_report(month="2024-01")
    assert result["total"] > 0
