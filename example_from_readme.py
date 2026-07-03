from rankyswanky import RankySwanky  
   
# 1. Wrap your search engine or retriever in a simple Python function:  
def my_search_engine(query):  
    # Return a list of results for the given query  
    return ["result1", "result2", "result3"]  
   
# 2. Create your questions list:  
questions = [  
    "Who invented the lightbulb?",  
    "What is the capital of Norway?",  
    "Explain quantum entanglement simply."  
]  
   
# 3. Run evaluation!  
ranker = RankySwanky(my_search_engine)  
results = ranker.evaluate(questions)  
   
# 4. Print or visualize results  
results.print_summary()
results.print_comparison()


