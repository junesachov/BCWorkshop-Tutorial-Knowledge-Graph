"""
BioCypher Workshop 2026 — Novice Track walkthrough (Session B: Adapters)
=======================================================================

Source slides:
https://ssciwr.github.io/slides-biocypher/Tuesday/B-BioCypher-Adapters/sessionb_novice_track_slides.html

What this is
------------
A guided *answer key + runner* for the novice-track adapter exercise. Every
"TODO" from the slides is reproduced here as a "# %%" cell: first the task as
stated, then a working solution, then (where relevant) a check.

This notebook is **self-contained**: it defines a completed adapter inline and
writes a completed schema config to a notebook-local file, then runs the
BioCypher pipeline in *offline* mode to generate the Neo4j import CSVs. It does
NOT overwrite the scaffolded TODO files in the repo (config/, src/, the script),
so you can still do the exercise by hand and diff against this reference.

How to run
----------
  - VS Code / Cursor: each "# %%" is a clickable "Run Cell" block.
  - Plain terminal:  uv run python notebooks/novice_track_walkthrough.py
    (runs TODO 1-6 + pipeline end to end; the Neo4j import/validate cells at the
    end are documentation only — they need a running Neo4j and are not executed.)

The slide TODOs map to cells below:
  TODO 1  BioCypher config — Neo4j bin path        (documented; machine-specific)
  TODO 2  Schema: protein node properties
  TODO 3  Schema: complete the 4 remaining edges
  TODO 4  Adapter.get_nodes() — yield protein nodes
  TODO 5  Adapter.get_edges() — yield interaction edges (5a-5e)
  TODO 6  Wire the script — instantiate adapter, collect into a list
  Run / Import / Validate
"""

# %%
# ---------------------------------------------------------------------------
# Setup: locate the repo root robustly, regardless of the working directory.
# (Interactive cells often run from the repo root; `uv run` from anywhere.)
# ---------------------------------------------------------------------------
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
print("Project root:", PROJECT_ROOT)


# %%
# ===========================================================================
# Setup (slide: "Fork and clone")
# ---------------------------------------------------------------------------
# Already done for this repo:
#     gh repo fork ecarrenolozano/BCWorkshop-Tutorial-Knowledge-Graph --clone
#     cd BCWorkshop-Tutorial-Knowledge-Graph
#     uv sync
#
# The dataset is a synthetic protein-interaction TSV hosted on Zenodo. The repo
# script downloads it via biocypher.FileDownload; here we read it directly so the
# notebook is easy to step through. Columns (confirmed from the file header):
#   source, target, source_genesymbol, target_genesymbol,
#   is_directed, is_stimulation, is_inhibition,
#   consensus_direction, consensus_stimulation, consensus_inhibition,
#   type, ncbi_tax_id_source, entity_type_source,
#   ncbi_tax_id_target, entity_type_target
# ===========================================================================
import pandas as pd

PROTEIN_INTERACTION_DATASET = (
    "https://zenodo.org/records/16902349/files/synthetic_protein_interactions.tsv"
)

df = pd.read_csv(PROTEIN_INTERACTION_DATASET, sep="\t")
print("Rows:", len(df))
print("Columns:", list(df.columns))
print("Interaction types present:", sorted(df["type"].unique()))
df.head()


# %%
# ===========================================================================
# TODO 1 — BioCypher config: Neo4j bin path  (file: config/biocypher_config.yaml)
# ---------------------------------------------------------------------------
# Task (slide): "Set the path to your Neo4j instance binary folder."
# Add under the `neo4j:` block:
#     import_call_bin_prefix: /path/to/your/neo4j-instance/bin/
# Hint: Neo4j Desktop -> Overview -> copy instance path -> append /bin/.
#
# Why it is only documented here: this path is machine-specific, and BioCypher
# in *offline* mode (offline: true in biocypher_config.yaml) does not need it to
# WRITE the CSVs — it only affects the path baked into the generated
# neo4j-admin-import-call.sh. Set it in the real config before you import.
#
# Example (macOS Neo4j Desktop):
#     import_call_bin_prefix: /Users/you/Library/Application Support/Neo4j Desktop/.../bin/
# ===========================================================================
print("TODO 1: set `neo4j.import_call_bin_prefix` in config/biocypher_config.yaml "
      "before running the Neo4j import (offline CSV generation below does not need it).")


