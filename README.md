# Email Intake and Processing Workflow - Azure Functions + Logic Apps

This project implements an end-to-end email intake pipeline using Azure Logic Apps, Azure Functions, and Azure Blob Storage.  
The goal is to simulate a real world intake system where incoming emails are captured, normalized, and stored in a data lake style layout for downstream processing and analytics.

---

## High Level Architecture

1. **User sends an email** to a monitored mailbox.
2. **Azure Logic App** triggers on new emails and extracts the key fields.
3. Logic App calls an **HTTP triggered Azure Function** (`email_intake`) with a clean JSON payload.
4. The **Azure Function** writes the full email payload to **Azure Blob Storage** using a partitioned path:
   - `landing/email/raw/{yyyy}/{MM}/{dd}/email_<internetMessageId>_<uuid>.json`
5. A **GitHub Actions pipeline** deploys the Function App to Azure on every push to `main` using Azure Functions Core Tools.

This pattern is similar to how support, ticketing, and operations teams automate email intake and feed downstream data platforms.

---

## Technologies Used

- **Azure Logic Apps (Consumption)**  
  - Trigger: "When a new email arrives (V3)"  
  - Action: HTTP POST to the Function App endpoint

- **Azure Functions - Python**  
  - Runtime: Python (v4 Functions)  
  - Trigger: HTTP route `email_intake`  
  - Writes JSON payloads into Azure Blob Storage

- **Azure Blob Storage**  
  - Container for raw email payloads  
  - Date partitioned folder structure for easy ingestion into data lakes

- **GitHub Actions CI CD**  
  - OIDC based login using `azure/login@v2`  
  - Builds and deploys using `func azure functionapp publish`

- **Azure Functions Core Tools**  
  - Local development and debugging  
  - Same `func publish` command used locally and in CI

---


## Repository Structure

```text
email-intake-functions/
  function_app.py         # main function app (email_intake)
  host.json               # Azure Functions host configuration
  requirements.txt        # Python dependencies
  local.settings.json     # local development settings (not committed)
  .funcignore             # files excluded from deployment
  .gitignore
  docs/
    logic-app-email-intake.png    # Logic app screenshot
  .github/
    workflows/
      main_fa-email-intake-dev.yml   # CI CD pipeline
  README.md               # this file

```

## Logic app Email Intake
![Logic App workflow](docs/logic-app-email-intake.png)



