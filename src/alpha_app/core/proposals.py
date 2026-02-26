from __future__ import annotations

from datetime import date, datetime, timedelta

from alpha_app.config import MUNICIPALITY_NAME
from alpha_app.domain.models import Proposal, ProposalLink


def _polygon(area: str, services: list[str], coords: list[list[float]]) -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {"area": area, "services": services},
        "geometry": {"type": "Polygon", "coordinates": [coords]},
    }


DETH_POLYGONS = {
    "type": "FeatureCollection",
    "features": [
        _polygon(
            "ΧΑΝΘ - ΔΕΘ",
            ["traffic", "electricity", "water"],
            [[22.9468, 40.6237], [22.9558, 40.6237], [22.9558, 40.6288], [22.9468, 40.6288], [22.9468, 40.6237]],
        ),
        _polygon(
            "Σιντριβάνι",
            ["traffic", "waste"],
            [[22.9520, 40.6282], [22.9580, 40.6282], [22.9580, 40.6316], [22.9520, 40.6316], [22.9520, 40.6282]],
        ),
    ],
}

NIKIS_POLYGONS = {
    "type": "FeatureCollection",
    "features": [
        _polygon(
            "Λεωφόρος Νίκης - Λευκός Πύργος",
            ["traffic", "electricity", "waste"],
            [[22.9418, 40.6260], [22.9543, 40.6260], [22.9543, 40.6310], [22.9418, 40.6310], [22.9418, 40.6260]],
        ),
        _polygon(
            "Παραλιακό μέτωπο (κεντρικό τμήμα)",
            ["water", "traffic"],
            [[22.9330, 40.6236], [22.9460, 40.6236], [22.9460, 40.6279], [22.9330, 40.6279], [22.9330, 40.6236]],
        ),
    ],
}

METRO_WEST_POLYGONS = {
    "type": "FeatureCollection",
    "features": [
        _polygon(
            "Μενεμένη - Κορδελιό",
            ["traffic", "water", "electricity"],
            [[22.8875, 40.6485], [22.9130, 40.6485], [22.9130, 40.6630], [22.8875, 40.6630], [22.8875, 40.6485]],
        ),
        _polygon(
            "Σταυρούπολη",
            ["traffic", "telecom", "waste"],
            [[22.9150, 40.6535], [22.9380, 40.6535], [22.9380, 40.6680], [22.9150, 40.6680], [22.9150, 40.6535]],
        ),
    ],
}


PROPOSALS: list[Proposal] = [
    Proposal(
        proposal_id="deth_park",
        title="Πάρκο στη ΔΕΘ",
        municipality=MUNICIPALITY_NAME,
        short_description="Μετατροπή μεγάλου μέρους της ΔΕΘ σε μητροπολιτικό πάρκο.",
        long_description=(
            "Ανάπλαση του εκθεσιακού χώρου με ενίσχυση πρασίνου, δημόσιους χώρους και "
            "βελτιωμένη περιβαλλοντική ποιότητα στο κέντρο."
        ),
        image_url="https://commons.wikimedia.org/wiki/Special:FilePath/OTE%20Tower%20square.jpg",
        status="planned",
        start_date=date(2027, 3, 1),
        end_date=date(2030, 12, 31),
        budget_eur=185_000_000,
        affected_areas=["ΧΑΝΘ", "Σιντριβάνι", "Τούμπα (κυκλοφοριακές επιδράσεις)"],
        affected_services=["traffic", "water", "electricity", "waste"],
        links=[
            ProposalLink("Context Source (GTP)", "https://www.gtp.gr/TDirectoryDetails.asp?ID=78842"),
            ProposalLink("Wikimedia Image", "https://commons.wikimedia.org/wiki/Special:FilePath/OTE%20Tower%20square.jpg"),
        ],
        map_polygon_geojson=DETH_POLYGONS,
    ),
    Proposal(
        proposal_id="nikis_pedestrian",
        title="Πεζοδρόμηση Λεωφόρου Νίκης (Παραλίας)",
        municipality=MUNICIPALITY_NAME,
        short_description="Σταδιακή πεζοδρόμηση με ανασχεδιασμό κινητικότητας.",
        long_description=(
            "Προτεραιότητα στους πεζούς και στον δημόσιο χώρο με παράλληλο σχεδιασμό για "
            "κυκλοφορία, τροφοδοσία και δημόσιες συγκοινωνίες."
        ),
        image_url="https://commons.wikimedia.org/wiki/Special:FilePath/Salonica%20White%20Tower.jpg",
        status="active",
        start_date=date(2026, 9, 1),
        end_date=date(2028, 6, 30),
        budget_eur=42_000_000,
        affected_areas=["Λευκός Πύργος", "Αριστοτέλους", "Παραλιακό μέτωπο"],
        affected_services=["traffic", "electricity", "waste", "water"],
        links=[
            ProposalLink("Context Source (ered)", "https://ered.gr/real-estate-news/pilot-pezodromisi-sti-leoforo-nikis-thessalonikis"),
            ProposalLink("Wikimedia Image", "https://commons.wikimedia.org/wiki/Special:FilePath/Salonica%20White%20Tower.jpg"),
        ],
        map_polygon_geojson=NIKIS_POLYGONS,
    ),
    Proposal(
        proposal_id="metro_west",
        title="Μετρό στα Δυτικά",
        municipality=MUNICIPALITY_NAME,
        short_description="Ωρίμανση επέκτασης μετρό προς δυτικές συνοικίες.",
        long_description=(
            "Στόχος είναι η ισότιμη πρόσβαση στις μετακινήσεις για δυτικές περιοχές, "
            "με σύνδεση σε λεωφορειακό δίκτυο και κόμβους μετεπιβίβασης."
        ),
        image_url="https://commons.wikimedia.org/wiki/Special:FilePath/Venizelou%20metro%20station.jpg",
        status="delayed",
        start_date=date(2028, 1, 15),
        end_date=date(2033, 9, 30),
        budget_eur=980_000_000,
        affected_areas=["Μενεμένη", "Εύοσμος", "Σταυρούπολη"],
        affected_services=["traffic", "electricity", "telecom", "water"],
        links=[
            ProposalLink("Context Source (GTP)", "https://www.gtp.gr/TDirectoryDetails.asp?ID=78790"),
            ProposalLink("Wikimedia Image", "https://commons.wikimedia.org/wiki/Special:FilePath/Venizelou%20metro%20station.jpg"),
        ],
        map_polygon_geojson=METRO_WEST_POLYGONS,
    ),
]


