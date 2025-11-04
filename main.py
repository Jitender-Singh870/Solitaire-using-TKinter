import sys
from pathlib import Path
import os
import tkinter as tk
from tkinter import ttk, messagebox
import random
import re
from PIL import Image, ImageTk, ImageDraw, ImageFont

IMAGE_DIR = "C:/Users/jatin/OneDrive/Desktop/College Notes and stuff/cpp/projectss/Playing Cards"

SUITS = ["D", "C", "H", "S"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUES = {r: (1 if r == "A" else 11 if r == "J" else 12 if r == "Q" else 13 if r == "K" else int(r)) for r in RANKS}
COLORS = {"D": "red", "H": "red", "C": "black", "S": "black"}

CARD_W = 90
CARD_H = 130

PADDING_X = 20
PADDING_Y = 20
GAP_X = 24
TABLEAU_GAP_Y_FACEUP = 28
TABLEAU_GAP_Y_FACEDOWN = 12
WASTE_GAP_X = 20

BG_COLOR = "#0b6623"  # Felt green

# Helper maps for tolerant name matching
_SUITE_WORD = {"D": "diamonds", "C": "clubs", "H": "hearts", "S": "spades"}
_RANK_WORD = {
    "A": "ace", "J": "jack", "Q": "queen", "K": "king",
    "10": "10", "9": "9", "8": "8", "7": "7", "6": "6",
    "5": "5", "4": "4", "3": "3", "2": "2"
}


def _levenshtein(a: str, b: str) -> int:
    # small/edit-distance optimized for short tokens
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    # initialize row
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * lb
        for j, cb in enumerate(b, 1):
            add = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + add)
        prev = cur
    return prev[-1]