# %%
# ===========================================================================
# TODO 2 + TODO 3 — Schema config  (file: config/schema_config.yaml)
# ---------------------------------------------------------------------------
# TODO 2: add `properties` (genesymbol, ncbi_tax_id, entity_type) to the
#         `protein` node entry.
# TODO 3: complete the four remaining edge types (binding, inhibition,
#         phosphorylation, ubiquitination) by copying the `activation` block.
#
# We write the COMPLETED schema to a notebook-local file and point BioCypher at
# it, leaving the scaffolded config/schema_config.yaml untouched for the manual
# exercise. The content below is exactly what you would type into the repo file.
# ===========================================================================
SOLUTION_SCHEMA = """\
#-------------------------------------------------------------------
#-------------------------      NODES      -------------------------
#-------------------------------------------------------------------
#====   PARENT NODES
protein:
    represented_as: node
    preferred_id: uniprot
    input_label: uniprot_protein
    # TODO 2 solution:
    properties:
        genesymbol: str
        ncbi_tax_id: str
        entity_type: str

#-------------------------------------------------------------------
#------------------      RELATIONSHIPS (EDGES)     -----------------
#-------------------------------------------------------------------
#====   PARENT EDGES
protein protein interaction:
    is_a: pairwise molecular interaction
    represented_as: edge
    input_label: protein_protein_interaction
    properties:
        is_directed: bool
        is_stimulation: bool
        is_inhibition: bool
        consensus_direction: bool
        consensus_stimulation: bool
        consensus_inhibition: bool

#====   INHERITED EDGES
# Reference entry (already complete in the repo):
activation:
    is_a: protein protein interaction
    inherit_properties: true
    represented_as: edge
    input_label: activation

# TODO 3 solution — the four remaining types:
binding:
    is_a: protein protein interaction
    inherit_properties: true
    represented_as: edge
    input_label: binding

inhibition:
    is_a: protein protein interaction
    inherit_properties: true
    represented_as: edge
    input_label: inhibition

phosphorylation:
    is_a: protein protein interaction
    inherit_properties: true
    represented_as: edge
    input_label: phosphorylation

ubiquitination:
    is_a: protein protein interaction
    inherit_properties: true
    represented_as: edge
    input_label: ubiquitination
"""

SOLUTION_SCHEMA_PATH = HERE / "_solution_schema_config.yaml"
SOLUTION_SCHEMA_PATH.write_text(SOLUTION_SCHEMA)
print("Wrote completed schema ->", SOLUTION_SCHEMA_PATH)

# Sanity check: every interaction type in the data must have a schema entry,
# otherwise BioCypher silently drops those edges.
schema_edge_labels = {"activation", "binding", "inhibition",
                      "phosphorylation", "ubiquitination"}
data_types = set(df["type"].unique())
missing = data_types - schema_edge_labels
print("Interaction types in data :", sorted(data_types))
print("Edge labels in schema     :", sorted(schema_edge_labels))
assert not missing, f"Schema is missing edge types present in data: {missing}"
print("OK: every interaction type in the data has a schema entry.")


# %%
# ===========================================================================
# TODO 4 + TODO 5 — The adapter
# (file: src/biocypher_tutorial_kg/adapters/protein_interaction_adapter.py)
# ---------------------------------------------------------------------------
# We define the COMPLETED adapter inline. The data-prep steps (Steps 1-2.4) are
# copied verbatim from the repo scaffold; the YOUR-CODE blocks (TODO 4 and
# TODO 5a-5e) are filled in. Paste the filled blocks back into the repo file to
# complete the manual exercise.
# ===========================================================================
import logging

logger = logging.getLogger("novice_track")


