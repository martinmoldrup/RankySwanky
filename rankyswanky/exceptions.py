class RetrieverResultsTypeError(TypeError):
    """Custom error for when the retriever returns results in an unexpected format."""


class RetrieverResultsEmptyError(ValueError):
    """Custom error for when the retriever returns an empty list of results."""