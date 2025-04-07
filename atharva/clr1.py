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

def compute_first(grammar):
    first = defaultdict(set)

    def _first(symbol):
        if not symbol.isupper():
            return {symbol}
        if symbol in first:
            return first[symbol]
        result = set()
        for prod in grammar[symbol]:
            for char in prod:
                f = _first(char)
                result.update(f - {'ε'})
                if 'ε' not in f:
                    break
            else:
                result.add('ε')
        first[symbol] = result
        return result

    for nonterminal in grammar:
        _first(nonterminal)
    return first

def closure_lr1(items, grammar, first):
    closure_set = set(items)
    queue = deque(items)

    while queue:
        lhs, rhs, la = queue.popleft()
        dot_pos = rhs.find(".")
        if dot_pos < len(rhs) - 1:
            B = rhs[dot_pos + 1]
            beta = rhs[dot_pos + 2:]
            lookaheads = set()

            if beta:
                f = set()
                for b in beta:
                    f.update(first[b] if b.isupper() else {b})
                    if 'ε' not in (first[b] if b.isupper() else {b}):
                        break
                else:
                    f.add(la)
                lookaheads.update(f)
            else:
                lookaheads.add(la)

            if B.isupper():
                for prod in grammar[B]:
                    for a in lookaheads:
                        item = (B, "." + prod, a)
                        if item not in closure_set:
                            closure_set.add(item)
                            queue.append(item)
    return frozenset(closure_set)

def goto_lr1(items, symbol, grammar, first):
    moved_items = []
    for lhs, rhs, la in items:
        dot_pos = rhs.find(".")
        if dot_pos < len(rhs) - 1 and rhs[dot_pos + 1] == symbol:
            new_rhs = rhs[:dot_pos] + symbol + "." + rhs[dot_pos + 2:]
            moved_items.append((lhs, new_rhs, la))
    return closure_lr1(moved_items, grammar, first) if moved_items else None

# -------------------------------
# 3. Build CLR(1) Canonical Collection
# -------------------------------

def build_clr1_canonical_collection(grammar, augmented_start):
    first = compute_first(grammar)
    start_items = [(augmented_start, "." + grammar[augmented_start][0], "$")]
    I0 = closure_lr1(start_items, grammar, first)

    states = [I0]
    transitions = dict()
    state_ids = {I0: 0}
    queue = deque([I0])

    symbols = set()
    for rhs_list in grammar.values():
        for prod in rhs_list:
            symbols.update(prod)
    symbols.update(grammar.keys())

    while queue:
        current = queue.popleft()
        current_id = state_ids[current]
        for symbol in symbols:
            next_state = goto_lr1(current, symbol, grammar, first)
            if next_state and next_state not in state_ids:
                state_ids[next_state] = len(states)
                states.append(next_state)
                queue.append(next_state)
            if next_state:
                transitions[(current_id, symbol)] = state_ids[next_state]

    return states, transitions, state_ids, first

# -------------------------------
# 4. Build CLR(1) Parsing Table
# -------------------------------

def build_clr1_parsing_table(states, transitions, state_ids, grammar, first):
    action = defaultdict(dict)
    goto_table = defaultdict(dict)
    productions = []
    prod_map = dict()

    for lhs in grammar:
        for rhs in grammar[lhs]:
            productions.append((lhs, rhs))
            prod_map[(lhs, rhs)] = len(productions) - 1

    for i, state in enumerate(states):
        for item in state:
            lhs, rhs, lookahead = item
            if rhs.endswith("."):
                if lhs == augmented_start:
                    action[i]["$"] = ("accept",)
                else:
                    prod = (lhs, rhs[:-1])
                    if prod in prod_map:
                        action[i][lookahead] = ("reduce", prod_map[prod])
            else:
                dot_pos = rhs.find(".")
                next_sym = rhs[dot_pos + 1]
                if (i, next_sym) in transitions:
                    next_state = transitions[(i, next_sym)]
                    if not next_sym.isupper():
                        action[i][next_sym] = ("shift", next_state)
                    else:
                        goto_table[i][next_sym] = next_state

    return action, goto_table, productions

# -------------------------------
# 5. Simulate CLR(1) Shift/Reduce Parsing
# -------------------------------

def simulate_clr_parsing(input_string, action, goto_table, productions):
    input_tokens = input_string.strip().split() + ["$"]
    stack = [0]
    steps = []

    idx = 0
    step = 1

    while True:
        current_state = stack[-1]
        current_token = input_tokens[idx]

        act = action.get(current_state, {}).get(current_token)
        stack_repr = ' '.join(str(s) for s in stack)
        input_repr = ' '.join(input_tokens[idx:])
        act_repr = str(act) if act else "ERROR"
        steps.append((step, stack_repr, input_repr, act_repr))

        if not act:
            print("\n🚫 Parsing Error! String rejected.\n")
            break

        if act[0] == "shift":
            stack.append(current_token)
            stack.append(act[1])
            idx += 1
        elif act[0] == "reduce":
            prod_index = act[1]
            lhs, rhs = productions[prod_index]
            if rhs != "":
                stack = stack[:-2 * len(rhs)]
            top_state = stack[-1]
            stack.append(lhs)
            stack.append(goto_table[top_state][lhs])
        elif act[0] == "accept":
            print("\n✅ String accepted by the grammar!\n")
            break
        step += 1

    print("\n=== PARSING STEPS ===")
    print(f"{'Step':<5} | {'Stack':<30} | {'Input':<15} | {'Action'}")
    print("-" * 70)
    for s in steps:
        print(f"{s[0]:<5} | {s[1]:<30} | {s[2]:<15} | {s[3]}")

# -------------------------------
# 6. Run It All (CLR(1) Parser)
# -------------------------------

states, transitions, state_ids, first = build_clr1_canonical_collection(grammar, augmented_start)
action, goto_table, productions = build_clr1_parsing_table(states, transitions, state_ids, grammar, first)

# Print item sets
for i, state in enumerate(states):
    print(f"\nItem Set I{i}:")
    for lhs, rhs, lookahead in sorted(state):
        print(f"  {lhs} -> {rhs} , {lookahead}")

# Print parsing tables
print("\n=== ACTION TABLE ===")
for state in sorted(action):
    for symbol in sorted(action[state]):
        print(f"ACTION[{state}, '{symbol}'] = {action[state][symbol]}")

print("\n=== GOTO TABLE ===")
for state in sorted(goto_table):
    for symbol in sorted(goto_table[state]):
        print(f"GOTO[{state}, '{symbol}'] = {goto_table[state][symbol]}")

print("\n=== PRODUCTIONS ===")
for i, (lhs, rhs) in enumerate(productions):
    print(f"{i}: {lhs} → {rhs}")

# Try it out
test_string = "c d d"
simulate_clr_parsing(test_string, action, goto_table, productions)