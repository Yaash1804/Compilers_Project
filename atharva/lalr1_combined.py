from collections import defaultdict, deque

# ----------- INPUT GRAMMAR -----------
raw_grammar = {
    "S": ["CC"],
    "C": ["cC", "d"]
}
start_symbol = "S"
aug_start = start_symbol + "'"
grammar = {aug_start: [start_symbol], **raw_grammar}

# ----------- FIRST SETS -----------
def compute_first(grammar):
    first = defaultdict(set)
    changed = True
    for symbol in grammar:
        first[symbol]
    while changed:
        changed = False
        for lhs, prods in grammar.items():
            for prod in prods:
                for sym in prod:
                    before = len(first[lhs])
                    if sym.isupper():
                        first[lhs].update(first[sym] - {'ε'})
                        if 'ε' not in first[sym]:
                            break
                    else:
                        first[lhs].add(sym)
                        break
                    if len(first[lhs]) != before:
                        changed = True
    return first

def first_of_string(grammar, string, first):
    result = set()
    for s in string:
        if s.isupper():
            result |= (first[s] - {'ε'})
            if 'ε' not in first[s]:
                return result
        else:
            result.add(s)
            return result
    result.add('ε')
    return result

# ----------- CLR(1) ITEM SET FUNCTIONS -----------
def closure(items, grammar, first):
    closure_set = set(items)
    queue = deque(items)

    while queue:
        lhs, rhs, la = queue.popleft()
        dot = rhs.find(".")
        if dot < len(rhs)-1:
            B = rhs[dot+1]
            rest = rhs[dot+2:]
            lookahead = first_of_string(grammar, rest + la, first)
            if B in grammar:
                for prod in grammar[B]:
                    for term in lookahead:
                        item = (B, "." + prod, term)
                        if item not in closure_set:
                            closure_set.add(item)
                            queue.append(item)
    return frozenset(closure_set)

def goto(items, symbol, grammar, first):
    moved = []
    for lhs, rhs, la in items:
        dot = rhs.find(".")
        if dot < len(rhs)-1 and rhs[dot+1] == symbol:
            new_rhs = rhs[:dot] + symbol + "." + rhs[dot+2:]
            moved.append((lhs, new_rhs, la))
    return closure(moved, grammar, first) if moved else None

# ----------- CLR(1) COLLECTION -----------
def build_clr1_collection(grammar, start):
    first = compute_first(grammar)
    I0 = closure([(start, "." + grammar[start][0], "$")], grammar, first)
    states = [I0]
    transitions = dict()
    state_ids = {I0: 0}
    queue = deque([I0])

    symbols = set(s for prods in grammar.values() for p in prods for s in p) | set(grammar.keys())

    while queue:
        curr = queue.popleft()
        i = state_ids[curr]
        for symbol in symbols:
            nxt = goto(curr, symbol, grammar, first)
            if nxt and nxt not in state_ids:
                state_ids[nxt] = len(states)
                states.append(nxt)
                queue.append(nxt)
            if nxt:
                transitions[(i, symbol)] = state_ids[nxt]
    return states, transitions, state_ids, first

# ----------- MERGE TO LALR(1) STATES -----------
def merge_states(states):
    core_map = defaultdict(list)
    for i, s in enumerate(states):
        core = frozenset((lhs, rhs) for lhs, rhs, _ in s)
        core_map[core].append(i)

    merged = {}
    named_sets = {}
    for core, indices in core_map.items():
        merged_items = set()
        for idx in indices:
            merged_items |= states[idx]
        name = "I" + ''.join(str(i) for i in sorted(indices))
        for idx in indices:
            merged[idx] = name
        named_sets[name] = merged_items
    return merged, named_sets

# ----------- PARSING TABLES -----------
def build_parsing_table(transitions, merged_map, named_sets, grammar, aug_start):
    ACTION, GOTO = defaultdict(dict), defaultdict(dict)
    productions = [(lhs, rhs) for lhs in grammar for rhs in grammar[lhs]]
    prod_ids = {prod: i for i, prod in enumerate(productions)}

    for old, name in merged_map.items():
        items = named_sets[name]
        for lhs, rhs, la in items:
            dot = rhs.find(".")
            if dot < len(rhs)-1:
                a = rhs[dot+1]
                t = transitions.get((old, a))
                if t is not None and not a.isupper():
                    ACTION[name][a] = ("shift", merged_map[t])
            elif lhs == aug_start:
                ACTION[name]["$"] = ("accept",)
            else:
                prod_num = prod_ids[(lhs, rhs.replace(".", ""))]
                ACTION[name][la] = ("reduce", prod_num)

        for sym in grammar:
            t = transitions.get((old, sym))
            if t is not None:
                GOTO[name][sym] = merged_map[t]
    return ACTION, GOTO, productions

# ----------- PARSING SIMULATION -----------
def simulate_parsing(string, ACTION, GOTO, prods):
    tokens = string.split() + ["$"]
    stack = ["I0"]
    i, step = 0, 1

    print("\n=== PARSING STEPS ===")
    print(f"{'Step':<4} | {'Stack':<20} | {'Input':<15} | Action")
    print("-" * 60)

    while True:
        state = stack[-1]
        tok = tokens[i]
        action = ACTION.get(state, {}).get(tok)

        print(f"{step:<4} | {' '.join(stack):<20} | {' '.join(tokens[i:]):<15} | {action}")

        if action is None:
            print("❌ Error: String rejected.")
            break
        if action[0] == "shift":
            stack += [tok, action[1]]
            i += 1
        elif action[0] == "reduce":
            lhs, rhs = prods[action[1]]
            if rhs:
                stack = stack[:-2*len(rhs)]
            state = stack[-1]
            stack += [lhs, GOTO[state][lhs]]
        elif action[0] == "accept":
            print("✅ Accepted!")
            break
        step += 1

# ----------- RUN EVERYTHING -----------
states, transitions, ids, first = build_clr1_collection(grammar, aug_start)
merged_map, named_sets = merge_states(states)
ACTION, GOTO, productions = build_parsing_table(transitions, merged_map, named_sets, grammar, aug_start)

print("\n=== CLR(1) ITEM SETS ===")
for idx, state in enumerate(states):
    print(f"\nI{idx}:")
    for lhs, rhs, la in sorted(state):
        print(f"  {lhs} -> {rhs}, {la}")

print("\n=== MERGED LALR(1) ITEM SETS ===")
for name in sorted(named_sets):
    print(f"\n{name}:")
    for lhs, rhs, la in sorted(named_sets[name]):
        print(f"  {lhs} -> {rhs}, {la}")

print("\n=== ACTION TABLE ===")
for state in sorted(ACTION):
    for sym in sorted(ACTION[state]):
        print(f"ACTION[{state}, '{sym}'] = {ACTION[state][sym]}")

print("\n=== GOTO TABLE ===")
for state in sorted(GOTO):
    for sym in sorted(GOTO[state]):
        print(f"GOTO[{state}, '{sym}'] = {GOTO[state][sym]}")

print("\n=== PRODUCTIONS ===")
for i, (lhs, rhs) in enumerate(productions):
    print(f"{i}: {lhs} -> {rhs}")

simulate_parsing("c d d", ACTION, GOTO, productions)