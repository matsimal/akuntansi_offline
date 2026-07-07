from .number_utils import format_number

def rupiah(value):
    try:
        return "Rp " + format_number(value, 0)
    except:
        return "Rp 0"