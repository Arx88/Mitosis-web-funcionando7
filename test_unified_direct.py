#!/usr/bin/env python3
"""
Test the unified function directly
"""

def test_unified_function():
    """Test the determine_unified_icon function logic directly"""
    
    def determine_unified_icon_test(task_message: str) -> str:
        """Test version of the unified function"""
        content_lower = task_message.lower()
        print(f"Testing: '{task_message}'")
        print(f"Lowercase: '{content_lower}'")
        
        # Check location condition
        location_words = ['restaurante', 'bar', 'comida', 'valencia', 'madrid', 'barcelona', 'lugar', 'ubicación', 'dirección', 'mapa', 'localizar']
        location_matches = [word for word in location_words if word in content_lower]
        print(f"Location matches: {location_matches}")
        
        if any(word in content_lower for word in location_words):
            return 'map'
        
        # Check search condition  
        search_words = ['buscar', 'investigar', 'estudiar', 'search', 'investigación', 'research']
        search_matches = [word for word in search_words if word in content_lower]
        print(f"Search matches: {search_matches}")
        
        if any(word in content_lower for word in search_words):
            return 'search'
        
        return 'target'
    
    # Test cases
    test_cases = [
        "Buscar restaurantes en Valencia",
        "Crear una aplicación web",
        "Analizar datos de ventas"
    ]
    
    for test in test_cases:
        result = determine_unified_icon_test(test)
        print(f"Result: {result}")
        print("-" * 50)

if __name__ == "__main__":
    test_unified_function()