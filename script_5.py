# Generate folder_watcher.py - File system monitoring
folder_watcher_content = '''"""
Folder watcher service for Code Backup Daemon
"""
import time
import logging
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirCreatedEvent

logger = logging.getLogger(__name__)

class FolderWatcher:
    """Monitors filesystem for new folders"""
    
    def __init__(self, config, on_new_folder_callback: Callable[[Path], None]):
        self.config = config
        self.code_folder = config.get_path('paths.code_folder')
        self.ignore_patterns = config.get('project_detection.ignore_patterns', [])
        self.on_new_folder_callback = on_new_folder_callback
        
        self.observer = Observer()
        self.is_running = False
        self.watched_folders: Set[str] = set()
        
        # Delay before processing new folders (let user set them up)
        self.processing_delay = 30  # seconds
    
    def start(self):
        """Start monitoring the code folder"""
        if self.is_running:
            logger.warning("Folder watcher is already running")
            return
        
        if not self.code_folder.exists():
            logger.error(f"Code folder does not exist: {self.code_folder}")
            return
        
        event_handler = NewFolderHandler(self)
        self.observer.schedule(
            event_handler, 
            str(self.code_folder), 
            recursive=False  # Only watch immediate subdirectories
        )
        
        self.observer.start()
        self.is_running = True
        
        logger.info(f"Started watching for new folders in: {self.code_folder}")
    
    def stop(self):
        """Stop monitoring"""
        if not self.is_running:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        
        logger.info("Stopped folder watcher")
    
    def should_ignore_folder(self, folder_path: Path) -> bool:
        """Check if folder should be ignored based on patterns"""
        folder_name = folder_path.name
        
        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern in folder_name.lower():
                return True
        
        # Ignore hidden folders
        if folder_name.startswith('.'):
            return True
        
        # Ignore common temporary/system folders
        temp_folders = [
            'tmp', 'temp', 'cache', 'logs', 'log', 
            'backup', 'backups', 'trash', 'recycle'
        ]
        
        if folder_name.lower() in temp_folders:
            return True
        
        return False
    
    def process_new_folder(self, folder_path: Path):
        """Process a newly created folder"""
        try:
            folder_str = str(folder_path)
            
            # Avoid duplicate processing
            if folder_str in self.watched_folders:
                return
            
            self.watched_folders.add(folder_str)
            
            # Check if we should ignore this folder
            if self.should_ignore_folder(folder_path):
                logger.debug(f"Ignoring folder: {folder_path}")
                return
            
            # Wait for user to set up the project
            logger.info(f"New folder detected: {folder_path.name} - waiting {self.processing_delay}s before processing...")
            time.sleep(self.processing_delay)
            
            # Check if folder still exists (user might have deleted it)
            if not folder_path.exists():
                logger.debug(f"Folder no longer exists: {folder_path}")
                return
            
            # Check if it's a valid project
            if self.is_valid_project(folder_path):
                logger.info(f"Processing new project: {folder_path.name}")
                self.on_new_folder_callback(folder_path)
            else:
                logger.debug(f"Not a valid project: {folder_path}")
                
        except Exception as e:
            logger.error(f"Error processing new folder {folder_path}: {e}")
    
    def is_valid_project(self, folder_path: Path) -> bool:
        """Determine if folder is a valid project worth backing up"""
        try:
            # Check if it's already a git repository
            if (folder_path / '.git').exists():
                logger.debug(f"Folder {folder_path} is already a git repository")
                return True
            
            # Get configuration
            min_size = self.config.get('project_detection.min_size_bytes', 1024)
            project_indicators = self.config.get('project_detection.project_indicators', [])
            code_extensions = self.config.get('project_detection.code_extensions', [])
            
            # Check for project indicator files
            has_indicator = False
            for indicator in project_indicators:
                if (folder_path / indicator).exists():
                    has_indicator = True
                    logger.debug(f"Found project indicator {indicator} in {folder_path}")
                    break
            
            # Check for code files
            has_code_files = False
            code_file_count = 0
            
            for extension in code_extensions:
                code_files = list(folder_path.glob(f"*{extension}"))
                if code_files:
                    has_code_files = True
                    code_file_count += len(code_files)
                    if code_file_count >= 2:  # Multiple code files indicate a project
                        break
                        
            # Also check subdirectories for code files (but not too deep)
            if not has_code_files:
                for subdir in folder_path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('.'):
                        for extension in code_extensions[:5]:  # Check only common extensions
                            if list(subdir.glob(f"*{extension}")):
                                has_code_files = True
                                break
                        if has_code_files:
                            break
            
            # Check folder size
            total_size = 0
            file_count = 0
            
            try:
                for file_path in folder_path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
                        
                        # Don't process huge folders
                        if total_size > 100 * 1024 * 1024:  # 100MB limit
                            break
                            
            except Exception as e:
                logger.debug(f"Error calculating folder size for {folder_path}: {e}")
                total_size = min_size  # Assume it meets minimum size
            
            is_substantial = total_size >= min_size
            has_multiple_files = file_count >= 3
            
            # Decision logic
            is_valid = (
                (has_indicator) or  # Has project files like package.json
                (has_code_files and is_substantial) or  # Has code and is substantial
                (has_code_files and has_multiple_files)  # Has code and multiple files
            )
            
            if is_valid:
                logger.info(
                    f"Valid project detected: {folder_path.name} "
                    f"(indicator: {has_indicator}, code: {has_code_files}, "
                    f"size: {total_size} bytes, files: {file_count})"
                )
            else:
                logger.debug(
                    f"Not a valid project: {folder_path.name} "
                    f"(indicator: {has_indicator}, code: {has_code_files}, "
                    f"size: {total_size} bytes, files: {file_count})"
                )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating project {folder_path}: {e}")
            return False
    
    def scan_existing_folders(self) -> list:
        """Scan for existing folders that might need processing"""
        existing_folders = []
        
        try:
            for item in self.code_folder.iterdir():
                if item.is_dir() and not self.should_ignore_folder(item):
                    if self.is_valid_project(item):
                        existing_folders.append(item)
            
            logger.info(f"Found {len(existing_folders)} existing projects")
            return existing_folders
            
        except Exception as e:
            logger.error(f"Error scanning existing folders: {e}")
            return []
    
    def get_status(self) -> dict:
        """Get status information about the watcher"""
        return {
            'is_running': self.is_running,
            'code_folder': str(self.code_folder),
            'watched_folders_count': len(self.watched_folders),
            'ignore_patterns': self.ignore_patterns
        }


class NewFolderHandler(FileSystemEventHandler):
    """Handles filesystem events for new folders"""
    
    def __init__(self, watcher: FolderWatcher):
        self.watcher = watcher
        super().__init__()
    
    def on_created(self, event):
        """Handle directory creation events"""
        if isinstance(event, DirCreatedEvent):
            folder_path = Path(event.src_path)
            logger.debug(f"Directory created: {folder_path}")
            
            # Process in background to avoid blocking the watcher
            import threading
            thread = threading.Thread(
                target=self.watcher.process_new_folder,
                args=(folder_path,)
            )
            thread.daemon = True
            thread.start()
    
    def on_moved(self, event):
        """Handle directory move/rename events"""
        if event.is_directory:
            dest_path = Path(event.dest_path)
            logger.debug(f"Directory moved/renamed to: {dest_path}")
            
            # Treat moves as new folder creation
            import threading
            thread = threading.Thread(
                target=self.watcher.process_new_folder,
                args=(dest_path,)
            )
            thread.daemon = True
            thread.start()
'''

with open("folder_watcher.py", "w") as f:
    f.write(folder_watcher_content)

print("✅ Generated folder_watcher.py")