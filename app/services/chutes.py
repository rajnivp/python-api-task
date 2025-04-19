import json
import re
from typing import Dict, Any, Optional, Union

import aiohttp
from aiohttp import ClientSession, ClientResponse

from app.core.config import settings
from app.core.logger import logger


async def get_sentiment(data: Dict[str, Any]) -> Optional[int]:
    api_token: str = settings.chutes_api_key

    headers: Dict[str, str] = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }

    body: Dict[str, Any] = {
        "model": "unsloth/Llama-3.2-3B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": f"provide sentiment score on this from this nested dict: {data}, "
                           f"where 100 is most positive and -100 being most negative, return only integer, "
                           f"Do not include an explaination, in response dict add key named sentiment_score "
                           f"with sentiment score as value of it"
            }
        ],
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.7
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                "https://llm.chutes.ai/v1/chat/completions",
                headers=headers,
                json=body
        ) as response:
            res: bytes = await response.content.read()
            res_dict: Dict[str, Any] = json.loads(res.decode("utf-8"))
            return extract_sentiment_score(res_dict)


def extract_sentiment_score(response: Dict[str, Any]) -> Optional[int]:
    try:
        content: str = response['choices'][0]['message']['content']
        # Look for an integer between -100 and 100 (adjust range as needed)
        match: Optional[re.Match] = re.search(r"(-?\d+)", content)
        if match:
            score: int = int(match.group(1))
            logger.info(f'Sentiment score: {score}')
            return score
    except (KeyError, IndexError, ValueError):
        pass
