from collections import defaultdict, deque

# Step 1: Define and augment the grammar
raw_grammar = {
    "S": ["CC"],
    "C": ["cC", "d"]
}

# Augment the grammar
start_symbol = "S"
augmented_start = start_symbol + "'"
grammar = {augmented_start: [start_symbol]}
grammar.update(raw_grammar)

# Function to get items for a given production
def get_items(lhs, rhs_list):
    return [(lhs, "." + rhs) for rhs in rhs_list]

# Function to compute closure
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

    return closure_set

# Step 2: Build I0
I0_start_items = get_items(augmented_start, grammar[augmented_start])
I0 = closure(I0_start_items, grammar)

# Print I0 nicely
print("Item Set I0:")
for lhs, rhs in I0:
    print(f"{lhs} -> {rhs}")