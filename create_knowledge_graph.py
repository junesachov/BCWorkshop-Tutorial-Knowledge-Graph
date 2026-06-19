#!/usr/bin/env python3
"""
BioCypherWorkshop Tutorial Knowledge Graph - A beginner-friendly BioCypher project for learning how to build and extend a small knowledge graph from multiple data sources.

This script creates a knowledge graph using BioCypher and the ProteinInteractionAdapter.
"""

import logging

from biocypher import (
    BioCypher,
    FileDownload,
)
from biocypher_tutorial_kg.adapters.protein_interaction_adapter import ProteinInteractionAdapter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#-------------------- DATASET URLS --------------------#
PROTEIN_INTERACTION_DATASET = (
    "https://zenodo.org/records/16902349/files/synthetic_protein_interactions.tsv"
)

#--------------------------------------------------------
#-------------------- MAIN FUNCTION ---------------------
#--------------------------------------------------------
def main():
    """Main function to create the knowledge graph."""
    logger.info("Starting BioCypherWorkshop Tutorial Knowledge Graph knowledge graph creation")
    
    # Initialize BioCypher
    bc = BioCypher(
        biocypher_config_path="config/biocypher_config.yaml",
        schema_config_path="config/schema_config.yaml"
    )

    # ── REFERENCE ────────────────────────────────────────────────────────────
    # Step 1: Download the dataset. Already implemented — read and continue.
    # ─────────────────────────────────────────────────────────────────────────
    protein_interaction_file = bc.download(
        FileDownload(
            name="synthetic_protein_interactions",
            url_s=PROTEIN_INTERACTION_DATASET,
        )
    )[0]
    logger.info("Downloaded protein interactions: %s", protein_interaction_file)

    # ── TODO 6a ──────────────────────────────────────────────────────────────
    # Task: Instantiate the ProteinInteractionAdapter.
    # Why:  The adapter wraps the downloaded file and exposes get_nodes() and
    #       get_edges() to BioCypher.
    # Hint: ProteinInteractionAdapter(data_source=protein_interaction_file)
    # ─────────────────────────────────────────────────────────────────────────
    # ---------- YOUR CODE STARTS HERE ----------
    protein_interaction_adapter = ProteinInteractionAdapter(
        data_source=protein_interaction_file
    )

    # ---------- YOUR CODE ENDS HERE ----------

    # ── TODO 6b ──────────────────────────────────────────────────────────────
    # Task: Collect all adapter instances into a single list.
    # Why:  A single list lets the write loop below process every adapter
    #       uniformly, making it easy to add more adapters later.
    # Hint: adapters = [protein_interaction_adapter]
    # ─────────────────────────────────────────────────────────────────────────
    # ---------- YOUR CODE STARTS HERE ----------
    adapters = [protein_interaction_adapter]
    # ---------- YOUR CODE ENDS HERE ----------

    # ── REFERENCE ────────────────────────────────────────────────────────────
    # Step 4: Write nodes and edges. Already implemented — read and continue.
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("Creating knowledge graph...")
    for adapter in adapters:
        bc.write_nodes(adapter.get_nodes())
        bc.write_edges(adapter.get_edges())
    
    logger.info("Knowledge graph creation completed successfully!")

    # Write import call
    bc.write_import_call()

    # Print summary
    # bc.summary() 


if __name__ == "__main__":
    main()
