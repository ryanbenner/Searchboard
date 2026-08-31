from unittest.mock import MagicMock, patch
from pathlib import Path
from searchboard.email import _md_to_html, send_digest


def test_md_to_html_converts_links_so_url_has_no_trailing_paren():
    md = "- **[Software Engineer](https://jobs.ashbyhq.com/notion/a6311f97)** at *Notion*"
    html = _md_to_html(md)
    assert '<a href="https://jobs.ashbyhq.com/notion/a6311f97">Software Engineer</a>' in html
    assert "](https://" not in html
    assert "https://jobs.ashbyhq.com/notion/a6311f97)" not in html


def test_md_to_html_converts_bold():
    html = _md_to_html("- **hello** world")
    assert "<strong>hello</strong>" in html
    assert "**" not in html


def test_md_to_html_converts_italic():
    html = _md_to_html("- at *Notion* today")
    assert "<em>Notion</em>" in html


def test_send_digest_attaches_xlsx(tmp_path):
    xlsx = tmp_path / "out.xlsx"
    xlsx.write_bytes(b"PK\x03\x04fake")
    with patch("searchboard.email.smtplib.SMTP") as smtp_cls:
        srv = MagicMock(); smtp_cls.return_value.__enter__.return_value = srv
        send_digest(
            host="smtp.example.com", port=587, user="u@example.com", password="p",
            to="dest@example.com", subject="Searchboard 2026-05-07",
            markdown_body="# hi\n- a", xlsx_path=xlsx,
        )
        srv.starttls.assert_called_once()
        srv.login.assert_called_once_with("u@example.com", "p")
        srv.send_message.assert_called_once()
        msg = srv.send_message.call_args.args[0]
        assert msg["Subject"] == "Searchboard 2026-05-07"
        assert msg["From"] == "u@example.com"
        parts = list(msg.iter_attachments())
        assert any(p.get_content_disposition() == "attachment" for p in parts)
