#!/usr/bin/env python3
"""
ascii_art.py
============
Converts an image into ASCII art using Pillow (PIL).

Features:
  - Resize proportionally while accounting for character aspect ratio
  - Convert to grayscale and map brightness to ASCII characters
  - Optional colored output via ANSI escape codes
  - Optional save to .txt file
  - CLI argument support via argparse

Usage:
  python ascii_art.py image.jpg
  python ascii_art.py image.jpg --width 120 --output result.txt
  python ascii_art.py image.jpg --width 100 --color
  python ascii_art.py image.jpg --chars "@%#*+=-:. "

Requires:
  pip install Pillow
"""

import argparse
import os
import sys
import datetime

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed. Run: pip install Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default ASCII character set — ordered from darkest (leftmost) to lightest.
# The rightmost character (space) represents the brightest pixels.
DEFAULT_CHARS = "@%#*+=-:. "

# Terminal character aspect ratio correction factor.
# Most monospace fonts are roughly twice as tall as they are wide,
# so we multiply the calculated height by this factor to keep the image
# looking proportional in the terminal.
CHAR_ASPECT_RATIO = 0.45

# Folder (relative to this script) where outputs are auto-saved.
RECEIVED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received")


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def ensure_received_dir() -> None:
    """
    Create the 'received' output directory next to this script if it does not
    already exist.
    """
    os.makedirs(RECEIVED_DIR, exist_ok=True)


def build_auto_save_path(image_path: str) -> str:
    """
    Build a unique save path inside RECEIVED_DIR based on the input image
    filename and the current timestamp.

    Parameters
    ----------
    image_path : str
        Path to the original input image.

    Returns
    -------
    str
        Full path for the auto-saved .txt file, e.g.:
        /path/to/ascii_art/received/IMG_8157_2026-02-25_07-26-40.txt
    """
    base_name  = os.path.splitext(os.path.basename(image_path))[0]  # e.g. IMG_8157
    timestamp  = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name  = f"{base_name}_{timestamp}.txt"
    return os.path.join(RECEIVED_DIR, file_name)


def load_image(path: str) -> Image.Image:
    """
    Load an image from the given file path.

    Parameters
    ----------
    path : str
        Absolute or relative path to the image file.

    Returns
    -------
    PIL.Image.Image
        The loaded image object.

    Raises
    ------
    SystemExit
        If the file does not exist or cannot be opened.
    """
    if not os.path.isfile(path):
        print(f"Error: File not found — '{path}'")
        sys.exit(1)

    try:
        img = Image.open(path)
        img.verify()           # Detect corrupt files early
        img = Image.open(path) # Re-open after verify (verify() consumes the object)
        return img
    except Exception as exc:
        print(f"Error: Could not open image — {exc}")
        sys.exit(1)


def resize_image(img: Image.Image, target_width: int) -> Image.Image:
    """
    Resize the image to `target_width` columns while preserving the aspect
    ratio and compensating for the terminal character aspect ratio.

    Parameters
    ----------
    img : PIL.Image.Image
        The source image.
    target_width : int
        Desired number of ASCII columns.

    Returns
    -------
    PIL.Image.Image
        The resized image.
    """
    original_width, original_height = img.size

    # Calculate the height that maintains aspect ratio, adjusted for the
    # fact that each character cell is taller than it is wide.
    target_height = int(original_height * target_width / original_width * CHAR_ASPECT_RATIO)

    # LANCZOS gives the best quality when downscaling
    resized = img.resize((target_width, target_height), Image.LANCZOS)
    return resized


def to_grayscale(img: Image.Image) -> Image.Image:
    """
    Convert the image to grayscale (luminosity mode).

    Parameters
    ----------
    img : PIL.Image.Image
        Any-mode source image.

    Returns
    -------
    PIL.Image.Image
        Single-channel 'L' (luminosity) image.
    """
    return img.convert("L")


def pixel_to_ascii(pixel_value: int, char_set: str) -> str:
    """
    Map a single 8-bit grayscale pixel value (0–255) to an ASCII character.

    The mapping is linear:
      - 0   (black)  → first character in char_set  (typically the most dense)
      - 255 (white)  → last character in char_set   (typically a space)

    Parameters
    ----------
    pixel_value : int
        Grayscale intensity in the range [0, 255].
    char_set : str
        Ordered string of ASCII characters, darkest to lightest.

    Returns
    -------
    str
        A single ASCII character.
    """
    # Scale pixel value to an index within the character set
    index = int(pixel_value / 255 * (len(char_set) - 1))
    return char_set[index]


def image_to_ascii(gray_img: Image.Image, char_set: str) -> list[str]:
    """
    Convert every pixel of a grayscale image into its corresponding ASCII
    character and return the result as a list of strings (one per row).

    Parameters
    ----------
    gray_img : PIL.Image.Image
        Grayscale ('L' mode) image.
    char_set : str
        Ordered string of ASCII characters, darkest to lightest.

    Returns
    -------
    list[str]
        Each element is one row of ASCII characters.
    """
    width, height = gray_img.size
    pixels = list(gray_img.getdata())  # Convert to list to support slicing

    rows = []
    for row_index in range(height):
        row_start = row_index * width
        row_end   = row_start + width
        row_pixels = pixels[row_start:row_end]

        # Convert every pixel in this row to an ASCII character
        ascii_row = "".join(pixel_to_ascii(p, char_set) for p in row_pixels)
        rows.append(ascii_row)

    return rows


# ---------------------------------------------------------------------------
# Colored (ANSI) output helpers
# ---------------------------------------------------------------------------

