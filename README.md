# 🃏 Solitaire (Klondike) — Python Tkinter Game

A fully functional **Solitaire (Klondike)** card game built in **Python** using the **Tkinter GUI library** and **Pillow (PIL)** for image handling.
The project features realistic drag-and-drop card mechanics, automatic foundation moves, dynamic card loading (from any image set), and smooth visual presentation.

---

## 📸 Features

✅ **Playable Solitaire (Klondike)** — Complete rules implemented with tableau, foundations, waste, and stock piles.
✅ **Dynamic Card Image Loading** — Automatically detects and loads any standard deck image set from a directory.
✅ **Drag-and-Drop Mechanics** — Move cards or stacks naturally with mouse control.
✅ **Auto Move to Foundation** — Double-click a card to send it to the foundation automatically if valid.
✅ **Smart Filename Recognition** — Loads cards even if filenames are inconsistent (`2_of_clubs.png`, `clubs2.jpg`, etc.) using fuzzy matching.
✅ **Keyboard Shortcuts** —

* `Space` → Deal new card from stock
* `N` → Start a new game
* `Esc` → Cancel drag
  ✅ **Fallback Card Placeholders** — Generates placeholder cards if images are missing.
  ✅ **Responsive Canvas Layout** — Dynamically arranged piles and visual outlines.

---

## 🖼️ Preview

| Gameplay Example                                                                         | Card Layout Example                                                                 |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| ![Game Screenshot](https://user-images.githubusercontent.com/example/solitaire-game.png) | ![Card Example](https://user-images.githubusercontent.com/example/card-example.png) |

*(Add your screenshots in the `assets/` folder and replace the URLs above.)*

---

## 🧱 Folder Structure

```
solitaire/
│
├── main.py                # The main game script (this file)
├── README.md              # Project documentation
├── requirements.txt       # Dependencies
└── Playing Cards/         # Folder containing all 52 card images + 1 back image
```

---

## ⚙️ Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/solitaire-tkinter.git
cd solitaire-tkinter
```

### Step 2: Install Dependencies

Make sure you have Python 3.8+ installed.

```bash
pip install pillow
```

Tkinter is included with most Python installations by default.
If not, install it using your system package manager:

* **Windows:** Included by default
* **Ubuntu/Debian:** `sudo apt install python3-tk`
* **Fedora:** `sudo dnf install python3-tkinter`

---

## 🃠 Running the Game

1. Make sure your **card images** are stored in the path specified in the code:

   ```python
   IMAGE_DIR = "C:/Users/jatin/OneDrive/Desktop/College Notes and stuff/cpp/projectss/Playing Cards"
   ```

   You can change this to any directory containing your card images.

2. Run the game:

   ```bash
   python main.py
   ```

---

## 🧩 Card Image Requirements

You can use **any standard deck image set**.
The loader accepts flexible naming formats such as:

```
ace_of_spades.png
10_of_hearts.jpg
king_hearts2.png
d8.png
clubs_j.png
```

If any cards are missing, **placeholder cards** will be automatically generated.

---

## 🎮 Controls

| Action                  | Key / Mouse  |
| ----------------------- | ------------ |
| Deal card from stock    | `Space`      |
| Start new game          | `N`          |
| Cancel drag             | `Esc`        |
| Auto move to foundation | Double-click |
| Drag stack              | Click + Drag |

---

## 🧠 Code Highlights

* **Object-Oriented Design** — Classes for `Card`, `Pile`, `TableauPile`, `StockPile`, etc.
* **Smart Image Cache** — Loads, caches, and resizes card images dynamically.
* **Levenshtein Matching** — Intelligent fuzzy filename matching for imperfect card names.
* **Separation of Concerns** — Independent model, view, and controller components.

---

## 📚 Dependencies

| Library                                | Use                                         |
| -------------------------------------- | ------------------------------------------- |
| `tkinter`                              | GUI framework                               |
| `Pillow`                               | Image handling (loading, resizing, drawing) |
| `os`, `re`, `random`, `sys`, `pathlib` | Core Python utilities                       |

Install all with:

```bash
pip install pillow
```

---

## 🏆 Future Enhancements

* [ ] Add timer and score tracking
* [ ] Implement move undo/redo
* [ ] Add multiple card-draw modes (1-card, 3-card)
* [ ] Save and load game state
* [ ] Add custom deck themes and animations

---

## 🧑‍💻 Author

**Jatinder Singh**
Web Developer • App Developer • Python Programmer • Data Scientist
📧 *[[your_email@example.com](mailto:your_email@example.com)]*
🌐 [Portfolio Website](https://your-portfolio-link.com)

---

## 📄 License

This project is licensed under the **MIT License** — you are free to use, modify, and distribute it with attribution.
