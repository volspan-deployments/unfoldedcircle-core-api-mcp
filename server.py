from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("unfolded-circle-core-apis")

# Base URLs for Unfolded Circle documentation and API specs
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/unfoldedcircle/core-api/main"
GITHUB_API_BASE = "https://api.github.com/repos/unfoldedcircle/core-api"
DEV_GUIDE_BASE = "https://unfoldedcircle.github.io/core-api"


async def fetch_url(url: str) -> str:
    """Fetch content from a URL, return text or error message."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
            else:
                return f"Error fetching {url}: HTTP {response.status_code}"
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


@mcp.tool()
async def get_api_overview() -> dict:
    """Get a high-level overview of all available Unfolded Circle Core APIs including Integration API, Core API (REST and WebSocket), and Dock API. Use this first to understand what APIs are available and which one to use for a given task."""
    readme_content = await fetch_url(f"{GITHUB_RAW_BASE}/README.md")
    
    overview = {
        "source": f"{GITHUB_RAW_BASE}/README.md",
        "developer_guide": "https://unfoldedcircle.github.io/core-api",
        "github_repo": "https://github.com/unfoldedcircle/core-api",
        "apis": {
            "integration_api": {
                "description": "WebSocket Integration API for writing device integrations (external drivers)",
                "type": "WebSocket (AsyncAPI)",
                "readme": f"{GITHUB_RAW_BASE}/integration-api/README.md",
                "spec": f"{GITHUB_RAW_BASE}/integration-api/asyncapi.yaml",
                "use_case": "Build external device integration drivers that the Remote connects to"
            },
            "core_api_rest": {
                "description": "REST Core API for controlling and configuring the Remote device",
                "type": "REST (OpenAPI)",
                "readme": f"{GITHUB_RAW_BASE}/core-api/rest/README.md",
                "spec": f"{GITHUB_RAW_BASE}/core-api/rest/openapi.yaml",
                "use_case": "Manage activities, macros, remotes, system settings, UI configuration"
            },
            "core_api_websocket": {
                "description": "WebSocket Core API for real-time control of the Remote device",
                "type": "WebSocket (AsyncAPI)",
                "readme": f"{GITHUB_RAW_BASE}/core-api/websocket/README.md",
                "spec": f"{GITHUB_RAW_BASE}/core-api/websocket/asyncapi.yaml",
                "use_case": "Real-time events and control of the Remote device"
            },
            "dock_api": {
                "description": "WebSocket Dock API for communicating with Unfolded Circle dock hardware",
                "type": "WebSocket (AsyncAPI)",
                "readme": f"{GITHUB_RAW_BASE}/dock-api/README.md",
                "spec": f"{GITHUB_RAW_BASE}/dock-api/asyncapi.yaml",
                "use_case": "Interact with charging dock or dock-specific features"
            }
        },
        "additional_docs": {
            "remote_ui": f"{GITHUB_RAW_BASE}/doc/remote-ui.md",
            "bluetooth_hid": f"{GITHUB_RAW_BASE}/doc/bt/README.md",
            "entities": f"{GITHUB_RAW_BASE}/doc/entities/README.md",
            "write_driver": f"{GITHUB_RAW_BASE}/doc/integration-driver/write-integration-driver.md",
            "websocket_handling": f"{GITHUB_RAW_BASE}/doc/integration-driver/websocket.md"
        },
        "readme_content": readme_content
    }
    return overview


@mcp.tool()
async def get_integration_api_docs(section: Optional[str] = "overview") -> dict:
    """Retrieve documentation and specifications for the WebSocket Integration API used to write device integrations for Unfolded Circle Remote devices. Use this when building or understanding external integration drivers, handling authentication, keep-alive, or error handling over WebSocket."""
    
    section = section or "overview"
    
    section_urls = {
        "overview": f"{GITHUB_RAW_BASE}/integration-api/README.md",
        "authentication": f"{GITHUB_RAW_BASE}/doc/integration-driver/websocket.md",
        "websocket": f"{GITHUB_RAW_BASE}/doc/integration-driver/websocket.md",
        "entities": f"{GITHUB_RAW_BASE}/doc/entities/README.md",
        "write-driver": f"{GITHUB_RAW_BASE}/doc/integration-driver/write-integration-driver.md"
    }
    
    url = section_urls.get(section, section_urls["overview"])
    content = await fetch_url(url)
    
    # Also fetch the AsyncAPI spec for the overview
    spec_content = None
    if section == "overview":
        spec_content = await fetch_url(f"{GITHUB_RAW_BASE}/integration-api/asyncapi.yaml")
    
    result = {
        "section": section,
        "source_url": url,
        "available_sections": list(section_urls.keys()),
        "spec_url": f"{GITHUB_RAW_BASE}/integration-api/asyncapi.yaml",
        "content": content
    }
    
    if spec_content:
        result["asyncapi_spec"] = spec_content
    
    return result


@mcp.tool()
async def get_entity_docs(entity_type: Optional[str] = None) -> dict:
    """Retrieve documentation about Remote Two entities supported by integration drivers. Use this when you need to understand what entity types exist (e.g., lights, media players, sensors), their attributes, and how to implement them in a driver."""
    
    # Known entity types and their doc paths
    entity_files = {
        "overview": f"{GITHUB_RAW_BASE}/doc/entities/README.md",
        "light": f"{GITHUB_RAW_BASE}/doc/entities/entity_light.md",
        "media_player": f"{GITHUB_RAW_BASE}/doc/entities/entity_media_player.md",
        "sensor": f"{GITHUB_RAW_BASE}/doc/entities/entity_sensor.md",
        "button": f"{GITHUB_RAW_BASE}/doc/entities/entity_button.md",
        "climate": f"{GITHUB_RAW_BASE}/doc/entities/entity_climate.md",
        "switch": f"{GITHUB_RAW_BASE}/doc/entities/entity_switch.md",
        "cover": f"{GITHUB_RAW_BASE}/doc/entities/entity_cover.md",
        "remote": f"{GITHUB_RAW_BASE}/doc/entities/entity_remote.md"
    }
    
    results = {}
    
    if entity_type is None:
        # Fetch overview and all entity docs
        overview_content = await fetch_url(entity_files["overview"])
        results["overview"] = {
            "source_url": entity_files["overview"],
            "content": overview_content
        }
        results["available_entity_types"] = [k for k in entity_files.keys() if k != "overview"]
        results["note"] = "Specify an entity_type parameter to get detailed docs for a specific entity"
    else:
        entity_type_lower = entity_type.lower()
        if entity_type_lower in entity_files:
            content = await fetch_url(entity_files[entity_type_lower])
            results["entity_type"] = entity_type_lower
            results["source_url"] = entity_files[entity_type_lower]
            results["content"] = content
        else:
            # Try to fetch anyway with the provided name
            url = f"{GITHUB_RAW_BASE}/doc/entities/entity_{entity_type_lower}.md"
            content = await fetch_url(url)
            results["entity_type"] = entity_type_lower
            results["source_url"] = url
            results["content"] = content
            results["available_entity_types"] = [k for k in entity_files.keys() if k != "overview"]
    
    return results


@mcp.tool()
async def get_core_api_docs(api_type: Optional[str] = "rest", section: Optional[str] = None) -> dict:
    """Retrieve documentation for the Core API (either REST or WebSocket). Use this when you need to control or configure the Remote device itself — such as managing activities, macros, remotes, system settings, or UI configuration — rather than writing an integration driver."""
    
    api_type = (api_type or "rest").lower()
    
    if api_type == "rest":
        readme_url = f"{GITHUB_RAW_BASE}/core-api/rest/README.md"
        spec_url = f"{GITHUB_RAW_BASE}/core-api/rest/openapi.yaml"
        spec_type = "OpenAPI"
    else:
        readme_url = f"{GITHUB_RAW_BASE}/core-api/websocket/README.md"
        spec_url = f"{GITHUB_RAW_BASE}/core-api/websocket/asyncapi.yaml"
        spec_type = "AsyncAPI"
    
    readme_content = await fetch_url(readme_url)
    spec_content = await fetch_url(spec_url)
    
    result = {
        "api_type": api_type,
        "spec_type": spec_type,
        "readme_url": readme_url,
        "spec_url": spec_url,
        "readme_content": readme_content,
        "spec_content": spec_content
    }
    
    if section:
        result["requested_section"] = section
        result["note"] = f"The full spec has been returned above. Search for '{section}' within the spec_content to find the relevant section."
    
    return result


@mcp.tool()
async def get_dock_api_docs() -> dict:
    """Retrieve documentation for the WebSocket Dock API used to communicate with Unfolded Circle dock hardware. Use this when building software that interacts with the charging dock or dock-specific features."""
    
    readme_url = f"{GITHUB_RAW_BASE}/dock-api/README.md"
    spec_url = f"{GITHUB_RAW_BASE}/dock-api/asyncapi.yaml"
    
    readme_content = await fetch_url(readme_url)
    spec_content = await fetch_url(spec_url)
    
    return {
        "api_name": "WebSocket Dock API",
        "spec_type": "AsyncAPI",
        "readme_url": readme_url,
        "spec_url": spec_url,
        "readme_content": readme_content,
        "spec_content": spec_content
    }


@mcp.tool()
async def get_remote_ui_docs(topic: Optional[str] = None) -> dict:
    """Retrieve documentation about the Remote Two user interface design, layout, and UI concepts. Use this when you need to understand how the Remote UI works, how pages and widgets are structured, or how to customize the interface."""
    
    main_url = f"{GITHUB_RAW_BASE}/doc/remote-ui.md"
    main_content = await fetch_url(main_url)
    
    result = {
        "source_url": main_url,
        "content": main_content
    }
    
    if topic:
        result["requested_topic"] = topic
        result["note"] = f"Search for '{topic}' within the content above to find the relevant section."
        
        # Try to also fetch any related pages doc if it exists
        topic_lower = topic.lower()
        extra_urls = {
            "pages": f"{GITHUB_RAW_BASE}/doc/remote-ui.md",
            "widgets": f"{GITHUB_RAW_BASE}/doc/remote-ui.md",
            "layout": f"{GITHUB_RAW_BASE}/doc/remote-ui.md",
            "navigation": f"{GITHUB_RAW_BASE}/doc/remote-ui.md",
            "buttons": f"{GITHUB_RAW_BASE}/doc/remote-ui.md"
        }
        if topic_lower in extra_urls:
            result["topic_hint"] = f"The main remote-ui.md document covers {topic}. Review the content field above."
    
    return result


@mcp.tool()
async def get_bluetooth_hid_docs() -> dict:
    """Retrieve documentation about Bluetooth HID (Human Interface Device) peripheral support on Unfolded Circle Remote devices. Use this when you need to understand BT HID profiles, pairing, or using the Remote as a Bluetooth peripheral."""
    
    readme_url = f"{GITHUB_RAW_BASE}/doc/bt/README.md"
    readme_content = await fetch_url(readme_url)
    
    # Try to fetch additional BT docs if they exist
    additional_urls = [
        f"{GITHUB_RAW_BASE}/doc/bt/bluetooth-hid.md",
        f"{GITHUB_RAW_BASE}/doc/bt/bt-hid.md"
    ]
    
    additional_content = {}
    for url in additional_urls:
        content = await fetch_url(url)
        if not content.startswith("Error"):
            additional_content[url] = content
    
    result = {
        "api_name": "Bluetooth HID Peripheral Support",
        "readme_url": readme_url,
        "content": readme_content
    }
    
    if additional_content:
        result["additional_docs"] = additional_content
    
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
