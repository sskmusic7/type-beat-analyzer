"""
Gemini API Integration for 3D Visualization Code Generation
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
import sys
from pathlib import Path

# Load environment
env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(env_path)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def get_available_models():
    """
    List available Gemini models for the current API key.
    
    Returns:
        List of available model names
    """
    if not GEMINI_API_KEY:
        return []
    
    try:
        models = genai.list_models()
        available = [m.name.split('/')[-1] for m in models if 'generateContent' in m.supported_generation_methods]
        return available
    except Exception as e:
        print(f"Error listing models: {e}")
        return []


def get_best_model():
    """
    Get the best available model, trying latest models first (February 2026).
    
    Returns:
        Model name string
    """
    # Latest models first (February 2026)
    preferred_models = [
        'gemini-2.5-flash',           # Latest stable (February 2026)
        'gemini-2.5-flash-image',      # Latest with image capabilities
        'gemini-3-flash-preview',     # Latest preview
        'gemini-3-pro-preview',       # Latest pro preview
        'gemini-1.5-pro',             # Fallback
        'gemini-1.5-flash',           # Fallback
        'gemini-pro',                 # Legacy fallback
        'gemini-1.0-pro'              # Legacy fallback
    ]
    
    available = get_available_models()
    
    # Try preferred models first
    for model in preferred_models:
        if model in available:
            return model
    
    # Fallback to first available
    if available:
        return available[0]
    
    # Default fallback to latest stable
    return 'gemini-2.5-flash'


def generate_3d_visualization_code(prompt: str, context: dict = None) -> str:
    """
    Use Gemini to generate 3D visualization code based on a prompt.
    
    Args:
        prompt: User's description of what visualization they want
        context: Optional context about available data (fingerprints, artists, etc.)
    
    Returns:
        Generated Python code as string
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Build system prompt with context (optimized for speed)
    system_prompt = """Generate Python code for 3D Plotly visualizations. Keep it concise and working.

Requirements:
- Use Plotly (go or px)
- Interactive 3D plots
- Include imports
- Streamlit compatible (st.plotly_chart)
- Ready to run

Be concise but complete."""
    
    # Add context if provided
    if context:
        context_str = "\n\nAvailable data context:\n"
        if 'fingerprints' in context:
            context_str += f"- Fingerprints: {context['fingerprints']} items, {context.get('fingerprint_dim', 128)}-dimensional embeddings\n"
        if 'artists' in context:
            context_str += f"- Artists: {', '.join(context['artists'][:5])}...\n"
        if 'data_path' in context:
            context_str += f"- Data path: {context['data_path']}\n"
        system_prompt += context_str
    
    # Full prompt
    full_prompt = f"""{system_prompt}

User request: {prompt}

Generate the complete Python code:"""
    
    try:
        # Get the best available model
        model_name = get_best_model()
        
        # Configure generation with timeout and retry settings
        generation_config = {
            'temperature': 0.7,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8192,
        }
        
        model = genai.GenerativeModel(
            model_name,
            generation_config=generation_config
        )
        
        # Generate with timeout handling
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Generate content (timeout handled by library default)
                response = model.generate_content(full_prompt)
                break
            except Exception as e:
                error_str = str(e)
                if "504" in error_str or "timeout" in error_str.lower():
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        raise Exception(f"Request timed out after {max_retries} attempts. The prompt might be too complex. Try simplifying it or try again later.")
                else:
                    raise
        
        # Extract code from response
        code = response.text
        
        # Try to extract code block if wrapped in markdown
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        return code
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


def execute_visualization_code(code: str, data_context: dict = None) -> dict:
    """
    Safely execute generated visualization code and return the figure.
    
    Args:
        code: Python code to execute
        data_context: Dictionary with available data (fingerprints, artists, etc.)
    
    Returns:
        Dictionary with 'success', 'figure' (Plotly figure), and 'error' (if any)
    """
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np
    import pandas as pd
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    import json
    from pathlib import Path
    
    # Prepare data context in local scope
    if data_context:
        fingerprints = data_context.get('fingerprints', [])
        artists = data_context.get('artists', [])
        tracks = data_context.get('tracks', [])
        training_data = data_context.get('training_data', [])
        
        # Convert fingerprints to numpy array if available
        if fingerprints:
            embeddings = np.array([fp if isinstance(fp, (list, np.ndarray)) else fp.get('fingerprint', []) 
                                 for fp in fingerprints])
        else:
            embeddings = None
    else:
        fingerprints = []
        artists = []
        tracks = []
        training_data = []
        embeddings = None
    
    # Create safe execution environment
    safe_globals = {
        'np': np,
        'pd': pd,
        'go': go,
        'px': px,
        'PCA': PCA,
        'TSNE': TSNE,
        'json': json,
        'Path': Path,
        'fingerprints': fingerprints,
        'artists': artists,
        'tracks': tracks,
        'training_data': training_data,
        'embeddings': embeddings,
        'len': len,
        'range': range,
        'list': list,
        'dict': dict,
        'zip': zip,
        'enumerate': enumerate,
        'sorted': sorted,
        'set': set,
    }
    
    try:
        # Execute code
        exec(code, safe_globals)
        
        # Try to find the figure (common variable names)
        figure = None
        for var_name in ['fig', 'figure', 'plot', 'chart']:
            if var_name in safe_globals:
                figure = safe_globals[var_name]
                break
        
        if figure is None:
            # Check if it's a Plotly figure in any variable
            for var_name, var_value in safe_globals.items():
                if isinstance(var_value, (go.Figure, go.FigureWidget)):
                    figure = var_value
                    break
        
        if figure is None:
            return {
                'success': False,
                'error': 'No Plotly figure found in generated code. Make sure the code creates a variable named "fig" or "figure".',
                'figure': None
            }
        
        return {
            'success': True,
            'figure': figure,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'figure': None
        }


def load_training_data_for_context(data_path: str = None) -> dict:
    """
    Load training data to provide context for Gemini.
    
    Returns:
        Dictionary with fingerprints, artists, tracks, etc.
    """
    import json
    import numpy as np
    from pathlib import Path
    
    if data_path is None:
        data_path = Path(__file__).parent.parent / "ml" / "data" / "training_fingerprints" / "final_training_data.json"
    else:
        data_path = Path(data_path)
    
    if not data_path.exists():
        return {
            'fingerprints': [],
            'artists': [],
            'tracks': [],
            'training_data': [],
            'fingerprint_dim': 128
        }
    
    with open(data_path, 'r') as f:
        training_data = json.load(f)
    
    fingerprints = [item.get('fingerprint', []) for item in training_data]
    artists = [item.get('artist', 'Unknown') for item in training_data]
    tracks = [item.get('track_name', 'Unknown') for item in training_data]
    
    # Get fingerprint dimension
    if fingerprints and len(fingerprints[0]) > 0:
        fingerprint_dim = len(fingerprints[0]) if isinstance(fingerprints[0], (list, np.ndarray)) else 128
    else:
        fingerprint_dim = 128
    
    return {
        'fingerprints': fingerprints,
        'artists': artists,
        'tracks': tracks,
        'training_data': training_data,
        'fingerprint_dim': fingerprint_dim,
        'data_path': str(data_path)
    }
