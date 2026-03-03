from typing import Any, TypeAlias
import re
import streamlit as st
from langchain.callbacks.streamlit import StreamlitCallbackHandler
from neo4j import Record
from typing_extensions import Literal
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.types import Command
import json
import uuid
import os
import sys

from rag import qdrant



from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSerializable
from textwrap import dedent
from uuid import uuid4
from langchain_core.exceptions import OutputParserException



try:
    from ..utils import utils_functions
    # from ..domain import fragments
    from .agent_data_definitions import (
        UserWish,
        QueryRewrite,
        RelevanceRanking,
        CypherResult,
        GeneratedAnswer
    )
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
    #sys.path.append(os.path.abspath('../domain'))
    #sys.path.append(os.path.abspath('../infrastructure'))
    #sys.path.append(os.path.abspath('../utils'))
    # import neo4jconnector
    # import fragments
    from utils import utils_functions

    from agents_src.agent_data_definitions import (
        UserWish,
        QueryRewrite,
        RelevanceRanking,
        CypherResult,
        GeneratedAnswer
    )


class agentCollection:
    def __init__(
        self,
        model_name_powerful: str = "deepseek-chat",
        model_name_fast: str = "deepseek-chat"
    ) -> None:
        self.model_powerful = init_chat_model(model_name_powerful)
        self.model_fast = init_chat_model(model_name_fast)
        self.intent_decider = self.create_agent("decide_user_wish")
        self.rewriter = self.create_agent("query_rewrite")
        self.judge_relevance = self.create_agent("judge_relevance")
        self.cypher_generator = self.create_agent("cypher_generation")
        self.answer_writer = self.create_agent("answer_generation_nodes")

    def create_agent(self, prompt_name: str) -> RunnableSerializable:
        """
        Creates the chain for an agent.

        Args:
            prompt_name (str): The name of the prompt.
        Returns:
            RunnableSerializable:  Chain of prompt with LLM and parser.
        """
        prompt = utils_functions.return_prompt(prompt_name)
        if prompt_name == "decide_user_wish":
            parser = PydanticOutputParser(pydantic_object=UserWish)
            chain = prompt | self.model_fast | parser
        elif prompt_name == "query_rewrite":
            parser = PydanticOutputParser(pydantic_object=QueryRewrite)
            chain = prompt | self.model_fast | parser
        elif prompt_name == "judge_relevance":
            parser = PydanticOutputParser(pydantic_object=RelevanceRanking)
            chain = prompt | self.model_powerful | parser
        elif prompt_name == "cypher_generation":
            parser = PydanticOutputParser(pydantic_object=CypherResult)
            chain = prompt | self.model_powerful | parser
        elif prompt_name == "answer_generation_nodes":
            parser = PydanticOutputParser(pydantic_object=GeneratedAnswer)
            chain = prompt | self.model_powerful | parser

        return chain

    def decide_indent_agent(self, user_input: str) -> bool:
        """
        Invokes the agent to decide on the user ident of either
        searching in the translations or in the KG.

        Args:
            user_input (str): The input of the user.

        Returns:
            bool: If the user wants to search in the translations
            or not.
        """
        user_prompt = utils_functions.build_user_wish_prompt(
            user_input=user_input
        )
        return self.intent_decider.invoke(user_prompt).searchTranslation

    def rewrite_agent(
        self,
        query: str,
        snippets: list[str]
    ) -> str:
        """
        Invokes the agent to rewrite the query for a type of
        vector.

        Args:
            snippets (list[str]): The snippets extracted by the user
            quey.
            query (str): Query to use for vector store.

        Returns:
            str: THe rewrote query
        """
        user_prompt = utils_functions.build_query_rewrite_prompt(
            query=query,
            snippets=snippets
        )
        query = self.rewriter.invoke(user_prompt)
        return query.final_query

    def relevance_agent(
        self,
        user_input: str,
        relevant_fragments: list[dict]
    ) -> dict:
        """
        Invokes the agent to judge the relevance of fragments.

        Args:
        relevant_fragments (list[dict]): Retrieved relevant fragments.
        user_input (str): Query to use for vector store.

        Returns:
            dict: The ranked fragments.
        """
        user_prompt = utils_functions.build_relevance_prompt(
            user_input=user_input,
            relevant_fragments=relevant_fragments
        )
        ranked_result = self.judge_relevance.invoke(user_prompt)
        return ranked_result

    def cypher_agent(
        self,
        user_input: str
    ) -> str:
        """
        Invokes the agent to create a cypher query out of the
        user input.

        Args:
            user_input (str): Query to use for KG.

        Returns:
            str: Created Cypher query.
        """
        user_prompt = utils_functions.build_cypher_prompt(
            user_input=user_input
        )
        return self.cypher_generator.invoke(user_prompt)

    def answer_writing_agent(
        self,
        user_input: str,
        result: list[Record] | Any | None
    ) -> str:
        st_callback = StreamlitCallbackHandler(st.empty())

        user_prompt = utils_functions.build_answer_writer_prompt(
            user_input=user_input,
            result=result
        )
        prompt = utils_functions.return_prompt("answer_generation_nodes")

        raw_chain = prompt | self.model_powerful

        collected_text = ""

        # stream events: these may be AIMessageChunk objects
        for event in raw_chain.stream(
            user_prompt,
            config={"callbacks": [st_callback]}
        ):
            if hasattr(event, "content"):
                collected_text += event.content or ""

        # 🔎 clean markdown fences like ```json ... ```
        match = re.search(r"```(?:json)?(.*?)```", collected_text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            # fallback: try to find just a JSON object
            match = re.search(r"\{.*\}", collected_text, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError(f"No valid JSON found in output: {collected_text}")

        # ✅ now safe to parse with Pydantic
        parsed = GeneratedAnswer.model_validate_json(json_str)
        return parsed.answer.replace("\\n", "\n")

