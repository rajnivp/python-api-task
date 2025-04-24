"""
Chutes AI service integration for sentiment analysis.

This module provides functionality for analyzing sentiment of text data using
the Chutes AI API. It uses a fine-tuned Llama model to generate sentiment
scores for the provided data.
"""

import json
import re
from typing import Dict, Any, Optional, List

import aiohttp

from app.core.config import settings
from app.core.logger import logger


async def get_sentiment(data: List[Dict[str, Any]]) -> Optional[int]:
    """
    Get sentiment score for the provided data using Chutes AI API.
    
    This function sends the data to Chutes AI's Llama model and processes
    the response to extract a sentiment score between -100 and 100.
    
    Args:
        data (List[Dict[str, Any]]): List of dictionaries containing text data
                                    to analyze for sentiment
        
    Returns:
        Optional[int]: Sentiment score between -100 and 100, or None if an error occurs
    """
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
                "content": f"provide sentiment score on this from this nested dict after extracting "
                           f"relevant data correctly: {data}, "
                           f"where 100 is most positive and -100 being most negative, return only integer, "
                           f"Do not include an explaination, in response dict add key named sentiment_score "
                           f"with sentiment score as value of it"
            }
        ],
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.7
    }
    try:

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    "https://llm.chutes.ai/v1/chat/completions",
                    headers=headers,
                    json=body
            ) as response:
                res: bytes = await response.content.read()
                res_dict: Dict[str, Any] = json.loads(res.decode("utf-8"))
                return extract_sentiment_score(res_dict)
    except Exception as e:
        logger.error(f"Error getting sentiment data from chutes: {str(e)}", exc_info=True)


def extract_sentiment_score(response: Dict[str, Any]) -> Optional[int]:
    """
    Extract sentiment score from the Chutes AI API response.
    
    This function parses the API response to find an integer between -100 and 100
    that represents the sentiment score.
    
    Args:
        response (Dict[str, Any]): Response from the Chutes AI API
        
    Returns:
        Optional[int]: Extracted sentiment score, or None if extraction fails
    """
    try:
        content: str = response['choices'][0]['message']['content']
        # Look for an integer between -100 and 100 (adjust range as needed)
        match: Optional[re.Match] = re.search(r"(-?\d+)", content)
        if match:
            score: int = int(match.group(1))
            logger.info(f'Sentiment score: {score}')
            return score
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Error getting extracting sentiment score: {str(e)}", exc_info=True)
