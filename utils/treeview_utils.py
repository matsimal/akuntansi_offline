from .number_utils import parse_number

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
