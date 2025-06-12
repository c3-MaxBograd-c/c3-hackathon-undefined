import os
import requests

def get_jira_ticket_info(ticket_id):
    """
    Fetch Jira ticket info using the Jira REST API.
    Requires JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN env vars.
    """
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    if not all([base_url, email, api_token]):
        raise RuntimeError("JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set in environment.")

    url = f"{base_url}/rest/api/2/issue/{ticket_id}"
    auth = (email, api_token)
    headers = {"Accept": "application/json"}
    resp = requests.get(url, auth=auth, headers=headers)
    resp.raise_for_status()
    return resp.json()
