"""
🎯 Lista de herramientas MCP permitidas
Solo las herramientas esenciales para el sistema Bedrock MCP
"""

# Herramientas MCP permitidas por categoría
ALLOWED_TOOLS = {
    # Core MCP - Funcionalidades básicas
    'core': [
        'prompt_understanding',
    ],
    
    # Diagramas AWS - Generación de arquitecturas
    'diagrams': [
        'generate_diagram',
        'list_icons', 
        'get_diagram_examples',
    ],
    
    # Documentación AWS - Búsqueda y consulta
    'documentation': [
        'search_documentation',
        'read_documentation', 
        'recommend',
    ],
    
    # CloudFormation - Templates e infraestructura
    'cloudformation': [
        'create_resource',
        'read_resource',
        'update_resource', 
        'delete_resource',
        'list_resources',
        'get_resource_schema',
        'generate_template',
    ],
    
    # Pricing - Calculadoras de costos (usando nuestros generadores internos)
    'pricing': [
        # Estas se manejan internamente con document_endpoints.py
        # No necesitamos herramientas MCP adicionales para pricing
    ]
}

# Lista plana de todas las herramientas permitidas
ALL_ALLOWED_TOOLS = []
for category, tools in ALLOWED_TOOLS.items():
    ALL_ALLOWED_TOOLS.extend(tools)

def is_tool_allowed(tool_name: str) -> bool:
    """Verifica si una herramienta está permitida"""
    return tool_name in ALL_ALLOWED_TOOLS

def get_allowed_tools_by_category(category: str) -> list:
    """Obtiene herramientas permitidas por categoría"""
    return ALLOWED_TOOLS.get(category, [])

def get_all_categories() -> list:
    """Obtiene todas las categorías disponibles"""
    return list(ALLOWED_TOOLS.keys())
