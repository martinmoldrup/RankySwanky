

# Start Here: How It Works

## The main idea
Effortless, annotation-free evaluation for AI search, retrieval, and ranking systems, powered by LLMs as judges. 

## The problem
There are excellent metrics like NDCG for evaluating search / retrieval / ranking systems, but they require manual annotation of relevance. This is time-consuming, expensive, and often not feasible at scale. 

The idea is that we want to give a list of questions and a search engine, and have the system automatically query the engine, get results, and use LLMs to score the relevance of those results without any human annotation.

## The solution
First lets see how NDCG is calculated:
1. For each question, you get a list of results from the search engine.
2. You have a set of relevance judgments for those results (e.g. 0, 1, 2 for not relevant, somewhat relevant, very relevant).
3. You calculate the Discounted Cumulative Gain (DCG) for the ranked list of results, which is a weighted sum of the relevance scores, where higher-ranked results contribute more to the score.
4. You calculate the Ideal DCG (IDCG) which is the DCG of the ideal ranking (where the most relevant results are ranked highest).
5. You then compute NDCG as DCG / IDCG, which gives you a score between 0 and 1 indicating how well the search engine's ranking matches the ideal ranking.
6. You can then average the NDCG scores across all questions to get an overall performance metric for the search engine.

The key innovation in RankySwanky is that instead of requiring human annotators to assign relevance scores to the search results, we use LLMs to automatically judge the relevance of each result for each question. This allows us to compute NDCG and other metrics without any manual annotation, making it much easier and faster to evaluate search engines at scale.

### The NCG metric
In RAG applications, we actually do not care about the order of the results, as long as we have all the relevant information in the retrieved results. This is why we also calculate NCG (Normalized Cumulative Gain), which is similar to NDCG but does not take into account the order of the results. This makes it more suitable for RAG applications where the LLM can extract information from any of the retrieved documents regardless of their position in the ranked list.

The only difference is step 4
4. You calculate the Ideal Cumulative Gain (ICG) which is the CG of the ideal set of results (where you have all the relevant results), this is different than in NDCG, since we can simply multiply the number of relevant results by the maximum relevance score to get the ICG.


# How to calculate the gain of a result
This is where it gets tricky, the gain is how much value a results add to the ability to provide a good answer for a specific user profile. We need to measure:
- Relevance: how relevant is the result to the question?
- Novelty: how much new information does the result add compared to the other results?

Then we can combine relevance and novelty to calculate the gain of a result.
```
gain = relevance * novelty
```

## Approach 1: LLM assigns relevance scores to each result independently.
One approach is just to ask the LLM to assign a relevance score (e.g. 0, 1, 2) to each result for each question and context pair. 

The approach is implemented in `rankyswanky\application\metrics\retrieved_document_metrics.py`.

The approach is simple and straightforward, but it can be noisy since the LLM does not have reference points to other results.

## Approach 2:
An alternative approach is to first ask the LLM to figure out for a given question, what are the different relevant dimensions of this question. When we do that we can provide a profile of the user, since relevance can be subjective and depend on the user's background, preferences, etc. 

Now that we have all the different dimensions, we use these dimensions and structured output to asign boolean values to each result for each dimension. This approach has the additional advantage that we have have details we can use to analyze novelty as well as relevance. If a result is adding information to a dimension that has already been covered, that does not add as much gain as if it is adding information to a dimension that has not been covered at all.

This approach is implemented in `rankyswanky\application\metrics\retrieved_document_metrics_validation_criteria.py`

<!-- Notes:
Questions:
- The approach of making the novelty based on the previous results is tricky, since the order of the results can affect the novelty score. 
 -->

The way it is calculated is as follows:
Relevance_doc = sum of normalized importance_i for the dimensions the document covers.
(Since importance_i sums to 1, relevance_doc is just the sum over covered dimensions.)


## Approach 3: LLM compares results pairwise.
An alternative and perhaps complimentary approach is to ask the LLM if result A is more relevant than result B for a given question and user profile. This approach can be more robust since the LLM can directly compare the two results and make a judgment based on that comparison.


### Getting from the pairs into a ranking
The ideal algorithm should follow these principles:
- You have items with noisy pairwise comparison votes saying one is better, worse, or equal.
- You want to produce a global ranking that minimizes disagreement with the votes.
- You also have LLM‑predicted relevance scores (0–1) that should serve as starting values.
- New pairwise votes will arrive continuously, so the ranking must update online.
- You want to identify the items with highest uncertainty/entropy to request more human annotations.
- The ranking does not need to be perfect; a good approximation is fine, if it means more efficient updates and simpler implementation.

You have search results for a query and an ML model that outputs initial relevance scores. LLM also compare result pairs and vote which one is more relevant. These votes are noisy and inconsistent. As new votes arrive, you want to update each document’s relevance score, combining ML predictions with human comparisons. You also want to detect which results are most uncertain so you can ask annotators to label the pairs that will most improve ranking quality.

The best algorithm for combining the results from approach 2 and 3 into a ranking algorithm is the TrueSkill algorithm, which is a Bayesian ranking algorithm that can handle noisy pairwise comparisons and can update the rankings online as new comparisons arrive. It also provides a measure of uncertainty for each item, which can be used to identify which items would benefit most from additional annotations.

The TrueSkill is inspired by the Bradley-Terry model, which is a probabilistic model for pairwise comparisons. The TrueSkill algorithm extends the Bradley-Terry model by incorporating uncertainty and allowing for online updates.

