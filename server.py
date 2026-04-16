from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("unfolded-circle-core-api")

# Base URLs for Unfolded Circle documentation
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/unfoldedcircle/core-api/main"
GITHUB_API_BASE = "https://api.github.com/repos/unfoldedcircle/core-api"
DEV_GUIDE_BASE = "https://unfoldedcircle.github.io/core-api"


async def fetch_github_content(path: str) -> str:
    """Fetch raw content from GitHub repository."""
    url = f"{GITHUB_RAW_BASE}/{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
            else:
                return f"Could not fetch content from {url} (status {response.status_code})"
        except Exception as e:
            return f"Error fetching content: {str(e)}"


async def fetch_multiple_paths(paths: list) -> dict:
    """Fetch multiple GitHub paths and return combined results."""
    results = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        for path in paths:
            url = f"{GITHUB_RAW_BASE}/{path}"
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    results[path] = response.text
                else:
                    results[path] = f"Not found (status {response.status_code})"
            except Exception as e:
                results[path] = f"Error: {str(e)}"
    return results


@mcp.tool()
async def get_api_overview() -> dict:
    """Get an overview of all available Unfolded Circle Core APIs including Integration API, Core API (REST and WebSocket), and Dock API. Use this as the starting point to understand what APIs are available and how they relate to each other."""
    readme_content = await fetch_github_content("README.md")
    
    overview = {
        "title": "Unfolded Circle Core APIs Overview",
        "developer_guide_url": "https://unfoldedcircle.github.io/core-api",
        "github_repository": "https://github.com/unfoldedcircle/core-api",
        "apis": {
            "integration_api": {
                "description": "WebSocket Integration-API for writing device integrations for Unfolded Circle Remote devices",
                "type": "WebSocket (AsyncAPI)",
                "readme": "https://github.com/unfoldedcircle/core-api/blob/main/integration-api/README.md",
                "notes": "Integration driver acts as server, Remote device acts as client. Supports entity integration for home automation."
            },
            "core_api_websocket": {
                "description": "WebSocket Core-API for real-time control and configuration of the Remote device",
                "type": "WebSocket (AsyncAPI)",
                "readme": "https://github.com/unfoldedcircle/core-api/blob/main/core-api/websocket/README.md"
            },
            "core_api_rest": {
                "description": "REST Core-API for controlling and configuring the Unfolded Circle Remote device",
                "type": "REST (OpenAPI)",
                "readme": "https://github.com/unfoldedcircle/core-api/blob/main/core-api/rest/README.md"
            },
            "dock_api": {
                "description": "WebSocket Dock-API for communicating with Unfolded Circle dock hardware",
                "type": "WebSocket (AsyncAPI)",
                "readme": "https://github.com/unfoldedcircle/core-api/blob/main/dock-api/README.md"
            }
        },
        "additional_docs": {
            "remote_ui": "Remote Two user interface documentation",
            "bluetooth_hid": "Bluetooth HID peripheral support",
            "entities": "Remote Two entity types for integration drivers",
            "write_driver": "Guide on how to write an integration driver",
            "websocket_handling": "WebSocket authentication, keep alive, error handling"
        },
        "readme_content": readme_content
    }
    return overview


