"""A transitive reasoning system for binary relations."""
from typing import Dict, Set, Tuple, List

class TransitiveReasoner:
    """Performs transitive reasoning over binary relations."""

    def __init__(self) -> None:
        """Initializes the reasoner with an empty relation set."""
        self.relations: Dict[str, Set[str]] = {}

    def add_relation(self, a: str, b: str) -> None:
        """Adds a direct relation a -> b."""
        if a not in self.relations:
            self.relations[a] = set()
        self.relations[a].add(b)

    def compute_transitive_closure(self) -> Dict[str, Set[str]]:
        """Computes the transitive closure of the relations."""
        closure: Dict[str, Set[str]] = {k: set(v) for k, v in self.relations.items()}
        changed: bool = True
        while changed:
            changed = False
            for a in list(closure.keys()):
                to_add: Set[str] = set()
                for b in closure[a]:
                    to_add |= closure.get(b, set())
                if not to_add.issubset(closure[a]):
                    closure[a] |= to_add
                    changed = True
        return closure

    def query(self, a: str, b: str) -> bool:
        """Checks if a is transitively related to b."""
        closure = self.compute_transitive_closure()
        return b in closure.get(a, set())

    def all_relations(self) -> List[Tuple[str, str]]:
        """Returns all direct relations as a list of tuples."""
        return [(a, b) for a, bs in self.relations.items() for b in bs]
    
    def calculate_information_gain(self, a: str, b: str) -> int:
        """Calculates the information gain of adding a relation a -> b."""
        closure = self.compute_transitive_closure()
        original_count = sum(len(v) for v in closure.values())
        self.add_relation(a, b)
        new_closure = self.compute_transitive_closure()
        new_count = sum(len(v) for v in new_closure.values())
        self.relations[a].remove(b)
        return new_count - original_count

    def calculate_new_reasoned_pairs(self) -> List[Tuple[str, str]]:
        """Calculate new reasoned pairs that can be derived from existing relations and added as new relations."""
        closure: Dict[str, Set[str]] = self.compute_transitive_closure()
        new_pairs: List[Tuple[str, str]] = []
        for a, bs in closure.items():
            for b in bs:
                if a not in self.relations or b not in self.relations[a]:
                    new_pairs.append((a, b))
        return new_pairs
        

if __name__ == "__main__":
    # Test
    reasoner = TransitiveReasoner()
    reasoner.add_relation("A", "B")
    reasoner.add_relation("C", "D")


    print("Transitive Closure:", reasoner.compute_transitive_closure())
    print("Is A related to D?", reasoner.query("A", "D"))
    print("All Relations:", reasoner.all_relations())
    print("Information Gain of adding A -> D:", reasoner.calculate_information_gain("A", "D"))

    print("New Reasoned Pairs:", reasoner.calculate_new_reasoned_pairs())

    # Get an example where the information gain is more than 1
    print()
    reasoner = TransitiveReasoner()
    reasoner.add_relation("B", "C")
    reasoner.add_relation("D", "E")
    print("New Reasoned Pairs:", reasoner.calculate_new_reasoned_pairs())
    print("Information Gain of adding B -> D:", reasoner.calculate_information_gain("B", "D"))
    reasoner.add_relation("B", "D")
    print("New Reasoned Pairs after adding B -> D:", reasoner.calculate_new_reasoned_pairs())