from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
import json
from typing import Optional

mcp = FastMCP("unfolded-circle-core-apis")

BASE_RAW_URL = "https://raw.githubusercontent.com/unfoldedcircle/core-api/main"
BASE_GITHUB_URL = "https://github.com/unfoldedcircle/core-api"
BASE_PAGES_URL = "https://unfoldedcircle.github.io/core-api"

API_RESOURCES = {
    "rest_openapi": f"{BASE_RAW_URL}/core-api/rest/UCR-core-openapi.yaml",
    "integration_readme": f"{BASE_RAW_URL}/integration-api/README.md",
    "core_websocket_readme": f"{BASE_RAW_URL}/core-api/websocket/README.md",
    "dock_api_readme": f"{BASE_RAW_URL}/dock-api/README.md",
    "entities_readme": f"{BASE_RAW_URL}/doc/entities/README.md",
    "write_integration_driver": f"{BASE_RAW_URL}/doc/integration-driver/write-integration-driver.md",
    "websocket_handling": f"{BASE_RAW_URL}/doc/integration-driver/websocket.md",
    "remote_ui": f"{BASE_RAW_URL}/doc/remote-ui.md",
    "bluetooth_readme": f"{BASE_RAW_URL}/doc/bt/README.md",
    "main_readme": f"{BASE_RAW_URL}/README.md",
    "rest_readme": f"{BASE_RAW_URL}/core-api/rest/README.md",
}

ENTITY_TYPES = {
    "light": f"{BASE_RAW_URL}/doc/entities/entity_light.md",
    "media_player": f"{BASE_RAW_URL}/doc/entities/entity_media_player.md",
    "sensor": f"{BASE_RAW_URL}/doc/entities/entity_sensor.md",
    "switch": f"{BASE_RAW_URL}/doc/entities/entity_switch.md",
    "button": f"{BASE_RAW_URL}/doc/entities/entity_button.md",
    "climate": f"{BASE_RAW_URL}/doc/entities/entity_climate.md",
    "cover": f"{BASE_RAW_URL}/doc/entities/entity_cover.md",
    "remote": f"{BASE_RAW_URL}/doc/entities/entity_remote.md",
    "activity": f"{BASE_RAW_URL}/doc/entities/entity_activity.md",
}