class ImageCache:
    def __init__(self, image_dir, card_w, card_h):
        self.dir = image_dir
        self.w = card_w
        self.h = card_h
        self.fronts = {}  # (suit, rank) -> PhotoImage
        self.back = None
        self._load_all()

    def _tokens(self, name):
        # split filename into simple tokens (letters/numbers)
        base = name.lower()
        base = re.sub(r"\.png$|\.jpg$|\.jpeg$", "", base)
        parts = re.split(r"[^a-z0-9]+", base)
        # strip trailing digits like "...2"
        parts = [re.sub(r"\d+$", "", p) for p in parts if p]
        return parts

    def _find_suit_in_tokens(self, tokens):
        # return suit letter or None
        for t in tokens:
            for s, word in _SUITE_WORD.items():
                if word in t:
                    return s
                # allow small typo tolerance
                if _levenshtein(t, word) <= 1:
                    return s
        return None

    def _find_rank_in_tokens(self, tokens):
        # return rank string (A,2..10,J,Q,K) or None
        for t in tokens:
            # numeric ranks
            for num in [str(n) for n in range(10, 1, -1)] + [str(n) for n in range(1, 10)]:
                if num in t:
                    # "1" alone is not a rank except as part of 10
                    if num == "1":
                        continue
                    if num == "10" or "10" in t or "io" in t or "i0" in t or "l0" in t:
                        return "10"
                    return num
            # word ranks
            for rk, word in _RANK_WORD.items():
                if word in t:
                    return rk
                if _levenshtein(t, word) <= 1:
                    return rk
        return None

    @staticmethod
    def _load_img_from_path(path, w, h):
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize((w, h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _make_placeholder(self, suit, rank, w, h):
        # create a simple placeholder image so the UI stays usable
        img = Image.new("RGBA", (w, h), (200, 200, 200, 255))
        draw = ImageDraw.Draw(img)
        # try a default font; if not available, PIL will use a basic bitmap
        txt = f"{rank}{suit}"
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), txt, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rectangle([(2, 2), (w - 3, h - 3)], outline=(100, 100, 100, 255), width=3)
        draw.text(((w - text_w) / 2, (h - text_h) / 2), txt, fill=(0, 0, 0), font=font)
        return ImageTk.PhotoImage(img)
    def _load_all(self):
        # scan available files
        files = []
        try:
            files = os.listdir(self.dir)
        except Exception:
            files = []

        # candidate mapping from detected (suit, rank) to filename
        detected = {}

        # scan and try to detect suit+rank tokens in each filename
        for fn in files:
            low = fn.lower()
            # skip obvious non-image names
            if not low.endswith((".png", ".jpg", ".jpeg")):
                continue
            tokens = self._tokens(fn)
            suit = self._find_suit_in_tokens(tokens)
            rank = self._find_rank_in_tokens(tokens)
            # special-case: if filename like 'd8.jpg' or '8d.jpg'
            if suit is None or rank is None:
                compact = re.sub(r"[^a-z0-9]", "", low)
                # try patterns like d8, 8d, da, ad etc.
                m = re.match(r"^([dchs])([0-9aajqk]{1,2})", compact)
                if m:
                    s1 = m.group(1)
                    r1 = m.group(2)
                    # interpret letters
                    suit_map = {"d": "D", "c": "C", "h": "H", "s": "S"}
                    if s1 in suit_map and r1:
                        suit = suit_map[s1]
                        # map r1 to rank token
                        for rk in RANKS:
                            if rk.lower() == r1 or (rk == "10" and r1 in ("10", "io", "i0", "l0")):
                                rank = rk
                                break

            if suit and rank:
                key = (suit, rank)
                # prefer exact matches that include both words
                detected[key] = fn

        # load detected images, fallback to common patterns
        for s in SUITS:
            for r in RANKS:
                key = (s, r)
                img = None
                # priority 1: detected filename from tokens
                if key in detected:
                    path = os.path.join(self.dir, detected[key])
                    img = self._load_img_from_path(path, self.w, self.h)
                # priority 2: try common naming patterns
                if img is None:
                    candidates = [
                        f"{s}{r}.jpg", f"{s}{r}.png",
                        f"{r}_of_{_SUITE_WORD[s]}.png", f"{r}_of_{_SUITE_WORD[s]}.jpg",
                        f"{_RANK_WORD.get(r, r)}_of_{_SUITE_WORD[s]}.png",
                        f"{_RANK_WORD.get(r, r)}_of_{_SUITE_WORD[s]}.jpg",
                        f"{_RANK_WORD.get(r, r)}_{_SUITE_WORD[s]}.png",
                        f"{_RANK_WORD.get(r, r)}_{_SUITE_WORD[s]}.jpg",
                    ]
                    # also try variations with optional trailing "2" (some files have "...2.png")
                    candidates += [c.replace(".png", "2.png") for c in candidates if ".png" in c]
                    for c in candidates:
                        p = os.path.join(self.dir, c)
                        if os.path.exists(p):
                            img = self._load_img_from_path(p, self.w, self.h)
                            if img:
                                break
                # priority 3: if not found, attempt to use any file that contains suit and rank substrings
                if img is None:
                    for fn in files:
                        low = fn.lower()
                        if (_SUITE_WORD[s] in low or _SUITE_WORD[s][:4] in low) and (
                            _RANK_WORD.get(r, str(r)) in low or (r == "10" and ("10" in low or "io" in low))
                        ):
                            path = os.path.join(self.dir, fn)
                            img = self._load_img_from_path(path, self.w, self.h)
                            if img:
                                break
                # last resort: placeholder (so app doesn't crash)
                if img is None:
                    img = self._make_placeholder(s, r, self.w, self.h)
                self.fronts[key] = img

        # Back image: prefer file with "back", else any "joker", else any image, else generated
        back_img = None
        for fn in files:
            low = fn.lower()
            if "back" in low and low.endswith((".png", ".jpg", ".jpeg")):
                back_img = self._load_img_from_path(os.path.join(self.dir, fn), self.w, self.h)
                if back_img:
                    break
        if back_img is None:
            for fn in files:
                low = fn.lower()
                if "joker" in low and low.endswith((".png", ".jpg", ".jpeg")):
                    back_img = self._load_img_from_path(os.path.join(self.dir, fn), self.w, self.h)
                    if back_img:
                        break
        if back_img is None and files:
            # try any image file
            for fn in files:
                if fn.lower().endswith((".png", ".jpg", ".jpeg")):
                    back_img = self._load_img_from_path(os.path.join(self.dir, fn), self.w, self.h)
                    if back_img:
                        break
        if back_img is None:
            # generate simple back placeholder
            img = Image.new("RGBA", (self.w, self.h), (50, 50, 150, 255))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 18)
            except Exception:
                font = ImageFont.load_default()
            text = "BACK"
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((self.w - tw) / 2, (self.h - th) / 2), text, fill=(255, 255, 255), font=font)
            back_img = ImageTk.PhotoImage(img)
        self.back = back_img

    def get_front(self, suit, rank):
        return self.fronts.get((suit, rank))

    def get_back(self):
        return self.back

