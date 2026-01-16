import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """Configure standard logging for the project."""
    
    logger = logging.getLogger("eu_ai_gdpr")
    logger.setLevel(log_level)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_file:
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
