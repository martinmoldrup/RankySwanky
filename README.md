# 🕺 RankySwanky 🕺  
> NOTE: This is being actively developed and may change frequently.

**Effortless, annotation-free evaluation for AI search, retrieval, and ranking systems. Let LLMs do the judging — so you can get swanky with your ranks!**  
   
---  
   
## What is RankySwanky?  
   
**RankySwanky** makes comparing and benchmarking search engines, retrievers, and rankers a breeze — with zero manual annotation. Just connect your engine and hand over a list of questions; RankySwanky automatically queries, scores results using state-of-the-art LLMs (Large Language Models), and computes all the vital metrics you need to optimize your RAG (Retrieval Augmented Generation) pipelines or search products.  
   
No data labeling, no configs, no headaches. Instantly see how different engines/configurations stack up!  
   
---  
   
## Features  
   
- 🪄 **Plug & Play:** Simple interface to connect any search engine or ranker.  
- 🤖 **LLM-Powered Judging:** Harness generative AI (LLMs) to score search/retrieval results, no human annotation required!  
- 🏅 **Comprehensive Metrics:** Computes NDCG, relevance, novelty, and **normalized cumulative gain (NCG)** — designed specifically for order-agnostic RAG and AI scenarios.  
- 📊 **Clear Comparisons:** Instantly compare engines/settings side-by-side with easy-to-understand summaries & visuals.  
- 🥳 **Zero Hassle:** Just supply your engine function and a question list. RankySwanky does the rest!  
- 🌱 **Open Source & Friendly:** Perfect for projects large and small, hobbyists or startups.  
   
---  
   
## Installation  
   
```bash  
pip install rankyswanky  
```  
   
Or install from source:  
   
```bash  
git clone https://github.com/yourusername/rankyswanky.git  
cd rankyswanky  
pip install .  
```  
   
---  
   
## Quickstart  
   
```python  
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
print(results.summary())  
results.plot_comparison()  
```  
   
*Tip: Easily compare two or more engines by evaluating each and comparing summaries!*  
   
---  
   
## Metrics  
   
- **NDCG** *(Normalized Discounted Cumulative Gain)*  
- **NCG** *(Normalized Cumulative Gain — order does NOT matter, RAG-friendly!)*  
- **Relevance** *(LLM-judged relevance for any query-result pair)*  
- **Novelty**  
   
All metrics are automatically scored by the LLM judge—no labeled data needed!  
   
---  
   
## Why RankySwanky?  
   
- **No more manual annotation:** Small team? Big impact. No labeling needed.  
- **Compare any engine:** From in-house retrievers to search SaaS APIs.  
- **Instant insights:** See strengths, weaknesses, and pick the best configuration for your AI/RAG projects.  
   
---  
   
## Docs & Examples  
   
- [📘 Full documentation (coming soon!)](https://github.com/yourusername/rankyswanky/wiki)  
- [✨ Example notebook (quick tour)](examples/demo.ipynb)  
   
---  
   
## Contributing  
   
Pull requests, issues, and ideas are all welcome!    
Whether you're adding metrics, new LLM providers, UI improvements, or docs—join the swanky crew!  
   
Check `CONTRIBUTING.md` for more info.  
   
---  
   
## License  
   
MIT License. See [LICENSE](LICENSE) for details.  
   
---  
   
**Made with 💃 by [YourName]**    
*Swank up your search & AI evaluation!*  
  
   
---  
