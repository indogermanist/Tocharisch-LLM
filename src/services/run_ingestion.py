import os
import argparse
from pathlib import Path

from dotenv import load_dotenv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run XML ingestion pipeline into Neo4j (and optional Qdrant load)."
    )
    parser.add_argument(
        "--fragments-xml",
        default="Tocharisch_Fragmente/fragments_dummy.xml",
        help="Path to fragments XML file.",
    )
    parser.add_argument(
        "--dictionary-xml",
        default="Tocharisch_Fragmente/dictionaries_dummy.xml",
        help="Path to dictionary XML file.",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not clear Neo4j graph before ingestion.",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip REFERS_TO_INFLECTED_FORM and NEXT relationship enrichment.",
    )
    parser.add_argument(
        "--with-qdrant",
        action="store_true",
        help="Also push fragment translations from Neo4j into Qdrant after ingestion.",
    )
    return parser


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    load_dotenv(project_root / ".env")

    from src.infrastructure.neo4jconnector import Neo4jConnection
    from src.services.ingestion import run_xml_ingestion_pipeline

    args = build_parser().parse_args()

    neo4j_host = os.environ.get("NEO_4J_HOST", "localhost").strip('"')
    neo4j_port = os.environ.get("NEO_4J_PORT", "8687").strip('"')
    neo4j_user = os.environ.get("NEO_4J_USER", "neo4j").strip('"')
    neo4j_password = os.environ.get("NEO_4J_PASSWORD", "your_password").strip('"')

    conn = Neo4jConnection(
        uri=f"neo4j://{neo4j_host}:{neo4j_port}",
        user=neo4j_user,
        pwd=neo4j_password,
    )

    try:
        stats = run_xml_ingestion_pipeline(
            fragments_xml_path=str(project_root / args.fragments_xml),
            dictionary_xml_path=str(project_root / args.dictionary_xml),
            conn=conn,
            reset_graph=not args.no_reset,
            enrich_word_graph=not args.no_enrich,
        )
        print("Neo4j ingestion finished:", stats)

        if args.with_qdrant:
            from src.rag.qdrant import QdrantConnection
            from src.rag.neo4j_qdrant_connection import Neo4jQdrantConnector

            qdrant_conn = QdrantConnection()
            neo4j_qdrant_connector = Neo4jQdrantConnector(
                neo4j_conn=conn,
                qdrant_conn=qdrant_conn,
            )
            neo4j_qdrant_connector.insert_all_fragments_translation()
            print("Qdrant load finished.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
