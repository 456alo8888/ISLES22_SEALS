import os
from glob import glob


def resolve_input_root():
    candidates = ("/input/images", "input/images")
    for root in candidates:
        if os.path.isdir(root):
            return root
    raise FileNotFoundError(
        "Could not find ISLES22 input folder. Expected one of: /input/images, input/images"
    )


def require_single_image(root, folder):
    matches = glob(os.path.join(root, folder, "*.mha"))
    if not matches:
        raise FileNotFoundError(
            f"Missing required input image under {os.path.join(root, folder)}"
        )
    return matches[0]


def optional_single_image(root, folder):
    matches = glob(os.path.join(root, folder, "*.mha"))
    return matches[0] if matches else None
