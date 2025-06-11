import yaml
from pathlib import Path

_rules_data = None
_rules_file_path = Path(__file__).parent.parent.parent / "configs" / "chunk_rules.yaml"

def get_rule(doc_type: str) -> dict:
    """
    Retrieves the chunking rule for a given document type.

    Args:
        doc_type: The type of the document (e.g., 'email', 'pdf').

    Returns:
        A dictionary containing the chunking rules for the specified type.

    Raises:
        KeyError: If the document type is not found in the rules.
        FileNotFoundError: If the rules YAML file is not found.
    """
    global _rules_data
    if _rules_data is None:
        if not _rules_file_path.exists():
            raise FileNotFoundError(f"Rules file not found at {_rules_file_path}")
        with open(_rules_file_path, 'r') as f:
            _rules_data = yaml.safe_load(f)

    if doc_type not in _rules_data:
        raise KeyError(f"Document type '{doc_type}' not found in chunking rules.")
    return _rules_data[doc_type]

def get_all_rules() -> dict:
    """
    Retrieves all chunking rules.

    Returns:
        A dictionary containing all chunking rules.

    Raises:
        FileNotFoundError: If the rules YAML file is not found.
    """
    global _rules_data
    if _rules_data is None:
        if not _rules_file_path.exists():
            raise FileNotFoundError(f"Rules file not found at {_rules_file_path}")
        with open(_rules_file_path, 'r') as f:
            _rules_data = yaml.safe_load(f)
    return _rules_data

def get_all_doc_types() -> list:
    """
    Retrieves all document types defined in the chunking rules.

    Returns:
        A list of document types.

    Raises:
        FileNotFoundError: If the rules YAML file is not found.
    """
    rules = get_all_rules()
    return list(rules.keys())

