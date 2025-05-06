from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from task_manager import AgentTaskManager
from agent import SonarqubeAgent
import click
import os
import logging
from dotenv import load_dotenv
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    SseServerParams,
    StdioServerParameters,
)
import contextlib
import asyncio
import json
from contextlib import AsyncExitStack

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_tools_async(json_file: str = "mcp_config.json"):
    """Loads MCP server tool configurations from a JSON file."""
    with open(json_file, "r") as f:
        config = json.load(f)

    print("Attempting to connect to MCP Servers...")

    tools = []
    stack = AsyncExitStack()

    mcp_servers = config.get("mcpServers", {})

    for name, server in mcp_servers.items():
        command = server.get("command")
        args = server.get("args", [])
        env = server.get("env", {})

        print(command, args, env)

        toolset, server_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command=command,
                args=args,
                env=env or None
            )
        )
        tools.extend(toolset)
        await stack.enter_async_context(server_stack)

        print(f"Connected to MCP server '{name}'")

    print("All MCP toolsets loaded successfully.")
    return tools, stack

# async def get_tools_async():
#     """Gets tools from the File System MCP Server."""
#     print("Attempting to connect to MCP Filesystem server...")
#     tools, exit_stack = await MCPToolset.from_server(
#         # Use StdioServerParameters for local process communication
#         connection_params=StdioServerParameters(
#             command="python",  # Command to run the server
#             args=["sonar_mcp.py"],
#         )
#         # For remote servers, you would use SseServerParams instead:
#         # connection_params=SseServerParams(url="http://remote-server:port/path", headers={...})
#     )
#     print("MCP Toolset created successfully.")
#     # MCP requires maintaining a connection to the local MCP Server.
#     # exit_stack manages the cleanup of this connection.

#     return tools, exit_stack

async def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    tools, exit_stack = await get_tools_async()
    print(f"Fetched {len(tools)} tools from MCP server.")
    root_agent = SonarqubeAgent(
        description="This agent handle request for Sonarqube",
        instruction="""
You are an agent who handles request for Sonarque.
""",
        tools=tools, 
    )

    return root_agent, exit_stack


async def async_main(host, port):
    try:
        if not os.getenv("GOOGLE_API_KEY"):
            raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="process_Sonarqube",
            name="Process Sonarqube Tool",
            description="Helps with the Sonarqube process",
            tags=["Sonarqube"],
            examples=["Can you list Sonarqube project"],
        )
        agent_card = AgentCard(
            name="Sonarqube Agent",
            description="This agent handles the Sonarqube tasks.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=SonarqubeAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=SonarqubeAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        async with contextlib.AsyncExitStack() as exit_stack:
            sonar_agent, tools_exit_stack = await get_agent_async()
            await exit_stack.enter_async_context(tools_exit_stack)

            server = A2AServer(
                agent_card=agent_card,
                task_manager=AgentTaskManager(agent=sonar_agent),
                host=host,
                port=port,
            )
            await server.start_async()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(async_main("localhost", 10002))
    except Exception as e:
        print(f"An error occurred: {e}")
