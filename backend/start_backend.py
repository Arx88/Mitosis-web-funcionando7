#!/usr/bin/env python3
"""
Startup script for Unified Mitosis Agent Backend
"""

import os
import sys
import logging
from unified_api import create_unified_api, AgentConfig

def main():
    """Main startup function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Unified Mitosis Agent Backend...")
    
    # Create agent configuration
    config = AgentConfig(
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        prefer_local_models=True,
        max_cost_per_1k_tokens=0.01,
        memory_db_path="unified_agent.db",
        max_short_term_messages=100,
        max_concurrent_tasks=2,
        debug_mode=True
    )
    
    # Create and start the unified API
    api = create_unified_api(config)
    
    try:
        # Get port from environment or use default
        port = int(os.getenv("PORT", 5000))
        host = os.getenv("HOST", "0.0.0.0")
        
        logger.info(f"Starting server on {host}:{port}")
        api.run(host=host, port=port, debug=False)
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        logger.info("Shutting down...")
        api.shutdown()

if __name__ == "__main__":
    main()

