from typing import List, Dict, Any

from datura_py import Datura

from app.core.config import settings
from app.core.logger import logger


def get_tweets(prompt: str) -> List[Dict[str, Any]]:
    datura: Datura = Datura(api_key=settings.datura_api_key)
    result: List[Dict[str, Any]] = datura.ai_search(
        prompt=prompt,
        tools=[
            'twitter'
        ],
        model='NOVA',
        date_filter='PAST_24_HOURS',
        streaming=False,
    )
    logger.info(f'Tweets fetched for prompt: {prompt}')

    return result
