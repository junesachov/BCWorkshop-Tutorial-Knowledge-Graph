"""
ProteinInteractionAdapter Adapter

This adapter handles protein interaction TSV data for BioCypher.
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class ProteinInteractionAdapter:
    """
    Adapter for protein interaction TSV data source.

    This adapter implements the BioCypher adapter interface and is intentionally
    scaffolded as a workshop exercise.
    """
    
    def __init__(self, data_source: str | Path, **kwargs):
        """
        Initialize the adapter.

        Args:
            data_source: Path to the TSV data source
            **kwargs: Additional configuration parameters
        """
        self.data_source = data_source
        self.config = kwargs
        logger.info(
            "Initialized ProteinInteractionAdapter with data source: %s", data_source
        )
        
    def get_nodes(self):
        """
        Extract nodes from the data source.

        Yields:
            Tuples of (node_id, node_label, properties) for each node.
        """
        logger.info("Extracting nodes from data source")

        # BioCypher node tuple format:
        # (node_id, node_label, properties)

        # ── REFERENCE ────────────────────────────────────────────────────────
        # Steps 1–2.4 are already implemented. Read them to understand the
        # data preparation before you implement the yield step (TODO 4).
        # ─────────────────────────────────────────────────────────────────────

        # Step 1: Read the interaction TSV into a DataFrame.
        df = pd.read_csv(self.data_source, sep="\t")

        # Step 2.1: Build the source-side Protein table.
        source_nodes = df[
            ["source", "source_genesymbol", "ncbi_tax_id_source", "entity_type_source"]
        ].copy()
        source_nodes = source_nodes.rename(
            columns={
                "source": "node_id",
                "source_genesymbol": "genesymbol",
                "ncbi_tax_id_source": "ncbi_tax_id",
                "entity_type_source": "entity_type",
            }
        )

        # Step 2.2: Build the target-side Protein table.
        target_nodes = df[
            ["target", "target_genesymbol", "ncbi_tax_id_target", "entity_type_target"]
        ].copy()
        target_nodes = target_nodes.rename(
            columns={
                "target": "node_id",
                "target_genesymbol": "genesymbol",
                "ncbi_tax_id_target": "ncbi_tax_id",
                "entity_type_target": "entity_type",
            }
        )

        # Step 2.3: Merge source-side and target-side proteins.
        proteins_df = pd.concat([source_nodes, target_nodes], ignore_index=True)

        # Step 2.4: Remove duplicate proteins by node_id.
        proteins_df = proteins_df.drop_duplicates(subset=["node_id"])

        # ── TODO 4 ───────────────────────────────────────────────────────────
        # Task: Yield one BioCypher node tuple per unique protein.
        # Why:  BioCypher expects this exact 3-element tuple shape:
        #       (node_id, node_label, properties)
        # Hint: Iterate over proteins_df rows. For each row yield:
        #         (str(row["node_id"]),
        #          "uniprot_protein",
        #          {"genesymbol": ..., "ncbi_tax_id": str(...), "entity_type": ...})
        # ─────────────────────────────────────────────────────────────────────
        # ---------- YOUR CODE STARTS HERE ----------
        # we write loop that gives us one tuple per prot
        for _, row in proteins_df.iterrows():
            yield (
                str(row["node_id"]),  #node_id
                "uniprot_protein",   #node_label <- must match schema input_label
                {
                    "genesymbol": row["genesymbol"],
                    "ncbi_tax_id": str(row["ncbi_tax_id"]),
                    "entity_type": row["entity_type"],
                },
            )
        # ---------- YOUR CODE ENDS HERE ----------

        
    
    def get_edges(self):
        """
        Extract edges from the data source.

        Yields:
            Tuples of (edge_id, source_id, target_id, edge_label, properties)
            for each edge.
        """
        logger.info("Extracting edges from data source")

        # BioCypher edge tuple format:
        # (edge_id, source_id, target_id, edge_label, properties)

        # ── TODO 5a ──────────────────────────────────────────────────────────
        # Task: Read the interaction TSV into a DataFrame.
        # Why:  Each row represents one interaction and maps to one edge tuple.
        # Hint: Use pd.read_csv(self.data_source, sep="\t").
        # ─────────────────────────────────────────────────────────────────────
        # ---------- YOUR CODE STARTS HERE ----------
        df = pd.read_csv(self.data_source, sep="\t")

        flag_cols = [
            "is_directed", "is_stimulation", "is_inhibition",
            "consensus_direction", "consensus_stimulation", "consensus_inhibition",
        ]
        # ---------- YOUR CODE ENDS HERE ----------

        # ── TODO 5b ──────────────────────────────────────────────────────────
        # Task: Iterate over interaction rows and extract edge identifiers.
        # Why:  Each row produces one edge; stable IDs make the graph easier
        #       to validate and debug.
        # Hint: Use df.iterrows(). From each row extract:
        #         source_id  = str(row["source"])
        #         target_id  = str(row["target"])
        #         interaction_type = str(row["type"])
        # ─────────────────────────────────────────────────────────────────────
        # ---------- YOUR CODE STARTS HERE ----------
        for _, row in df.iterrows():
            source_id = str(row["source"])
            target_id = str(row["target"])
            interaction_type = str(row["type"])
            
            # ── 5e guard: skip rows missing essentials ──
            if not source_id or not target_id or not interaction_type:
                continue
            if interaction_type in ("nan", "None", ""):
                continue
        # ---------- YOUR CODE ENDS HERE ----------

        # ── TODO 5c ──────────────────────────────────────────────────────────
        # Task: Build a deterministic edge_id.
        # Why:  A predictable edge_id makes tracing and deduplication easier.
        # Hint: Use f"{source_id}_{target_id}_{interaction_type}".
        # ─────────────────────────────────────────────────────────────────────
        # ---------- YOUR CODE STARTS HERE ----------
            edge_id = f"{source_id}_{target_id}_{interaction_type}"
        # ---------- YOUR CODE ENDS HERE ----------

        # ── TODO 5d ──────────────────────────────────────────────────────────
        # Task: Build edge properties from interaction flags.
        # Why:  These boolean flags carry biological meaning and must be
        #       preserved as edge-level attributes in the graph.
        # Hint: Build a dict with these keys, converting values to bool:
        #         is_directed, is_stimulation, is_inhibition,
        #         consensus_direction, consensus_stimulation,
        #         consensus_inhibition
        # ─────────────────────────────────────────────────────────────────────
        # ---------- YOUR CODE STARTS HERE ----------
            properties = {col: bool(int(row[col])) for col in flag_cols}
            #--OR--
            #properties = {
                #"is_directed": bool(int(row["is_directed"])),
                #"is_stimulation": bool(int(row["is_stimulation"])),
                #"is_inhibition": bool(int(row["is_inhibition"])),
                #"consensus_direction": bool(int(row["consensus_direction"])),
                #"consensus_stimulation": bool(int(row["consensus_stimulation"])),
                #"consensus_inhibition": bool(int(row["consensus_inhibition"])),
            #}

        # ---------- YOUR CODE ENDS HERE ----------

        # ── TODO 5e ──────────────────────────────────────────────────────────
        # Task: Yield one BioCypher edge tuple per interaction row.
        # Why:  BioCypher expects this exact 5-element tuple shape:
        #       (edge_id, source_id, target_id, edge_label, properties)
        # Hint: Use interaction_type as the edge_label. Optionally skip rows
        #       where source, target, or type is missing.
        # ─────────────────────────────────────────────────────────────────────
        # ---------- YOUR CODE STARTS HERE ----------
            yield (edge_id, source_id, target_id, interaction_type, properties)
        # ---------- YOUR CODE ENDS HERE ----------

    
    def get_metadata(self) -> dict[str, Any]:
        """
        Get metadata about the data source.

        Returns:
            Dictionary containing metadata
        """
        return {
            "name": "ProteinInteractionAdapter",
            "data_source": str(self.data_source),
            "data_type": "tsv",
            "version": "0.1.0",
            "adapter_class": "ProteinInteractionAdapter",
        }
    
    def validate_data_source(self) -> bool:
        """
        Validate that the TSV data source is accessible and properly formatted.

        Returns:
            True if data source is valid, False otherwise
        """
        try:
            data_path = Path(self.data_source)
            if not data_path.exists() or not data_path.is_file():
                return False

            # Read one row to validate TSV format and required columns.
            df = pd.read_csv(data_path, sep="\t", nrows=1)
            required_columns = {"source", "target"}
            return required_columns.issubset(df.columns)

        except (OSError, ValueError, pd.errors.ParserError) as exc:
            logger.exception("Data source validation failed: %s", exc)
            return False
