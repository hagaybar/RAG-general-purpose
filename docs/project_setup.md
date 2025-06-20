# Project Setup and Configuration

This document outlines the setup for your project directory and the crucial `config.yml` file that controls how the RAG pipeline interacts with your project's data.

## Project Directory Structure

When you initiate a new project or process data, the system relies on a specific directory structure and a configuration file (`config.yml`) located at the root of your project directory.

Example project directory (`my_project/`):

```
my_project/
├── config.yml           # Project-specific configurations
├── input/               # Default directory for your raw data files
└── output/              # Default directory for processed files
    ├── logs/            # Default directory for log files
    ├── faiss/           # Default directory for FAISS indexes
    └── metadata/        # Default directory for metadata stores
```

## The `config.yml` File

The `config.yml` file is essential for tailoring the RAG pipeline to your specific project. It tells the `ProjectManager` where to find input data, where to store outputs, logs, and other artifacts.

If this file is not found at the root of your project directory (`your_project_root/config.yml`) when `ProjectManager` is initialized, it will proceed with default path settings. However, for clarity and explicit control, creating a `config.yml` is highly recommended.

### Structure of `config.yml`

The `config.yml` uses YAML format. The primary section you'll configure is `paths`, which defines the locations for various directories.

Here are the configurable keys under `paths` and their default values:

*   `paths.input_dir`: Specifies the directory where the pipeline looks for your raw input documents.
    *   Default: `input`
*   `paths.output_dir`: Specifies the main directory for storing all processed outputs.
    *   Default: `output`
*   `paths.logs_dir`: Specifies the subdirectory within `output_dir` for storing log files.
    *   Default: `output/logs` (relative to `root_dir`, effectively `output_dir` / `logs`)
*   `paths.faiss_dir`: Specifies the subdirectory within `output_dir` for storing FAISS vector indexes.
    *   Default: `output/faiss` (relative to `root_dir`, effectively `output_dir` / `faiss`)
*   `paths.metadata_dir`: Specifies the subdirectory within `output_dir` for storing metadata associated with your processed data (e.g., chunk metadata).
    *   Default: `output/metadata` (relative to `root_dir`, effectively `output_dir` / `metadata`)

### Creating `config.yml`

1.  Create a new file named `config.yml` in the root of your project directory.
2.  Add the `paths` section and specify any directories you wish to customize. If you omit a key, the default value will be used.

**Example `config.yml`:**

```yaml
# my_project/config.yml

paths:
  input_dir: "source_documents"  # Custom input directory
  output_dir: "processed_data"   # Custom output directory
  # logs_dir, faiss_dir, metadata_dir will use defaults relative to "processed_data"
  # e.g., logs_dir will be "processed_data/logs"
```

You can also specify full paths, but relative paths are recommended for portability.

### Path Configuration: Relative Paths Recommended

**It is strongly recommended to use relative paths in your `config.yml` file.** Relative paths are specified from the location of the `config.yml` file itself (i.e., your project root). This makes your project more portable, allowing it to be moved to different locations on your filesystem or shared with others without needing to modify the configuration.

**Example using relative paths (Recommended):**

```yaml
# my_project/config.yml
paths:
  input_dir: "input_data"          # Located at my_project/input_data/
  output_dir: "pipeline_output"    # Located at my_project/pipeline_output/
  logs_dir: "pipeline_output/logs" # Located at my_project/pipeline_output/logs/
```

**Example using absolute paths (Less portable, use with caution):**

```yaml
# my_project/config.yml
paths:
  input_dir: "/path/to/my/project/input_data"
  output_dir: "/path/to/my/project/pipeline_output"
```

### How `ProjectManager` Uses These Paths

The `ProjectManager` class reads `config.yml` upon initialization with your project's root directory.
- It resolves all specified paths relative to this root directory.
- If a path is not specified in `config.yml`, `ProjectManager` uses the default value (e.g., `input` for `input_dir`).
- `ProjectManager` will automatically create these directories if they do not already exist, ensuring the pipeline has the necessary structure to operate. For example, if `output/logs` doesn't exist, it will be created.

By understanding and configuring `config.yml`, you gain fine-grained control over your project's data organization.
