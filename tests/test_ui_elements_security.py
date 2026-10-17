"""Security regression tests for reusable frontend UI components."""

from frontend.components import ui_elements


def test_metric_card_escapes_dynamic_html(monkeypatch):
    rendered = []
    monkeypatch.setattr(ui_elements.st, "markdown", lambda body, **kwargs: rendered.append((body, kwargs)))

    ui_elements.render_metric_card(
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "Pump & motor <unsafe>",
    )

    html, kwargs = rendered[0]
    assert "<script>" not in html
    assert "<img" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert "Pump &amp; motor &lt;unsafe&gt;" in html
    assert kwargs["unsafe_allow_html"] is True


def test_metric_card_rejects_unsafe_css_color(monkeypatch):
    rendered = []
    monkeypatch.setattr(ui_elements.st, "markdown", lambda body, **kwargs: rendered.append(body))

    ui_elements.render_metric_card("Fleet", 12, "Assets monitored", "#fff; background:url(javascript:alert(1))")

    assert "border-top: 3px solid #334155;" in rendered[0]
    assert "javascript:" not in rendered[0]


def test_metric_card_accepts_valid_hex_color(monkeypatch):
    rendered = []
    monkeypatch.setattr(ui_elements.st, "markdown", lambda body, **kwargs: rendered.append(body))

    ui_elements.render_metric_card("Fleet", 12, "Assets monitored", "#0A84FF")

    assert "border-top: 3px solid #0A84FF;" in rendered[0]
