"""
BioCypher Workshop 2026 — Novice Track walkthrough (Wednesday B: Croissant Metadata)
====================================================================================

Source slides:
https://ssciwr.github.io/slides-biocypher/Wednesday/B-Harmonizing-Biomedical-data-Croissant-Metadata/wednesday_b_croissant_metadata_slides.html

What this is
------------
A guided *answer key + runner* for the novice-track Croissant exercise. The
session asks you to inspect a `croissant.jsonld` metadata file, map its fields to
the adapter code, and commit the file to the repo root. The slides' example
adapter is `ProteinInteractionAdapter` — the very adapter implemented in this
repo (src/biocypher_tutorial_kg/adapters/protein_interaction_adapter.py), so
every "map metadata to code" step uses *our own* code.

This notebook is **self-contained**: it authors a reference `croissant.jsonld`
inline (accurate to THIS repo's adapter + Zenodo data source), writes it to a
notebook-local file (notebooks/_reference_croissant.jsonld), and prints the
inspection answers + the field→code mapping. It does NOT overwrite anything in
the repo root, so you can still do Step 4 by hand and diff against this reference.

How to run
----------
  - VS Code / Cursor: each "# %%" is a clickable "Run Cell" block.
  - Plain terminal:  uv run python notebooks/croissant_metadata_walkthrough.py

The slide steps map to cells below:
  Concept   What Croissant is, in one breath
  Step 1    Adapter-level metadata — inspect the top-level fields
  Step 2    Dataset-level metadata — inspect hasPart / distribution / recordSet
  Step 3    Connect metadata to code — field → adapter mapping
  Step 4    Add croissant.jsonld to the repo root + commit (documented)
  Reflect   The 5 inspection + 5 reflection questions
"""

# %%
# ---------------------------------------------------------------------------
# Setup: locate the repo root robustly, regardless of the working directory.
# ---------------------------------------------------------------------------
import json
from pathlib import Path


def find_project_root(start: Path) -> Path:
    """Walk upward until we find the repo root (has pyproject.toml)."""
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return start.parent


try:
    HERE = Path(__file__).resolve().parent           # running as a script
except NameError:
    HERE = Path.cwd()                                # running as a cell

PROJECT_ROOT = find_project_root(HERE)
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"
print("Project root:", PROJECT_ROOT)


# %%
# ===========================================================================
# Concept (slide: "What is MLCroissant?")
# ---------------------------------------------------------------------------
# Croissant (by MLCommons) is a metadata *format* for ML-ready datasets: a single
# `croissant.jsonld` file in JSON-LD using schema.org vocabulary. It describes
# what a dataset is, where its files live, and what records/fields it contains —
# WITHOUT touching the data itself. Payoff: discoverability, portability,
# interoperability, reproducibility. Three nested levels (this is the whole idea):
#
#   Adapter-level metadata   ← what the adapter is, who made it, license, keywords
#     └─ hasPart: Dataset    ← the data source(s) it consumes
#          └─ distribution   ← the actual file(s): contentUrl, format
#          └─ recordSet      ← the rows
#               └─ field      ← each column → a node id / property / edge
print(__doc__.splitlines()[1])


# %%
# ===========================================================================
# Reference croissant.jsonld for THIS repo's ProteinInteractionAdapter
# ---------------------------------------------------------------------------
# Authored to match:
#   - data source: Zenodo TSV (see create_knowledge_graph.py)
#   - node props:  genesymbol, ncbi_tax_id, entity_type  (adapter get_nodes)
#   - edge label:  the interaction `type` itself (activation/binding/inhibition/
#                  phosphorylation/ubiquitination), per schema_config.yaml
#   - edge props:  the 6 boolean flags (adapter get_edges)
# In the session you may be HANDED a file — use that one for Step 4 and treat this
# as the "what good looks like" reference for the inspection questions.

DATA_URL = "https://zenodo.org/records/16902349/files/synthetic_protein_interactions.tsv"

