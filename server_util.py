# Set of allowed file extensions for Excel files
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'xlsm'}


def get_file_extension(filename: str) -> str:
    """
    Returns the file extension of the given filename.

    Args:
        filename (str): The name of the file.

    Returns:
        str: The file extension in lowercase.
    """
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """
    Checks if the file has an allowed extension.

    Args:
        filename (str): The name of the file.
        allowed_extensions (set, optional): A set of allowed extensions.
            If None, uses the global ALLOWED_EXTENSIONS. Defaults to None.

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    global ALLOWED_EXTENSIONS
    return ('.' in filename
            and get_file_extension(filename) in (allowed_extensions or ALLOWED_EXTENSIONS))