from mcp.server.fastmcp import FastMCP
import requests
import os

SONARQUBE_URL = os.environ.get("SONARQUBE_URL", "http://localhost:9000")
SONARQUBE_TOKEN = os.environ.get("SONARQUBE_TOKEN", "")

mcp = FastMCP()


def call_sonarqube_api(endpoint: str, method: str = "GET", params: dict = None, json: dict = None):
    url = f"{SONARQUBE_URL}/api/{endpoint}"
    auth = (SONARQUBE_TOKEN, "")
    response = requests.request(method=method, url=url, auth=auth, params=params, json=json)
    response.raise_for_status()
    return response.json()


@mcp.tool(description="Generic SonarQube API call tool")
def sonar_api_call(endpoint: str, method: str = "GET", query: str = "") -> dict:
    """
    Makes a generic call to any SonarQube API endpoint.
    - endpoint: path like 'projects/search'
    - method: GET, POST, etc.
    - query: query string like 'q=project-name&pageSize=10'
    """
    query_params = dict(pair.split("=", 1) for pair in query.split("&") if "=" in pair)
    return call_sonarqube_api(endpoint, method, query_params)

@mcp.tool(description="List all SonarQube projects")
def list_projects() -> list[str]:
    data = call_sonarqube_api("projects/search")
    projects = [
        f"Project Name: {project['name']} - Project Key: {project['key']}"
        for project in data.get("components", [])
    ]
    return projects


@mcp.tool(description="List issues in a SonarQube project")
def list_issues(project_key: str) -> list[str]:
    data = call_sonarqube_api("issues/search", params={"componentKeys": project_key})
    issues = [
        f"Key: {i['key']} | Severity: {i['severity']} | Message: {i['message']} | "
        f"Line: {i.get('line', 'N/A')} | Rule: {i['rule']} | Status: {i['status']}"
        for i in data.get("issues", [])
    ]
    return issues

@mcp.tool(description="Get detailed information about a specific issue")
def get_issue_details(issue_key: str) -> dict:
    data = call_sonarqube_api("issues/show", params={"issue": issue_key})
    
    issue = data.get("issue", {})
    
    return {
        "Key": issue.get("key", "N/A"),
        "Severity": issue.get("severity", "N/A"),
        "Message": issue.get("message", "N/A"),
        "Line": issue.get("line", "N/A"),
        "Component": issue.get("component", "N/A"),
        "Rule": issue.get("rule", "N/A"),
        "Status": issue.get("status", "N/A"),
        "Created At": issue.get("createdAt", "N/A"),
        "Updated At": issue.get("updatedAt", "N/A"),
        "Assignee": issue.get("assignee", "N/A"),
        "Resolution": issue.get("resolution", "N/A"),
        "Project Key": issue.get("project", "N/A"),
    }



@mcp.tool(description="List available metrics")
def list_metrics() -> list[str]:
    data = call_sonarqube_api("metrics/search")
    return [f"{m['key']}: {m['name']}" for m in data.get("metrics", [])]


@mcp.tool(description="List quality gates")
def list_quality_gates() -> list[str]:
    data = call_sonarqube_api("qualitygates/list")
    return [qg["name"] for qg in data.get("qualitygates", [])]


@mcp.tool(description="Get SonarQube system info")
def get_system_info() -> dict:
    return call_sonarqube_api("system/info")

@mcp.tool(description="Create a new SonarQube project")
def create_project(project_key: str, project_name: str) -> str:
    response = call_sonarqube_api(
        endpoint="projects/create",
        method="POST",
        params={"project": project_key, "name": project_name}
    )
    return f"Project '{project_name}' with key '{project_key}' created successfully."


if __name__ == "__main__":
    mcp.run()
