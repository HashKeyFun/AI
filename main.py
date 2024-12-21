import os
from fastapi import FastAPI, HTTPException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging
import json

from model import SerializableJsonOutputParser

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class Score(BaseModel):
    violentness: float = Field(description="violentness score of element")
    sensationality: float = Field(description="sensationality score of element")


class Description(BaseModel):
    description: str


def load_model():
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
    return chain


@app.post("/inspect/description")
async def inspect_description(description: Description):

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise HTTPException(status_code=500, detail="API key not configured.")

        # 체인 실행
        data = load_model().invoke({"element": str(description.description)})
        # Pydantic 검증
        score = Score(**data)
        return {"result": score.dict()}
    except Exception as e:
        logger.error(f"Error during description inspection: {e}")
        raise HTTPException(status_code=500, detail="Error processing the request.")
