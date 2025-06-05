from dataclasses import dataclass, field


@dataclass
class SearchIndex:
    index_name: str
    api_path: str
    facets: set[str]
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
            "buurtNaamTabel",
        },
        needed_scopes={"brk"},
    ),
}
