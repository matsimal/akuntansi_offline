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