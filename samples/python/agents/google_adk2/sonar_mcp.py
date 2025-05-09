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
    return response

@mcp.tool(description="Create a new user in SonarQube")
def create_user(login: str, name: str, password: str, email: str = "") -> str:
    """
    Creates a new SonarQube user.

-    Args:
        login: Unique username (login).
        name: Full name.
        password: Plain text password.
        email: (Optional) Email address.

    Returns:
        A message confirming user creation.
    """
    params = {
        "login": login,
        "name": name,
        "password": password
    }
    if email:
        params["email"] = email

    response = call_sonarqube_api("users/create", method="POST", params=params)
    return response

@mcp.tool(description="Create a new user group in SonarQube")
def create_group(name: str, description: str = "") -> str:
    """
    Creates a new group in SonarQube.

    Args:
        name: The name of the group (must be unique).
        description: Optional description of the group.

    Returns:
        A confirmation message.
    """
    params = {"name": name}
    if description:
        params["description"] = description

    response = call_sonarqube_api("user_groups/create", method="POST", params=params)
    return response

@mcp.tool(description="""
          Add a user to a SonarQube group using the v2 API.
        you may need to use list_groups_v2 to get group_id and list_users_v2 to get user_id to complete this task
""")
def add_user_to_group_v2(user_id: str, group_id: str) -> str:
    """
    Adds a user to a specified group in SonarQube using the v2 API.

    Args:
        user_id (str): The ID of the user to be added to the group.
        group_id (str): The ID of the group to which the user will be added.

    Returns:
        str: A success message indicating that the user was added to the group.
    """
    # Prepare the API request to add the user to the group
    payload = {
        "userId": user_id,
        "groupId": group_id
    }
    response = call_sonarqube_api("v2/authorizations/group-memberships", method="POST", json=payload)
    
    return response

@mcp.tool(description="List group membership of a user using the v2 API")
def list_user_group_memberships_v2(user_id: str, page_size: int = 100, page_index: int = 1):
    """
    Lists the group memberships of a user in SonarQube using the v2 API.

    Args:
        user_id (str): The ID of the user whose group memberships are being listed.
        page_size (int): Number of results per page (default 100).
        page_index (int): Page number to retrieve (default 1).

    Returns:
        dict: A dictionary containing the user's group memberships.
    """
    # Prepare the API request parameters
    params = {
        "userId": user_id,
        "pageSize": page_size,
        "pageIndex": page_index
    }
    
    try:
        # Make the API request to get group memberships
        response = call_sonarqube_api("v2/authorizations/group-memberships", method="GET", params=params)
        
        group_memberships = response.get("groupMemberships", [])
        if group_memberships:
            return group_memberships
        else:
            return "No group memberships found for the user."
    
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Remove group membership of a user using the v2 API")
def remove_user_from_group(membership_id: str):
    """
    Removes a user from a group in SonarQube using the v2 API by deleting the group membership.

    Args:
        membership_id (str): The ID of the group membership to be removed.

    Returns:
        str: A success message indicating that the user was removed from the group.
    """
    try:
        # Prepare the DELETE request to remove the group membership
        endpoint = f"v2/authorizations/group-memberships/{membership_id}"
        response = call_sonarqube_api(endpoint, method="DELETE")
        
        # Return success message
        return response
    
    except requests.exceptions.RequestException as e:
        return f"An error occurred while removing the group membership: {str(e)}"

@mcp.tool(description="""
Grant a global or project-specific permission to a SonarQube user.

This tool assigns permissions such as project access or administrative rights. 
Global permissions apply system-wide, while project-level permissions can be restricted to a single project by specifying the `project_key`.

Requires the caller to have 'Administer System' or 'Administer' rights on the target project.
""")
def add_user_permission(
    user_login: str,
    permission: str,
    project_key: str = ""
) -> str:
    """
    Grants a specified permission to a SonarQube user.

    Args:
        user_login (str): The login name of the target user (e.g., 'g.hopper').
        permission (str): The permission key to grant.
            - Global permissions: 'admin', 'gateadmin', 'profileadmin', 'provisioning', 'scan', 'applicationcreator', 'portfoliocreator'
            - Project permissions: 'admin', 'codeviewer', 'issueadmin', 'securityhotspotadmin', 'scan', 'user'
        project_key (str, optional): If provided, the permission is granted for the specified project only.
            If omitted, the permission is granted globally.

    Returns:
        str: A message confirming that the permission was granted.
    """
    params = {
        "login": user_login,
        "permission": permission
    }
    if project_key:
        params["projectKey"] = project_key

    response = call_sonarqube_api("permissions/add_user", method="POST", params=params)
    return response

@mcp.tool(description="""
Remove a permission from a specific SonarQube user.

This tool supports revoking both global permissions (like system admin, scan rights)
and project-specific permissions (like code viewer or issue admin) based on the provided project key.

Permissions are only removed if the caller has sufficient rights:
- Global permissions require 'Administer System'
- Project permissions require 'Administer' on that project
""")
def remove_user_permission(
    user_login: str,
    permission: str,
    project_key: str = ""
) -> str:
    """
    Revokes a permission from a SonarQube user.

    Args:
        user_login (str): The login of the user to update (e.g., 'alice').
        permission (str): The permission key to revoke.
            - Global permissions: 'admin', 'gateadmin', 'profileadmin', 'provisioning', 'scan', 'applicationcreator', 'portfoliocreator'
            - Project permissions: 'admin', 'codeviewer', 'issueadmin', 'securityhotspotadmin', 'scan', 'user'
        project_key (str, optional): If provided, the permission will be removed only for that specific project (e.g., 'my_project').
            If omitted, the permission is removed globally.

    Returns:
        str: A success message indicating the permission was revoked and the scope.
    """
    params = {
        "login": user_login,
        "permission": permission
    }
    if project_key:
        params["projectKey"] = project_key

    response = call_sonarqube_api("permissions/remove_user", method="POST", params=params)
    return response

