"""PDF export sits next to the HTML report when the pdf extra is installed."""

from contractguard.html import write_pdf_report


def test_pdf_export_returns_none_without_weasyprint(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_weasyprint(name, *args, **kwargs):
        if name == "weasyprint":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_weasyprint)
    assert write_pdf_report(None, "en") is None
