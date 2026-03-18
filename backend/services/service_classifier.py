"""
services/service_classifier.py — Service Type Classifier
Infers the most likely service type from a problem description.
Used by the chatbot and can be used for auto-suggestion in future.
"""

# Keyword → Service mapping
SERVICE_KEYWORDS = {
    'Plumber': [
        'pipe', 'water', 'leak', 'drain', 'tap', 'flush', 'toilet', 'plumb',
        'sink', 'sewage', 'blockage', 'faucet', 'burst', 'flood'
    ],
    'Electrician': [
        'electric', 'wire', 'power', 'light', 'switch', 'socket', 'short circuit',
        'tripped', 'breaker', 'fuse', 'current', 'voltage', 'bulb', 'wiring', 'shock'
    ],
    'Mechanic': [
        'car', 'bike', 'vehicle', 'engine', 'tyre', 'tire', 'battery', 'brake',
        'gear', 'clutch', 'fuel', 'exhaust', 'puncture', 'accelerator', 'motor'
    ],
    'AC Repair': [
        'ac', 'air condition', 'cooling', 'refrigerator', 'fridge', 'compressor',
        'gas', 'remote', 'temperature', 'thermostat', 'hvac', 'heat pump'
    ],
    'Carpenter': [
        'wood', 'door', 'window', 'furniture', 'cabinet', 'shelf', 'chair',
        'table', 'hinge', 'lock', 'frame', 'wardrobe', 'joint', 'carpenter'
    ],
    'Handyman': [
        'fix', 'repair', 'broken', 'general', 'odd job', 'help', 'install',
        'wall', 'ceiling', 'paint', 'drill', 'screw', 'nail', 'assemble'
    ],
}


def classify_service(description: str) -> str | None:
    """
    Returns the best-matching service type from a text description.
    Returns None if no match found.
    """
    text     = description.lower()
    scores   = {svc: 0 for svc in SERVICE_KEYWORDS}

    for svc, keywords in SERVICE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[svc] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def get_all_services() -> list[str]:
    """Return list of all supported service types."""
    return list(SERVICE_KEYWORDS.keys())
