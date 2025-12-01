# MarkerTest_Final
import json
import logging
import os
from datetime import datetime
from uuid import uuid4

from azure.storage.blob import BlobServiceClient
import azure.functions as func
from bs4 import BeautifulSoup



# One FunctionApp instance for all functions
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="email_intake", methods=["POST"])
def email_intake(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Email intake function started")

    # Try to read JSON body from Logic App
    try:
        payload = req.get_json()
    except ValueError:
        logging.exception("Request body is not valid JSON")
        return func.HttpResponse(
            "Invalid JSON payload",
            status_code=400
        )

    # Extract some fields for logging and file naming
    internet_message_id = payload.get("internetMessageId")
    subject = payload.get("subject", "")
    received = payload.get("receivedDateTime")

    logging.info(f"Email received. internetMessageId={internet_message_id}, subject={subject}")

    # Read settings from environment
    connection_str = os.environ.get("BLOB_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER", "email-landing")

    if not connection_str:
        logging.error("BLOB_CONNECTION_STRING is not set")
        return func.HttpResponse(
            "Storage connection not configured",
            status_code=500
        )

    # Build blob path
    blob_path = build_blob_path(internet_message_id, received)

    # Create blob client and write the payload as pretty JSON
    blob_service = BlobServiceClient.from_connection_string(connection_str)
    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=blob_path
    )

    raw_json = json.dumps(payload, ensure_ascii=False, indent=2)
    blob_client.upload_blob(raw_json, overwrite=True)

    logging.info(f"Email payload written to blob path {blob_path}")

    # Build a compact summary for analytics
    body_html = payload.get("body")
    body_text = html_to_text(body_html)

    summary = {
        "id": payload.get("id"),
        "internetMessageId": internet_message_id,
        "subject": payload.get("subject"),
        "from": payload.get("from"),
        "receivedDateTime": received,
        "hasAttachments": payload.get("hasAttachments"),
        "bodyText": body_text,
        "rawBlobPath": blob_path
    }

    summary_path = build_summary_blob_path(internet_message_id, received)

    summary_client = blob_service.get_blob_client(
        container=container_name,
        blob=summary_path
    )
    summary_client.upload_blob(json.dumps(summary, ensure_ascii=False), overwrite=True)

    logging.info(f"Email summary written to blob path {summary_path}")


    return func.HttpResponse(
        json.dumps(
            {
                "status": "ok",
                "rawBlobPath": blob_path,
                "summaryBlobPath": summary_path
            }
        ),
        mimetype="application/json",
        status_code=200
    )



def build_blob_path(internet_message_id: str | None, received: str | None) -> str:
    """Builds a path like:
       landing/email/raw/2025/11/26/email_<cleanedId>.json
    """
    # Parse received datetime, fall back to now
    try:
        if received:
            dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
        else:
            dt = datetime.utcnow()
    except Exception:
        dt = datetime.utcnow()

    # Clean internetMessageId so it is safe for file name
    if internet_message_id:
        safe_id = (
            internet_message_id
            .replace("<", "")
            .replace(">", "")
            .replace("@", "_")
            .replace(":", "_")
            .replace("/", "_")
        )
    else:
        safe_id = dt.strftime("%Y%m%dT%H%M%S")

    unique_suffix = uuid4().hex[:8]

    return (
        f"landing/email/raw/"
        f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/"
        f"email_{safe_id}_{unique_suffix}.json"
    )

def html_to_text(html: str | None) -> str:
    """Convert HTML to plain text, trimmed to a reasonable length."""
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n")
        # Optional: collapse extra whitespace and trim
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return text[:4000]  # keep first 4000 chars to avoid crazy big summaries
    except Exception:
        # If anything goes wrong, just return the raw HTML snippet
        return html[:4000]
    
def build_summary_blob_path(internet_message_id: str | None, received: str | None) -> str:
    try:
        if received:
            dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
        else:
            dt = datetime.utcnow()
    except Exception:
        dt = datetime.utcnow()

    if internet_message_id:
        safe_id = (
            internet_message_id
            .replace("<", "")
            .replace(">", "")
            .replace("@", "_")
            .replace(":", "_")
            .replace("/", "_")
        )
    else:
        safe_id = dt.strftime("%Y%m%dT%H%M%S")

    unique_suffix = uuid4().hex[:8]

    return (
        f"processed/email/summary/"
        f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/"
        f"email_{safe_id}_{unique_suffix}.json"
    )


