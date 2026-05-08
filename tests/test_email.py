from unittest.mock import MagicMock, patch
from pathlib import Path
from jobscraper.email import send_digest


def test_send_digest_attaches_xlsx(tmp_path):
    xlsx = tmp_path / "out.xlsx"
    xlsx.write_bytes(b"PK\x03\x04fake")
    with patch("jobscraper.email.smtplib.SMTP") as smtp_cls:
        srv = MagicMock(); smtp_cls.return_value.__enter__.return_value = srv
        send_digest(
            host="smtp.example.com", port=587, user="u@example.com", password="p",
            to="dest@example.com", subject="JobScraper 2026-05-07",
            markdown_body="# hi\n- a", xlsx_path=xlsx,
        )
        srv.starttls.assert_called_once()
        srv.login.assert_called_once_with("u@example.com", "p")
        srv.send_message.assert_called_once()
        msg = srv.send_message.call_args.args[0]
        assert msg["Subject"] == "JobScraper 2026-05-07"
        assert msg["From"] == "u@example.com"
        parts = list(msg.iter_attachments())
        assert any(p.get_content_disposition() == "attachment" for p in parts)
