# Adapter documentation — `ProteinInteractionAdapter`

Documentation for the tutorial adapter in this repository, covering the adapter
name, its input dataset, the graph elements it emits, and the assumptions baked
into its logic.

- **Source:** [`src/biocypher_tutorial_kg/adapters/protein_interaction_adapter.py`](src/biocypher_tutorial_kg/adapters/protein_interaction_adapter.py)
- **Schema contract:** [`config/schema_config.yaml`](config/schema_config.yaml)
- **Machine-readable metadata:** [`croissant.jsonld`](croissant.jsonld) (BioCypher adapter profile)
- **Version:** `0.1.0` (from `get_metadata()`)

---

## 1. Adapter name

**`ProteinInteractionAdapter`** — a BioCypher adapter that reads an
OmniPath/pypath-style protein–protein interaction table (TSV) and yields
BioCypher node and edge tuples for a protein-interaction knowledge graph.

It implements the BioCypher adapter interface:
- `get_nodes()` → `(node_id, node_label, properties)`
- `get_edges()` → `(edge_id, source_id, target_id, edge_label, properties)`
- plus `get_metadata()` and `validate_data_source()` helpers.

---

## 2. The dummy dataset

A **synthetic** protein-interaction table — not real biological data, generated
for the workshop.

| Property | Value |
|---|---|
| File | `synthetic_protein_interactions.tsv` |
| Source | Zenodo — <https://zenodo.org/records/16902349> (DOI `10.5281/zenodo.16902349`) |
| Retrieval | downloaded by `create_knowledge_graph.py` via `biocypher.FileDownload` |
| Format | tab-separated values, header row |
| Size | 2012 bytes, **23 interaction rows** |
| Unique proteins | **15** (across source + target) |
| Interaction types | ubiquitination ×8, activation ×6, phosphorylation ×4, binding ×3, inhibition ×2 |
| Taxa present | `9606` (human), `10090` (mouse), `10116` (rat) |
| Entity types | `protein` only |

**Columns (TSV header):**

| Column | Meaning | Used as |
|---|---|---|
| `source`, `target` | UniProt accessions | **Protein node ids** |
| `source_genesymbol`, `target_genesymbol` | gene symbols | node property `genesymbol` |
| `ncbi_tax_id_source`, `ncbi_tax_id_target` | NCBI taxon ids | node property `ncbi_tax_id` |
| `entity_type_source`, `entity_type_target` | entity type | node property `entity_type` |
| `type` | interaction type | **edge label** |
| `is_directed`, `is_stimulation`, `is_inhibition` | interaction flags (0/1) | edge properties |
| `consensus_direction`, `consensus_stimulation`, `consensus_inhibition` | consensus flags (0/1) | edge properties |

---

## 3. Emitted nodes

One node type.

| | |
|---|---|
| **Label (BioCypher `input_label`)** | `uniprot_protein` |
| **Ontology class (schema_config)** | `protein` |
| **Node id** | UniProt accession (from `source` / `target`) |
| **Properties** | `genesymbol` (str), `ncbi_tax_id` (str), `entity_type` (str) |
| **Count for the dummy dataset** | 15 |

Built in `get_nodes()` by stacking the source-side and target-side protein
columns into one table and de-duplicating by `node_id`.

---

## 4. Emitted edges

One edge per interaction row. The **edge label is the value of the `type`
column**, so the adapter emits five concrete edge types, all of which the schema
declares as `is_a: protein protein interaction`:

| Edge label (`input_label`) | Schema parent | Count |
|---|---|---|
| `activation` | protein protein interaction | 6 |
| `binding` | protein protein interaction | 3 |
| `inhibition` | protein protein interaction | 2 |
| `phosphorylation` | protein protein interaction | 4 |
| `ubiquitination` | protein protein interaction | 8 |

| | |
|---|---|
| **Direction** | `source` → `target` |
| **Edge id** | `f"{source}_{target}_{type}"` |
| **Properties** | `is_directed`, `is_stimulation`, `is_inhibition`, `consensus_direction`, `consensus_stimulation`, `consensus_inhibition` — all booleans |

Resulting shape:

```
(:Protein)-[:activation|binding|inhibition|phosphorylation|ubiquitination]->(:Protein)
```

---

## 5. Assumptions & limitations

Recorded so a future user knows what the adapter takes for granted. These are
derived from the current implementation, not from a spec — verify before relying
on them.

1. **Node identity = UniProt accession.** Two proteins are "the same" iff their
   `source`/`target` string matches exactly. No normalisation or ID mapping.
2. **First occurrence wins on de-duplication.** `drop_duplicates(subset=["node_id"])`
   keeps the first row's `genesymbol` / `ncbi_tax_id` / `entity_type` for a given
   protein. If later rows disagree, the difference is **silently dropped** (no
   warning is emitted).
3. **Every row becomes one edge.** No interaction-level de-duplication in code.
   However, because `edge_id = source_target_type`, two rows with the same
   source, target, and type collapse to the **same edge id** — BioCypher will
   treat them as one edge, so genuine duplicate interactions are effectively
   merged (and differing properties would be overwritten).
4. **Edge label must exist in the schema.** The raw `type` string is used as the
   edge label, so any interaction type not declared in `schema_config.yaml`
   (currently the five above) would be dropped/unmapped by BioCypher.
5. **Boolean flags are `0`/`1` integers.** Parsed as `bool(int(value))`. A value
   that is empty or non-numeric would raise a `ValueError`. Note: `croissant.jsonld`
   types the `consensus_*` columns as `Int64` while the adapter coerces them to
   `bool` — a metadata/code mismatch worth reconciling.
6. **Taxon is stored as a string**, not an integer (`str(row["ncbi_tax_id"])`).
7. **`entity_type` is carried through** even though it is always `protein` in
   this dataset; it would pass through unchanged for other entity types.
8. **Rows missing `source`, `target`, or `type` are skipped** (and `type` values
   `"nan"`, `"None"`, `""` are treated as missing).
9. **Single file, single record set.** The adapter reads exactly one TSV path
   (`self.data_source`); it does not merge multiple files.
