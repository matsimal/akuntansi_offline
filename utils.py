from datetime import date
import tkinter as tk


def format_number(value, decimal=2):
    try:
        value = float(value)
        formatted = f"{value:,.{decimal}f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except:
        return "0"


def parse_number(text):
    try:
        text = str(text).strip()
        text = text.replace(".", "").replace(",", ".")
        return float(text)
    except:
        return 0


def rupiah(value):
    try:
        return "Rp " + format_number(value, 0)
    except:
        return "Rp 0"


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


def current_date():
    from datetime import datetime

    return datetime.now().strftime("%d/%m/%Y")


def treeview_sort_column(tree, col, reverse=False, numeric=False):

    data = [(tree.set(k, col), k) for k in tree.get_children("")]

    if numeric:

        def to_num(v):
            try:
                return parse_number(v)
            except:
                return 0

        data.sort(key=lambda t: to_num(t[0]), reverse=reverse)

    else:
        data.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

    for index, (_, k) in enumerate(data):
        tree.move(k, "", index)

    tree.heading(
        col, command=lambda: treeview_sort_column(tree, col, not reverse, numeric)
    )
