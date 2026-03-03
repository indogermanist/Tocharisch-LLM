import os
import json
from uuid import uuid4
import re
from langchain_core.prompts import ChatPromptTemplate
import sys
import yaml
import pandas as pd
from textwrap import dedent
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.documents import Document
from typing import Any, TypeAlias
from neo4j import Record


def get_cwd() -> str:
    """
    Returns the current working directory.

    Args:
        None.

    Returns:
        str: The current working directory.
    """
    return os.path.realpath(os.path.join(
        os.getcwd(), os.path.dirname(__file__)
    ))


def return_root_dir() -> str:
    """
    Returns the root directory of the project.

    Args:
        None.

    Returns:
        str: The root directory of the project.
    """
    path = get_cwd()
    return os.path.dirname(
        os.path.dirname(path)
    )


def read_file(path: str) -> str:
    """
    Reads file from path.

    Args:
        path (str): Path to the file.

    Returns:
        str: The content of the file.
    """
    with open(path, "r") as f:
        return f.read()


def read_json(path: str) -> dict:
    """
    Reads JSON from path.

    Args:
        path (str): Path to the JSON file

    Returns:
        dict: JSON as dict.
    """
    with open(path) as f:
        content = json.load(f)

    return content


def save_dict_as_json(dictionary: dict, path: str) -> None:
    """
    Saves JSON to path.

    Args:
        dictionary (str): Dict to save.
        path (str): Path to where the JSON should be saved.

    Returns:
        None.
    """
    with open(path, "w") as f:
        json.dump(dictionary, f)


def read_yml(path: str) -> dict[str, str]:
    """
    Reads and returns yml file.

    Args:
        path (str): Path to the yml file

    Returns:
        dict[str, str]: Yml file as dict
    """

    with open(path) as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}


def return_prompt(
    prompt_name: str
) -> PromptTemplate:
    """
    Returns prompt based on the specifed prompt name.

    Args:
        prompt_name (str): The name of the prompt.

    Returns:
        str: The prompt.
    """
    return PromptTemplate.from_file(
        os.path.join(
            return_root_dir(),
            "prompts",
            f"{prompt_name}.md"
        )
    )


def replace_single_curly_brackets(string_value: str) -> str:
    """
    Replaces every instance of single curly brackets with two
    curly brackets.

    Args:
        string_value (str): String to modify.

    Returns:
        str: Modified string.
    """
    text = re.sub(r'(?<!\{)\{(?!\{)', r'{{', string_value)
    # 2) Replace every single “}” (not part of “}}”) → “}}”
    text = re.sub(r'(?<!\})\}(?!\})', r'}}', text)
    return text


def build_user_wish_prompt(
    user_input: str
) -> dict[str, str]:
    """
    Build the prompt deciding on user intent.

    Args:
        user_input (str): The input of the user.

    Returns:
        dict[str, str]: The prompt dict.
    """

    return {
        "user_input": user_input
    }


def build_query_rewrite_prompt(
    query: str,
    snippets: list[str]
) -> dict[str, str]:
    """
    Builds the prompt for rewriting the query.

    Args:
        user_input (str): Query to use for vector store.
        snippets (list[str]): The snippets extracted by
        the user quey.

    Returns:
        dict[str, str]: The prompt dict.
    """
    return {
        "user_input": query,
        "snippets": replace_single_curly_brackets(
            json.dumps(snippets)
        )
    }


def build_relevance_prompt(
    relevant_fragments: list[dict],
    user_input: str
) -> dict:
    """
    Builds the prompt for judging the relevance.

    Args:
        relevant_fragments (list[dict]): Retrieved relevant fragments.
        user_input (str): Query to use for vector store.

    Returns:
        dict[str, str]: The prompt dict.
    """
    fragments = {}
    for element in relevant_fragments:
        lines = element["page_content"].split("\n")
        lines = {i: line for i, line in enumerate(lines, start=1)}
        fragments[element["metadata"]["frag_id"]] = lines

    return {
        "user_input": user_input,
        "fragments": replace_single_curly_brackets(
            json.dumps(fragments)
        )
    }


