"""QInputDialog wrapper for renaming elements."""
from PyQt6.QtWidgets import QInputDialog


def rename_element(current_label: str) -> str | None:
    """Show a rename dialog. Returns the new label, or None if cancelled."""
    new_label, ok = QInputDialog.getText(
        None, "Rename Element", "New label:", text=current_label
    )
    if ok and new_label.strip():
        return new_label.strip()
    return None
