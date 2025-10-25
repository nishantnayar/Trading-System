"""
CSS Configuration for Trading System Streamlit UI
Easy customization of colors, fonts, and styling
"""

# Color scheme configuration
COLORS = {
    "primary": "#1e40af",      # Blue
    "secondary": "#3b82f6",    # Light Blue
    "success": "#10b981",      # Green
    "warning": "#f59e0b",      # Orange
    "error": "#ef4444",        # Red
    "background": "#f8fafc",   # Light Gray
    "text": "#374151",         # Dark Gray
    "border": "#e2e8f0",       # Border Gray
    "sidebar": "#1e3a8a",     # Dark Blue for sidebar
}

# Font configuration
FONTS = {
    "primary": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "monospace": "'Fira Code', 'Monaco', 'Consolas', monospace",
    "heading": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
}

# Spacing configuration
SPACING = {
    "small": "0.5rem",
    "medium": "1rem",
    "large": "1.5rem",
    "xlarge": "2rem",
}

# Border radius configuration
BORDER_RADIUS = {
    "small": "4px",
    "medium": "6px",
    "large": "8px",
    "xlarge": "12px",
}

# Shadow configuration
SHADOWS = {
    "small": "0 1px 2px rgba(0, 0, 0, 0.05)",
    "medium": "0 2px 4px rgba(0, 0, 0, 0.1)",
    "large": "0 4px 8px rgba(0, 0, 0, 0.15)",
    "xlarge": "0 8px 16px rgba(0, 0, 0, 0.2)",
}

# Animation configuration
ANIMATIONS = {
    "fast": "0.15s",
    "normal": "0.2s",
    "slow": "0.3s",
    "slower": "0.5s",
}

def generate_css_variables():
    """Generate CSS variables from configuration"""
    css_vars = ":root {\n"
    
    # Add color variables
    for name, value in COLORS.items():
        css_vars += f"  --{name}-color: {value};\n"
    
    # Add font variables
    for name, value in FONTS.items():
        css_vars += f"  --{name}-font: {value};\n"
    
    # Add spacing variables
    for name, value in SPACING.items():
        css_vars += f"  --{name}-spacing: {value};\n"
    
    # Add border radius variables
    for name, value in BORDER_RADIUS.items():
        css_vars += f"  --{name}-radius: {value};\n"
    
    # Add shadow variables
    for name, value in SHADOWS.items():
        css_vars += f"  --{name}-shadow: {value};\n"
    
    # Add animation variables
    for name, value in ANIMATIONS.items():
        css_vars += f"  --{name}-duration: {value};\n"
    
    css_vars += "}\n"
    return css_vars

def get_theme_css():
    """Get theme-specific CSS"""
    return f"""
    /* Theme-specific styles using CSS variables */
    .main h1 {{
        color: var(--primary-color);
        border-bottom: 3px solid var(--secondary-color);
        font-family: var(--heading-font);
    }}
    
    .metric-container {{
        background: linear-gradient(135deg, var(--background-color) 0%, #e2e8f0 100%);
        border: 1px solid var(--border-color);
        border-radius: var(--large-radius);
        padding: var(--medium-spacing);
        box-shadow: var(--medium-shadow);
        transition: all var(--normal-duration) ease;
    }}
    
    .metric-container:hover {{
        box-shadow: var(--large-shadow);
        transform: translateY(-1px);
    }}
    
    .card {{
        background: white;
        border-radius: var(--large-radius);
        padding: var(--large-spacing);
        margin: var(--medium-spacing) 0;
        box-shadow: var(--medium-shadow);
        border: 1px solid var(--border-color);
        transition: all var(--normal-duration) ease;
    }}
    
    .card:hover {{
        box-shadow: var(--large-shadow);
        transform: translateY(-1px);
    }}
    """

# Export configuration for easy access
__all__ = ['COLORS', 'FONTS', 'SPACING', 'BORDER_RADIUS', 'SHADOWS', 'ANIMATIONS', 
           'generate_css_variables', 'get_theme_css']
