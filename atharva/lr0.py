from collections import defaultdict, deque

# -------------------------------
# 1. Input Grammar & Augmentation
# -------------------------------

raw_grammar = {
    "S": ["CC"],
    "C": ["cC", "d"]
}

start_symbol = "S"
augmented_start = start_symbol + "'"
grammar = {augmented_start: [start_symbol]}
grammar.update(raw_grammar)

# -------------------------------
# 2. Utility Functions
# -------------------------------

def get_items(lhs, rhs_list):
    """Generate initial items with dot at start"""
    return [(lhs, "." + rhs) for rhs in rhs_list]

def closure(items, grammar):
    """Compute closure of a set of LR(0) items"""
    closure_set = set(items)
    queue = deque(items)

    while queue:
        lhs, rhs = queue.popleft()
        dot_pos = rhs.find(".")
        if dot_pos < len(rhs) - 1:
            next_symbol = rhs[dot_pos + 1]
            if next_symbol.isupper():
                for prod in grammar.get(next_symbol, []):
                    item = (next_symbol, "." + prod)
                    if item not in closure_set:
                        closure_set.add(item)
                        queue.append(item)
    return frozenset(closure_set)

def goto(item_set, symbol, grammar):
    """Compute GOTO from a set of items and a symbol"""
    moved_items = []
    for lhs, rhs in item_set:
        dot_pos = rhs.find(".")
        if dot_pos < len(rhs) - 1 and rhs[dot_pos + 1] == symbol:
            new_rhs = rhs[:dot_pos] + symbol + "." + rhs[dot_pos + 2:]
            moved_items.append((lhs, new_rhs))
    return closure(moved_items, grammar) if moved_items else None

def get_terminals(grammar):
    """Extract terminal symbols from the grammar"""
    symbols = set()
    for rhs_list in grammar.values():
        for prod in rhs_list:
            for symbol in prod:
                if not symbol.isupper():
                    symbols.add(symbol)
    symbols.add("$")  # End marker
    return symbols

# -------------------------------
# 3. Build Canonical LR(0) Collection
# -------------------------------

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

# -------------------------------
# 4. Build ACTION and GOTO Tables
# -------------------------------

def build_parsing_table(states, transitions, grammar, augmented_start):
    ACTION = defaultdict(dict)
    GOTO = defaultdict(dict)

    productions = []      # index → (lhs, rhs)
    prod_map = dict()     # (lhs, rhs) → index

    for lhs in grammar:
        for rhs in grammar[lhs]:
            productions.append((lhs, rhs))
            prod_map[(lhs, rhs)] = len(productions) - 1

    for i, state in enumerate(states):
        for lhs, rhs in state:
            dot_pos = rhs.find(".")

            # Case 1: Shift
            if dot_pos < len(rhs) - 1:
                a = rhs[dot_pos + 1]
                if (i, a) in transitions and not a.isupper():
                    ACTION[i][a] = ("shift", transitions[(i, a)])

            # Case 2: Reduce or Accept
            elif dot_pos == len(rhs) - 1:
                if lhs == augmented_start:
                    ACTION[i]["$"] = ("accept",)
                else:
                    prod_num = prod_map[(lhs, rhs.replace(".", ""))]
                    for terminal in get_terminals(grammar):
                        if terminal not in ACTION[i]:
                            ACTION[i][terminal] = ("reduce", prod_num)

        # GOTO table for non-terminals
        for symbol in grammar.keys():
            if (i, symbol) in transitions:
                GOTO[i][symbol] = transitions[(i, symbol)]

    return ACTION, GOTO, productions

# -------------------------------
# 5. Run Everything and Display
# -------------------------------

# Build item sets and parsing table
states, transitions = build_canonical_collection(grammar, augmented_start)
ACTION, GOTO, productions = build_parsing_table(states, transitions, grammar, augmented_start)

# Print item sets
for i, state in enumerate(states):
    print(f"\nItem Set I{i}:")
    for lhs, rhs in sorted(state):
        print(f"  {lhs} -> {rhs}")

# Print transitions
print("\n=== TRANSITIONS ===")
for (from_state, symbol), to_state in sorted(transitions.items()):
    print(f"  I{from_state} -- {symbol} --> I{to_state}")

# Print ACTION table
print("\n=== ACTION TABLE ===")
for state in sorted(ACTION):
    for symbol in sorted(ACTION[state]):
        print(f"ACTION[{state}, '{symbol}'] = {ACTION[state][symbol]}")

# Print GOTO table
print("\n=== GOTO TABLE ===")
for state in sorted(GOTO):
    for symbol in sorted(GOTO[state]):
        print(f"GOTO[{state}, '{symbol}'] = {GOTO[state][symbol]}")

# Print production rules
print("\n=== PRODUCTIONS ===")
for i, (lhs, rhs) in enumerate(productions):
    print(f"{i}: {lhs} → {rhs}")

def simulate_lr0_parsing(input_string, ACTION, GOTO, productions):
    input_tokens = input_string.strip().split() + ["$"]
    stack = [0]
    steps = []

    idx = 0  # pointer to input
    step = 1

    while True:
        current_state = stack[-1]
        current_token = input_tokens[idx]

        action = ACTION.get(current_state, {}).get(current_token)

        # Record current step
        stack_repr = ' '.join(str(s) for s in stack)
        input_repr = ' '.join(input_tokens[idx:])
        action_repr = str(action) if action else "ERROR"
        steps.append((step, stack_repr, input_repr, action_repr))

        if not action:
            print("\n🚫 Parsing Error! String rejected.\n")
            break

        if action[0] == "shift":
            stack.append(current_token)
            stack.append(action[1])
            idx += 1

        elif action[0] == "reduce":
            prod_index = action[1]
            lhs, rhs = productions[prod_index]
            rhs_len = len(rhs) * 2  # because stack is symbol+state pairs
            if rhs != "ε":
                stack = stack[:-rhs_len]

            top_state = stack[-1]
            stack.append(lhs)
            stack.append(GOTO[top_state][lhs])

        elif action[0] == "accept":
            print("\n✅ String accepted by the grammar!\n")
            break

        step += 1

    # Print table
    print("\n=== PARSING STEPS ===")
    print(f"{'Step':<5} | {'Stack':<30} | {'Input':<15} | {'Action'}")
    print("-" * 70)
    for s in steps:
        print(f"{s[0]:<5} | {s[1]:<30} | {s[2]:<15} | {s[3]}")

# 🔥 Try it with a string
test_string = "c d d"
simulate_lr0_parsing(test_string, ACTION, GOTO, productions)