"""Seed Firestore with initial destinations and accommodations for travel-agent."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-d9aebf9c9790"

DESTINATIONS = [
    {
        "id": "kyoto-japan",
        "name": "Kyoto, Japan",
        "country": "Japan",
        "description": "Historic temples, sublime gardens, traditional teahouses, and serene bamboo groves.",
        "best_season": "Spring (Cherry Blossoms) or Autumn (Foliage)",
        "budget_level": "moderate-to-high",
        "tags": ["culture", "history", "temples", "food", "relaxation"],
        "top_attractions": [
            "Fushimi Inari Shrine",
            "Kinkaku-ji (Golden Pavilion)",
            "Arashiyama Bamboo Grove",
            "Gion Geisha District"
        ],
    },
    {
        "id": "interlaken-switzerland",
        "name": "Interlaken, Switzerland",
        "country": "Switzerland",
        "description": "Adventure capital nestled between Lake Thun and Lake Brienz, surrounded by Alpine peaks.",
        "best_season": "Summer (Hiking) or Winter (Skiing)",
        "budget_level": "high",
        "tags": ["mountains", "adventure", "hiking", "nature", "lakes"],
        "top_attractions": [
            "Jungfraujoch - Top of Europe",
            "Harder Kulm Panorama",
            "Lake Brienz Cruise",
            "Lauterbrunnen Valley"
        ],
    },
    {
        "id": "oaxaca-mexico",
        "name": "Oaxaca, Mexico",
        "country": "Mexico",
        "description": "Culinary wonderland renowned for mole, mezcal, artisan markets, and indigenous culture.",
        "best_season": "October to April (Dry Season, Day of the Dead)",
        "budget_level": "budget-to-moderate",
        "tags": ["food", "culinary", "art", "culture", "markets"],
        "top_attractions": [
            "Monte Albán Zapotec Ruins",
            "Hierve el Agua petrified waterfalls",
            "Mercado 20 de Noviembre",
            "Santo Domingo Church"
        ],
    },
    {
        "id": "cape-town-south-africa",
        "name": "Cape Town, South Africa",
        "country": "South Africa",
        "description": "Dramatic coastal scenery where Table Mountain meets the Atlantic, wine valleys, and penguins.",
        "best_season": "November to March (Summer)",
        "budget_level": "moderate",
        "tags": ["beaches", "mountains", "wildlife", "wine", "adventure"],
        "top_attractions": [
            "Table Mountain Cableway",
            "Boulders Beach Penguin Colony",
            "Cape Point Nature Reserve",
            "Kirstenbosch Botanical Gardens"
        ],
    },
]

ACCOMMODATIONS = [
    {
        "id": "ryokan-gion-matsu",
        "destination_id": "kyoto-japan",
        "name": "Gion Matsu Ryokan",
        "type": "Traditional Ryokan",
        "price_per_night_usd": 240,
        "rating": 4.9,
        "amenities": ["Kaiseki Dinner", "Private Onsen", "Garden View", "Tatami Rooms"],
    },
    {
        "id": "alpine-lake-lodge",
        "destination_id": "interlaken-switzerland",
        "name": "Alpine Heights Chalet & Spa",
        "type": "Boutique Alpine Hotel",
        "price_per_night_usd": 380,
        "rating": 4.8,
        "amenities": ["Mountain View Balcony", "Sauna", "Breakfast Buffet", "Ski Shuttle"],
    },
    {
        "id": "casa-de-barro-oaxaca",
        "destination_id": "oaxaca-mexico",
        "name": "Casa de Barro Heritage Hotel",
        "type": "Colonial Boutique Hotel",
        "price_per_night_usd": 110,
        "rating": 4.85,
        "amenities": ["Courtyard Garden", "Rooftop Mezcal Bar", "Artisanal Breakfast", "Walk to Zocalo"],
    },
]


def seed():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore with project '{PROJECT_ID}'...")

    for dest in DESTINATIONS:
        doc_ref = db.collection("destinations").document(dest["id"])
        doc_ref.set(dest)
        print(f"Seeded destination: {dest['name']}")

    for acc in ACCOMMODATIONS:
        doc_ref = db.collection("accommodations").document(acc["id"])
        doc_ref.set(acc)
        print(f"Seeded accommodation: {acc['name']}")

    print("Firestore seeding complete!")


if __name__ == "__main__":
    seed()
