from dataclasses import dataclass, field


@dataclass
class SearchIndex:
    index_name: str
    api_path: str
    facets: set[str]
    boolean_fields: set[str] | None = field(default_factory=set)
    needed_scopes: set = field(default_factory=set)


INDEX_MAPPING = {
    "bag": SearchIndex(
        index_name="benkagg_adresseerbareobjecten",
        api_path="benkagg/adresseerbareobjecten",
        facets={
            "woonplaatsNaam",
            "gebiedenStadsdeelNaam",
            "gebiedenGgwgebiedNaam",
            "gebiedenWijkNaam",
            "gebiedenBuurtNaam",
            "openbareruimteNaam",
            "postcode",
        },
    ),
    "brk": SearchIndex(
        index_name="benkagg_brkbasisdataselectie",
        api_path="benkagg/brkbasisdataselectie",
        facets={
            "grondeigenaar",
            "pandeigenaar",
            "appartementseigenaar",
            "subjectCategorie",
            "stadsdeelNaam",
            "ggwNaam",
            "wijkNaam",
            "buurtNaam",
        },
        boolean_fields={
            "grondeigenaar",
            "pandeigenaar",
            "appartementseigenaar",
        },
        needed_scopes={"BRK/RSN"},
    ),
    "hr": SearchIndex(
        index_name="benkagg_handelsregisterkvk",
        api_path="benkagg/handelsregisterkvk",
        facets={
            "bagOpenbareruimteNaam",
            "bagPostcode",
            "bijzondereRechtstoestandPersoon",
            "gebiedenBuurtNaam",
            "gebiedenGgwgebiedNaam",
            "gebiedenStadsdeelNaam",
            "gebiedenWijkNaam",
        },
        needed_scopes={"FP/MDW"},
    ),
}