............ Notes
Simpler alternatives
Option 1: Choix (Bradley–Terry / Plackett–Luce)
Pros:

perfect for 1‑vs‑1 ranking
designed for search/recommendation ranking
extremely lightweight
mathematically clean (MLE / MAP)
easy to embed directly in your project
Cons:

no uncertainty (unless using Bayesian variant)
no “sigma” to drive active learning
Option 2: Glicko‑2
Pros:

simple
supports rating + uncertainty (RD)
well‑tested, widely used
easy to copy into your project (few hundred lines)
stable, predictable updates
Cons:

originally designed for games, not pairwise ML
no Plackett–Luce (only 1‑vs‑1)
Option 3: TrueSkill / TrueSkill‑Through‑Time
Pros:

also pairwise-friendly
provides mu + sigma
used in recommender systems (implicit feedback)
Cons:
updates are larger unless tuned
more complex code than Glicko2 or Choix


## Novelty
Novelty is how much new information a result adds compared to the other results. This is important because if a result is adding information to a dimension that has already been covered, that does not add as much gain as if it is adding information to a dimension that has not been covered at all.


An obvious idea is to use vector embeddings, but this is tricky since we used embeddings to fetch the results in the first place, so we cannot use the same embeddings to calculate novelty, since that would be circular. We need to use a different method to calculate novelty, perhaps based on the dimensions we identified in approach 2.

We want a novelty metric that fulfills these parameters
• Novelty should never drop to exactly zero, even for already‑covered dimensions.
• Re‑seeing an important dimension should still give some gain, more than re‑seeing an unimportant one.
• The system should still give higher novelty for dimensions not yet covered, but without turning repeated ones into zero.
• Novelty must work cleanly with your formula `gain = relevance * novelty` so novelty must be bounded and stable.
• You want predictable behavior, not something overly sensitive or erratic.
• You want to keep the importance weights meaningful in how novelty is computed.
• Approach must be different to how the search engine works to avoid circularity (e.g. not using the same embeddings).
• The novelty should be between 0 and 1, so it can be easily combined with the relevance score in the gain formula. 
• The value should be 1 if a document covers all dimensions, and no dimensions have been covered before.

### The Importance‑Weighted Novelty Decay Model

One simple formula that meets these criteria is:

For each dimension i, we can calculate the novelty score as follows:
`importance_i`: How important is this dimension for the question? This can be determined by the LLM when it identifies the dimensions in approach 2. The importance is normalized such that the sum of the importance scores for all dimensions is 1.
`novelty_i`: The novelty score for dimension i, which is between 0 and 1. It starts at 1 when coverage is zero and decreases as coverage increases, but never drops to zero due to the structure of the formula.
`dimension_coverage_i`: How often has this dimension allready been covered by the previous results? This can be calculated based on counting the true booleans for this dimension in the previous results.
`alpha`: A constant hyperparameter that controls how quickly novelty decays as coverage increases. A common choice is alpha = 1, which gives a simple inverse relationship.

For this purpose we believe that a soft decay formula is the best choice, since it allows for novelty to decrease as coverage increases, but it never drops to zero, which is important to ensure that we still get some gain from re‑seeing important dimensions, while still giving higher novelty for dimensions not yet covered.
```
novelty_i = 1 / (1 + dimension_coverage_i^alpha * importance_i)
```

We also have a linear decay formula (rejected since it can drop to zero):
```
novelty_i = importance_i / (1 + alpha * dimension_coverage_i)
```

We need to calculate the overall novelty score for a document by combining the novelty scores for each dimension. One simple way to do this is to take a weighted average of the novelty scores for each dimension, where the weights are based on the importance of each dimension:

`novelty_doc`: The overall novelty score for the document, which is between 0 and 1. It is calculated as a weighted average of the novelty scores for each dimension, where the weights are based on the importance of each dimension. This way, dimensions that are more important for the question will have a greater influence on the overall novelty score of the document.

```
novelty_doc = sum(importance_i * novelty_i for i in dimensions)
```

This is only correct if importance have been normalized, otherwise we need to divide by the sum of the importance scores to ensure that the novelty_doc is between 0 and 1:


# Performance and caching
We might run multiple evaluations of a search engine, with different settings, or we might want to compare multiple search engines. It is important that the dimensions of a question in approach 2 are cached, since they can be reused across different evaluations, to make the results properly comparable and save cost and time. The same applies to the relevance scores for a document. Once a document has been judged for a question, we do not need to re-calculate its relevance score for that question, since it should not change based on the search engine settings. We also need to store the boolen results from each dimension though, because they are needed to calculate the novelty score, that is order dependent and cannot be cached. We can however cache the calculated input for this.

The cached algorithm for approach 2 would look like this:
1. For each evaluation run
   1. For each question
      1. check if the dimensions have already been calculated and cached. If not, calculate the dimensions and cache them.
      2. For each search result, check if the dimension booleans have already been calculated and cached. If not, run the structured output to get the dimension booleans and cache them.
      3. Calculate the relevance score and cache it, if it has not been calculated and cached already.
      4. Calculate the novelty score and gain score, but do not cache it since it is order dependent.
   5. Calculate the NCG score for the search engine based on the gain scores of the results. Since the gain scores are not cached, we need to calculate them for each evaluation, but we can use the cached relevance scores and dimension booleans to calculate the gain scores more efficiently.

