def label2str(label):
    """
    Convert a label of type `namedtuple` to a simple `string`.

    By default the string representation of a `namedtuple` contains the
    field name and the value names. This function will return a string with
    only the values separated by an underscore. Whitespaces are replaced by
    dashes. This allows it to use it a human readable key.
    """
    return "_".join(map(str, label._asdict().values())).replace(" ", "-")
