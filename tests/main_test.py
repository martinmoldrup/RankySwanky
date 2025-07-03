from rankyswanky import RankySwanky

def test_rankyswanky_easy_example():
    """Test the RankySwanky class with a simple example."""
    query = "What is the capital of France?"
    def my_search_engine(query: str) -> list[str]:
        """Dummy search engine that returns a fixed response."""
        search_results = [
            "France's capital is Paris.",
            "Paris is known for its art, fashion, and culture.",
            "There is a dish called 'French fries' that is popular in many countries.",
        ]
        return search_results

    ranky = RankySwanky(retriever=my_search_engine)
    results = ranky.evaluate([query])

    assert len(results.runs) == 1
    assert results.runs[0].per_query_results[0].query == "What is the capital of France?"
    assert len(results.runs[0].per_query_results[0].retrieved_documents) == 3
    assert results.runs[0].per_query_results[0].retrieved_documents[0].document_content == "France's capital is Paris."