async def fetch_url(url: str) -> str:
    """Fetch content from a URL with error handling."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


@mcp.tool()
async def get_api_overview() -> dict:
    """Retrieve a high-level overview of the Unfolded Circle Core APIs, including available API types (REST, WebSocket, AsyncAPI), their purposes, and links to documentation."""
    _track("get_api_overview")
    try:
        content = await fetch_url(API_RESOURCES["main_readme"])
        return {
            "success": True,
            "source": f"{BASE_GITHUB_URL}/blob/main/README.md",
            "developer_guide": BASE_PAGES_URL,
            "api_types": {
                "REST Core-API": {
                    "description": "OpenAPI-defined REST API for controlling and configuring Remote Two devices",
                    "spec_url": f"{BASE_RAW_URL}/core-api/rest/UCR-core-openapi.yaml",
                    "docs_url": f"{BASE_GITHUB_URL}/tree/main/core-api/rest"
                },
                "WebSocket Core-API": {
                    "description": "AsyncAPI-defined WebSocket API for real-time communication with Remote Two",
                    "docs_url": f"{BASE_GITHUB_URL}/tree/main/core-api/websocket"
                },
                "WebSocket Integration-API": {
                    "description": "AsyncAPI-defined WebSocket API for writing device integrations/drivers",
                    "docs_url": f"{BASE_GITHUB_URL}/tree/main/integration-api"
                },
                "WebSocket Dock-API": {
                    "description": "AsyncAPI-defined WebSocket API for the Unfolded Circle Dock device",
                    "docs_url": f"{BASE_GITHUB_URL}/tree/main/dock-api"
                }
            },
            "integration_resources": {
                "entities": f"{BASE_GITHUB_URL}/tree/main/doc/entities",
                "write_integration_driver": f"{BASE_RAW_URL}/doc/integration-driver/write-integration-driver.md",
                "websocket_handling": f"{BASE_RAW_URL}/doc/integration-driver/websocket.md"
            },
            "content": content
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"Failed to fetch overview: {str(e)}",
            "fallback_info": {
                "github_repo": BASE_GITHUB_URL,
                "developer_guide": BASE_PAGES_URL,
                "swagger_ui": f"https://unfoldedcircle.github.io/core-api/rest/"
            }
        }


@mcp.tool()
async def get_rest_api_spec(format: Optional[str] = "yaml") -> dict:
    """Fetch the full OpenAPI specification (UCR-core-openapi.yaml) for the Unfolded Circle REST Core-API."""
    _track("get_rest_api_spec")
    try:
        yaml_content = await fetch_url(API_RESOURCES["rest_openapi"])
        readme_content = await fetch_url(API_RESOURCES["rest_readme"])

        result = {
            "success": True,
            "source_url": API_RESOURCES["rest_openapi"],
            "swagger_ui": "https://unfoldedcircle.github.io/core-api/rest/",
            "format": format or "yaml",
            "readme": readme_content,
        }

        if format and format.lower() == "json":
            try:
                import yaml as yaml_lib
                parsed = yaml_lib.safe_load(yaml_content)
                result["spec"] = parsed
                result["note"] = "Spec returned as parsed Python dict (JSON-compatible)"
            except ImportError:
                result["spec"] = yaml_content
                result["note"] = "PyYAML not available, returning raw YAML. Install pyyaml for JSON conversion."
        else:
            result["spec"] = yaml_content

        return result
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"Failed to fetch REST API spec: {str(e)}",
            "spec_url": API_RESOURCES["rest_openapi"],
            "swagger_ui": "https://unfoldedcircle.github.io/core-api/rest/"
        }


@mcp.tool()
async def get_integration_api_docs(section: Optional[str] = None) -> dict:
    """Retrieve documentation for the WebSocket Integration-API, which allows writing device integrations for Unfolded Circle Remote devices."""
    _track("get_integration_api_docs")
    section_map = {
        "websocket": API_RESOURCES["websocket_handling"],
        "authentication": API_RESOURCES["websocket_handling"],
        "keep-alive": API_RESOURCES["websocket_handling"],
        "error-handling": API_RESOURCES["websocket_handling"],
        "write-integration-driver": API_RESOURCES["write_integration_driver"],
        "integration-driver": API_RESOURCES["write_integration_driver"],
        "getting-started": API_RESOURCES["write_integration_driver"],
        "entities": API_RESOURCES["entities_readme"],
        "overview": API_RESOURCES["integration_readme"],
    }

    urls_to_fetch = []
    section_lower = section.lower() if section else None

    if section_lower and section_lower in section_map:
        urls_to_fetch = [(section_lower, section_map[section_lower])]
    elif section_lower:
        urls_to_fetch = [("integration_readme", API_RESOURCES["integration_readme"]),
                         ("write_integration_driver", API_RESOURCES["write_integration_driver"]),
                         ("websocket_handling", API_RESOURCES["websocket_handling"])]
    else:
        urls_to_fetch = [
            ("integration_readme", API_RESOURCES["integration_readme"]),
            ("write_integration_driver", API_RESOURCES["write_integration_driver"]),
            ("websocket_handling", API_RESOURCES["websocket_handling"])
        ]

    results = {}
    errors = []
    for name, url in urls_to_fetch:
        try:
            content = await fetch_url(url)
            results[name] = {"url": url, "content": content}
        except httpx.HTTPError as e:
            errors.append({"name": name, "url": url, "error": str(e)})

    return {
        "success": len(results) > 0,
        "section_requested": section,
        "available_sections": list(section_map.keys()),
        "docs": results,
        "errors": errors if errors else None,
        "async_api_spec_location": f"{BASE_GITHUB_URL}/tree/main/integration-api",
        "architecture_note": "The integration driver acts as server, and the Remote device acts as client. The Remote connects to the integration when configured."
    }


@mcp.tool()
async def get_entity_docs(entity_type: Optional[str] = None) -> dict:
    """Retrieve documentation about Remote Two entities supported by integration drivers, such as lights, media players, sensors, and other controllable devices."""
    _track("get_entity_docs")
    results = {}
    errors = []

    if entity_type:
        entity_lower = entity_type.lower().replace("-", "_")
        if entity_lower in ENTITY_TYPES:
            try:
                content = await fetch_url(ENTITY_TYPES[entity_lower])
                results[entity_lower] = {"url": ENTITY_TYPES[entity_lower], "content": content}
            except httpx.HTTPError as e:
                errors.append({"entity_type": entity_lower, "url": ENTITY_TYPES[entity_lower], "error": str(e)})
        else:
            errors.append({
                "entity_type": entity_type,
                "error": f"Unknown entity type. Available types: {list(ENTITY_TYPES.keys())}"
            })
    else:
        try:
            overview = await fetch_url(API_RESOURCES["entities_readme"])
            results["overview"] = {"url": API_RESOURCES["entities_readme"], "content": overview}
        except httpx.HTTPError as e:
            errors.append({"name": "entities_readme", "error": str(e)})

    return {
        "success": len(results) > 0,
        "entity_type_requested": entity_type,
        "available_entity_types": list(ENTITY_TYPES.keys()),
        "entity_docs_base": f"{BASE_GITHUB_URL}/tree/main/doc/entities",
        "docs": results,
        "errors": errors if errors else None
    }


@mcp.tool()
async def get_websocket_api_spec(api_target: str) -> dict:
    """Fetch the AsyncAPI specification for either the WebSocket Core-API or the WebSocket Dock-API."""
    _track("get_websocket_api_spec")
    target_map = {
        "core": {
            "readme_url": API_RESOURCES["core_websocket_readme"],
            "description": "WebSocket Core-API for real-time communication with Remote Two",
            "repo_path": f"{BASE_GITHUB_URL}/tree/main/core-api/websocket",
            "asyncapi_spec": f"{BASE_RAW_URL}/core-api/websocket/UCR-core-asyncapi.yaml"
        },
        "integration": {
            "readme_url": API_RESOURCES["integration_readme"],
            "description": "WebSocket Integration-API for writing device integrations",
            "repo_path": f"{BASE_GITHUB_URL}/tree/main/integration-api",
            "asyncapi_spec": f"{BASE_RAW_URL}/integration-api/UCR-integration-asyncapi.yaml"
        },
        "dock": {
            "readme_url": API_RESOURCES["dock_api_readme"],
            "description": "WebSocket Dock-API for the Unfolded Circle Dock device",
            "repo_path": f"{BASE_GITHUB_URL}/tree/main/dock-api",
            "asyncapi_spec": f"{BASE_RAW_URL}/dock-api/UCR-dock-asyncapi.yaml"
        }
    }

    target_lower = api_target.lower() if api_target else ""
    if target_lower not in target_map:
        return {
            "success": False,
            "error": f"Unknown api_target '{api_target}'. Must be one of: {list(target_map.keys())}",
            "available_targets": list(target_map.keys())
        }

    target_info = target_map[target_lower]
    results = {}
    errors = []

    for resource_name, url in [("readme", target_info["readme_url"]), ("asyncapi_spec", target_info["asyncapi_spec"])]:
        try:
            content = await fetch_url(url)
            results[resource_name] = {"url": url, "content": content}
        except httpx.HTTPError as e:
            errors.append({"resource": resource_name, "url": url, "error": str(e)})

    return {
        "success": len(results) > 0,
        "api_target": api_target,
        "description": target_info["description"],
        "repo_path": target_info["repo_path"],
        "docs": results,
        "errors": errors if errors else None
    }


@mcp.tool()
async def search_api_docs(query: str, scope: Optional[str] = "all") -> dict:
    """Search across all Unfolded Circle API documentation and specifications for a specific term, endpoint, message type, or concept."""
    _track("search_api_docs")
    if not query:
        return {"success": False, "error": "Query parameter is required"}

    scope_lower = (scope or "all").lower()

    scope_resources = {
        "rest": {
            "REST OpenAPI Spec": API_RESOURCES["rest_openapi"],
            "REST README": API_RESOURCES["rest_readme"],
        },
        "websocket": {
            "Core WebSocket README": API_RESOURCES["core_websocket_readme"],
            "Integration API README": API_RESOURCES["integration_readme"],
            "Dock API README": API_RESOURCES["dock_api_readme"],
            "WebSocket Handling Docs": API_RESOURCES["websocket_handling"],
        },
        "docs": {
            "Main README": API_RESOURCES["main_readme"],
            "Write Integration Driver": API_RESOURCES["write_integration_driver"],
            "Entities README": API_RESOURCES["entities_readme"],
            "Remote UI Docs": API_RESOURCES["remote_ui"],
            "Bluetooth README": API_RESOURCES["bluetooth_readme"],
        }
    }

    if scope_lower == "all":
        resources_to_search = {}
        for s in scope_resources.values():
            resources_to_search.update(s)
    elif scope_lower in scope_resources:
        resources_to_search = scope_resources[scope_lower]
    else:
        return {
            "success": False,
            "error": f"Unknown scope '{scope}'. Must be one of: all, rest, websocket, docs"
        }

    query_lower = query.lower()
    search_results = []
    fetch_errors = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for resource_name, url in resources_to_search.items():
            try:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text
                if query_lower in content.lower():
                    lines = content.split("\n")
                    matching_lines = []
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            start = max(0, i - 1)
                            end = min(len(lines), i + 3)
                            context = "\n".join(lines[start:end])
                            matching_lines.append({
                                "line_number": i + 1,
                                "context": context
                            })
                        if len(matching_lines) >= 10:
                            break
                    search_results.append({
                        "resource": resource_name,
                        "url": url,
                        "match_count": content.lower().count(query_lower),
                        "matches": matching_lines
                    })
            except httpx.HTTPError as e:
                fetch_errors.append({"resource": resource_name, "url": url, "error": str(e)})

    search_results.sort(key=lambda x: x["match_count"], reverse=True)

    return {
        "success": True,
        "query": query,
        "scope": scope_lower,
        "total_resources_searched": len(resources_to_search),
        "resources_with_matches": len(search_results),
        "results": search_results,
        "fetch_errors": fetch_errors if fetch_errors else None
    }


@mcp.tool()
async def get_developer_guide(topic: Optional[str] = None) -> dict:
    """Retrieve sections from the Unfolded Circle Developer Guide, which covers remote UI, Bluetooth HID peripheral support, and integration driver tutorials."""
    _track("get_developer_guide")
    topic_map = {
        "remote-ui": {
            "url": API_RESOURCES["remote_ui"],
            "description": "Remote Two user interface documentation"
        },
        "remote_ui": {
            "url": API_RESOURCES["remote_ui"],
            "description": "Remote Two user interface documentation"
        },
        "bluetooth": {
            "url": API_RESOURCES["bluetooth_readme"],
            "description": "Bluetooth HID peripheral support documentation"
        },
        "bt": {
            "url": API_RESOURCES["bluetooth_readme"],
            "description": "Bluetooth HID peripheral support documentation"
        },
        "integration-driver": {
            "url": API_RESOURCES["write_integration_driver"],
            "description": "How to write an integration driver"
        },
        "write-integration-driver": {
            "url": API_RESOURCES["write_integration_driver"],
            "description": "How to write an integration driver"
        },
        "getting-started": {
            "url": API_RESOURCES["write_integration_driver"],
            "description": "Getting started with integration driver development"
        },
        "websocket": {
            "url": API_RESOURCES["websocket_handling"],
            "description": "WebSocket handling: authentication, keep-alive, error handling"
        },
        "authentication": {
            "url": API_RESOURCES["websocket_handling"],
            "description": "Authentication documentation"
        },
        "entities": {
            "url": API_RESOURCES["entities_readme"],
            "description": "Remote Two entity types and documentation"
        },
        "overview": {
            "url": API_RESOURCES["main_readme"],
            "description": "Top-level overview of all Unfolded Circle APIs"
        }
    }

    results = {}
    errors = []

    if topic:
        topic_lower = topic.lower().replace("_", "-")
        matched_key = None
        for key in topic_map:
            if topic_lower in key or key in topic_lower:
                matched_key = key
                break
        if not matched_key:
            matched_key = topic_lower if topic_lower in topic_map else None

        if matched_key and matched_key in topic_map:
            topic_info = topic_map[matched_key]
            try:
                content = await fetch_url(topic_info["url"])
                results[matched_key] = {
                    "url": topic_info["url"],
                    "description": topic_info["description"],
                    "content": content
                }
            except httpx.HTTPError as e:
                errors.append({"topic": matched_key, "url": topic_info["url"], "error": str(e)})
        else:
            errors.append({
                "topic": topic,
                "error": f"Topic not found. Available topics: {list(set(topic_map.keys()))}"
            })
    else:
        fetch_urls = [
            ("main_readme", API_RESOURCES["main_readme"], "Top-level overview of all Unfolded Circle APIs"),
            ("remote_ui", API_RESOURCES["remote_ui"], "Remote Two user interface documentation"),
        ]
        for name, url, description in fetch_urls:
            try:
                content = await fetch_url(url)
                results[name] = {"url": url, "description": description, "content": content}
            except httpx.HTTPError as e:
                errors.append({"name": name, "url": url, "error": str(e)})

    return {
        "success": len(results) > 0,
        "topic_requested": topic,
        "available_topics": list(set(topic_map.keys())),
        "developer_guide_url": BASE_PAGES_URL,
        "github_repo": BASE_GITHUB_URL,
        "docs": results,
        "errors": errors if errors else None
    }




_SERVER_SLUG = "unfoldedcircle-core-api"
_REQUIRES_AUTH = False

def _get_api_key() -> str:
    """Get API key from environment. Clients pass keys via MCP config headers."""
    return os.environ.get("API_KEY", "")

def _auth_headers() -> dict:
    """Build authorization headers for upstream API calls."""
    key = _get_api_key()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}", "X-API-Key": key}

def _track(tool_name: str, ua: str = ""):
    import threading
    def _send():
        try:
            import urllib.request, json as _json
            data = _json.dumps({"slug": _SERVER_SLUG, "event": "tool_call", "tool": tool_name, "user_agent": ua}).encode()
            req = urllib.request.Request("https://www.volspan.dev/api/analytics/event", data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

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