@mcp.tool()
async def get_integration_api_docs(section: Optional[str] = "overview") -> dict:
    """Retrieve documentation and specifications for the WebSocket Integration API used to write device integrations for Unfolded Circle Remote devices. Use this when building or understanding external integration drivers, entity support, or WebSocket authentication/keep-alive handling.
    
    Args:
        section: The section of integration API docs to retrieve. Options: 'overview', 'entities', 'websocket', 'write-driver', 'authentication'. Defaults to overview.
    """
    section = section or "overview"
    section = section.lower().strip()
    
    section_map = {
        "overview": ["integration-api/README.md"],
        "entities": ["doc/entities/README.md"],
        "websocket": ["doc/integration-driver/websocket.md"],
        "write-driver": ["doc/integration-driver/write-integration-driver.md"],
        "authentication": ["doc/integration-driver/websocket.md"]
    }
    
    paths = section_map.get(section, section_map["overview"])
    
    result = {
        "section": section,
        "title": "Unfolded Circle WebSocket Integration API",
        "api_type": "WebSocket (AsyncAPI)",
        "github_url": "https://github.com/unfoldedcircle/core-api/tree/main/integration-api",
        "developer_guide_url": "https://unfoldedcircle.github.io/core-api",
        "content": {}
    }
    
    for path in paths:
        content = await fetch_github_content(path)
        result["content"][path] = content
    
    # Add section-specific metadata
    if section == "overview":
        result["description"] = (
            "The WebSocket Integration API allows writing device integrations for Remote devices. "
            "The integration driver acts as server and the Remote device as client."
        )
        result["key_concepts"] = [
            "Integration driver acts as WebSocket server",
            "Remote device connects as WebSocket client",
            "Supports external integrations and on-device drivers (beta 1.9.0+)",
            "Focus on entity integration, not device control",
            "Entity types: button, switch, light, media_player, climate, sensor, etc."
        ]
    elif section == "authentication":
        result["description"] = "WebSocket authentication, keep-alive, and error handling for integration drivers."
    elif section == "write-driver":
        result["description"] = "Step-by-step guide to writing an integration driver for Unfolded Circle Remote devices."
    
    return result


@mcp.tool()
async def get_core_api_docs(api_type: Optional[str] = "rest", section: Optional[str] = None) -> dict:
    """Retrieve documentation for the Core API, which covers both the WebSocket Core-API and the REST Core-API for controlling and configuring the Unfolded Circle Remote device. Use this when you need to understand device control, configuration endpoints, or real-time communication with the remote.
    
    Args:
        api_type: Which Core API type to retrieve docs for. Options: 'rest', 'websocket'. Defaults to 'rest'.
        section: Optional specific section or topic within the Core API docs to focus on, e.g. 'authentication', 'endpoints', 'events'.
    """
    api_type = (api_type or "rest").lower().strip()
    
    path_map = {
        "rest": "core-api/rest/README.md",
        "websocket": "core-api/websocket/README.md"
    }
    
    path = path_map.get(api_type, path_map["rest"])
    content = await fetch_github_content(path)
    
    result = {
        "api_type": api_type,
        "title": f"Unfolded Circle Core API - {api_type.upper()}",
        "github_url": f"https://github.com/unfoldedcircle/core-api/tree/main/core-api/{api_type}",
        "developer_guide_url": "https://unfoldedcircle.github.io/core-api",
        "content": content
    }
    
    if api_type == "rest":
        result["description"] = (
            "The REST Core-API provides HTTP endpoints for controlling and configuring the Unfolded Circle Remote. "
            "Defined with OpenAPI specification."
        )
        result["openapi_spec"] = "https://github.com/unfoldedcircle/core-api/blob/main/core-api/rest/openapi.yaml"
        result["key_features"] = [
            "Device configuration and status",
            "Integration management",
            "Entity and activity configuration",
            "Profile and UI customization",
            "Firmware updates"
        ]
    elif api_type == "websocket":
        result["description"] = (
            "The WebSocket Core-API provides real-time bidirectional communication with the Remote device. "
            "Defined with AsyncAPI specification."
        )
        result["asyncapi_spec"] = "https://github.com/unfoldedcircle/core-api/blob/main/core-api/websocket/asyncapi.yaml"
        result["key_features"] = [
            "Real-time device events",
            "Entity state updates",
            "Activity execution",
            "System events and notifications"
        ]
    
    if section:
        result["requested_section"] = section
        result["note"] = f"For detailed '{section}' information, refer to the content above and the developer guide."
    
    return result


