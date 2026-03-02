from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings

classifier_llm = ChatOpenAI(
    model=settings.classifier_model,
    model_kwargs={"reasoning_effort": "low"},
)

challenger_llm = ChatOpenAI(
    model=settings.challenger_model,
    model_kwargs={"reasoning_effort": "medium"},
)

agent_llm = ChatOpenAI(
    model=settings.agent_model,
    model_kwargs={"reasoning_effort": "medium"},
)

evaluator_llm = ChatOpenAI(
    model=settings.evaluator_model,
    model_kwargs={"reasoning_effort": "low"},
)

generator_llm = ChatOpenAI(
    model=settings.generator_model,
    temperature=0.7,
)

embeddings = OpenAIEmbeddings(model=settings.embedding_model)
