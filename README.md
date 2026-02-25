# 🖼️ ASCII Art Converter

Convert any image into detailed ASCII art right in your terminal — with optional color output, auto-save, and full CLI control.

---

## ✨ Features

- 🔍 **High-detail output** — 70-character brightness gradient for fine grayscale mapping
- 🎨 **Colored output** — ANSI 24-bit true-color mode preserves the original image colors
- ⚡ **Image preprocessing** — automatic contrast boost + unsharp mask sharpening before conversion
- 💾 **Auto-save** — every run saves a `.txt` file to the `received/` folder (timestamped, never overwrites)
- 📐 **Aspect-ratio-aware** — compensates for monospace font proportions so the output looks correct
- 🖥️ **Cross-platform** — works on macOS, Linux, and Windows terminals

---

## 📦 Requirements

- Python 3.10+
- [Pillow](https://pypi.org/project/Pillow/)

```bash
pip install Pillow
```

---

## 🚀 Usage

```bash
python ascii_art.py <image_path> [options]
```

### Basic examples

```bash
# Convert with default settings (width 100, high-detail, auto-saved to received/)
python ascii_art.py photo.jpg

# Set a custom width
python ascii_art.py photo.jpg --width 120

# Enable colored output (requires a true-color terminal)
python ascii_art.py photo.jpg --color

# Save an extra copy to a specific file
python ascii_art.py photo.jpg --output my_art.txt

# Use a custom character set
python ascii_art.py photo.jpg --chars "@#+-. "
```

---

## ⚙️ Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `image` | — | *(required)* | Path to the input image (JPG, PNG, etc.) |
| `--width` | `-w` | `100` | Output width in characters |
| `--chars` | `-c` | 70-char gradient | ASCII characters ordered darkest → lightest |
| `--output` | `-o` | *(none)* | Extra save path for the `.txt` output |
| `--color` | — | off | Wrap each character in ANSI 24-bit color codes |

---

## 📁 Project Structure

```
ascii_art/
├── ascii_art.py       # Main script
├── README.md          # This file
└── received/          # Auto-created — all saved outputs land here
    └── photo_2026-02-25_07-35-00.txt
```

---

## 🧠 How It Works

1. **Load** — Pillow opens the image
2. **Resize** — scaled to `--width` columns with aspect-ratio correction (`×0.45` height factor for monospace fonts)
3. **Preprocess** — UnsharpMask filter → contrast boost (`×1.5`) → sharpness boost (`×2.0`)
4. **Grayscale** — converted to single-channel luminosity
5. **Map** — each pixel's brightness (0–255) is mapped to one of 70 ASCII characters
6. **Output** — printed to the terminal and auto-saved to `received/`

---

## 💡 Tips

- **Wider = more detail**: try `--width 200` or `--width 300` for ultra-detailed output (save to file and open in a text editor)
- **Colored mode** works best in iTerm2, Windows Terminal, or any true-color terminal
- Saved `.txt` files open beautifully in VS Code with a small font size (e.g. 4px)

---

## 📄 License

MIT — free to use, modify, and share.