@mcp.tool()
async def get_entity_docs(entity_type: Optional[str] = None) -> dict:
    """Retrieve documentation about Remote Two entity types supported by integration drivers, such as buttons, switches, media players, climate controls, etc. Use this when designing or implementing integration driver entities, understanding entity attributes, commands, or state models.
    
    Args:
        entity_type: Specific entity type to look up, e.g. 'button', 'switch', 'media_player', 'climate', 'light', 'sensor'. Leave null to get an overview of all entity types.
    """
    entity_file_map = {
        "button": "doc/entities/button.md",
        "switch": "doc/entities/switch.md",
        "media_player": "doc/entities/media_player.md",
        "climate": "doc/entities/climate.md",
        "light": "doc/entities/light.md",
        "sensor": "doc/entities/sensor.md",
        "cover": "doc/entities/cover.md",
        "remote": "doc/entities/remote.md",
        "activity": "doc/entities/activity.md"
    }
    
    result = {
        "title": "Unfolded Circle Remote Two - Entity Types",
        "github_url": "https://github.com/unfoldedcircle/core-api/tree/main/doc/entities",
        "developer_guide_url": "https://unfoldedcircle.github.io/core-api",
        "available_entity_types": list(entity_file_map.keys()),
        "content": {}
    }
    
    if entity_type:
        entity_type = entity_type.lower().strip()
        path = entity_file_map.get(entity_type)
        if path:
            content = await fetch_github_content(path)
            result["entity_type"] = entity_type
            result["content"][entity_type] = content
        else:
            result["error"] = f"Unknown entity type '{entity_type}'. Available types: {list(entity_file_map.keys())}"
            # Fall back to overview
            overview = await fetch_github_content("doc/entities/README.md")
            result["content"]["overview"] = overview
    else:
        # Get overview
        overview = await fetch_github_content("doc/entities/README.md")
        result["content"]["overview"] = overview
        result["entity_descriptions"] = {
            "button": "Simple button entity for triggering actions",
            "switch": "On/off switch entity",
            "media_player": "Media player with playback controls, volume, source selection",
            "climate": "Climate control with temperature, HVAC modes, fan modes",
            "light": "Light entity with on/off, brightness, color, color temperature",
            "sensor": "Read-only sensor for data values",
            "cover": "Cover/blind/curtain control",
            "remote": "IR/RF remote control entity",
            "activity": "Activity macro entity for sequences of commands"
        }
    
    return result


@mcp.tool()
async def get_dock_api_docs(section: Optional[str] = "overview") -> dict:
    """Retrieve documentation and specifications for the WebSocket Dock API used to communicate with Unfolded Circle dock hardware. Use this when integrating with or building firmware/software that interacts with the dock accessory.
    
    Args:
        section: Section of the Dock API documentation to retrieve. Options: 'overview', 'messages', 'authentication', 'events'.
    """
    section = (section or "overview").lower().strip()
    
    # Dock API paths
    dock_paths = {
        "overview": ["dock-api/README.md"],
        "messages": ["dock-api/README.md"],
        "authentication": ["dock-api/README.md"],
        "events": ["dock-api/README.md"]
    }
    
    paths = dock_paths.get(section, dock_paths["overview"])
    
    result = {
        "section": section,
        "title": "Unfolded Circle WebSocket Dock API",
        "api_type": "WebSocket (AsyncAPI)",
        "github_url": "https://github.com/unfoldedcircle/core-api/tree/main/dock-api",
        "developer_guide_url": "https://unfoldedcircle.github.io/core-api",
        "content": {}
    }
    
    for path in paths:
        content = await fetch_github_content(path)
        result["content"][path] = content
    
    result["description"] = (
        "The WebSocket Dock API enables communication with the Unfolded Circle dock hardware accessory. "
        "Used for firmware/software development interacting with the dock device."
    )
    result["key_features"] = [
        "WebSocket-based bidirectional communication",
        "Dock hardware control and status",
        "IR blaster control",
        "Charging dock functionality",
        "Authentication and session management"
    ]
    
    if section != "overview":
        result["section_note"] = (
            f"For '{section}' specific details, refer to the content above. "
            f"The full AsyncAPI specification is available in the dock-api directory."
        )
    
    return result