CROISSANT = {
    "@context": {
        "@vocab": "https://schema.org/",
        "cr": "http://mlcommons.org/croissant/",
        "data": {"@id": "cr:data", "@type": "@json"},
        "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
        "field": "cr:field",
        "fileObject": "cr:fileObject",
        "recordSet": "cr:recordSet",
        "source": "cr:source",
    },
    "@type": "cr:Dataset",
    "name": "ProteinInteractionAdapter",
    "description": (
        "BioCypher adapter that reads a synthetic OmniPath/pypath-style "
        "protein-protein interaction TSV and yields Protein nodes and typed "
        "interaction edges (activation, binding, inhibition, phosphorylation, "
        "ubiquitination) in BioCypher tuple format."
    ),
    "version": "0.1.0",
    "license": "MIT",
    "codeRepository": "https://github.com/ecarrenolozano/BCWorkshop-Tutorial-Knowledge-Graph",
    "creator": {"@type": "Person", "name": "June Sachov"},
    "keywords": [
        "protein-protein interaction",
        "BioCypher",
        "knowledge graph",
        "OmniPath",
        "UniProt",
    ],
    "hasPart": [
        {
            "@type": "cr:Dataset",
            "name": "synthetic_protein_interactions",
            "description": (
                "Synthetic interaction table. Each row is one interaction "
                "between two proteins identified by UniProt accession."
            ),
            "version": "0.1.0",
            "license": "MIT",
            "url": "https://omnipathdb.org/",
            "distribution": [
                {
                    "@type": "cr:FileObject",
                    "@id": "ppi-tsv",
                    "name": "synthetic_protein_interactions.tsv",
                    "contentUrl": DATA_URL,
                    "encodingFormat": "text/tab-separated-values",
                }
            ],
            "recordSet": [
                {
                    "@type": "cr:RecordSet",
                    "name": "interactions",
                    "description": (
                        "One record per interaction row; source/target become "
                        "Protein nodes, remaining columns become edge properties."
                    ),
                    "field": [
                        {"@type": "cr:Field", "name": "source", "dataType": "Text",
                         "description": "UniProt accession of source protein -> Protein node id."},
                        {"@type": "cr:Field", "name": "target", "dataType": "Text",
                         "description": "UniProt accession of target protein -> Protein node id."},
                        {"@type": "cr:Field", "name": "source_genesymbol", "dataType": "Text",
                         "description": "Gene symbol of source -> Protein.genesymbol."},
                        {"@type": "cr:Field", "name": "target_genesymbol", "dataType": "Text",
                         "description": "Gene symbol of target -> Protein.genesymbol."},
                        {"@type": "cr:Field", "name": "ncbi_tax_id_source", "dataType": "Text",
                         "description": "NCBI taxon id of source -> Protein.ncbi_tax_id."},
                        {"@type": "cr:Field", "name": "entity_type_source", "dataType": "Text",
                         "description": "Entity type of source -> Protein.entity_type."},
                        {"@type": "cr:Field", "name": "type", "dataType": "Text",
                         "description": "Interaction type -> EDGE LABEL (activation|binding|inhibition|phosphorylation|ubiquitination)."},
                        {"@type": "cr:Field", "name": "is_directed", "dataType": "Boolean",
                         "description": "Edge property: interaction is directed."},
                        {"@type": "cr:Field", "name": "is_stimulation", "dataType": "Boolean",
                         "description": "Edge property: interaction is stimulatory."},
                        {"@type": "cr:Field", "name": "is_inhibition", "dataType": "Boolean",
                         "description": "Edge property: interaction is inhibitory."},
                        {"@type": "cr:Field", "name": "consensus_direction", "dataType": "Boolean",
                         "description": "Edge property: consensus on direction."},
                        {"@type": "cr:Field", "name": "consensus_stimulation", "dataType": "Boolean",
                         "description": "Edge property: consensus on stimulation."},
                        {"@type": "cr:Field", "name": "consensus_inhibition", "dataType": "Boolean",
                         "description": "Edge property: consensus on inhibition."},
                    ],
                }
            ],
        }
    ],
}

REFERENCE_PATH = NOTEBOOK_DIR / "_reference_croissant.jsonld"
REFERENCE_PATH.write_text(json.dumps(CROISSANT, indent=2) + "\n", encoding="utf-8")
print("Wrote reference metadata ->", REFERENCE_PATH)


# %%
# ===========================================================================
# Step 1 — Adapter-level metadata (slide: "Open the file")
# ---------------------------------------------------------------------------
# Self-check: "Can you understand what the adapter does from this section alone?"
ADAPTER_LEVEL = ["@type", "name", "description", "version", "license",
                 "codeRepository", "creator", "keywords", "hasPart"]
print("Adapter-level fields present:")
for key in ADAPTER_LEVEL:
    present = "✓" if key in CROISSANT else "✗"
    val = CROISSANT.get(key)
    shown = "<list of datasets>" if key == "hasPart" else val
    print(f"  {present} {key:14} = {shown}")


# %%
# ===========================================================================
# Step 2 — Dataset-level metadata (slide: "Inspect datasets")
# ---------------------------------------------------------------------------
dataset = CROISSANT["hasPart"][0]
dist = dataset["distribution"][0]
rs = dataset["recordSet"][0]
print("Dataset name :", dataset["name"])
print("File (contentUrl):", dist["contentUrl"])
print("Format       :", dist["encodingFormat"])
print("RecordSet    :", rs["name"], f"({len(rs['field'])} fields)")

