import json
import re
import logging
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)

def extract_sentiment_score_from_stream(stream_data: List[Dict[str, Any]]) -> Optional[float]:
    """
    Extract the sentiment score from a streaming LLM response.
    
    Args:
        stream_data: List of JSON objects from the streaming response
        
    Returns:
        The extracted sentiment score as a float, or None if not found
    """
    try:
        # Combine all content chunks to reconstruct the full response
        full_text = ""
        for chunk in stream_data:
            if "choices" in chunk and chunk["choices"]:
                for choice in chunk["choices"]:
                    if "delta" in choice and "content" in choice["delta"]:
                        full_text += choice["delta"]["content"]
        
        # Look for a number that appears after "sentiment score" or similar phrases
        # This regex pattern looks for a number (integer or decimal) after phrases like "sentiment score is"
        pattern = r"(?:sentiment score|score)(?:\s+is|\s+for|\s+of)?\s*[:=]?\s*(\d+(?:\.\d+)?)"
        match = re.search(pattern, full_text, re.IGNORECASE)
        
        if match:
            score = float(match.group(1))
            logger.info(f"Extracted sentiment score: {score}")
            return score
        
        # If the above pattern doesn't work, try to find any number in the text
        # This is a fallback in case the model formats the response differently
        number_pattern = r"(\d+(?:\.\d+)?)"
        matches = re.findall(number_pattern, full_text)
        
        if matches:
            # Convert all found numbers to floats
            numbers = [float(num) for num in matches]
            # If there's only one number, use it
            if len(numbers) == 1:
                logger.info(f"Found single number in response: {numbers[0]}")
                return numbers[0]
            # If there are multiple numbers, look for one in a reasonable range (0-100)
            for num in numbers:
                if 0 <= num <= 100:
                    logger.info(f"Found number in reasonable range: {num}")
                    return num
        
        logger.warning("No sentiment score found in the response")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting sentiment score: {str(e)}")
        return None

def process_sentiment_response(response_data: Union[str, List[Dict[str, Any]]]) -> Optional[float]:
    """
    Process a sentiment analysis response, handling both streaming and non-streaming formats.
    
    Args:
        response_data: Either a JSON string or a list of streaming response chunks
        
    Returns:
        The extracted sentiment score as a float, or None if not found
    """
    try:
        # If response_data is a string, try to parse it as JSON
        if isinstance(response_data, str):
            try:
                parsed_data = json.loads(response_data)
                # If it's a list, treat it as streaming data
                if isinstance(parsed_data, list):
                    return extract_sentiment_score_from_stream(parsed_data)
                # Otherwise, try to extract from a single response
                elif isinstance(parsed_data, dict):
                    if "sentiment_score" in parsed_data:
                        return float(parsed_data["sentiment_score"])
                    elif "score" in parsed_data:
                        return float(parsed_data["score"])
            except json.JSONDecodeError:
                # If it's not valid JSON, try to extract a number directly
                number_pattern = r"(\d+(?:\.\d+)?)"
                match = re.search(number_pattern, response_data)
                if match:
                    return float(match.group(1))
        
        # If response_data is already a list, treat it as streaming data
        elif isinstance(response_data, list):
            return extract_sentiment_score_from_stream(response_data)
        
        # If response_data is a dict, try to extract the score
        elif isinstance(response_data, dict):
            if "sentiment_score" in response_data:
                return float(response_data["sentiment_score"])
            elif "score" in response_data:
                return float(response_data["score"])
        
        logger.warning("Could not extract sentiment score from response")
        return None
        
    except Exception as e:
        logger.error(f"Error processing sentiment response: {str(e)}")
        return None 