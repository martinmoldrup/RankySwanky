from openskill.models import PlackettLuce  

# set to 25/3 by default, which means that the initial uncertainty is such that the 99% confidence interval for the skill level would be approximately [0, 50]. You can adjust this value based on how much you want to rely on the ML prior versus user feedback. A smaller sigma value will make the model more confident in the initial ML scores and less influenced by user feedback, while a larger sigma value will make it more open to being influenced by user feedback and less reliant on the initial ML scores.
sigma_default = 25/3  # Default uncertainty in OpenSkill ratings, can be adjusted based on your needs
# A smaller sigma value, means that it will put more weight on the ML prior and be less influenced by user feedback, while a larger sigma value means it will be more influenced by user feedback and less by the ML prior. You can experiment with different sigma values to find the right balance for your use case.

max_mu_default = 25  # Default mean skill level in OpenSkill ratings, can be adjusted based on your needs
# The default mean (mu) in OpenSkill is typically set to 25, which represents an average skill level. You can adjust this value based on the expected skill levels in your specific application. For example, if you expect most items to be of higher skill, you might set a higher default mean, while if you expect most items to be of lower skill, you might set a lower default mean.

# 1. Create the model (defaults are fine)  
model = PlackettLuce()  
  
# 2. Example: ML scores for each item (0–1 scale)  
ml_prior = {  
    "A": 0.9,  
    "B": 0.3,  
    "C": 0.5,  
    "D": 0.7,  
}  
  
# 3. Convert ML scores into OpenSkill priors  
# mu ≈ 25 * score   (scale mu to match OpenSkill's default mean, score is between 0 and 1)
items = {  
    name: model.rating(mu=max_mu_default * ml_prior[name], sigma=sigma_default, name=name)  
    for name in ml_prior  
}  
  
# 4. Helper function for pairwise update (winner beats loser)  
def update(winner, loser):  
    w = [items[winner]]  
    l = [items[loser]]  
    [w_new, l_new] = model.rate([w, l])  
    items[winner] = w_new[0]  
    items[loser] = l_new[0]  

def most_uncertain_item(items):  
    # items = {"A": rating, "B": rating, ...}  
    return max(items.items(), key=lambda x: x[1].sigma)  

# 5. Example user feedback / comparisons  
feedback = [  
    ("A", "B"),  # A > B  (as expected from ML)
    ("C", "B"),  # C > B  (as expected from ML)
    ("A", "C"),  # A > C  (as expected from ML)
    ("D", "A"),  # D > A  (unexpected, maybe user disagrees with ML on A)
    ("D", "C"),  # D > C  (unexpected, maybe user disagrees with ML on C)
]  
  
# apply feedback  
for w, l in feedback:  
    update(w, l)  
  
# 6. Print skill values  
print("Final scores:")  
for name, r in items.items():  
    print(name, "mu=", round(r.mu, 3), "sigma=", round(r.sigma, 3))  
  
# 7. Rank items by skill mean  
ranking = sorted(items.items(), key=lambda x: x[1].mu, reverse=True)  
print("\nRanking:")  
for name, r in ranking:  
    print(name, round(r.mu, 2))  

# 8. Identify most uncertain item to ask for feedback on next
uncertain_item = most_uncertain_item(items)
print("\nMost uncertain item to ask about next:", uncertain_item[0], "with sigma =", round(uncertain_item[1].sigma, 3))