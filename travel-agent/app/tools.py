"""Firestore database tools for travel-agent."""

from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-d9aebf9c9790"

_db: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded project ID string."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def search_destinations(query: str = "", tag: str = "") -> List[Dict[str, Any]]:
    """Search or list travel destinations by keyword or tag.

    Args:
        query: Optional search keyword to filter by name, country, or description.
        tag: Optional category tag (e.g. 'culture', 'adventure', 'food', 'nature').

    Returns:
        A list of matching destination records.
    """
    db = get_db()
    docs = db.collection("destinations").stream()
    results = []

    q_lower = query.lower().strip()
    tag_lower = tag.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if tag_lower:
            item_tags = [t.lower() for t in data.get("tags", [])]
            if tag_lower not in item_tags:
                continue

        if q_lower:
            text_blob = f"{data.get('name', '')} {data.get('country', '')} {data.get('description', '')}".lower()
            if q_lower not in text_blob:
                continue

        results.append(data)

    return results


def get_destination_details(destination_id: str) -> Dict[str, Any]:
    """Retrieve detailed information for a specific destination by its ID.

    Args:
        destination_id: The ID of the destination (e.g. 'kyoto-japan', 'interlaken-switzerland').

    Returns:
        The destination record dictionary, or an error message if not found.
    """
    db = get_db()
    doc = db.collection("destinations").document(destination_id).get()
    if not doc.exists:
        return {"error": f"Destination '{destination_id}' not found."}
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def search_accommodations(destination_id: str = "", max_price_usd: float = 0.0) -> List[Dict[str, Any]]:
    """Search accommodations for a destination with optional budget filter.

    Args:
        destination_id: The destination ID to filter stays for (e.g. 'kyoto-japan').
        max_price_usd: Optional maximum price per night in USD (0 for no limit).

    Returns:
        A list of matching accommodation records.
    """
    db = get_db()
    query = db.collection("accommodations")
    if destination_id:
        query = query.where(filter=firestore.FieldFilter("destination_id", "==", destination_id))

    docs = query.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if max_price_usd > 0 and data.get("price_per_night_usd", 0) > max_price_usd:
            continue
        results.append(data)

    return results


def save_itinerary_item(
    destination_name: str,
    day_number: int,
    activity_title: str,
    notes: str = "",
    estimated_cost_usd: float = 0.0,
) -> Dict[str, Any]:
    """Save or plan an itinerary item/activity into the user's travel itinerary.

    Args:
        destination_name: Name of the destination (e.g. 'Kyoto').
        day_number: Day index of the trip (e.g. 1, 2, 3).
        activity_title: Description or title of the planned activity.
        notes: Optional extra notes, tips, or location info.
        estimated_cost_usd: Optional estimated cost for the activity in USD.

    Returns:
        Confirmation dictionary with the saved itinerary record details and ID.
    """
    db = get_db()
    record = {
        "destination_name": destination_name,
        "day_number": day_number,
        "activity_title": activity_title,
        "notes": notes,
        "estimated_cost_usd": estimated_cost_usd,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    update_time, doc_ref = db.collection("itineraries").add(record)
    return {
        "status": "success",
        "itinerary_id": doc_ref.id,
        "message": f"Successfully added Day {day_number} activity '{activity_title}' for {destination_name}.",
    }


def list_itinerary() -> List[Dict[str, Any]]:
    """List all saved itinerary items in the user's current travel plan.

    Returns:
        List of saved itinerary activities.
    """
    db = get_db()
    docs = db.collection("itineraries").stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        # Convert timestamp to ISO string if present
        if "created_at" in data and data["created_at"]:
            data["created_at"] = str(data["created_at"])
        results.append(data)

    results.sort(key=lambda x: x.get("day_number", 0))
    return results


# --- Google Maps Platform Tools ---

def geocode_address(address: str) -> Dict[str, Any]:
    """Convert an address or place name into geographic coordinates (latitude and longitude).

    Args:
        address: The street address, city, or location name to geocode (e.g. 'Kyoto Station', 'Eiffel Tower').

    Returns:
        A dictionary with the formatted address, latitude, and longitude.
    """
    import os
    import json
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") != "OK" or not data.get("results"):
            return {
                "error": f"Geocoding failed: {data.get('status')} - {data.get('error_message', 'No results found.')}"
            }

        first_res = data["results"][0]
        location = first_res["geometry"]["location"]
        return {
            "name": address,
            "address": first_res.get("formatted_address"),
            "location": {
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
            },
        }
    except Exception as e:
        return {"error": f"Failed to call Geocoding API: {str(e)}"}


def find_nearby_places(latitude: float, longitude: float, place_type: str = "restaurant", radius_meters: float = 1000.0) -> List[Dict[str, Any]]:
    """Find nearby places (e.g. restaurants, tourist attractions, lodging) using Places API (New).

    Args:
        latitude: The center latitude coordinate.
        longitude: The center longitude coordinate.
        place_type: Type of place to search for (e.g. 'tourist_attraction', 'restaurant', 'cafe', 'museum', 'lodging').
        radius_meters: Search radius in meters (default 1000.0, max 50000.0).

    Returns:
        A list of nearby places with name, address, and location coordinates.
    """
    import os
    import json
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}]

    endpoint = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        places = data.get("places", [])
        results = []
        for p in places:
            display_name = p.get("displayName", {}).get("text", "")
            address = p.get("formattedAddress", "")
            loc = p.get("location", {})
            results.append({
                "name": display_name,
                "address": address,
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                },
            })

        return results
    except Exception as e:
        return [{"error": f"Failed to call Places API (New): {str(e)}"}]


# --- Image Generation Tool ---

BUCKET_NAME = "travel-agent-media-qwiklabs-gcp-03-d9aebf9c9790"


def generate_travel_image(prompt: str, tool_context: Any = None) -> Dict[str, Any]:
    """Generate a scenic travel photograph or postcard for a destination, landmark, or activity.

    Uses the gemini-3.1-flash-lite-image model, saves the image as an ADK artifact,
    and uploads it to public Cloud Storage.

    Args:
        prompt: A descriptive prompt for the image (e.g. 'Golden hour sunset over Kyoto bamboo forest').
        tool_context: ToolContext injected automatically by ADK at runtime.

    Returns:
        A dictionary containing the public Cloud Storage image URL, filename, and status.
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        image_bytes = None
        mime_type = "image/jpeg"

        candidates = getattr(response, "candidates", [])
        if candidates and candidates[0].content and candidates[0].content.parts:
            for part in candidates[0].content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    image_bytes = inline.data
                    mime_type = inline.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return {"error": "Model did not return any image data for the given prompt."}

        # 1. Save artifact with tool_context if available (appears in Playground Artifacts panel)
        filename = f"postcard_{uuid.uuid4().hex[:8]}.jpg"
        if tool_context and hasattr(tool_context, "save_artifact"):
            try:
                artifact_part = types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=image_bytes,
                    )
                )
                tool_context.save_artifact(filename=filename, artifact=artifact_part)
            except Exception as e:
                # Non-fatal if context saving fails outside an active ADK run
                pass

        # 2. Upload image bytes directly to the public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return {
            "status": "success",
            "image_url": public_url,
            "filename": filename,
            "prompt": prompt,
        }
    except Exception as e:
        return {"error": f"Failed to generate or upload image: {str(e)}"}
