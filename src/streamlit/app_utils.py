import streamlit as st
import streamlit.components.v1 as components
from streamlit_agraph import agraph, Node, Edge, Config
import os
import sys
from typing import Any, TypeAlias
from neo4j import Record
from textwrap import dedent

sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
from agents_src.agents import agentCollection
from utils.utils_functions import get_lines_for_fragment


def special_chars():
    """
    Renders the special characters so that the user can copy them.

    Args:
        None.

    Returns:
        None.
    """
    special_chars = [
        "ā", "ḍ", "ī", "ḷ", "ṃ", "ṇ", "ñ", "ṅ", "ṛ", "ś",
        "ṣ", "š", "ß", "ṭ", "ū", "ä", "ö", "=", "-"
    ]

    buttons_html = """
    <div style="display:flex; gap:8px; flex-wrap: wrap; font-size:24px;">
    """
    for ch in special_chars:
        buttons_html += f"""
        <button
        style="padding:8px; border-radius:4px; border:1px solid #ccc; background:#f9f9f9; cursor:pointer;"
        onclick="navigator.clipboard.writeText('{ch}').then(()=>{{this.textContent='✓'; setTimeout(()=>{{this.textContent='{ch}'}}, 800);}})"
        >{ch}</button>
        """
    buttons_html += "</div>"

    st.markdown("### Special characters — click to copy!")
    components.html(buttons_html, height=100)


def neo4j_to_agraph_with_tooltips(result):
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    for record in result:
        for value in record.values():
            # -- Node? --
            if hasattr(value, "id") and hasattr(value, "labels"):
                nid = str(value.id)
                if nid not in nodes:
                    props = dict(value)  # everything in this node
                    # pick a “best” label
                    label = props.get("frag_id") or props.get("name") or next(iter(value.labels), nid)
                    # build a little HTML/Markdown tooltip of all props
                    title = "<br>".join(f"<b>{k}</b>: {v}" for k, v in props.items())
                    nodes[nid] = Node(
                        id=nid,
                        label=label,
                        title=title,         # hover tooltip
                        shape="box",         # rectangle so multi‑line labels wrap
                        font={"multi": "html"}  # allow HTML in labels/tooltips
                    )

            # -- Relationship? --
            elif hasattr(value, "start_node") and hasattr(value, "end_node"):
                src = str(value.start_node.id)
                dst = str(value.end_node.id)
                # ensure nodes exist first
                for n in (value.start_node, value.end_node):
                    if str(n.id) not in nodes:
                        props = dict(n)
                        lbl = props.get("frag_id") or props.get("name") or next(iter(n.labels), str(n.id))
                        nodes[str(n.id)] = Node(
                            id=str(n.id),
                            label=lbl,
                            title="<br>".join(f"<b>{k}</b>: {v}" for k, v in props.items()),
                            shape="box",
                            font={"multi": "html"}
                        )
                # edge tooltip too
                edge_props = dict(value)
                etitle = "<br>".join(f"<b>{k}</b>: {v}" for k, v in edge_props.items())
                edges.append(
                    Edge(
                        source=src,
                        target=dst,
                        label=value.type,   # always‑visible relation type
                        title=etitle        # hover to see all rel props
                    )
                )

            # -- Path? just recurse it all --
            elif hasattr(value, "nodes") and hasattr(value, "relationships"):
                # you could call the above two blocks again, or simply unpack:
                for n in value.nodes:
                    if str(n.id) not in nodes:
                        props = dict(n)
                        lbl = props.get("frag_id") or props.get("name") or next(iter(n.labels), str(n.id))
                        nodes[str(n.id)] = Node(
                            id=str(n.id),
                            label=lbl,
                            title="<br>".join(f"<b>{k}</b>: {v}" for k, v in props.items()),
                            shape="box",
                            font={"multi": "html"}
                        )
                for r in value.relationships:
                    edges.append(
                        Edge(
                            source=str(r.start_node.id),
                            target=str(r.end_node.id),
                            label=r.type,
                            title="<br>".join(f"<b>{k}</b>: {v}" for k, v in dict(r).items())
                        )
                    )

    return list(nodes.values()), edges


def display_graph(result: list[Record] | Any | None) -> None:
    """
    Displays the generated graph.

    Args:
        result (list): The result of the user input

    Returns:
        None.
    """
    nodes, edges = neo4j_to_agraph_with_tooltips(result)

    config = Config(
        width=800,
        height=600,
        directed=True,
        physics=True,
        hierarchical=False,
        # you can tweak VisJS interaction directly:
        **{
            "interaction": {
                "hover": True,        # show hover events
                "tooltipDelay": 200   # ms before tooltip pops up
            }
        }
    )

    agraph(nodes=nodes, edges=edges, config=config)


def display_translation_search_result(
    result: dict[str, dict[str, str]],
    neo_conn
) -> None:
    # Only the three most relevant fragments are returned
    fragment_text_list = []
    frag_ids = []
    for i in range(1, min(4, len(result) + 1)):
        frag_ids.append(result[str(i)]["frag_id"])
        lines = get_lines_for_fragment(
            frag_id=result[str(i)]["frag_id"],
            neo_conn=neo_conn
        )
        fragment_text_temp = []
        for line in lines:
            line_id = line["line_id"].split(".")[-1]
            if str(line["line_position"]) == result[str(i)]["relevant_line"]:
                fragment_text_temp.append(f"{line_id}: **{line['words']}**")
                fragment_text_temp.append(f"{line_id}: **{line['translations']}**")
            else:
                fragment_text_temp.append(f"{line_id}: {line['words']}")
                fragment_text_temp.append(f"{line_id}: {line['translations']}\n")
        fragment_text_list.append("\n".join(fragment_text_temp))

    st.markdown(
        "#### 3 most relevant Fragments (relevant line is bold)"
    )
    for text, frag_id in zip(fragment_text_list, frag_ids):
        st.markdown(f"##### {frag_id}")
        html = text.replace("\n", "<br/>")
        st.markdown(html, unsafe_allow_html=True)