@mcp.tool(description="""
Grant a permission to a SonarQube group, either globally or for a specific project.

Supports adding permissions like 'scan', 'admin', or 'codeviewer' to groups such as 'sonar-users' or 'sonar-administrators'.
Set the `project_key` if you want to limit the permission to a specific project.

Requires:
- 'Administer System' for global permissions
- 'Administer' rights on the project for project-level permissions
""")
def add_group_permission(
    group_name: str,
    permission: str,
    project_key: str = ""
) -> str:
    """
    Grants a permission to a group in SonarQube.

    Args:
        group_name (str): The name of the target group (e.g., 'sonar-administrators' or 'anyone').
        permission (str): The permission to grant.
            - Global permissions: 'admin', 'gateadmin', 'profileadmin', 'provisioning', 'scan', 'applicationcreator', 'portfoliocreator'
            - Project permissions: 'admin', 'codeviewer', 'issueadmin', 'securityhotspotadmin', 'scan', 'user'
        project_key (str, optional): If provided, permission is granted for this project only. If empty, it's granted globally.

    Returns:
        str: Confirmation message.
    """
    params = {
        "groupName": group_name,
        "permission": permission
    }
    if project_key:
        params["projectKey"] = project_key

    response = call_sonarqube_api("permissions/add_group", method="POST", params=params)
    return response


@mcp.tool(description="""
Revoke a global or project-specific permission from a SonarQube group.

This tool removes permissions such as 'scan', 'admin', or 'codeviewer' from groups like 'sonar-users' or 'sonar-administrators'.
If `project_key` is provided, the permission is revoked only for that project.

Requires:
- 'Administer System' for global permissions
- 'Administer' rights on the project for project-level permissions
""")
def remove_group_permission(
    group_name: str,
    permission: str,
    project_key: str = ""
) -> str:
    """
    Revokes a specified permission from a SonarQube group.

    Args:
        group_name (str): The name of the group (e.g., 'sonar-users' or 'anyone').
        permission (str): The permission to revoke.
            - Global permissions: 'admin', 'gateadmin', 'profileadmin', 'provisioning', 'scan', 'applicationcreator', 'portfoliocreator'
            - Project permissions: 'admin', 'codeviewer', 'issueadmin', 'securityhotspotadmin', 'scan', 'user'
        project_key (str, optional): If provided, the permission is revoked for the specified project.
            If empty, the permission is removed globally.

    Returns:
        str: Confirmation message.
    """
    params = {
        "groupName": group_name,
        "permission": permission
    }
    if project_key:
        params["projectKey"] = project_key

    response = call_sonarqube_api("permissions/remove_group", method="POST", params=params)
    return response



@mcp.tool(description="List all known SonarQube global and project-level permissions")
def list_available_permissions() -> dict:
    """
    Returns a dictionary of common SonarQube permissions.

    Returns:
        A dictionary with global and project-level permission keys.
    """
    return {
        "global_permissions": [
            "admin",                   # Global administrator
            "gateadmin",              # Manage quality gates
            "profileadmin",           # Manage quality profiles
            "provisioning",           # Provision projects/users
            "scan",                   # Run analysis
            "system",                 # Access System Info
            "securityhotspotadmin"   # Manage security hotspots
        ],
        "project_permissions": [
            "admin",                   # Project administrator
            "codeviewer",             # View source code
            "issueadmin",             # Manage issues
            "securityhotspotadmin",   # Manage security hotspots
            "user"                    # Browse project
        ]
    }

@mcp.tool(description="Get global permissions assigned to a user")
def get_user_global_permissions(user_login: str) -> dict:
    return call_sonarqube_api("permissions/users", params={"login": user_login})

@mcp.tool(description="Get project-specific permissions assigned to a user")
def get_user_project_permissions(user_login: str, project_key: str) -> dict:
    return call_sonarqube_api("permissions/search_users", params={"projectKey": project_key, "q": user_login})

@mcp.tool(description="Get project-specific permissions assigned to a group")
def get_group_project_permissions(group_name: str, project_key: str) -> dict:
    return call_sonarqube_api("permissions/search_groups", params={"projectKey": project_key})

@mcp.tool(description="List SonarQube user groups using the v2 API")
def list_groups_v2(query: str = "", page_index: int = 1) -> list[str]:
    """
    Lists user groups with details using SonarQube v2 API.

    Args:
        query: Optional search filter.
        page_index: Page number (starting from 1).

    Returns:
        A list of formatted group entries.
    """
    params = {"q": query, "pageIndex": page_index}
    data = call_sonarqube_api("v2/authorizations/groups", params=params)
    groups = data.get("groups", [])
    return [
        f"{g['name']} (ID: {g['id']}) | Description: {g.get('description', 'None')} | "
        f"Default: {g['default']} | Managed: {g['managed']}"
        for g in groups
    ]


@mcp.tool(description="List all SonarQube users using the v2 API")
def list_users_v2() -> list[str]:
    """
    Lists all users in the SonarQube instance using the v2 API.
    
    Returns:
        list: A list of user details, including login and name.
    """
    data = call_sonarqube_api("v2/users-management/users", method="GET")
    users = [
        f"User ID: {user['id']} | Login: {user['login']} | Name: {user['name']}"
        for user in data.get("users", [])
    ]
    return users


if __name__ == "__main__":
    mcp.run()
