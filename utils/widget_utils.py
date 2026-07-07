import tkinter as tk
from .number_utils import format_number, parse_number


def bind_number_entry(entry):

    def format_input(event=None):

        text = entry.get()

        if not text:
            return

        cursor = entry.index(tk.INSERT)

        number = parse_number(text)

        formatted = format_number(number)

        entry.delete(0, tk.END)
        entry.insert(0, formatted)

        try:
            entry.icursor(cursor)
        except:
            pass

    entry.bind("<FocusOut>", format_input)
    entry.bind("<KeyRelease>", lambda e: format_input())