def make_ansi_color(r: int, g: int, b: int, text: str) -> str:
    """
    Wrap `text` in a 24-bit (true-color) ANSI foreground color escape code.

    Parameters
    ----------
    r, g, b : int
        Red, green, blue components of the desired color (0–255).
    text : str
        The character(s) to colorize.

    Returns
    -------
    str
        The text wrapped in ANSI escape sequences.
    """
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def image_to_ascii_colored(
    original_img: Image.Image,
    gray_img: Image.Image,
    char_set: str,
) -> list[str]:
    """
    Like `image_to_ascii`, but each character is wrapped in an ANSI color
    code sampled from the original (RGB) image.

    Parameters
    ----------
    original_img : PIL.Image.Image
        The original resized image in RGB (or RGBA) mode — used for color sampling.
    gray_img : PIL.Image.Image
        The grayscale version — used for ASCII character selection.
    char_set : str
        Ordered string of ASCII characters, darkest to lightest.

    Returns
    -------
    list[str]
        Each element is one row of ANSI-colored ASCII characters.
    """
    # Ensure we work in RGB for clean color extraction
    rgb_img = original_img.convert("RGB")

    width, height = gray_img.size
    gray_pixels  = list(gray_img.getdata())   # Convert to list to support indexing
    color_pixels = list(rgb_img.getdata())

    rows = []
    for row_index in range(height):
        row_start = row_index * width
        row_end   = row_start + width

        ascii_row = ""
        for col_index in range(row_start, row_end):
            char  = pixel_to_ascii(gray_pixels[col_index], char_set)
            r, g, b = color_pixels[col_index]
            ascii_row += make_ansi_color(r, g, b, char)

        rows.append(ascii_row)

    return rows


# ---------------------------------------------------------------------------
# Output functions
# ---------------------------------------------------------------------------

def print_ascii(rows: list[str]) -> None:
    """
    Print the ASCII art rows to the terminal.

    Parameters
    ----------
    rows : list[str]
        Lines of ASCII (or ANSI-colored ASCII) characters.
    """
    print("\n".join(rows))


def save_ascii(rows: list[str], output_path: str) -> None:
    """
    Save plain ASCII art (no ANSI codes) to a text file.

    Parameters
    ----------
    rows : list[str]
        Lines of ASCII characters. ANSI codes are stripped automatically.
    output_path : str
        Destination .txt file path.
    """
    import re
    # Strip ANSI escape codes so the saved file is readable in any editor
    ansi_escape = re.compile(r"\033\[[0-9;]*m")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for row in rows:
                clean_row = ansi_escape.sub("", row)
                f.write(clean_row + "\n")
        print(f"\nASCII art saved to: {output_path}")
    except OSError as exc:
        print(f"Error: Could not write file — {exc}")


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the argument parser for the CLI.

    Returns
    -------
    argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="ascii_art.py",
        description="Convert an image into ASCII art.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python ascii_art.py photo.jpg\n"
            "  python ascii_art.py photo.jpg --width 120 --output art.txt\n"
            "  python ascii_art.py photo.jpg --color\n"
            "  python ascii_art.py photo.jpg --chars '@#+-. '\n"
        ),
    )

    parser.add_argument(
        "image",
        help="Path to the input image file.",
    )
    parser.add_argument(
        "--width", "-w",
        type=int,
        default=100,
        help="Output width in characters (default: 100).",
    )
    parser.add_argument(
        "--chars", "-c",
        type=str,
        default=DEFAULT_CHARS,
        help=(
            f"ASCII character set ordered from darkest to lightest "
            f"(default: '{DEFAULT_CHARS}')."
        ),
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Optional path to save the ASCII art as a .txt file.",
    )
    parser.add_argument(
        "--color",
        action="store_true",
        help="Enable colored output using ANSI 24-bit escape codes.",
    )

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Orchestrate the full image → ASCII art conversion pipeline.

    Steps
    -----
    1. Parse CLI arguments.
    2. Load the source image.
    3. Resize it (accounting for character aspect ratio).
    4. Convert to grayscale.
    5. Map every pixel to an ASCII character.
    6. Print the result to the terminal.
    7. Optionally save the result to a file.
    """
    parser = build_parser()
    args   = parser.parse_args()

    # --- Step 1: Validate the character set -----------------------------------
    if len(args.chars) < 2:
        print("Error: --chars must contain at least 2 characters.")
        sys.exit(1)

    # --- Step 2: Load the image -----------------------------------------------
    print(f"Loading image: {args.image}")
    img = load_image(args.image)

    # --- Step 3: Resize -------------------------------------------------------
    print(f"Resizing to width={args.width} characters …")
    resized = resize_image(img, args.width)

    # --- Step 4: Grayscale conversion ----------------------------------------
    gray = to_grayscale(resized)

    # --- Step 5: Generate ASCII rows -----------------------------------------
    if args.color:
        print("Generating colored ASCII art …\n")
        rows = image_to_ascii_colored(resized, gray, args.chars)
    else:
        print("Generating ASCII art …\n")
        rows = image_to_ascii(gray, args.chars)

    # --- Step 6: Print to terminal -------------------------------------------
    print_ascii(rows)

    # --- Step 7: Always auto-save to received/ folder -----------------------
    ensure_received_dir()
    auto_path = build_auto_save_path(args.image)
    save_ascii(rows, auto_path)

    # --- Step 8: Optionally save to an extra user-specified file -------------
    if args.output:
        save_ascii(rows, args.output)


# ---------------------------------------------------------------------------
# Script guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
