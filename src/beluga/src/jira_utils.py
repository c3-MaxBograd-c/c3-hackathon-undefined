import os
import requests

def get_jira_ticket_info(ticket_id):
    """
    Fetch Jira ticket info using the Jira REST API.
    Requires JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN env vars.
    """
    if not all([base_url, email, api_token]):
        raise RuntimeError("JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set in environment.")

    url = f"{base_url}/rest/api/2/issue/{ticket_id}"
    auth = (email, api_token)
    headers = {"Accept": "application/json"}
    resp = requests.get(url, auth=auth, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    fields = data.get("fields", {})
    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "")
    assignee = fields.get("assignee", {}).get("displayName", "")
    return f"{ticket_id}: {summary} | Status: {status} | Assignee: {assignee}"