@mcp.tool()
async def get_remote_ui_docs(section: Optional[str] = None) -> dict:
    """Retrieve documentation about the Remote Two user interface, including UI layout, page structure, button mappings, and UI customization options. Use this when designing UI configurations or understanding how the physical remote interface is structured.
    
    Args:
        section: Specific UI documentation section to retrieve, e.g. 'layout', 'pages', 'buttons', 'profiles'. Leave null for full UI overview.
    """
    content = await fetch_github_content("doc/remote-ui.md")
    
    result = {
        "title": "Unfolded Circle Remote Two - User Interface Documentation",
        "github_url": "https://github.com/unfoldedcircle/core-api/blob/main/doc/remote-ui.md",
        "developer_guide_url": "https://unfoldedcircle.github.io/core-api",
        "content": content
    }
    
    result["ui_structure"] = {
        "description": "The Remote Two features a touchscreen display with customizable UI",
        "key_concepts": [
            "Pages: Individual screens/views on the remote",
            "Profiles: User-specific UI configurations",
            "Groups: Logical groupings of entities and activities",
            "Buttons: Physical button mappings and assignments",
            "Activities: Macro sequences shown on the UI",
            "Entities: Device controls displayed on pages"
        ]
    }
    
    if section:
        result["requested_section"] = section
        result["section_note"] = (
            f"For '{section}' specific information, refer to the full content above. "
            f"Use the Core REST API to programmatically configure UI elements."
        )
    
    return result


@mcp.tool()
async def get_bluetooth_hid_docs(section: Optional[str] = "overview") -> dict:
    """Retrieve documentation for Bluetooth HID peripheral support on the Unfolded Circle Remote. Use this when working with Bluetooth Human Interface Device features, pairing, or HID descriptor configurations.
    
    Args:
        section: Section of the Bluetooth HID documentation to retrieve. Options: 'overview', 'pairing', 'descriptors', 'profiles'.
    """
    section = (section or "overview").lower().strip()
    
    # Fetch BT README
    bt_readme = await fetch_github_content("doc/bt/README.md")
    
    result = {
        "section": section,
        "title": "Unfolded Circle Remote - Bluetooth HID Peripheral Support",
        "github_url": "https://github.com/unfoldedcircle/core-api/tree/main/doc/bt",
        "developer_guide_url": "https://unfoldedcircle.github.io/core-api",
        "content": {
            "readme": bt_readme
        }
    }
    
    result["description"] = (
        "The Unfolded Circle Remote supports Bluetooth HID peripheral mode, "
        "allowing it to act as a Bluetooth Human Interface Device."
    )
    result["key_features"] = [
        "Bluetooth HID peripheral mode",
        "Device pairing and bonding",
        "HID descriptor configuration",
        "Keyboard and media control profiles",
        "Custom HID profiles"
    ]
    
    # Try to fetch additional BT docs based on section
    section_paths = {
        "pairing": "doc/bt/pairing.md",
        "descriptors": "doc/bt/descriptors.md",
        "profiles": "doc/bt/profiles.md"
    }
    
    if section in section_paths:
        additional_content = await fetch_github_content(section_paths[section])
        result["content"][section] = additional_content
    
    return result


