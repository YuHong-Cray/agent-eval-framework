def read_file_lines(filepath: str) -> list[str]:
    f = open(filepath, 'r')
    lines = f.read().split('\n')
    return lines
