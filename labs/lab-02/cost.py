"""
OpenRouter Token Cost Calculator

A simple library to calculate the cost of OpenRouter API calls
based on token usage from chat completion responses.

INSTALLATION:
    pip install requests

USAGE:

    from cost import calculate_cost
    import requests
    
    # After making an API call, pass the completion response
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'anthropic/claude-3.5-sonnet',
            'messages': [{'role': 'user', 'content': 'Hello!'}]
        }
    )
    
    completion = response.json()
    
    # Calculate the cost
    cost = calculate_cost(completion)
    print(f"Total cost: ${cost['total']:.6f}")
    print(f"Tokens used: {cost['tokens']['total']}")

RETURN VALUE:

    {
        'input': 0.000060,      # Cost for input tokens
        'output': 0.000225,     # Cost for output tokens
        'total': 0.000285,      # Total cost
        'tokens': {
            'prompt': 20,       # Number of input tokens
            'completion': 75,   # Number of output tokens
            'total': 95        # Total tokens
        },
        'model': 'anthropic/claude-3.5-sonnet'
    }

ALTERNATIVE USAGE WITH OPENAI SDK:

    from openai import OpenAI
    from token_cost import calculate_cost
    
    client = OpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=API_KEY
    )
    
    completion = client.chat.completions.create(
        model='anthropic/claude-3.5-sonnet',
        messages=[{'role': 'user', 'content': 'Hello!'}]
    )
    
    # Convert to dict for our function
    completion_dict = completion.model_dump()
    cost = calculate_cost(completion_dict)
"""

import requests
from typing import Dict, Any


def _get_model_pricing(model_id: str) -> Dict[str, float]:
    """
    Fetches pricing information for a specific model from OpenRouter
    
    Args:
        model_id: The model ID
    
    Returns:
        Dictionary with 'prompt' and 'completion' pricing per token
    """
    try:
        response = requests.get(
            'https://openrouter.ai/api/v1/models'
        )
        response.raise_for_status()
        
        data = response.json()
        model = next(
            (m for m in data['data'] if m['id'] == model_id), 
            None
        )
        
        if not model or 'pricing' not in model:
            print(f'Warning: No pricing found for {model_id}')
            return {'prompt': 0.0, 'completion': 0.0}
        
        return {
            'prompt': float(model['pricing']['prompt'] or 0),
            'completion': float(
                model['pricing']['completion'] or 0
            )
        }
    except Exception as e:
        print(f'Error fetching pricing: {e}')
        return {'prompt': 0.0, 'completion': 0.0}


def calculate_cost(completion: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the cost in USD from a chat completion response
    
    Args:
        completion: The chat completion response object
    
    Returns:
        Dictionary with 'input', 'output', 'total' costs, token 
        counts, and model name
    
    Raises:
        ValueError: If completion is missing required fields
    """
    model_id = completion.get('model')
    usage = completion.get('usage')
    
    if not model_id:
        raise ValueError(
            'Completion response missing model field'
        )
    
    if not usage:
        raise ValueError(
            'Completion response missing usage field'
        )
    
    # Fetch pricing for the model used
    pricing = _get_model_pricing(model_id)
    
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)
    
    input_cost = prompt_tokens * pricing['prompt']
    output_cost = completion_tokens * pricing['completion']
    total_cost = input_cost + output_cost
    
    return {
        'input': input_cost,
        'output': output_cost,
        'total': total_cost,
        'tokens': {
            'prompt': prompt_tokens,
            'completion': completion_tokens,
            'total': total_tokens
        },
        'model': model_id
    }