import pytest
import tempfile
import os
from scripts.chunking import chunker_v3
from scripts.ingestion.csv import load_csv
# get_rule is used by chunker_v3.split, so direct import here isn't strictly necessary
# from scripts.chunking.rules import get_rule # Assuming rules_v3.py is the one to be used.
                                            # chunker_v3 uses rules_v3.get_rule

# CSV content designed to test chunking logic with rules:
# min_tokens: 150, max_tokens: 800, overlap: 20 (words, space-separated)
CSV_HEADER = "ID,TransactionDate,CustomerName,ProductCategory,ProductName,Quantity,UnitPrice,TotalPrice,Currency,PaymentMethod,ShippingAddress,BillingAddress,OrderStatus,Notes"
# Tokens in header: 14

# Each data row will have roughly the same number of tokens.
# Let's make each data row have exactly 20 tokens to make calculations easier.
# "Val1,Val2,Val3,Val4,Val5,Val6,Val7,Val8,Val9,Val10,Val11,Val12,Val13,Val14,Val15,Val16,Val17,Val18,Val19,Val20"
DATA_ROW_TEMPLATE = "R{idx}_C1,R{idx}_C2,R{idx}_C3,R{idx}_C4,R{idx}_C5,R{idx}_C6,R{idx}_C7,R{idx}_C8,R{idx}_C9,R{idx}_C10,R{idx}_C11,R{idx}_C12,R{idx}_C13,R{idx}_C14,R{idx}_C15,R{idx}_C16,R{idx}_C17,R{idx}_C18,R{idx}_C19,R{idx}_C20"
# Tokens in data row: 20

# Helper to count tokens for a line
def count_tokens(line: str) -> int:
    return len(line.split())

@pytest.fixture
def csv_file_path() -> str:
    # Create CSV content
    # Chunking rules for CSV: min_tokens: 150, max_tokens: 800, overlap: 20
    # Header: 14 tokens
    # Data row: 20 tokens

    # Let's aim for the first chunk to be close to max_tokens.
    # max_tokens = 800. Header is 14. Remaining for data rows = 800 - 14 = 786
    # Number of data rows for first chunk = 786 / 20 = 39.3. So, 39 rows.
    # Total tokens for Header + 39 data rows = 14 + (39 * 20) = 14 + 780 = 794 tokens. (This will be Chunk 1)

    # For the second chunk:
    # It will start with an overlap from the first chunk.
    # The overlap is 20 tokens, which is 1 data row.
    # Let's add enough rows to meet min_tokens (150).
    # Remaining for new rows = 150 - 20 (overlap) = 130 tokens.
    # Number of new data rows = 130 / 20 = 6.5. So, 7 new rows.
    # Total data rows = 39 (for C1) + 7 (for C2) = 46 rows.

    num_first_chunk_data_rows = 39
    num_second_chunk_data_rows = 7
    total_data_rows = num_first_chunk_data_rows + num_second_chunk_data_rows

    csv_lines = [CSV_HEADER]
    for i in range(1, total_data_rows + 1):
        csv_lines.append(DATA_ROW_TEMPLATE.format(idx=i))

    csv_content = "\n".join(csv_lines) + "\n" # Ensure trailing newline like load_csv expects

    # Create a temporary file
    # Need to use delete=False because load_csv will open it by path
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline='') as tmp_file:
        tmp_file.write(csv_content)
        filepath = tmp_file.name

    yield filepath

    # Cleanup
    os.remove(filepath)

