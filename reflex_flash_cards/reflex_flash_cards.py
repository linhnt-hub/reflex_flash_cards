"""Flashcard app for learning English words with Vietnamese descriptions."""
import reflex as rx
import json
import os
from typing import List, Dict, Any

DATA_FILE = "flashcards.json"


class FlashcardState(rx.State):
    """State for the flashcard application."""
    
    flashcards: List[Dict[str, Any]] = []
    current_index: int = 0
    show_answer: bool = False
    new_english: str = ""
    new_vietnamese: str = ""
    filter_learned: bool = False
    search_query: str = ""
    sort_alpha: bool = False
    view_mode: str = "single"  # "single" or "grid"
    flipped_cards: List[int] = []  # Track which cards are flipped in grid view (by index)
    flipped_words: List[str] = []  # Track which cards are flipped in grid view (by word)
    temp_word: str = ""  # Temporary storage for word operations
    
    def set_temp_word(self, word: str):
        """Set the temporary word."""
        self.temp_word = word
    
    def load_flashcards(self):
        """Load flashcards from JSON file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.flashcards = json.load(f)
            except Exception as e:
                print(f"Error loading flashcards: {e}")
                self.flashcards = []
        else:
            self.flashcards = []
    
    def save_flashcards(self):
        """Save flashcards to JSON file."""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.flashcards, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving flashcards: {e}")
    
    @rx.var
    def filtered_flashcards(self) -> List[Dict[str, Any]]:
        """Get flashcards based on filter."""
        if self.filter_learned:
            return [card for card in self.flashcards if not card.get("learned", False)]
        return self.flashcards
    
    @rx.var
    def visible_flashcards(self) -> List[Dict[str, Any]]:
        """Apply search and sort to the filtered flashcards."""
        cards = list(self.filtered_flashcards)
        query = (self.search_query or "").strip().lower()
        if query:
            cards = [
                c for c in cards
                if query in (c.get("english", "") or "").lower()
                or query in (c.get("vietnamese", "") or "").lower()
            ]
        if self.sort_alpha:
            cards = sorted(cards, key=lambda c: (c.get("english", "") or "").lower())
        return cards
    
    @rx.var
    def current_card(self) -> Dict[str, Any] | None:
        """Get the current flashcard."""
        filtered = self.visible_flashcards
        if not filtered:
            return None
        if self.current_index >= len(filtered):
            return filtered[0] if filtered else None
        return filtered[self.current_index]
    
    @rx.var
    def card_count(self) -> int:
        """Get the number of filtered cards."""
        return len(self.visible_flashcards)
    
    @rx.var
    def card_counter_text(self) -> str:
        """Get the card counter text."""
        count = len(self.visible_flashcards)
        if count == 0:
            return "No cards"
        return f"Card {self.current_index + 1} of {count}"
    
    def next_card(self):
        """Move to the next card."""
        filtered = self.visible_flashcards
        if filtered:
            self.current_index = (self.current_index + 1) % len(filtered)
            self.show_answer = False
    
    def previous_card(self):
        """Move to the previous card."""
        filtered = self.visible_flashcards
        if filtered:
            self.current_index = (self.current_index - 1) % len(filtered)
            self.show_answer = False
    
    def toggle_answer(self):
        """Toggle showing the answer."""
        self.show_answer = not self.show_answer
    
    def add_flashcard(self):
        """Add a new flashcard."""
        if self.new_english.strip() and self.new_vietnamese.strip():
            new_card = {
                "english": self.new_english.strip(),
                "vietnamese": self.new_vietnamese.strip(),
                "learned": False
            }
            self.flashcards.append(new_card)
            self.new_english = ""
            self.new_vietnamese = ""
            self.save_flashcards()
            # Reset index if needed
            filtered = self.visible_flashcards
            if self.current_index >= len(filtered):
                self.current_index = max(0, len(filtered) - 1)
    
    def remove_current_card(self):
        """Remove the current flashcard."""
        current = self.current_card
        if current:
            self.flashcards = [card for card in self.flashcards if card != current]
            self.save_flashcards()
            filtered = self.visible_flashcards
            if filtered:
                if self.current_index >= len(filtered):
                    self.current_index = max(0, len(filtered) - 1)
            else:
                self.current_index = 0
    
    def toggle_learned(self):
        """Toggle learned status of current card in single view."""
        # Toggle for current card in single view
        current = self.current_card
        if current:
            # Find the card in the original list and update it
            for card in self.flashcards:
                if card == current:
                    card["learned"] = not card.get("learned", False)
                    break
            self.save_flashcards()
    
    def toggle_learned_by_index(self, card_index: int):
        """Toggle learned status for a specific card by index (for grid view)."""
        filtered = self.visible_flashcards
        if 0 <= card_index < len(filtered):
            card = filtered[card_index]
            # Find in original list
            for original_card in self.flashcards:
                if original_card == card:
                    original_card["learned"] = not original_card.get("learned", False)
                    break
            self.save_flashcards()
    
    def toggle_learned_by_word(self, english_word: str):
        """Toggle learned status by English word."""
        # Find the card in filtered list
        filtered = self.visible_flashcards
        for card in filtered:
            if card.get("english") == english_word:
                # Find in original list
                for original_card in self.flashcards:
                    if original_card == card:
                        original_card["learned"] = not original_card.get("learned", False)
                        break
                self.save_flashcards()
                break
    
    def toggle_flip(self, card_index: int = None):
        """Toggle flip state for a card in grid view."""
        if card_index is None:
            return
        if card_index in self.flipped_cards:
            self.flipped_cards = [idx for idx in self.flipped_cards if idx != card_index]
        else:
            self.flipped_cards = self.flipped_cards + [card_index]
    
    def toggle_flip_by_word(self, english_word: str):
        """Toggle flip state for a card by its English word."""
        if english_word in self.flipped_words:
            self.flipped_words = [word for word in self.flipped_words if word != english_word]
        else:
            self.flipped_words = self.flipped_words + [english_word]
    
    def set_temp_word_and_flip(self):
        """Flip card using temp_word."""
        if self.temp_word:
            self.toggle_flip_by_word(self.temp_word)
            self.temp_word = ""
    
    def set_temp_word_and_mark_learned(self):
        """Mark card as learned using temp_word."""
        if self.temp_word:
            self.toggle_learned_by_word(self.temp_word)
            self.temp_word = ""
    
    def flip_from_data(self):
        """Flip card - this won't work without knowing which card."""
        # This is a limitation of Reflex - we can't pass parameters to event handlers
        # For now, grid view cards won't be individually flippable
        # Users can use single view for card operations
        pass
    
    def mark_learned_from_data(self):
        """Mark learned - this won't work without knowing which card."""
        # This is a limitation of Reflex - we can't pass parameters to event handlers
        # For now, grid view cards won't have individual learned buttons
        # Users can use single view for card operations
        pass
    
    
    
    
    def toggle_view_mode(self):
        """Toggle between single and grid view."""
        self.view_mode = "grid" if self.view_mode == "single" else "single"
        self.show_answer = False
        self.flipped_cards = []
    
    def toggle_filter(self):
        """Toggle filter for learned words."""
        self.filter_learned = not self.filter_learned
        self.current_index = 0
        self.show_answer = False


