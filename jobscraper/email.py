from __future__ import annotations
from email.message import EmailMessage
from pathlib import Path
import smtplib


def _md_to_html(md: str) -> str:
    html_lines = []
    for line in md.splitlines():
        if line.startswith("# "):
            html_lines.append(f"<h2>{line[2:]}</h2>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif not line.strip():
            html_lines.append("")
        else:
            html_lines.append(f"<p>{line}</p>")
    body = "\n".join(html_lines).replace("<li>", "<ul><li>", 1)
    if "<li>" in body and not body.rstrip().endswith("</ul>"):
        body += "</ul>"
    return f"<html><body>{body}</body></html>"


def send_digest(*, host: str, port: int, user: str, password: str,
                to: str, subject: str, markdown_body: str,
                xlsx_path: Path | None = None) -> None:
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(markdown_body)
    msg.add_alternative(_md_to_html(markdown_body), subtype="html")
    if xlsx_path:
        with open(xlsx_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=Path(xlsx_path).name,
            )
    with smtplib.SMTP(host, port) as srv:
        srv.starttls()
        srv.login(user, password)
        srv.send_message(msg)
