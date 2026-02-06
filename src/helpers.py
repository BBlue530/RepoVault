def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.2f} MB"
    else:
        return f"{size_bytes / 1024**3:.2f} GB"
    
def sterilize_output(output, forbidden_value):
    not_sterilized_output = output.stderr or output.stdout or str(output)

    if isinstance(not_sterilized_output, bytes):
        not_sterilized_output = not_sterilized_output.decode("utf-8", errors="replace")

    sterilized_output = not_sterilized_output.replace(forbidden_value, "***")

    return sterilized_output