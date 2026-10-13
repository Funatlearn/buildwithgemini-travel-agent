# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback


from app.tools import (
    find_nearby_places,
    geocode_address,
    generate_travel_image,
    search_destinations,
)


MODEL = "gemini-3.6-flash"


def get_weather(query: str) -> str:
    """Fetch real-time weather information for any city or destination using Open-Meteo public API.

    Args:
        query: The city or destination name (e.g. 'Kyoto', 'Cape Town', 'Paris').

    Returns:
        A string with real-time weather, temperature, humidity, and wind conditions.
    """
    import json
    import urllib.parse
    import urllib.request

    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(query)}&count=1&language=en&format=json"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "TravelAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode())

        results = geo_data.get("results")
        if not results:
            return f"Could not find coordinates for location: {query}."

        place = results[0]
        lat, lon = place["latitude"], place["longitude"]
        place_name = f"{place.get('name')}, {place.get('country', '')}"

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        )
        req2 = urllib.request.Request(weather_url, headers={"User-Agent": "TravelAgent/1.0"})
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            weather_data = json.loads(resp2.read().decode())

        current = weather_data.get("current", {})
        temp_c = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")

        return (
            f"Current weather in {place_name}: {temp_c}°C, "
            f"Relative Humidity: {humidity}%, Wind Speed: {wind} km/h."
        )
    except Exception as e:
        return f"Unable to fetch live weather for '{query}': {str(e)}"


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Load Agent Engine sandbox metadata if present
_agent_engine_resource_name = None
_metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "deployment_metadata.json")
if os.path.exists(_metadata_path):
    try:
        with open(_metadata_path, "r") as f:
            _meta = json.load(f)
            _agent_engine_resource_name = _meta.get("agent_engine_resource_name")
    except Exception:
        pass

code_executor = (
    AgentEngineSandboxCodeExecutor(agent_engine_resource_name=_agent_engine_resource_name)
    if _agent_engine_resource_name
    else AgentEngineSandboxCodeExecutor()
)

# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


try:
    from a2ui.basic_catalog.provider import BasicCatalog
    from a2ui.schema.manager import A2uiSchemaManager

    schema_manager = A2uiSchemaManager(
        version="0.8",
        catalogs=[BasicCatalog.get_config("0.8")],
    )

    instruction = schema_manager.generate_system_prompt(
        role_description=(
            "You are an expert travel assistant that helps users discover destinations, "
            "explore attractions, and plan trips. You remember the user's travel preferences, "
            "budget constraints, and past experiences across sessions. Crucially, always remember, "
            "track, and strictly respect all user allergies, food intolerances, and dietary restrictions "
            "in every recommendation and itinerary planning turn. "
            "You have tools to search the destination catalog (search_destinations), "
            "check live weather (get_weather), look up coordinates for any location (geocode_address), "
            "find nearby places like restaurants, attractions, or hotels (find_nearby_places), "
            "and generate scenic travel postcards or photographs (generate_travel_image). "
            "You also have a safe Python code execution sandbox to perform precise trip calculations, "
            "currency conversions, and budget estimates."
        ),
        workflow_description="Analyze the request and return structured UI when appropriate.",
        ui_description=(
            "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
            "Never nest a Card inside a Card. "
            "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
            "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
            "nothing in adk web). "
            "You may include one Image component, but only when you have a public https "
            "URL for the image (for example the URL an image tool returns after uploading "
            "to a public bucket). Set the Image url to that exact https link, for example "
            "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
            "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
            "not have a public URL, add a short Text line noting the image instead. "
            "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
            "headings and emphasis. "
            "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
            "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
        ),
        include_schema=True,
        include_examples=True,
    )
except Exception:
    from app.a2ui_instruction import INSTRUCTION as instruction

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        search_destinations,
        get_weather,
        get_current_time,
        geocode_address,
        find_nearby_places,
        generate_travel_image,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
