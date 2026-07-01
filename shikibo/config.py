import os
import getpass
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationError
 
class BAD_VALUE(ValueError):
    """Raised when an operation receives an invalid or empty parameter value."""
    pass

class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError as e:
            msg = e.errors()[0]["msg"]
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            raise BAD_VALUE(msg)

    user_id: str = Field(default="")
    role: str = Field(default="")
    display_name: str = Field(default="")
    root_dir: str = Field(default=r"G:\My Drive\shikibo_test")
    
    # Path configuration
    local_draft_root: str = Field(default="")
    outbox_root: str = Field(default="")
    receipt_root: str = Field(default="")
    thread_root: str = Field(default="")
    index_root: str = Field(default="")
    archive_root: str = Field(default="")
    
    # Coordinator configuration
    scan_interval: int = Field(default=5)  # seconds between background scans
    use_fs_events: bool = Field(default=True)
    
    # Logging configuration
    log_file: str = Field(default=r"C:\temp\shikibo.log")

    @model_validator(mode="before")
    @classmethod
    def resolve_paths(cls, data):
        if isinstance(data, dict):
            # Resolve user_id default
            user_provided = False
            if "user_id" in data and data["user_id"] is not None and str(data["user_id"]).strip() != "":
                user_provided = True
                
            if not user_provided:
                import getpass
                import socket
                data["user_id"] = f"{getpass.getuser()}@{socket.gethostname()}"
                
            uid = data["user_id"]
            if len(uid) < 4:
                raise BAD_VALUE(f"Username '{uid}' must be 4 or more characters.")
                
            if user_provided:
                if uid.startswith("__") or uid.endswith("__"):
                    raise BAD_VALUE("User-defined username cannot start or end with '__' (system reserved).")
            
            # Resolve display_name default
            if "display_name" not in data or not data["display_name"]:
                data["display_name"] = data["user_id"]
                
            # Resolve root_dir
            root_dir_val = data.get("root_dir", r"G:\My Drive\shikibo_test")
            root = Path(root_dir_val).resolve()
            data["root_dir"] = str(root)
            
            # Resolve role default
            role_provided = False
            if "role" in data and data["role"] is not None and str(data["role"]).strip() != "":
                role_provided = True
                
            if not role_provided:
                data["role"] = "__DEF__"
                
            role = data["role"]
            if len(role) < 4:
                raise BAD_VALUE(f"Role '{role}' must be 4 or more characters.")
                
            if role_provided:
                if role != "__DEF__":
                    if role.startswith("__") or role.endswith("__"):
                        raise BAD_VALUE("User-defined role cannot start or end with '__' (system reserved).")
            
            # Build default paths if not explicitly configured
            if role:
                if not data.get("local_draft_root"):
                    data["local_draft_root"] = str(root / "drafts" / uid / role)
                if not data.get("outbox_root"):
                    data["outbox_root"] = str(root / "users" / uid / role / "outbox")
                if not data.get("receipt_root"):
                    data["receipt_root"] = str(root / "users" / uid / role / "receipts")
            else:
                if not data.get("local_draft_root"):
                    data["local_draft_root"] = str(root / "drafts" / uid)
                if not data.get("outbox_root"):
                    data["outbox_root"] = str(root / "users" / uid / "outbox")
                if not data.get("receipt_root"):
                    data["receipt_root"] = str(root / "users" / uid / "receipts")
                    
            if not data.get("thread_root"):
                data["thread_root"] = str(root / "system" / "threads")
            if not data.get("index_root"):
                data["index_root"] = str(root / "system" / "index")
            if not data.get("archive_root"):
                data["archive_root"] = str(root / "system" / "archive")
        return data

def load_settings(
    config_path: str = None,
    root_dir: str = None,
    user_id: str = None,
    role: str = None,
    use_fs_events: bool = None,
    scan_interval: int = None
) -> Settings:
    """Load settings from environment variables, an optional JSON config file, or defaults.
    All overrides are fully resolved and stabilized before the Settings object is constructed.
    """
    data = {}
    if config_path and os.path.exists(config_path):
        import json
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            
    # Allow environment variable overrides
    env_keys = [
        "user_id", "role", "display_name", "root_dir", 
        "local_draft_root", "outbox_root", "receipt_root", 
        "thread_root", "index_root", "archive_root", "scan_interval",
        "use_fs_events", "log_file"
    ]
    for key in env_keys:
        env_val = os.environ.get(f"SHIKIBO_{key.upper()}")
        if env_val is not None:
            if key == "use_fs_events":
                data[key] = env_val.lower() in ("true", "1", "yes")
            else:
                data[key] = env_val
            
    # Apply explicit overrides from CLI/parameters before Pydantic initialization
    if root_dir is not None:
        data["root_dir"] = root_dir
    if user_id is not None:
        data["user_id"] = user_id
    if role is not None:
        data["role"] = role
    if use_fs_events is not None:
        data["use_fs_events"] = use_fs_events
    if scan_interval is not None:
        data["scan_interval"] = scan_interval
        
    return Settings(**data)

def setup_logging(settings: Settings) -> None:
    """Configures the root logger to write to both stdout and the configured log file path."""
    import logging
    log_path = Path(settings.log_file)
    try:
        os.makedirs(log_path.parent, exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create log directory {log_path.parent}: {e}")
        
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handlers = []
    
    try:
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    except Exception as e:
        print(f"Warning: Failed to create log file handler for {log_path}: {e}")
        
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        force=True
    )
