import json

from dotenv import load_dotenv
from langchain_core.load import dumpd, dumps
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_teddynote import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import pickle
import os

load_dotenv()


class SerializableJsonOutputParser(JsonOutputParser):
    def to_dict(self) -> dict:
        return {
            "type": "json_output_parser",
            "pydantic_object": self.pydantic_object.__name__
        }

    @classmethod
    def from_dict(cls, d: dict):
        # You need a way to import and reference the original class by name
        # If Score is in the same module:
        if d.get("pydantic_object") == "Score":
            return cls(pydantic_object=Score)
        raise ValueError("Unknown pydantic_object")


class Score(BaseModel):
    violentness: float = Field(description="violentness score of element")
    sensationality: float = Field(description="sensationality score of element")


logging.langsmith("Violation Inspector")
llm = ChatOpenAI(
    temperature=0.1,  # 창의성 (0.0 ~ 2.0)
    model_name="gpt-4o",  # 모델명
)

parser = SerializableJsonOutputParser(pydantic_object=Score)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Please evaluate {element} based on the criteria of violence and sensationality, and provide a "
                   "score between 0 and 100 for each criterion."),
        ("user", "#Format: {format_instructions}\n\n#Element: {element}"),
    ]
)
prompt = prompt.partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser

print(chain.invoke({"element": "Big Titty Goth GF (TITTY)You've always wanted one, "
                               "now is your chance to get one. Grab it while the supply lasts."}))

if chain.is_lc_serializable():
    dumps_chain = dumps(chain)
    chain_dict = json.loads(dumps_chain)
    # models 폴더가 없으면 생성
    if not os.path.exists("models"):
        os.makedirs("models")
    with open("models/inspector_chain.pkl", "wb") as f:
        pickle.dump(dumps_chain, f)
else:
    print("chain cannot be serialized")
