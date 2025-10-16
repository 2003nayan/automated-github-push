"""
Main entry point for Code Backup Daemon
"""
import logging
import sys
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from backup_service import BackupService

logger = logging.getLogger(__name__)

def setup_logging(config):
    """Setup logging configuration"""
    log_level = config.get('daemon.log_level', 'INFO')
    log_file = config.get_path('daemon.log_file')

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point"""
    try:
        # Load configuration
        config = Config()

        # Setup logging
        setup_logging(config)

        logger.info("Starting Code Backup Daemon")

        # Validate configuration
        if not config.validate():
            logger.error("Configuration validation failed")
            sys.exit(1)

        # Create and start backup service
        service = BackupService(config)
        service.start()

        # Keep running until interrupted
        try:
            import signal
            import time

            def signal_handler(signum, frame):
                logger.info("Received shutdown signal")
                service.stop()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            while service.is_running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            service.stop()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
