from typing import TypedDict, Annotated
from pydantic import BaseModel, Field, RootModel, model_validator


class UserWish(BaseModel):
    searchTranslation: bool = Field(
        ...,
        description="If the user wants to search in text"
    )


class QueryRewrite(BaseModel):
    expanded_query: str = Field(..., description="The expanded user query")
    final_query: str = Field(..., description="The keyword query")


class RelevanceJudge(BaseModel):
    frag_id: str = Field(..., description="The ID of the Fragment")
    relevant_line: str = Field(..., description="The relevant line")


class RelevanceRanking(RootModel[dict[str, RelevanceJudge]]):

    """
    A mapping from *any* slot-name (string) to its SlotDetail.
    """
    pass


class CypherResult(BaseModel):
    cypher: str = Field(
        ...,
        description="The generated Cypher query string to execute against Neo4j"
    )


class GeneratedAnswer(BaseModel):
    answer: str = Field(
        ...,
        description="The generated answer from the user input and result"
    )