from rankyswanky import RankySwanky
from snappylapy import Expect

def test_rankyswanky_easy_example(expect: Expect) -> None:
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
    expect.dict(results).to_match_snapshot()

def test_rankyswanky_compare_to_results():
    """Test the RankySwanky class with a comparison to expected results."""
    ranky = RankySwanky()
    query = "What is the capital of France?"
    def my_search_engine(query: str) -> list[str]:
        """Dummy search engine that returns a fixed response."""
        search_results = [
            "France's capital is Paris.",
            "Paris is known for its art, fashion, and culture.",
            "There is a dish called 'French fries' that is popular in many countries.",
        ]
        return search_results

    def my_other_search_engine(query: str) -> list[str]:
        """Another dummy search engine that returns a different fixed response."""
        search_results = [
            "Paris is famous for its Eiffel Tower.",
            "The capital of France is Paris and it is a major European city.",
            "French cuisine is renowned worldwide.",
        ]
        return search_results
    ranky.add_retriever("my_search_engine", my_search_engine)
    ranky.add_retriever("my_other_search_engine", my_other_search_engine)
    results = ranky.evaluate([query])
    results.print_comparison()