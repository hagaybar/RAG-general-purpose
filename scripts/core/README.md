# Core Scripts

The `scripts/core` folder contains central components for managing project structure and configuration.

- `__init__.py`: Marks the folder as a Python package.
- `project_manager.py`: Defines the `ProjectManager` class.

## ProjectManager

The `ProjectManager` class is responsible for managing the workspace of a Retrieval Augmented Generation (RAG) project. It handles:
- **Project Root Directory**: Initializes with a root directory for the project.
- **Configuration**: Loads project-specific configurations from a `config.yml` file located in the root directory using `scripts.utils.config_loader.ConfigLoader`.
- **Directory Structure**: Defines and ensures the existence of several key directories within the project:
    - `input_dir`: For storing input documents. (Defaults to `<root_dir>/input`)
    - `output_dir`: For storing general outputs. (Defaults to `<root_dir>/output`)
    - `logs_dir`: For storing log files. (Defaults to `<root_dir>/output/logs`)
    - `faiss_dir`: For storing FAISS index files. (Defaults to `<root_dir>/output/faiss`)
    - `metadata_dir`: For storing metadata associated with embeddings or documents. (Defaults to `<root_dir>/output/metadata`)
- **Path Accessors**: Provides methods to get paths to specific files or directories within the managed structure (e.g., `get_input_dir()`, `get_faiss_path(doc_type)`, `get_metadata_path(doc_type)`, `get_log_path(module, run_id)`).

This class helps in organizing project files and configurations in a standardized way.