def test_chunk_csv_split_on_rows(csv_file_path: str):
    # 1. Load CSV
    text_content, metadata = load_csv(csv_file_path)
    # metadata['doc_type'] is already 'csv' from load_csv

    # 2. Chunk the content
    # Rules for CSV are expected to be loaded by get_rule within chunker_v3.split
    # based on metadata['doc_type'] = 'csv'
    # Default rules from configs/chunk_rules.yaml for .csv:
    # strategy: split_on_rows, min_tokens: 150, max_tokens: 800, overlap: 20
    chunks = chunker_v3.split(text_content, metadata)

    # 3. Assertions
    assert len(chunks) == 2, "Expected two chunks based on the CSV content and rules."

    # --- Calculate expected content for Chunk 1 ---
    # Header (14 tokens) + 39 data rows (39 * 20 = 780 tokens) = 794 tokens
    # These are lines 0 to 39 from the original text_content.split('\n')
    all_rows = [row.strip() for row in text_content.strip().split('\n') if row.strip()]

    expected_chunk1_rows = all_rows[0 : 1 + 39] # Header + 39 data rows
    expected_chunk1_text = " ".join(expected_chunk1_rows)
    expected_chunk1_tokens = count_tokens(expected_chunk1_text)

    assert chunks[0].text == expected_chunk1_text
    assert chunks[0].token_count == expected_chunk1_tokens
    assert chunks[0].meta['doc_type'] == 'csv'
    assert CSV_HEADER in chunks[0].text # Header should be in the first chunk

    # --- Calculate expected content for Chunk 2 ---
    # Overlap: last 20 tokens from chunk 1. This is the last data row of chunk 1 (row index 39).
    # This is all_rows[39]
    overlap_row_text = expected_chunk1_rows[-1] # This is R39_...
    assert count_tokens(overlap_row_text) == 20 # Sanity check

    # New rows for chunk 2: 7 data rows
    # These are rows with original index 1+39 to 1+39+7-1  (i.e. all_rows[40] to all_rows[46])
    # Original row indices: 40, 41, 42, 43, 44, 45, 46
    # Data rows R40 to R46

    new_rows_for_chunk2 = all_rows[1 + 39 : 1 + 39 + 7]

    expected_chunk2_text_list = [overlap_row_text] + new_rows_for_chunk2
    expected_chunk2_text = " ".join(expected_chunk2_text_list)
    expected_chunk2_tokens = count_tokens(expected_chunk2_text)

    # Check if the overlap logic in merge_chunks_with_overlap is word-based or row-based for this strategy
    # The current merge_chunks_with_overlap takes `prev_tail_tokens` (list of words)
    # and prepends it to the `buffer` (list of paragraphs/rows).
    # So, the overlap should be the *words* of the last overlapping row(s).

    # The overlap is defined as `rule.overlap` tokens.
    # `prev_tail_tokens = chunk_tokens[-rule.overlap:]`
    # `chunk_tokens = " ".join(prev_tail_tokens + buffer).split()`
    # `buffer` contains the rows.
    # So, if `prev_tail_tokens` is `['R39_C18,', 'R39_C19,', 'R39_C20']` (example, if overlap was 3)
    # and `buffer` is `['R40_...']`, then `chunk_text` becomes `R39_C18, R39_C19, R39_C20 R40_...`

    # Let's re-evaluate chunk2 text based on how merge_chunks_with_overlap works:
    # prev_tail_tokens for chunk2 will be the last 20 words of chunk1_text.
    chunk1_words = expected_chunk1_text.split()
    overlap_words_from_chunk1 = chunk1_words[-20:] # These are exactly the words of the last row of chunk1

    # The buffer for chunk2 starts empty, then accumulates new_rows_for_chunk2
    # merge_chunks_with_overlap does: " ".join(prev_tail_tokens + buffer)
    # where buffer is a list of strings (rows)
    # and prev_tail_tokens is a list of strings (words)
    # This means it will be `word1 word2 ... word_overlap rowA rowB`
    # The space between `word_overlap` and `rowA` is important.

    expected_chunk2_text_from_logic = " ".join(overlap_words_from_chunk1 + new_rows_for_chunk2)
    expected_chunk2_tokens_from_logic = count_tokens(expected_chunk2_text_from_logic)

    assert chunks[1].text == expected_chunk2_text_from_logic
    assert chunks[1].token_count == expected_chunk2_tokens_from_logic
    assert chunks[1].meta['doc_type'] == 'csv'

    # Further check: min_tokens for chunk2
    # 20 (overlap words) + 7 rows * 20 tokens/row = 20 + 140 = 160 tokens.
    # This is > min_tokens (150).
    assert expected_chunk2_tokens_from_logic >= 150 # Check against min_tokens for CSV

    # Check that the overlapped row from chunk1 is indeed part of chunk2's text,
    # specifically, its content (not just some random words that sum to 20 tokens).
    # The overlap words are literally the last 20 words of the last row of chunk 1.
    # R39_C1 ... R39_C20
    assert " ".join(overlap_words_from_chunk1) == all_rows[39] # The 39th data row (index 39)
    assert all_rows[39] in chunks[1].text # The text of the overlapping row R39 should be in chunk 2
                                          # More precisely, the words should be at the start.
    assert chunks[1].text.startswith(all_rows[39])


if __name__ == "__main__":
    # This allows running the test directly for quick checks, e.g., during development
    # You would typically use `pytest tests/test_chunker_csv.py`

    # Create a dummy csv_file_path for direct execution
    header = "ID,TransactionDate,CustomerName,ProductCategory,ProductName,Quantity,UnitPrice,TotalPrice,Currency,PaymentMethod,ShippingAddress,BillingAddress,OrderStatus,Notes"
    data_template = "R{idx}_C1,R{idx}_C2,R{idx}_C3,R{idx}_C4,R{idx}_C5,R{idx}_C6,R{idx}_C7,R{idx}_C8,R{idx}_C9,R{idx}_C10,R{idx}_C11,R{idx}_C12,R{idx}_C13,R{idx}_C14,R{idx}_C15,R{idx}_C16,R{idx}_C17,R{idx}_C18,R{idx}_C19,R{idx}_C20"
    num_rows_c1 = 39
    num_rows_c2 = 7
    total_rows = num_rows_c1 + num_rows_c2

    lines = [header]
    for i in range(1, total_rows + 1):
        lines.append(data_template.format(idx=i))
    content = "\n".join(lines) + "\n"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline='') as tmp:
        tmp.write(content)
        test_path = tmp.name

    print(f"Test CSV file created at: {test_path}")
    print(f"Header tokens: {count_tokens(header)}")
    print(f"Data row tokens: {count_tokens(data_template.format(idx=1))}")

    # Manually call the test function
    try:
        test_chunk_csv_split_on_rows(test_path)
        print("\nTest passed when run directly.")
    except Exception as e:
        print(f"\nTest failed when run directly: {e}")
    finally:
        os.remove(test_path)

```