class SolutionProteinInteractionAdapter:
    """Completed reference adapter for the novice-track exercise."""

    def __init__(self, data_source, **kwargs):
        self.data_source = data_source
        self.config = kwargs

    # ----- TODO 4: get_nodes() -------------------------------------------
    def get_nodes(self):
        """Yield one (node_id, node_label, properties) tuple per unique protein."""
        df = pd.read_csv(self.data_source, sep="\t")

        # Step 2.1: source-side proteins
        source_nodes = df[
            ["source", "source_genesymbol", "ncbi_tax_id_source", "entity_type_source"]
        ].copy().rename(columns={
            "source": "node_id",
            "source_genesymbol": "genesymbol",
            "ncbi_tax_id_source": "ncbi_tax_id",
            "entity_type_source": "entity_type",
        })
        # Step 2.2: target-side proteins
        target_nodes = df[
            ["target", "target_genesymbol", "ncbi_tax_id_target", "entity_type_target"]
        ].copy().rename(columns={
            "target": "node_id",
            "target_genesymbol": "genesymbol",
            "ncbi_tax_id_target": "ncbi_tax_id",
            "entity_type_target": "entity_type",
        })
        # Steps 2.3-2.4: merge and de-duplicate
        proteins_df = pd.concat([source_nodes, target_nodes], ignore_index=True)
        proteins_df = proteins_df.drop_duplicates(subset=["node_id"])

        # ---------- TODO 4 SOLUTION ----------
        for _, row in proteins_df.iterrows():
            yield (
                str(row["node_id"]),
                "uniprot_protein",
                {
                    "genesymbol": row["genesymbol"],
                    "ncbi_tax_id": str(row["ncbi_tax_id"]),
                    "entity_type": row["entity_type"],
                },
            )

    # ----- TODO 5: get_edges() -------------------------------------------
    def get_edges(self):
        """Yield one (edge_id, source_id, target_id, edge_label, properties) per row."""
        # 5a: read TSV
        df = pd.read_csv(self.data_source, sep="\t")

        flag_cols = [
            "is_directed", "is_stimulation", "is_inhibition",
            "consensus_direction", "consensus_stimulation", "consensus_inhibition",
        ]

        for _, row in df.iterrows():
            # 5b: extract identifiers
            source_id = str(row["source"])
            target_id = str(row["target"])
            interaction_type = str(row["type"])

            # 5e (guard): skip rows missing the essentials
            if not source_id or not target_id or not interaction_type:
                continue
            if interaction_type in ("nan", "None", ""):
                continue

            # 5c: deterministic edge id
            edge_id = f"{source_id}_{target_id}_{interaction_type}"

            # 5d: properties from the 6 boolean flags (0/1 -> bool)
            properties = {col: bool(int(row[col])) for col in flag_cols}

            # 5e: yield the 5-tuple; edge_label is the interaction type
            yield (edge_id, source_id, target_id, interaction_type, properties)


# Quick local checks of the adapter output shape (not BioCypher yet).
adapter = SolutionProteinInteractionAdapter(PROTEIN_INTERACTION_DATASET)

sample_nodes = []
for i, n in enumerate(adapter.get_nodes()):
    if i < 3:
        sample_nodes.append(n)
    last_node = n
n_nodes = i + 1

sample_edges = []
for j, e in enumerate(adapter.get_edges()):
    if j < 3:
        sample_edges.append(e)
n_edges = j + 1

print(f"Unique protein nodes: {n_nodes}")
print(f"Interaction edges    : {n_edges}")
print("\nFirst nodes:")
for n in sample_nodes:
    print("  ", n)
print("First edges:")
for e in sample_edges:
    print("  ", e)

# Probe the contract shape (mirrors what BioCypher expects).
nid, nlabel, nprops = sample_nodes[0]
assert isinstance(nid, str) and isinstance(nlabel, str) and isinstance(nprops, dict)
assert set(nprops) == {"genesymbol", "ncbi_tax_id", "entity_type"}
eid, esrc, etgt, elabel, eprops = sample_edges[0]
assert isinstance(eid, str) and isinstance(esrc, str) and isinstance(etgt, str)
assert isinstance(elabel, str) and isinstance(eprops, dict)
assert set(eprops) == {
    "is_directed", "is_stimulation", "is_inhibition",
    "consensus_direction", "consensus_stimulation", "consensus_inhibition",
}
print("\nOK: node tuples are 3-element, edge tuples are 5-element, props match schema.")


# %%
# ===========================================================================
# TODO 6 — Wire the script + run the pipeline (offline)
# (file: create_knowledge_graph.py)
# ---------------------------------------------------------------------------
# TODO 6a: instantiate the adapter.
# TODO 6b: collect adapters into a list.
# Then BioCypher writes the Neo4j import CSVs (offline mode -> no live DB needed).
#
# We run from PROJECT_ROOT so BioCypher resolves config/biocypher_config.yaml,
# and override the schema path to our completed solution schema.
# ===========================================================================
import os
from biocypher import BioCypher