# The 5 novice-track inspection questions, answered from the metadata:
print("\nNovice-track inspection answers:")
print("  Which dataset is used?      ", dataset["name"], "(hasPart.name)")
print("  Which file is used?         ", dist["contentUrl"], "(distribution.contentUrl)")
print("  Which columns define proteins? source, target (recordSet.field)")
print("  Which column defines edge type? type")
print("  Which graph elements emitted?  (:Protein)-[:<type>]->(:Protein)")


# %%
# ===========================================================================
# Step 3 — Connect metadata to code (slide: "Compare to adapter")
# ---------------------------------------------------------------------------
# Map each metadata element to protein_interaction_adapter.py in THIS repo.
MAPPING = [
    ("distribution.contentUrl",            "create_knowledge_graph.py FileDownload(...) -> data_source passed to adapter"),
    ("field source / target",              "get_nodes(): node_id from source & target columns, deduped"),
    ("field source_genesymbol",            "get_nodes() property 'genesymbol'"),
    ("field ncbi_tax_id_source",           "get_nodes() property 'ncbi_tax_id'"),
    ("field entity_type_source",           "get_nodes() property 'entity_type'"),
    ("node label",                         "'uniprot_protein' (matches schema_config input_label)"),
    ("field type",                         "get_edges(): used as the edge LABEL (activation/binding/...)"),
    ("fields is_*/consensus_*",            "get_edges(): the 6 boolean flag edge properties"),
    ("edge_id",                            "get_edges(): f'{source}_{target}_{type}'"),
]
print("Metadata field            ->  Adapter code")
for meta, code in MAPPING:
    print(f"  {meta:26}->  {code}")


# %%
# ===========================================================================
# Step 4 — Add croissant.jsonld to the repo root + commit (DOCUMENTED ONLY)
# ---------------------------------------------------------------------------
# Use the session-provided file if you got one; otherwise the reference above.
# This cell prints the commands — it does NOT run git for you.
ROOT_TARGET = PROJECT_ROOT / "croissant.jsonld"
print("To complete Step 4, run in a terminal at the repo root:\n")
print(f"  cp notebooks/_reference_croissant.jsonld croissant.jsonld   # or the session file")
print(f"  ls")
print(f"  cat croissant.jsonld | head")
print(f"  git add croissant.jsonld")
print(f'  git commit -m "Add Croissant metadata"')
print(f"\n(Target path: {ROOT_TARGET})")
print("Exists already?", ROOT_TARGET.exists())


# %%
# ===========================================================================
# Reflect (slide: "Reflection questions" + "Session checkpoint")
# ---------------------------------------------------------------------------
REFLECTION = """
Discuss in pairs:
  1. What was easy to understand from the metadata alone?
  2. What required looking at the adapter code?
  3. Which fields helped connect data to graph elements?
  4. Which information would help another developer reuse the adapter?
  5. What assumptions are still implicit (captured nowhere)?

Session checkpoint — by the end you should have:
  [ ] inspected a Croissant metadata file
  [ ] identified adapter-level metadata        (Step 1)
  [ ] identified dataset-level metadata         (Step 2)
  [ ] connected fields to adapter code          (Step 3)
  [ ] added croissant.jsonld to the repo root   (Step 4)
"""
print(REFLECTION)


# %%
# ===========================================================================
# Tooling note — you don't have to hand-author croissant.jsonld
# ---------------------------------------------------------------------------
# We hand-authored / hand-edited the JSON-LD above to learn the structure, but in
# practice you can GENERATE a Croissant file from a dataset automatically:
#
#   - Croissant Baker  — generates a croissant.jsonld FROM a dataset (infers the
#                        distribution/recordSet/fields from the data files), so
#                        you start from a draft instead of a blank file.
#   - Croissant Editor — a GUI for creating/editing Croissant metadata.
#   - mlcroissant      — the Python library/CLI we used to VALIDATE:
#                            mlcroissant validate --jsonld croissant.jsonld
#                        (success logs "Done."; failures print errors).
#
# Typical workflow: bake a draft from the dataset -> hand-edit descriptions,
# license, creator, and the field->graph-element mapping -> validate with
# mlcroissant -> commit. (Generated drafts still need human review: field
# descriptions and the "how this maps to nodes/edges" intent are not inferable
# from the data alone.)
print("Tooling: Croissant Baker (generate) -> hand-edit -> mlcroissant validate -> commit")
