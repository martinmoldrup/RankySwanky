import numpy as np  
  
class BradleyTerry:  
    def __init__(self, item_ids, ml_scores):  
        # Convert ML scores 0–1 into initial log‑strengths  
        # Add small epsilon so we never hit ±inf  
        eps = 1e-6  
        self.theta = {item: np.log(score + eps) for item, score in ml_scores.items()}  
        self.items = item_ids  
  
        # Track counts for uncertainty estimates  
        self.wins = {i: 0 for i in item_ids}  
        self.loss = {i: 0 for i in item_ids}  
  
    def prob(self, a, b):  
        ta = np.exp(self.theta[a])  
        tb = np.exp(self.theta[b])  
        return ta / (ta + tb)  
  
    def update_pair(self, winner, loser, lr=0.05):  
        # Online gradient update  
        p = self.prob(winner, loser)  
  
        # Gradient steps  
        self.theta[winner] += lr * (1 - p)  
        self.theta[loser]  += lr * (0 - (1 - p))  
  
        # Track stats for uncertainty  
        self.wins[winner] += 1  
        self.loss[loser]  += 1  
  
    def ranking(self):  
        return sorted(self.items, key=lambda x: self.theta[x], reverse=True)  
  
    def uncertainty(self, item):  
        # Simple uncertainty proxy: fewer total comparisons = higher uncertainty  
        c = self.wins[item] + self.loss[item]  
        return 1.0 / np.sqrt(c + 1)  
  
    def most_uncertain_items(self, top_k=5):  
        return sorted(self.items, key=self.uncertainty, reverse=True)[:top_k]  
  
  
# ---------------------------------------------------  
# Example usage  
# ---------------------------------------------------  
  
items = ["A", "B", "C", "D"]  
  
# ML model outputs initial score 0–1  
ml_scores = {  
    "A": 0.85,  
    "B": 0.60,  
    "C": 0.30,  
    "D": 0.10,  
}  
  
bt = BradleyTerry(items, ml_scores)  

print("Starting Ranking:", bt.ranking())  


# Stream in pairwise votes  
stream_votes = [  
    ("A", "B"),  # A > B  
    ("C", "B"),  # C > B
    ("A", "C"),  # A > C  
    ("D", "C"),  # D > C  
]  
  
for w, l in stream_votes:  
    bt.update_pair(w, l)  
  
# Current ranking  
print("Ranking:", bt.ranking())  
  
# Items with highest uncertainty (ask annotators)  
print("Most uncertain:", bt.most_uncertain_items(top_k=2)) 