@mcp.tool()
async def search_developer_guide(query: str, api_scope: Optional[str] = None) -> dict:
    """Search across the full Unfolded Circle Developer Guide documentation for a specific topic, concept, or keyword. Use this when you need to find information about a specific feature, API behavior, or implementation detail across all API types and documentation sections.
    
    Args:
        query: The search query or topic to look up in the developer guide, e.g. 'authentication', 'keep alive', 'IR codes', 'custom driver install'.
        api_scope: Optionally narrow the search to a specific API scope. Options: 'integration', 'core-rest', 'core-websocket', 'dock', 'ui', 'bluetooth'. Leave null to search all docs.
    """
    query_lower = query.lower()
    
    # Define scope-to-paths mapping
    scope_paths = {
        "integration": [
            "integration-api/README.md",
            "doc/integration-driver/write-integration-driver.md",
            "doc/integration-driver/websocket.md",
            "doc/entities/README.md"
        ],
        "core-rest": [
            "core-api/rest/README.md"
        ],
        "core-websocket": [
            "core-api/websocket/README.md"
        ],
        "dock": [
            "dock-api/README.md"
        ],
        "ui": [
            "doc/remote-ui.md"
        ],
        "bluetooth": [
            "doc/bt/README.md"
        ]
    }
    
    # All paths for broad search
    all_paths = [
        "README.md",
        "integration-api/README.md",
        "doc/integration-driver/write-integration-driver.md",
        "doc/integration-driver/websocket.md",
        "doc/entities/README.md",
        "core-api/rest/README.md",
        "core-api/websocket/README.md",
        "dock-api/README.md",
        "doc/remote-ui.md",
        "doc/bt/README.md"
    ]
    
    if api_scope and api_scope.lower() in scope_paths:
        paths_to_search = scope_paths[api_scope.lower()]
    else:
        paths_to_search = all_paths
    
    result = {
        "query": query,
        "api_scope": api_scope,
        "developer_guide_url": f"https://unfoldedcircle.github.io/core-api",
        "search_note": f"Searched documentation for '{query}'",
        "matches": {},
        "summary": ""
    }
    
    # Fetch content from relevant paths
    contents = await fetch_multiple_paths(paths_to_search)
    
    matched_sections = []
    
    for path, content in contents.items():
        if isinstance(content, str) and query_lower in content.lower():
            # Find relevant excerpts
            lines = content.split('\n')
            relevant_lines = []
            for i, line in enumerate(lines):
                if query_lower in line.lower():
                    # Include surrounding context
                    start = max(0, i - 2)
                    end = min(len(lines), i + 5)
                    excerpt = '\n'.join(lines[start:end])
                    relevant_lines.append(excerpt)
            
            if relevant_lines:
                result["matches"][path] = {
                    "found": True,
                    "excerpts": relevant_lines[:5],  # Limit to 5 excerpts per file
                    "full_content_available": True
                }
                matched_sections.append(path)
    
    if matched_sections:
        result["summary"] = f"Found '{query}' in {len(matched_sections)} documentation file(s): {', '.join(matched_sections)}"
    else:
        result["summary"] = f"No direct matches found for '{query}'. Try the developer guide at https://unfoldedcircle.github.io/core-api for full-text search."
        # Include main README as fallback
        result["fallback_content"] = contents.get("README.md", "")
    
    result["helpful_links"] = {
        "developer_guide": "https://unfoldedcircle.github.io/core-api",
        "github_repo": "https://github.com/unfoldedcircle/core-api",
        "integration_api": "https://github.com/unfoldedcircle/core-api/tree/main/integration-api",
        "core_rest_api": "https://github.com/unfoldedcircle/core-api/tree/main/core-api/rest",
        "core_ws_api": "https://github.com/unfoldedcircle/core-api/tree/main/core-api/websocket",
        "dock_api": "https://github.com/unfoldedcircle/core-api/tree/main/dock-api"
    }
    
    return result




_SERVER_SLUG = "unfoldedcircle-core-api"

def _track(tool_name: str, ua: str = ""):
    try:
        import urllib.request, json as _json
        data = _json.dumps({"slug": _SERVER_SLUG, "event": "tool_call", "tool": tool_name, "user_agent": ua}).encode()
        req = urllib.request.Request("https://www.volspan.dev/api/analytics/event", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

sse_app = mcp.http_app(transport="sse")

app = Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", sse_app),
    ],
    lifespan=sse_app.lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
