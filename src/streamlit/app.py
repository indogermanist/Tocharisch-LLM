import streamlit as st
import streamlit.components.v1 as components
from streamlit_agraph import agraph, Node, Edge, Config
import json
import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))

load_dotenv()

from agents_src.agents import agentCollection
from rag.query_rag import RagQuerier
from rag.neo4j_qdrant_connection import Neo4jQdrantConnector, qdrant
from infrastructure.neo4jconnector import Neo4jConnection
import app_utils

# 1. Wide layout and page setup
st.set_page_config(
    page_title="Tocharian Fragment Search",
    layout="wide"
)

# 2. Sidebar with special characters (with scroll if needed)
with st.sidebar:
    st.header("Special Characters")
    st.markdown("Click to copy:")
    special_chars = [
        "ā", "ḍ", "ī", "ḷ", "ṃ", "ṇ", "ñ", "ṅ", "ṛ", "ś",
        "ṣ", "š", "ß", "ṭ", "ū", "ä", "ö", "=", "-"
    ]
    # ensure container can scroll if buttons overflow
    btns_html = '<div style="display:flex; flex-wrap: wrap; gap:8px; max-height: 240px; overflow-y: auto;">'
    for ch in special_chars:
        btns_html += f"""
          <button style="font-size:20px; padding:6px 10px; border:1px solid #ccc; border-radius:4px; cursor:pointer; background:#fff;" 
                  onclick="navigator.clipboard.writeText('{ch}')">{ch}</button>
        """
    btns_html += '</div>'
    # height >= max-height + padding to avoid clipping
    components.html(btns_html, height=260)

# 3. Initialize connections once per session
if "neo4j_connection" not in st.session_state:
    neo4j_host = os.environ.get("NEO_4J_HOST", "localhost")
    neo4j_port = os.environ.get("NEO_4J_PORT", "8687")
    st.session_state.neo4j_connection = Neo4jConnection(
        uri=f"neo4j://{neo4j_host}:{neo4j_port}",
        user=os.environ.get("NEO_4J_USER"),
        pwd=os.environ.get("NEO_4J_PASSWORD")
    )
if "qdrant_conn" not in st.session_state:
    st.session_state.qdrant_conn = qdrant.QdrantConnection()
if "neo4j_qdrant_connector" not in st.session_state:
    st.session_state.neo4j_qdrant_connector = Neo4jQdrantConnector(
        neo4j_conn=st.session_state.neo4j_connection,
        qdrant_conn=st.session_state.qdrant_conn
    )
if "agents" not in st.session_state:
    st.session_state.agents = agentCollection()
if "rag_querier" not in st.session_state:
    st.session_state.rag_querier = RagQuerier(
        qdrant_conn=st.session_state.qdrant_conn,
        agents=st.session_state.agents
    )

# 4. Main content
st.title("🔍 Tocharian Fragment Search")
st.markdown("Search in Tocharian fragments using **natural language**!")
st.divider()
st.markdown("### Write your question")

st.markdown("Du musst noch einbauen, dass die tocharische Übersetzung von einem deutschen Wort hast.")

question = st.text_input(
    "Question",
    key="question",
    placeholder="e.g. What does 'tanañ' mean?"
)
search_clicked = st.button("🔎 Search")

if search_clicked:
    if not question:
        st.error("Please input a question!")
    else:
        indent = st.session_state.agents.decide_indent_agent(question)
        if not indent:
            st.info("🔍 Searching in Fragment Information...")
            with st.spinner("Querying Neo4j database..."):
                query = st.session_state.agents.cypher_agent(
                    user_input=question
                )
                result = st.session_state.neo4j_connection.query(
                    query.cypher
                )
            with st.expander("🔧 Debug: Cypher Query", expanded=False):
                cypher_str = getattr(query, "cypher", str(query))
                st.code(cypher_str, language="cypher")
            st.success("Database search complete.")
            st.info("✍️ Generating answer...")
            with st.spinner("Writing answer..."):
                answer = st.session_state.agents.answer_writing_agent(
                    user_input=question, result=result
                )
            st.markdown(answer)
            try:
                app_utils.display_graph(result)
            except TypeError:
                pass
        else:
            st.info("🔍 Searching in Translations...")
            with st.spinner("Retrieving fragments..."):
                result = st.session_state.rag_querier.get_relevant_fragments(
                    query=question
                )
            app_utils.display_translation_search_result(
                result, neo_conn=st.session_state.neo4j_connection
            )
