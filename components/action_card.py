import customtkinter as ctk
from config import THEME

class ActionCard(ctk.CTkFrame):
    """
    Reusable Action Card
    """

    def __init__(
        self,
        master,
        title="Button",
        icon="➕",
        command=None,
        width=80,
        height=80,
        bg=THEME["button_color"],
        fg=THEME["button_text_color"],
        hover_bg=THEME["button_hover_color"],
        border_color=THEME["button_border_color"],
        font=("Segoe UI", 12),
        icon_font=("Segoe UI Emoji", 16),
    ):
        super().__init__(
            master,
            fg_color="transparent"
        )

        self.command = command
        self.normal_bg = bg
        self.hover_bg = hover_bg
        self.border_color = border_color

        self.configure(cursor="hand2")

        # Card
        self.canvas = ctk.CTkFrame(
            self,
            width=width,
            height=height,
            fg_color=bg,
            corner_radius=12,
            border_width=1,
            border_color=border_color,
        )
        self.canvas.pack()
        self.canvas.pack_propagate(False)

        # Icon
        self.icon_label = ctk.CTkLabel(
            self.canvas,
            text=icon,
            text_color=fg,
            font=icon_font,
            fg_color="transparent",
        )
        self.icon_label.pack(expand=True, pady=(8, 2))

        # Title
        self.text_label = ctk.CTkLabel(
            self.canvas,
            text=title,
            text_color=fg,
            font=font,
            fg_color="transparent",
            justify="center",
            anchor="center",
        )
        self.text_label.pack(pady=(0, 8))

        # Hover & Click Events
        widgets = (
            self,
            self.canvas,
            self.icon_label,
            self.text_label,
        )

        for widget in widgets:
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)
            widget.bind("<Button-1>", self._click)

    def _enter(self, event=None):
        self.canvas.configure(
            fg_color=self.hover_bg,
            border_color=THEME["button_border_color"],
        )

    def _leave(self, event=None):
        self.canvas.configure(
            fg_color=self.normal_bg,
            border_color=THEME["button_border_color"],
        )

    def _click(self, event=None):
        if self.command:
            self.command()

    def refresh_theme(self):
        self.normal_bg = THEME["button_color"]
        self.hover_bg = THEME["button_hover_color"]

        self.canvas.configure(
            fg_color=self.normal_bg,
            border_color=THEME["button_border_color"],
        )

        self.icon_label.configure(
            text_color=THEME["button_text_color"]
        )

        self.text_label.configure(
            text_color=THEME["button_text_color"]
        )