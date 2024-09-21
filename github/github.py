import requests
from typing import Any

# Check if the user is valid
def check_usr_valid(username: str) -> bool | None:
    api_url = f"https://api.github.com/users/{username}"
    response = requests.get(api_url)
    if (response.status_code == 200):
        return True
    elif (response.status_code == 404):
        return False
    return None

# Get the user's repos
def get_repos(username: str, max_repos: int) -> list[dict[str, Any]] | None:
    api_url = f"https://api.github.com/users/{username}"
    repsonse = requests.get(f"{api_url}/repos?per_page={max_repos}")
    if (repsonse.status_code == 200):
        return repsonse.json()
    return None

# Check if repo is a fork
def check_fork(repo: dict[str, Any]) -> bool:
    if (repo.get('fork') == True):
        return True
    return False

