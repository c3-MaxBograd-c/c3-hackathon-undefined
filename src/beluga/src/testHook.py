import requests
import json
from beluga.src.git_utils import get_repo
import subprocess

def makeRestCall():
    url = ''
    authToken = ''
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "c3auth " + authToken,
    }
    gitObj = get_repo()
    branchName = gitObj.active_branch.name
    print(f"Branch Name: {branchName}")
    body = {
        "branchName": branchName
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        print(response.json())
    except Exception as error:
        raise ValueError(f"Error sending request: {str(error)}") from error
        
if __name__ == "__main__":
    makeRestCall()