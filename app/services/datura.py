"""
Datura service integration for social media data retrieval.

This module provides functionality for retrieving social media data (specifically tweets)
using the Datura API. It uses the NOVA model to search for relevant tweets based on
the provided prompt.
"""

from typing import List, Dict, Any

from datura_py import Datura

from app.core.config import settings
from app.core.logger import logger


def get_tweets(prompt: str) -> List[Dict[str, Any]]:
    """
    Retrieve tweets related to the given prompt using Datura API.
    
    This function uses Datura's AI search capability to find relevant tweets
    from the past 24 hours that match the provided prompt.
    
    Args:
        prompt (str): Search query to find relevant tweets
        
    Returns:
        List[Dict[str, Any]]: List of tweets matching the prompt, or empty list if an error occurs
    """
    datura: Datura = Datura(api_key=settings.datura_api_key)
    try:
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
    except Exception as e:
        logger.error(f"Error getting tweets from datura: {str(e)}", exc_info=True)
