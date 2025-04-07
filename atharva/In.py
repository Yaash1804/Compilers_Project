from collections import defaultdict, deque

# Define and augment the grammar
raw_grammar = {
    "S": ["CC"],
    "C": ["cC", "d"]
}
start_symbol = "S"
augmented_start = start_symbol + "'"
grammar = {augmented_start: [start_symbol]}
grammar.update(raw_grammar)

# Item as (lhs, rhs with dot), e.g., ("S", ".CC")
def get_items(lhs, rhs_list):
    return [(lhs, "." + rhs) for rhs in rhs_list]

def closure(items, grammar):
    closure_set = set(items)
    queue = deque(items)

    while queue:
        lhs, rhs = queue.popleft()
        dot_pos = rhs.find(".")

        if dot_pos < len(rhs) - 1:
            next_symbol = rhs[dot_pos + 1]
            if next_symbol.isupper():  # Non-terminal
                for prod in grammar.get(next_symbol, []):
                    item = (next_symbol, "." + prod)
                    if item not in closure_set:
                        closure_set.add(item)
                        queue.append(item)
    return frozenset(closure_set)

def goto(item_set, symbol, grammar):
    moved_items = []
    for lhs, rhs in item_set:
        dot_pos = rhs.find(".")
        if dot_pos < len(rhs) - 1 and rhs[dot_pos + 1] == symbol:
            new_rhs = rhs[:dot_pos] + symbol + "." + rhs[dot_pos + 2:]
            moved_items.append((lhs, new_rhs))
    return closure(moved_items, grammar) if moved_items else None

# Build canonical collection of item sets
def build_canonical_collection(grammar, start_symbol):
    start_items = get_items(start_symbol, grammar[start_symbol])
    I0 = closure(start_items, grammar)
    states = [I0]
    transitions = dict()
    state_ids = {I0: 0}
    queue = deque([I0])

    symbols = set()
    for rhs_list in grammar.values():
        for prod in rhs_list:
            symbols.update(prod)
    symbols.update(grammar.keys())  # Include non-terminals

    while queue:
        current = queue.popleft()
        current_id = state_ids[current]
        for symbol in symbols:
            next_state = goto(current, symbol, grammar)
            if next_state and next_state not in state_ids:
                state_ids[next_state] = len(states)
                states.append(next_state)
                queue.append(next_state)
            if next_state:
                transitions[(current_id, symbol)] = state_ids[next_state]

    return states, transitions

# Run and display item sets
states, transitions = build_canonical_collection(grammar, augmented_start)

# Display results
for i, state in enumerate(states):
    print(f"\nItem Set I{i}:")
    for lhs, rhs in sorted(state):
        print(f"  {lhs} -> {rhs}")

print("\nTransitions:")
for (from_state, symbol), to_state in transitions.items():
    print(f"  I{from_state} -- {symbol} --> I{to_state}")