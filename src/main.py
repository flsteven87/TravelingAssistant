#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TravelingAssistant - Main Application Entry Point

This module serves as the main entry point for the TravelingAssistant application.
It initializes the application, sets up the command-line interface, and handles
the main program flow.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow imports from other modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import application modules
from src.ui.cli import create_cli
from src.utils.config import Config
from src.utils.logger import setup_logger

def main():
    """Main application entry point."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Setup logging
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting TravelingAssistant application")
    
    # Load configuration
    config = Config()
    logger.debug("Configuration loaded successfully")
    
    try:
        # Create and run the command-line interface
        cli = create_cli()
        cli()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1
    
    logger.info("TravelingAssistant application completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())