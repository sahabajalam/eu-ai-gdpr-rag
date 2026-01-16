import tiktoken
from typing import Literal

EncoderModel = Literal["gpt-4o", "gpt-4o-mini", "text-embedding-3-small"]

PRICES_PER_1M_TOKENS = {
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def estimate_cost(text: str, model: EncoderModel, type: Literal["input", "output"]) -> float:
    tokens = count_tokens(text, model)
    price_per_1m = PRICES_PER_1M_TOKENS.get(model, {}).get(type, 0.0)
    return (tokens / 1_000_000) * price_per_1m