def flashcard_display() -> rx.Component:
    """Display flashcards based on view mode."""
    return rx.cond(
        FlashcardState.card_count > 0,
        rx.cond(
            FlashcardState.view_mode == "grid",
            _grid_view(),
            _single_card_view(),
        ),
        _empty_state(),
    )


def _empty_state() -> rx.Component:
    """Display when no flashcards are available."""
    return rx.box(
        rx.text(
            "No flashcards available. Add some to get started!",
            font_size="1.2em",
            text_align="center",
            color="gray",
        ),
        padding="2em",
        text_align="center",
    )


def _single_card_view() -> rx.Component:
    """Display single card view with flip animation."""
    return rx.vstack(
        rx.box(
            rx.vstack(
                # English word (front)
                rx.cond(
                    ~FlashcardState.show_answer,
                    rx.cond(
                        FlashcardState.current_card["learned"],
                        rx.box(
                            rx.heading(
                                FlashcardState.current_card["english"],
                                size="8",
                                font_weight="bold",
                                color="teal",
                                text_align="center",
                            ),
                            padding="2em",
                            width="100%",
                            height="200px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                        rx.box(
                            rx.heading(
                                FlashcardState.current_card["english"],
                                size="8",
                                font_weight="bold",
                                color="tomato",
                                text_align="center",
                            ),
                            padding="2em",
                            width="100%",
                            height="200px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                    ),
                ),
                # Vietnamese description (back)
                rx.cond(
                    FlashcardState.show_answer,
                    rx.box(
                        rx.vstack(
                            rx.text(
                                FlashcardState.current_card["vietnamese"],
                                font_size="1.3em",
                                color="#059669",
                                text_align="center",
                                font_weight="medium",
                            ),
                            rx.cond(
                                FlashcardState.current_card["learned"],
                                rx.badge(
                                    "✓ Learned",
                                    color_scheme="green",
                                    margin_top="1em",
                                ),
                            ),
                            spacing="2",
                            align="center",
                        ),
                        padding="2em",
                        width="100%",
                        height="200px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        background="#f0fdf4",
                        border="2px solid #10b981",
                        border_radius="12px"
                    ),
                ),
                spacing="0",
                align="center",
                width="100%",
            ),
            width="100%",
            max_width="500px",
            border_radius="12px",
            background="white",
            box_shadow="0 8px 24px rgba(0,0,0,0.15)",
            transition="transform 0.3s ease-in-out",
            transform=rx.cond(
                FlashcardState.show_answer,
                "rotateY(360deg)",
                "rotateY(0deg)",
            ),
            style={
                "perspective": "1000px",
                "transform-style": "preserve-3d",
            },
        ),
        # Card counter
        rx.text(
            FlashcardState.card_counter_text,
            font_size="0.9em",
            color="gray",
            text_align="center",
            margin_top="1em",
        ),
        spacing="3",
        align="center",
        width="100%",
    )


def _grid_view() -> rx.Component:
    """Display cards in a grid layout with flip animations."""
    return rx.box(
        rx.grid(
            rx.foreach(
                FlashcardState.visible_flashcards,
                _grid_card_with_index,
            ),
            columns="3",
            spacing="4",
            width="100%",
            justify="center",
        ),
        width="100%",
        padding="1em",
    )


def _grid_card_with_index(card: Dict[str, Any], index: int) -> rx.Component:
    """Wrapper to create grid card with index."""
    return _grid_card(card, index)


def _grid_card(card: Dict[str, Any], index: int) -> rx.Component:
    """Individual card in grid view with flip effect."""
    english_word = card.get("english", "")
    is_flipped = FlashcardState.flipped_words.contains(english_word)
    is_learned = card.get("learned", False)
    
    # Store word in data attribute and use event handlers that read from state
    # We'll use a workaround: set the word in state via a computed approach
    return rx.box(
        rx.vstack(
            # Front of card (English)
            rx.cond(
                ~is_flipped,
                rx.box(
                    rx.vstack(
                        rx.cond(
                            is_learned,
                            rx.heading(
                                card["english"],
                                size="6",
                                font_weight="bold",
                                color="teal",
                                text_align="center",
                            ),
                            rx.heading(
                                card["english"],
                                size="6",
                                font_weight="bold",
                                color="tomato",
                                text_align="center",
                            ),
                        ),
                        rx.cond(
                            is_learned,
                            rx.badge(
                                "✓",
                                color_scheme="green",
                                position="absolute",
                                top="0.5em",
                                right="0.5em",
                            ),
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                        height="100%",
                    ),
                    padding="5em",
                    width="100%",
                    height="180px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    background="white",
                    border_radius="8px",
                ),
            ),
            # Back of card (Vietnamese)
            rx.cond(
                is_flipped,
                rx.box(
                    rx.vstack(
                        rx.text(
                            card["vietnamese"],
                            font_size="1em",
                            color="#059669",
                            text_align="center",
                            font_weight="medium",
                        ),
                        # Note: Individual card operations in grid view are limited
                        # due to Reflex's event handler constraints
                        # Use single view for marking cards as learned
                        spacing="2",
                        align="center",
                    ),
                    padding="1.5em",
                    width="100%",
                    height="180px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    background="#f0fdf4",
                    border="2px solid #10b981",
                    border_radius="8px",
                ),
            ),
            spacing="0",
            align="center",
            width="100%",
            position="relative",
        ),
        width="100%",
        cursor="pointer",
        # Note: Card flip in grid view is disabled due to Reflex limitations
        # Use single view to flip cards individually
        transition="transform 0.3s ease-in-out",
        transform=rx.cond(
            is_flipped,
            "rotateY(180deg)",
            "rotateY(0deg)",
        ),
        style={
            "perspective": "1000px",
            "transform-style": "preserve-3d",
        },
        box_shadow="0 4px 16px rgba(0,0,0,0.1)",
        _hover={
            "box_shadow": "0 4px 12px rgba(0,0,0,0.15)",
            "transform": "translateY(-2px)",
        },
    )


def add_card_form() -> rx.Component:
    """Form to add new flashcards."""
    return rx.box(
        rx.vstack(
            rx.heading("Add New Flashcard", size="5", margin_bottom="1em"),
            rx.input(
                placeholder="English word",
                value=FlashcardState.new_english,
                on_change=FlashcardState.set_new_english,
                width="100%",
                margin_bottom="0.5em",
            ),
            rx.input(
                placeholder="Vietnamese description",
                value=FlashcardState.new_vietnamese,
                on_change=FlashcardState.set_new_vietnamese,
                width="100%",
                margin_bottom="0.5em",
            ),
            rx.button(
                "Add Card",
                on_click=FlashcardState.add_flashcard,
                color_scheme="teal",
                width="100%",
            ),
            spacing="3",
            align="stretch",
        ),
        padding="2em",
        border_radius="8px",
        background="white",
        box_shadow="0 10px 50px rgba(0,0,0,0.1)",
    )


def index() -> rx.Component:
    """Main page component."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "English Vocabulary Flashcards",
                size="8",
                text_align="center",
                margin_bottom="1.5em",
                color="#1e40af",
                font_weight="bold",
            ),
            rx.hstack(
                rx.vstack(
                    rx.flex(
                        rx.text("Show new words", font_size="0.9em", color="gray"),
                        rx.switch(
                            "Hide Learned Words",
                            checked=FlashcardState.filter_learned,
                            on_change=FlashcardState.toggle_filter,
                        ),
                        spacing="3"
                    ),
                    rx.flex(
                        rx.text("Sort A–Z", font_size="0.9em", color="gray"),
                        rx.switch(
                            checked=FlashcardState.sort_alpha,
                            on_change=FlashcardState.set_sort_alpha,
                        ),
                        spacing="9"
                    ),
                ),
                rx.flex(
                    rx.input(
                        placeholder="Search word or meaning",
                        value=FlashcardState.search_query,
                        on_change=FlashcardState.set_search_query,
                        width="16em",
                        height="2em"
                    ),
                    spacing="2",
                ),
                rx.button(
                    rx.cond(
                        FlashcardState.view_mode == "grid",
                        "Single View",
                        "Grid View",
                    ),
                    on_click=FlashcardState.toggle_view_mode,
                    color_scheme="purple",
                    radius="medium",
                    size="1",
                ),
                rx.cond(
                    FlashcardState.view_mode == "single",
                    rx.flex(
                        rx.button(
                            rx.cond(
                                FlashcardState.current_card["learned"],
                                "Mark as Unlearned",
                                "Mark as Learned",
                            ),
                            on_click=FlashcardState.toggle_learned,
                            color_scheme="green",
                            size="1",
                        ),
                        rx.button(
                            rx.icon(tag="x"),
                            on_click=FlashcardState.remove_current_card,
                            color_scheme="red",
                            size="1",
                        ),
                        spacing="2",
                    ),
                ),
                spacing="8",
                justify="center",
                margin_bottom="1.5em",
            ),
            rx.spacer(),
            rx.spacer(),
            flashcard_display(),
            # Single view controls
            rx.cond(
                FlashcardState.view_mode == "single",
                rx.vstack(
                    rx.hstack(
                        rx.button(
                            rx.icon(tag="chevron-left"),
                            on_click=FlashcardState.previous_card,
                            color_scheme="teal",
                            style={
                                "color":"black",
                                "bg":"white",
                                "border-radius": "15px 15px",
                                "box-shadow": "6px 6px 12px #c5c5c5, -6px -6px 12px #ffffff",
                            },
                            size="2",
                        ),
                        rx.button(
                            rx.cond(
                                FlashcardState.show_answer,
                                "Hide Answer",
                                "Show Answer",
                            ),
                            rx.box(  # lớp nền gradient ẩn (mô phỏng ::before)
                                bg="linear-gradient(90deg, #FDBB2D 0%, #22C1C3 100%)",
                                border_radius="30em",
                                position="absolute",
                                top="0",
                                left="0",
                                height="3em",
                                width="0em",  # mặc định ẩn
                                transition="width 0.5s ease",
                                z_index="-1",
                            ),
                            on_click=FlashcardState.toggle_answer,
                            # color_scheme="indigo",
                            style={
                                "color": "black",
                                "background": "white",
                                "border-radius": "30em",
                                "border": "none",
                                "position": "relative",
                                "overflow": "hidden",
                                "z-index": "1",
                                "box-shadow": "6px 6px 12px #c5c5c5, -6px -6px 12px #ffffff",
                                "cursor": "pointer",
                                "width":"10em"
                            },
                            _hover={
                                # hiệu ứng gradient mở rộng
                                "& > div:first-child": {  # chọn phần tử rx.box bên trong
                                    "width": "10em",
                                },
                            },
                            size="2",
                        ),
                        rx.button(
                            rx.icon(tag="chevron-right"),
                            on_click=FlashcardState.next_card,
                            style={
                                "color":"black",
                                "bg":"white",
                                "border-radius": "15px 15px",
                                "box-shadow": "6px 6px 12px #c5c5c5, -6px -6px 12px #ffffff",
                            },
                            size="2",
                        ),
                        spacing="3",
                        justify="center",
                        margin_bottom="1em",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
            ),
            rx.spacer(),
            rx.spacer(),
            rx.box(
                add_card_form(),
                width="100%",
                max_width="500px",
                margin="0 auto",
            ),
            spacing="4",
            align="center",
            width="100%",
        ),
        padding="2em",
        max_width="1200px",
        margin="0 auto",
        center_content=True,
        on_mount=FlashcardState.load_flashcards,
    )


# Create app
app = rx.App()
app.add_page(index, route="/", title="English Vocabulary Flashcards")