_BASE = datetime(2026, 2, 20, 9, 0, 0)

SEEDED_COMMENTS: dict[str, list[dict[str, object]]] = {
    "deth_park": [
        {"author": "Μαρία", "text": "Επιτέλους περισσότερο πράσινο στο κέντρο, πολύ θετικό.", "reactions": {"likes": 19, "support": 11, "angry": 1, "laugh": 0}, "submitted_at": _BASE + timedelta(hours=2)},
        {"author": "Γιώργος", "text": "Φοβάμαι την απώλεια στάθμευσης χωρίς εναλλακτική.", "reactions": {"likes": 7, "support": 2, "angry": 6, "laugh": 0}, "submitted_at": _BASE + timedelta(hours=6)},
        {"author": "Ελένη", "text": "Καλή ιδέα αν συνοδευτεί από ασφάλεια και συντήρηση.", "reactions": {"likes": 12, "support": 6, "angry": 1, "laugh": 0}, "submitted_at": _BASE + timedelta(hours=10)},
    ],
    "nikis_pedestrian": [
        {"author": "Νίκος", "text": "Η παραλία πρέπει να δοθεί στους πεζούς, ναι στην πεζοδρόμηση.", "reactions": {"likes": 23, "support": 14, "angry": 2, "laugh": 1}, "submitted_at": _BASE + timedelta(days=1, hours=2)},
        {"author": "Αναστασία", "text": "Αν κλείσει τελείως ο δρόμος θα μπλοκάρει η κυκλοφορία.", "reactions": {"likes": 10, "support": 2, "angry": 9, "laugh": 0}, "submitted_at": _BASE + timedelta(days=1, hours=6)},
        {"author": "Θοδωρής", "text": "Συμφωνώ μόνο με ενίσχυση ΜΜΜ και καθαρές διαδρομές.", "reactions": {"likes": 15, "support": 9, "angry": 1, "laugh": 0}, "submitted_at": _BASE + timedelta(days=1, hours=10)},
    ],
    "metro_west": [
        {"author": "Δήμητρα", "text": "Τα δυτικά περιμένουν χρόνια, είναι θέμα ισότητας.", "reactions": {"likes": 28, "support": 20, "angry": 1, "laugh": 0}, "submitted_at": _BASE + timedelta(days=2, hours=1)},
        {"author": "Στέλιος", "text": "Πάλι υποσχέσεις χωρίς χρονοδιάγραμμα, δύσκολο να πιστέψω.", "reactions": {"likes": 13, "support": 1, "angry": 10, "laugh": 0}, "submitted_at": _BASE + timedelta(days=2, hours=5)},
        {"author": "Κατερίνα", "text": "Αν συνδεθεί σωστά με λεωφορεία θα αλλάξει την καθημερινότητα.", "reactions": {"likes": 17, "support": 12, "angry": 0, "laugh": 0}, "submitted_at": _BASE + timedelta(days=2, hours=9)},
    ],
}

