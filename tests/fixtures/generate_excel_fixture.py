"""Generate a real .xlsx test fixture with known edge cases."""

from pathlib import Path

import openpyxl


def generate(output_path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"

    headers = ["SKU", "Product Name", "Category", "Unit Price", "Currency", "Qty", "Supplier", "Description"]
    ws.append(headers)

    rows = [
        # Valid rows
        ("0001", "Widget Alpha", "Tools", 15.99, "USD", 10, "Excel Supplier", "Standard widget"),
        ("0002", "Gadget Beta", "Electronics", 29.50, "EUR", 5, "Excel Supplier", "Premium gadget"),
        # Leading-zero SKU
        ("0010", "Zero-Lead Item", "Tools", 8.00, "USD", 20, "Excel Supplier", "Leading zero test"),
        # Empty SKU → should be rejected
        (None, "Orphan Product", "Misc", 5.00, "USD", 3, "Excel Supplier", "No SKU"),
        # Invalid price (text)
        ("0003", "Bad Price Item", "Tools", "not-a-price", "USD", 7, "Excel Supplier", "Bad price"),
        # Negative price
        ("0004", "Negative Price", "Tools", -12.50, "USD", 2, "Excel Supplier", "Negative"),
        # Zero quantity (valid)
        ("0005", "Out of Stock", "Tools", 10.00, "USD", 0, "Excel Supplier", "Zero qty ok"),
        # Negative quantity
        ("0006", "Bad Qty Item", "Tools", 10.00, "USD", -5, "Excel Supplier", "Negative qty"),
        # Duplicate of row 1
        ("0001", "Widget Alpha", "Tools", 15.99, "USD", 10, "Excel Supplier", "Duplicate of first"),
        # Blank product name
        ("0007", "", "Tools", 10.00, "USD", 1, "Excel Supplier", "Blank name"),
        # Whitespace-only product name
        ("0008", "   ", "Tools", 10.00, "USD", 1, "Excel Supplier", "Whitespace name"),
        # Valid with whitespace padding
        ("0009", "  Padded Name  ", "Electronics", 22.00, "GBP", 15, "Excel Supplier", "Needs trim"),
    ]

    for row in rows:
        ws.append(row)

    wb.save(output_path)


if __name__ == "__main__":
    out = Path(__file__).parent / "test_workbook.xlsx"
    generate(out)
    print(f"Generated {out}")
