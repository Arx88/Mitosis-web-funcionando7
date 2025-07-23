#!/usr/bin/env python3
"""
Debug the override logic directly
"""

def debug_override_logic():
    """Debug why override logic isn't working"""
    
    message = "Buscar restaurantes en Valencia"
    current_icon = "target"
    
    print(f"Message: {message}")
    print(f"Current icon: {current_icon}")
    print(f"Message lower: {message.lower()}")
    
    # Test location words detection
    location_words = ['restaurante', 'bar', 'comida', 'valencia', 'madrid', 'barcelona', 'lugar', 'ubicación']
    location_matches = [word for word in location_words if word in message.lower()]
    print(f"Location matches: {location_matches}")
    
    has_location = any(word in message.lower() for word in location_words)
    print(f"Has location words: {has_location}")
    
    not_map_icon = current_icon not in ['map', 'navigation', 'globe']
    print(f"Not a map icon: {not_map_icon}")
    
    should_override = has_location and not_map_icon
    print(f"Should override: {should_override}")
    
    # Test unified function
    def determine_unified_icon_test(task_message: str) -> str:
        """Test version"""
        content_lower = task_message.lower()
        
        # Priority 2: Location/Maps  
        location_words = ['restaurante', 'bar', 'comida', 'valencia', 'madrid', 'barcelona', 'lugar', 'ubicación', 'dirección', 'mapa', 'localizar']
        if any(word in content_lower for word in location_words):
            return 'map'
        
        return 'target'
    
    unified_icon = determine_unified_icon_test(message)
    print(f"Unified function result: {unified_icon}")
    
    # Test target override logic
    is_target_generic = current_icon == 'target' and unified_icon != 'target'
    print(f"Target override condition: {is_target_generic}")

if __name__ == "__main__":
    debug_override_logic()