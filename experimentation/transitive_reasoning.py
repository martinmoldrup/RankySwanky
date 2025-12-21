"""A transitive reasoning system for binary relations with edge metadata."""
from typing import Dict, Set, Tuple, List, Any, Optional
from pydantic import BaseModel, Field

class Relation(BaseModel):
    """Represents a binary relation with metadata."""
    source: str = ""
    target: str = ""
    properties: Dict[str, Any] = Field(default_factory=dict)

class TransitiveReasoner:
    """Performs transitive reasoning over binary relations with edge metadata."""

    def __init__(self) -> None:
        """Initializes the reasoner with an empty relation set."""
        self.relations: List[Relation] = []

    def add_relation(self, a: str, b: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Adds a direct relation a -> b with optional properties."""
        if properties is None:
            properties = {}
        # Remove existing relation if present
        self.relations = [
            rel for rel in self.relations
            if not (rel.source == a and rel.target == b)
        ]
        self.relations.append(Relation(source=a, target=b, properties=properties))

    def get_properties(self, a: str, b: str) -> Optional[Dict[str, Any]]:
        """Returns the properties for the edge a -> b, or None if not present."""
        for rel in self.relations:
            if rel.source == a and rel.target == b:
                return rel.properties
        return None

    def _relation_dict(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Returns the internal relation dict for fast lookup."""
        rel_dict: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for rel in self.relations:
            if rel.source not in rel_dict:
                rel_dict[rel.source] = {}
            rel_dict[rel.source][rel.target] = rel.properties
        return rel_dict

    def compute_transitive_closure(self) -> Dict[str, Set[str]]:
        """Computes the transitive closure of the relations (ignoring properties)."""
        rel_dict = self._relation_dict()
        closure: Dict[str, Set[str]] = {k: set(v.keys()) for k, v in rel_dict.items()}
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

    def relation_direction(self, a: str, b: str) -> int:
        """Returns 1 if a->b, -1 if b->a, 0 if no direct relation."""
        for rel in self.relations:
            if rel.source == a and rel.target == b:
                return 1
            if rel.source == b and rel.target == a:
                return -1
        return 0

    def all_relations(self) -> List[Relation]:
        """Returns all direct relations as a list of Relation objects."""
        return self.relations.copy()

    def calculate_information_gain(self, a: str, b: str) -> int:
        """Calculates the information gain of adding a relation a -> b."""
        closure = self.compute_transitive_closure()
        original_count: int = sum(len(v) for v in closure.values())
        self.add_relation(a, b, {})
        new_closure = self.compute_transitive_closure()
        new_count: int = sum(len(v) for v in new_closure.values())
        # Remove the relation we just added
        self.relations = [
            rel for rel in self.relations
            if not (rel.source == a and rel.target == b)
        ]
        return new_count - original_count

    def calculate_new_reasoned_pairs(self) -> List[Tuple[str, str]]:
        """Calculate new reasoned pairs that can be derived from existing relations and added as new relations."""
        rel_dict = self._relation_dict()
        closure: Dict[str, Set[str]] = self.compute_transitive_closure()
        new_pairs: List[Tuple[str, str]] = []
        for a, bs in closure.items():
            for b in bs:
                if a not in rel_dict or b not in rel_dict[a]:
                    new_pairs.append((a, b))
        return new_pairs


if __name__ == "__main__":
    # Test
    reasoner = TransitiveReasoner()
    reasoner.add_relation("A", "B", {"weight": 1})
    reasoner.add_relation("C", "D", {"label": "friend"})
    reasoner.add_relation("B", "C", {"type": "colleague"})

    print("Transitive Closure:", reasoner.compute_transitive_closure())
    print("Is A related to D?", reasoner.query("A", "D"))
    print("All Relations:", reasoner.all_relations())
    print("Properties of A->B:", reasoner.get_properties("A", "B"))
    print("Information Gain of adding A -> D:", reasoner.calculate_information_gain("A", "D"))

    reasoned_pairs = reasoner.calculate_new_reasoned_pairs()
    print("New Reasoned Pairs:", reasoned_pairs)
    for a, b in reasoned_pairs:
        reasoner.add_relation(a, b, {"type": "derived"})
    print("All Relations after adding new reasoned pairs:", reasoner.all_relations())

    # Get an example where the information gain is more than 1
    print()
    reasoner = TransitiveReasoner()
    reasoner.add_relation("B", "C", {"type": "knows"})
    reasoner.add_relation("D", "E", {"type": "knows"})
    print("New Reasoned Pairs:", reasoner.calculate_new_reasoned_pairs())
    print("Information Gain of adding B -> D:", reasoner.calculate_information_gain("B", "D"))
    reasoner.add_relation("B", "D", {"type": "knows"})
    print("New Reasoned Pairs after adding B -> D:", reasoner.calculate_new_reasoned_pairs())