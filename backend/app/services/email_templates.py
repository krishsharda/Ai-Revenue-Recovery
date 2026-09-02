"""Professional HTML + plain-text recovery email templates."""
from __future__ import annotations

import html as _html
from typing import Optional


def _esc(s: str) -> str:
    return _html.escape(s or "")


def render_html(*, customer_name: str, amount_display: str, body: str,
                payment_link: Optional[str], brand: str = "AI Revenue Recovery") -> str:
    name = _esc(customer_name or "there")
    body_html = _esc(body).replace("\n", "<br>")
    cta = ""
    if payment_link:
        cta = f"""
        <tr><td style="padding:8px 0 4px;">
          <a href="{_esc(payment_link)}" target="_blank"
             style="display:inline-block;background:#0f172a;color:#ffffff;text-decoration:none;
                    font-weight:600;font-size:15px;padding:13px 26px;border-radius:10px;">
            Complete Payment
          </a>
        </td></tr>
        <tr><td style="padding:6px 0 0;font-size:12px;color:#64748b;">
          Or paste this secure link into your browser:<br>
          <span style="color:#334155;word-break:break-all;">{_esc(payment_link)}</span>
        </td></tr>"""
    return f"""<!doctype html>
<html><body style="margin:0;background:#f1f5f9;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:28px 12px;">
    <tr><td align="center">
      <table role="presentation" width="520" cellpadding="0" cellspacing="0"
             style="max-width:520px;background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;">
        <tr><td style="padding:22px 28px;border-bottom:1px solid #eef2f7;">
          <span style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#64748b;font-weight:600;">{_esc(brand)}</span>
          <div style="font-size:19px;font-weight:700;margin-top:4px;">Payment Recovery</div>
        </td></tr>
        <tr><td style="padding:26px 28px;">
          <p style="margin:0 0 14px;font-size:15px;">Hi {name},</p>
          <p style="margin:0 0 16px;font-size:15px;line-height:1.55;color:#334155;">
            Your payment of <strong>{_esc(amount_display)}</strong> could not be completed.
          </p>
          <p style="margin:0 0 18px;font-size:15px;line-height:1.55;color:#334155;">{body_html}</p>
          <table role="presentation" cellpadding="0" cellspacing="0">{cta}</table>
          <p style="margin:20px 0 0;font-size:13px;color:#94a3b8;">
            If you have already completed the payment, no further action is required.
          </p>
        </td></tr>
        <tr><td style="padding:16px 28px;border-top:1px solid #eef2f7;font-size:12px;color:#94a3b8;">
          Sent by {_esc(brand)} · This is a payment recovery notification.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def render_text(*, customer_name: str, amount_display: str, body: str,
                payment_link: Optional[str], brand: str = "AI Revenue Recovery") -> str:
    lines = [
        f"{brand} — Payment Recovery",
        "",
        f"Hi {customer_name or 'there'},",
        "",
        f"Your payment of {amount_display} could not be completed.",
        "",
        body,
    ]
    if payment_link:
        lines += ["", "Complete your payment securely:", payment_link]
    lines += ["", "If you have already completed the payment, no further action is required.",
              "", "Thank you,", brand]
    return "\n".join(lines)