# -------------------- Model --------------------
class Card:
    def __init__(self, suit, rank, images, face_up=False):
        self.suit = suit
        self.rank = rank
        self.value = VALUES[rank]
        self.color = COLORS[suit]
        self.face_up = face_up
        self.images = images
        self.canvas_item = None
        self.x = 0
        self.y = 0
        self.pile = None  # reference to current pile

    def image(self):
        return self.images.get_front(self.suit, self.rank) if self.face_up else self.images.get_back()

    def flip_up(self):
        if not self.face_up:
            self.face_up = True

    def flip_down(self):
        if self.face_up:
            self.face_up = False

    def __repr__(self):
        return f"{self.suit}{self.rank}{'^' if self.face_up else 'v'}"


class Pile:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.cards = []
        self.outline = None  # for empty pile visual

    def add_cards(self, cards):
        for c in cards:
            c.pile = self
        self.cards.extend(cards)
        self.relayout()

    def remove_from(self, card):
        if card not in self.cards:
            return []
        idx = self.cards.index(card)
        moving = self.cards[idx:]
        self.cards = self.cards[:idx]
        for c in moving:
            c.pile = None
        self.relayout()
        return moving

    def top(self):
        return self.cards[-1] if self.cards else None

    def is_point_inside(self, px, py):
        # Bounding box of pile area (covers current stack area)
        w = CARD_W
        h = self.height()
        return (self.x - w // 2 <= px <= self.x + w // 2) and (self.y - CARD_H // 2 <= py <= self.y - CARD_H // 2 + h)

    def height(self):
        # Default: a single card height
        return CARD_H
    def relayout(self):
        # Override in subclasses if needed
        for c in self.cards:
            self._place_card(c, self.x, self.y)
        self._update_outline()

    def _place_card(self, card, x, y):
        if card.canvas_item is None:
            card.canvas_item = self.canvas.create_image(x, y, image=card.image(), anchor="center", tags=("card",))
        else:
            self.canvas.coords(card.canvas_item, x, y)
        card.x, card.y = x, y
        self.canvas.tag_raise(card.canvas_item)
        # Update face image in case flip state changed
        self.canvas.itemconfig(card.canvas_item, image=card.image())

    def _update_outline(self):
        if self.outline is None:
            self.outline = self.canvas.create_rectangle(
                self.x - CARD_W // 2, self.y - CARD_H // 2,
                self.x + CARD_W // 2, self.y + CARD_H // 2,
                outline="#bbbbbb", width=2, dash=(4, 4)
            )
        if self.cards:
            self.canvas.itemconfigure(self.outline, state="hidden")
        else:
            self.canvas.itemconfigure(self.outline, state="normal")


class StockPile(Pile):
    def relayout(self):
        # Stack all at the same position, face-down
        for c in self.cards:
            c.flip_down()
            self._place_card(c, self.x, self.y)
        # Ensure only the top is visible
        for c in self.cards[:-1]:
            self.canvas.itemconfigure(c.canvas_item, state="hidden")
        if self.cards:
            self.canvas.itemconfigure(self.cards[-1].canvas_item, state="normal")
        self._update_outline()


class WastePile(Pile):
    def height(self):
        return CARD_H

    def relayout(self):
        # Fan top 3 horizontally
        n = len(self.cards)
        for i, c in enumerate(self.cards):
            c.flip_up()
            dx = 0
            if n >= 3:
                dx = max(0, (i - (n - 3))) * WASTE_GAP_X
            elif n == 2:
                dx = max(0, i - 1) * WASTE_GAP_X
            self._place_card(c, self.x + dx, self.y)
            # Hide all but last 3
            if n > 3 and i < n - 3:
                self.canvas.itemconfigure(c.canvas_item, state="hidden")
            else:
                self.canvas.itemconfigure(c.canvas_item, state="normal")
        self._update_outline()


class FoundationPile(Pile):
    def height(self):
        return CARD_H

    def can_accept(self, card):
        if not card or isinstance(card, list):
            return False
        top = self.top()
        if top is None:
            return card.value == 1  # Ace
        return (card.suit == top.suit) and (card.value == top.value + 1)

    def add_cards(self, cards):
        # Foundations accept single card at a time
        if len(cards) != 1:
            return False
        card = cards[0]
        if not self.can_accept(card):
            return False
        card.flip_up()
        super().add_cards([card])
        return True

    def relayout(self):
        # Stack all at the same spot, only top visible
        for i, c in enumerate(self.cards):
            c.flip_up()
            self._place_card(c, self.x, self.y)
            self.canvas.itemconfigure(c.canvas_item, state="hidden" if i < len(self.cards) - 1 else "normal")
        self._update_outline()


class TableauPile(Pile):
    def height(self):
        h = CARD_H
        if not self.cards:
            return h
        total = CARD_H
        for c in self.cards[:-1]:
            total += (TABLEAU_GAP_Y_FACEUP if c.face_up else TABLEAU_GAP_Y_FACEDOWN)
        return total

    @staticmethod
    def _alternating_colors(c1, c2):
        return c1.color != c2.color

    def can_accept_head(self, card):
        top = self.top()
        if top is None:
            return card.value == 13  # King
        return top.face_up and self._alternating_colors(top, card) and (card.value == top.value - 1)

    def add_stack(self, cards):
        head = cards[0]
        if not self.can_accept_head(head):
            return False
        for c in cards:
            c.flip_up()
        for c in cards:
            c.pile = self
        self.cards.extend(cards)
        self.relayout()
        return True

    def relayout(self):
        y = self.y
        for c in self.cards:
            gap = TABLEAU_GAP_Y_FACEUP if c.face_up else TABLEAU_GAP_Y_FACEDOWN
            self._place_card(c, self.x, y)
            self.canvas.itemconfigure(c.canvas_item, state="normal")
            y += gap
        self._update_outline()

# -------------------- Game Controller --------------------
class SolitaireGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Solitaire (Klondike)")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # Compute canvas size based on layout
        cols = 7
        width = PADDING_X * 2 + cols * CARD_W + (cols - 1) * GAP_X
        height = PADDING_Y * 2 + CARD_H * 2 + 16 + CARD_H + 12 + TABLEAU_GAP_Y_FACEUP * 12
        self.canvas = tk.Canvas(root, width=width, height=height, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        self.images = ImageCache(IMAGE_DIR, CARD_W, CARD_H)

        # Piles
        self.stock = None
        self.waste = None
        self.foundations = []
        self.tableau = []

        # Drag state
        self.dragging_stack = []
        self.drag_origin = None
        self.drag_offsets = []  # per card
        self.drag_start_mouse = (0, 0)

        # Buttons
        self._create_ui(width)

        # Set up and deal a new game
        self.new_game()

        # Event bindings
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<space>", lambda _: self.deal_from_stock())
        self.root.bind("<space>", lambda _: self.deal_from_stock())
        self.root.bind("<Escape>", lambda _: self.cancel_drag())
    def _create_ui(self, width):
        # Positions
        top_y = PADDING_Y + CARD_H // 2
        left_x = PADDING_X + CARD_W // 2

        # Stock and Waste
        self.stock_pos = (left_x, top_y)
        self.waste_pos = (left_x + CARD_W + GAP_X, top_y)

        # Foundations 4 piles to the right
        fx0 = width - PADDING_X - (4 * CARD_W + 3 * GAP_X) + CARD_W // 2
        self.foundation_positions = [(fx0 + i * (CARD_W + GAP_X), top_y) for i in range(4)]

        # Tableau 7 columns
        tx0 = PADDING_X + CARD_W // 2
        tab_y = top_y + CARD_H + 40
        self.tableau_positions = [(tx0 + i * (CARD_W + GAP_X), tab_y) for i in range(7)]

        # Top UI text
        self.status_text = self.canvas.create_text(
            width // 2, PADDING_Y // 2 + 6, text="Space: Deal • Double-click: Auto to foundation • New Game: N",
            fill="#ffffff", font=("Segoe UI", 10))
        self.root.bind("n", lambda _: self.new_game())
        self.canvas.delete("all")
        # Recreate status text
        width = int(self.canvas["width"])
        self.status_text = self.canvas.create_text(
            width // 2, PADDING_Y // 2 + 6, text="Space: Deal • Double-click: Auto to foundation • New Game: N",
            fill="#ffffff", font=("Segoe UI", 10)
        )
        self.stock = StockPile(self.canvas, *self.stock_pos)
        self.waste = WastePile(self.canvas, *self.waste_pos)
        self.foundations = [FoundationPile(self.canvas, *pos) for pos in self.foundation_positions]
        self.tableau = [TableauPile(self.canvas, *pos) for pos in self.tableau_positions]

        # Build, shuffle, deal
        deck = [Card(s, r, self.images, face_up=False) for s in SUITS for r in RANKS]
        random.shuffle(deck)

        # Deal to tableau: 1..7 with last face up
        deal_idx = 0
        for col in range(7):
            stack = []
            for row in range(col + 1):
                c = deck[deal_idx]
                deal_idx += 1
                # Only last card face up
                c.face_up = (row == col)
                stack.append(c)
            self.tableau[col].add_cards(stack)

        # Remaining cards to stock
        remain = deck[deal_idx:]
        self.stock.add_cards(remain)

        # Draw dummy outlines for target areas
        # Already handled by piles' _update_outline()

        # Re-bind events (canvas was recreated)
        self.canvas.tag_bind("card", "<Button-1>", self.on_click)
        self.canvas.tag_bind("card", "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind("card", "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind("card", "<Double-Button-1>", self.on_double_click)

    def new_game(self):
        # Reset game by clearing and rebuilding the layout and dealing a fresh deck
        width = int(self.canvas["width"])
        self.dragging_stack = []
        self.drag_origin = None
        self.drag_offsets = []
        self._create_ui(width)

    # -------------------- Helpers --------------------
    def all_piles(self):
        return [self.stock, self.waste] + self.foundations + self.tableau

    def card_at(self, x, y):
        # Return topmost visible card under point
        items = self.canvas.find_overlapping(x, y, x, y)
        items = [i for i in items if "card" in self.canvas.gettags(i)]
        if not items:
            return None
        # Last in list is topmost
        top_item = items[-1]
        # Map canvas item to Card
        for pile in self.all_piles():
            for c in pile.cards:
                if c.canvas_item == top_item and self.canvas.itemcget(c.canvas_item, "state") == "normal":
                    return c
        return None

    def cancel_drag(self):
        if not self.dragging_stack:
            return
        # Snap back to origin pile layout
        self.drag_origin.relayout()
        self.dragging_stack = []
        self.drag_origin = None
        self.drag_offsets = []

    def try_auto_move_to_foundation(self, card):
        for f in self.foundations:
            if f.can_accept(card):
                # Remove from current pile
                from_pile = card.pile
                moving = from_pile.remove_from(card)
                if len(moving) != 1:
                    # If it was a stack, move only card
                    moving = [card]
                ok = f.add_cards([moving[0]])
                if not ok:
                    # put back
                    from_pile.add_cards([moving[0]])
                    return False
                # Flip origin top if needed
                if isinstance(from_pile, TableauPile) or isinstance(from_pile, WastePile) or isinstance(from_pile, FoundationPile):
                    top = from_pile.top()
                    if top and not top.face_up and not isinstance(from_pile, FoundationPile):
                        top.flip_up()
                        self.canvas.itemconfig(top.canvas_item, image=top.image())
                self.check_win()
                return True
        return False

    def check_win(self):
        if all(len(f.cards) == 13 for f in self.foundations):
            messagebox.showinfo("You win!", "Congratulations! You completed the game.")
            return True
        return False

    # -------------------- Event Handlers --------------------
    def on_click(self, event):
        x, y = event.x, event.y
        # Click stock to deal
        if self.stock.is_point_inside(x, y):
            self.deal_from_stock()
            return

        c = self.card_at(x, y)
        if c is None:
            self.cancel_drag()
            return

        # Determine draggable stack based on pile rules
        pile = c.pile
        if pile is self.stock:
            # Cannot drag directly from stock
            return
        elif pile is self.waste:
            # Only top card
            if c != pile.top():
                return
            stack = [c]
            offsets = [(c.x - x, c.y - y)]
        elif isinstance(pile, FoundationPile):
            # Allow dragging top card back to tableau
            if c != pile.top():
                return
            stack = [c]
            offsets = [(c.x - x, c.y - y)]
        elif isinstance(pile, TableauPile):
            # Can drag any face-up stack (sequence validation happens on drop)
            idx = pile.cards.index(c)
            # Ensure clicked card is face up
            if not c.face_up:
                # If it's face-down top, flip it
                if c == pile.top():
                    c.flip_up()
                    self.canvas.itemconfig(c.canvas_item, image=c.image())
                return
            stack = pile.cards[idx:]
            # Compute offsets for each in stack
            offsets = []
            base_dx = c.x - x
            base_dy = c.y - y
            # Respect tableau gaps for visual during drag
            for i, sc in enumerate(stack):
                dy = base_dy + i * TABLEAU_GAP_Y_FACEUP
                offsets.append((base_dx, dy))
        else:
            return

        # Start dragging
        self.dragging_stack = stack
        self.drag_origin = pile
        self.drag_offsets = offsets
        self.drag_start_mouse = (x, y)

        # Raise dragged items above others
        for sc in stack:
            self.canvas.tag_raise(sc.canvas_item)

    def on_drag(self, event):
        if not self.dragging_stack:
            return
        x, y = event.x, event.y
        for (dx, dy), c in zip(self.drag_offsets, self.dragging_stack):
            self.canvas.coords(c.canvas_item, x + dx, y + dy)

    def on_release(self, event):
        if not self.dragging_stack:
            return
        x, y = event.x, event.y
        stack = self.dragging_stack
        head = stack[0]
        origin = self.drag_origin

        # Try foundations first if single card
        target = None
        if len(stack) == 1:
            for f in self.foundations:
                if f.is_point_inside(x, y) and f.can_accept(head):
                    target = f
                    break

        # Then tableau
        if target is None:
            legal_tableaus = []
            for t in self.tableau:
                if t.is_point_inside(x, y) and t.can_accept_head(head):
                    legal_tableaus.append(t)
            if legal_tableaus:
                # If multiple candidates, pick the one whose x is closest to mouse
                target = sorted(legal_tableaus, key=lambda p: abs(p.x - x))[0]

        moved = False
        if target is not None:
            # Execute move
            moving = origin.remove_from(head)
            if target in self.foundations:
                if len(moving) != 1:
                    moving = [head]
                moved = target.add_cards([moving[0]])
                if not moved:
                    # put back
                    origin.add_cards(moving)
            elif isinstance(target, TableauPile):
                moved = target.add_stack(moving)
                if not moved:
                    origin.add_cards(moving)

        if not moved:
            # Snap back
            origin.relayout()
        else:
            # Flip origin's new top if needed
            if isinstance(origin, TableauPile):
                top = origin.top()
                if top and not top.face_up:
                    top.flip_up()
                    self.canvas.itemconfig(top.canvas_item, image=top.image())
            self.check_win()

        # Clear drag state
        self.dragging_stack = []
        self.drag_origin = None
        self.drag_offsets = []

    def on_double_click(self, event):
        c = self.card_at(event.x, event.y)
        if c is None:
            return
        # Try auto move to foundation
        self.try_auto_move_to_foundation(c)

    # -------------------- Game Mechanics --------------------
    def deal_from_stock(self):
        # If stock has cards, move one to waste and flip
        if self.stock.cards:
            c = self.stock.cards.pop()
            c.flip_up()
            c.pile = self.waste
            self.waste.cards.append(c)
            # Show previous stock top
            self.stock.relayout()
            self.waste.relayout()
        else:
            # Recycle waste to stock (face-down, reverse order)
            if not self.waste.cards:
                return
            moving = list(reversed(self.waste.cards))
            self.waste.cards = []
            for c in moving:
                c.flip_down()
                c.pile = self.stock
            self.stock.cards.extend(moving)
            self.stock.relayout()
            self.waste.relayout()


if __name__ == "__main__":
    root = tk.Tk()
    game = SolitaireGame(root)
    root.mainloop()