os.chdir(PROJECT_ROOT)  # so relative paths in biocypher_config.yaml resolve

bc = BioCypher(
    biocypher_config_path="config/biocypher_config.yaml",
    schema_config_path=str(SOLUTION_SCHEMA_PATH),
)

# TODO 6a + 6b solution:
protein_interaction_adapter = SolutionProteinInteractionAdapter(
    data_source=PROTEIN_INTERACTION_DATASET
)
adapters = [protein_interaction_adapter]

# Write loop (already implemented in the repo script):
for a in adapters:
    bc.write_nodes(a.get_nodes())
    bc.write_edges(a.get_edges())

bc.write_import_call()
print("\nPipeline finished. Summary:")
bc.summary()


# %%
# ===========================================================================
# Run the pipeline — inspect the output  (slide: "Run the pipeline")
# ---------------------------------------------------------------------------
# Equivalent of:  uv run python create_knowledge_graph.py
#                 ls biocypher-out
#                 head -n 5 biocypher-out/*part000.csv
# ===========================================================================
out_root = PROJECT_ROOT / "biocypher-out"
# Some BioCypher versions write into a timestamped subdir, others write straight
# into biocypher-out/. Find whichever directory actually holds the *-header.csv.
def _find_output_dir(root: Path) -> Path:
    if any(root.glob("*-header.csv")):
        return root
    subdirs = [p for p in root.iterdir() if p.is_dir() and any(p.glob("*-header.csv"))]
    return max(subdirs, key=lambda p: p.name)

latest = _find_output_dir(out_root)
print("Output dir:", latest, "\n")
for f in sorted(latest.glob("*.csv")):
    print("  ", f.name)

print("\n--- header + first rows of each *part000.csv ---")
for part in sorted(latest.glob("*part000.csv")):
    print(f"\n### {part.name}")
    print("\n".join(part.read_text().splitlines()[:5]))


# %%
# ===========================================================================
# Import into Neo4j  (slide: "Import into Neo4j")  -- DOCUMENTATION ONLY
# ---------------------------------------------------------------------------
# Offline mode generated a ready-to-run import script. Run it against a STOPPED,
# empty Neo4j database (neo4j-admin import is for initial bulk load only).
#
#   # 1. Make sure TODO 1 (import_call_bin_prefix) is set in biocypher_config.yaml.
#   # 2. Stop the DB:
#   sudo systemctl stop neo4j        # Linux service
#   #    (Neo4j Desktop: press Stop on the instance)
#   # 3. Run the generated import call:
#   bash biocypher-out/<timestamp>/neo4j-admin-import-call.sh
#   # 4. Start the DB:
#   sudo systemctl start neo4j       # or Start in Neo4j Desktop
#
# Not executed here — it requires a local Neo4j instance.
# ===========================================================================
# The import script sits in the output dir (or its parent, depending on version).
import_script = next(
    (p for p in (latest / "neo4j-admin-import-call.sh",
                 out_root / "neo4j-admin-import-call.sh") if p.exists()),
    latest / "neo4j-admin-import-call.sh",
)
print("Generated import script:", import_script, "| exists:", import_script.exists())
if import_script.exists():
    print("\n--- neo4j-admin-import-call.sh ---")
    print(import_script.read_text())


# %%
# ===========================================================================
# Validate in Neo4j  (slide: "Validate in Neo4j")  -- run these in the browser
# ---------------------------------------------------------------------------
# Open http://localhost:7474 and run:
#
#   // Count all nodes
#   MATCH (n) RETURN count(n) AS nodes;
#
#   // Count all relationships
#   MATCH ()-[r]->() RETURN count(r) AS relationships;
#
#   // Relationships broken down by type
#   MATCH ()-[r]->() RETURN type(r) AS edge_type, count(*) AS n ORDER BY n DESC;
#
#   // Peek at a few proteins
#   MATCH (p:Protein) RETURN p.id, p.genesymbol, p.ncbi_tax_id LIMIT 10;
#
#   // A small subgraph
#   MATCH (a:Protein)-[r]->(b:Protein) RETURN a, r, b LIMIT 25;
# ===========================================================================
print("Session checkpoint: fork+clone -> TODO 1-6 -> generate CSVs -> import -> query. Done.")
