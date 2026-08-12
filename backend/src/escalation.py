import os
import uuid
import logging
import requests

logger = logging.getLogger("escalation")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_ESCALATION_WEBHOOK_URL")


def create_escalation(
    caller_name: str,
    what_happened: str,
    already_checked: str,
    urgency: str,
    language: str,
    follow_up_method: str,
):
    """Build a short safe summary, send it to Discord, and return a reference ID."""
    reference_id = "ESC-" + uuid.uuid4().hex[:8].upper()

    message = (
        f"**New Escalation — {reference_id}**\n"
        f"**Who:** {caller_name}\n"
        f"**What happened:** {what_happened}\n"
        f"**Already checked:** {already_checked}\n"
        f"**Urgency:** {urgency}\n"
        f"**Language:** {language}\n"
        f"**Preferred follow-up:** {follow_up_method}\n"
    )

    if not DISCORD_WEBHOOK_URL:
        logger.error("DISCORD_ESCALATION_WEBHOOK_URL is not set - cannot send escalation")
        return reference_id, False

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=5)
        response.raise_for_status()
        logger.info(f"Escalation {reference_id} sent to Discord successfully")
        return reference_id, True
    except Exception as e:
        logger.error(f"Failed to send escalation {reference_id} to Discord: {e}")
        return reference_id, False