def build_cypher_prompt(user_input: str) -> dict[str, str]:
    """
    Builds the prompt for creating cypher queries.

    Args:
        user_input (str): Query to use for KG.

    Returns:
        dict[str, str]: The prompt dict.
    """
    schema_yaml = read_yml(os.path.join(
        return_root_dir(),
        "node_ontology.yml"
    ))

    return {
        "user_input": user_input,
        "schema_yaml": replace_single_curly_brackets(json.dumps(schema_yaml))
    }


def build_answer_writer_prompt(
    user_input: str,
    result: list[Record] | Any | None
) -> dict[str, str | list[Record] | Any | None]:
    """
    Builds the prompt for creating the answer writing prompt.

    Args:
        user_input (str): Query used for KG.
        result (list): The result of the user input

    Returns:
        dict[str, str | list]: The prompt dict.
    """
    return {
        "user_input": user_input,
        "result": result
    }


def get_words_for_line(
    frag_id: str,
    line_id: str,
    neo_conn
) -> list[str]:
    """
    Returns the words for a line of a fragment.

    Args:
        frag_id (str): ID of fragment.
        line_id (str): ID of line.
        neo_conn (infrastructure.neo4jconnector.Neo4jConnection): Conn to
        the Neo4j database.

    Returns:
        str: Words of the line.
    """
    result = neo_conn.query(
        query=f"""
            MATCH (f:Fragment {{frag_id: '{frag_id}'}})-[r:HAS_LINE]-(l:Line {{line_id: '{line_id}'}})-[hw:HAS_WORD]-(w:Word)
            RETURN w.word ORDER BY l.line_position ASC, w.position_in_line ASC
        """
    )
    return " ".join([word.get("w.word") for word in result])


def get_translation_for_line(
    frag_id: str,
    line_id: str,
    neo_conn
) -> list[str]:
    """
    Returns the translations for a line of a fragment.

    Args:
        frag_id (str): ID of fragment.
        line_id (str): ID of line.
        neo_conn (infrastructure.neo4jconnector.Neo4jConnection): Conn to
        the Neo4j database.

    Returns:
        str: translations of the line.
    """
    result = neo_conn.query(query=f"""
        MATCH (f:Fragment {{frag_id: '{frag_id}'}})
        -[r:HAS_LINE]->(l:Line {{line_id:'{line_id}'}})
        -[hm:HAS_MEANING]->(tr:Translation)
        OPTIONAL MATCH
        (tr)<-[:HAS_MEANING]-(other:Line)
        WITH f, r, l, hm, tr,
            min(other.line_position) AS spanStart
        ORDER BY
        CASE WHEN spanStart < l.line_position THEN 0 ELSE 1 END,
        spanStart,
        hm.order
        RETURN tr.translation;
    """)
    return "\n".join([translation.get("tr.translation") for translation in result])


def get_lines_for_fragment(
    frag_id: str,
    neo_conn
):
    """
    Gets the line_id and line_position for every line in a fragment.

    frag_id (str): ID of fragment.
    neo_conn (infrastructure.neo4jconnector.Neo4jConnection): Conn to
    the Neo4j database.
    """
    result = neo_conn.query(query=f"""
    MATCH (f:Fragment {{frag_id:"{frag_id}"}})
    -[r:HAS_LINE]->(l:Line)
    RETURN l.line_id AS line_id, l.line_position AS line_position;
    """)
    fields = ["line_id", "line_position"]

    lines = [
        {field: line.get(field) for field in fields}
        for line in result
    ]

    for line in lines:
        line["words"] = get_words_for_line(
            frag_id=frag_id,
            line_id=line["line_id"],
            neo_conn=neo_conn
        )
        line["translations"] = get_translation_for_line(
            frag_id=frag_id,
            line_id=line["line_id"],
            neo_conn=neo_conn
        )

    return lines