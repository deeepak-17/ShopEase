from pathlib import Path


def test_dashboard_renders_names_as_text_not_html():
    dashboard = Path(__file__).parents[2] / "web" / "dashboard" / "index.html"
    content = dashboard.read_text(encoding="utf-8")

    assert "textContent" in content
    assert "<span>${customer.name}</span>" not in content
