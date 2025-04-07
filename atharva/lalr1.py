# Complete LALR(1) parser implementation in Python
from collections import defaultdict, deque
from copy import deepcopy

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

def first(grammar, symbol, memo=None):
    if memo is None:
        memo = {}
    if symbol in memo:
        return memo[symbol]
    if not symbol.isupper():
        return {symbol}
    result = set()
    for prod in grammar[symbol]:
        if not prod:
            result.add('ε')
        else:
            for char in prod:
                sub_first = first(grammar, char, memo)
                result.update(sub_first - {'ε'})
                if 'ε' not in sub_first:
                    break
            else:
                result.add('ε')
    memo[symbol] = result
    return result

def compute_follow(grammar, start_symbol):
    follow = defaultdict(set)
    follow[start_symbol].add("$")
    changed = True
    while changed:
        changed = False
        for lhs, prods in grammar.items():
            for prod in prods:
                for i, symbol in enumerate(prod):
                    if symbol.isupper():
                        trailer = set()
                        beta = prod[i + 1:]
                        if beta:
                            for b in beta:
                                if b.isupper():
                                    trailer.update(first(grammar, b))
                                    if 'ε' not in first(grammar, b):
                                        break
                                else:
                                    trailer.add(b)
                                    break
                            else:
                                trailer.add('ε')
                        else:
                            trailer.add('ε')
                        trailer.discard('ε')
                        old_len = len(follow[symbol])
                        follow[symbol].update(trailer)
                        if 'ε' in trailer or not beta:
                            follow[symbol].update(follow[lhs])
                        if len(follow[symbol]) > old_len:
                            changed = True
    return follow

# -------------------------------
# 3. Closure and GOTO with Lookahead
# -------------------------------

def closure_lr1(items, grammar):
    closure_set = set(items)
    queue = deque(items)

    while queue:
        lhs, rhs, lookahead = queue.popleft()
        dot_pos = rhs.find(".")
        if dot_pos < len(rhs) - 1:
            B = rhs[dot_pos + 1]
            beta = rhs[dot_pos + 2:]
            lookaheads = set()
            if beta:
                first_beta = set()
                for b in beta:
                    first_beta |= first(grammar, b)
                    if 'ε' not in first(grammar, b):
                        break
                else:
                    first_beta.add(lookahead)
                if 'ε' in first_beta:
                    first_beta.remove('ε')
                lookaheads |= first_beta
            else:
                lookaheads.add(lookahead)
            if B.isupper():
                for prod in grammar[B]:
                    for la in lookaheads:
                        item = (B, "." + prod, la)
                        if item not in closure_set:
                            closure_set.add(item)
                            queue.append(item)
    return frozenset(closure_set)

def goto_lr1(item_set, symbol, grammar):
    moved_items = []
    for lhs, rhs, la in item_set:
        dot_pos = rhs.find(".")
        if dot_pos < len(rhs) - 1 and rhs[dot_pos + 1] == symbol:
            new_rhs = rhs[:dot_pos] + symbol + "." + rhs[dot_pos + 2:]
            moved_items.append((lhs, new_rhs, la))
    return closure_lr1(moved_items, grammar) if moved_items else None

# -------------------------------
# 4. Build LALR(1) Canonical Collection
# -------------------------------

def build_lalr1_states(grammar, start_symbol):
    initial = closure_lr1([(start_symbol, "." + grammar[start_symbol][0], "$")], grammar)
    C = [initial]
    transitions = dict()
    state_ids = {initial: 0}
    queue = deque([initial])

    symbols = set()
    for rhs_list in grammar.values():
        for prod in rhs_list:
            symbols.update(prod)
    symbols.update(grammar.keys())

    while queue:
        current = queue.popleft()
        current_id = state_ids[current]
        for symbol in symbols:
            next_state = goto_lr1(current, symbol, grammar)
            if next_state and next_state not in state_ids:
                state_ids[next_state] = len(C)
                C.append(next_state)
                queue.append(next_state)
            if next_state:
                transitions[(current_id, symbol)] = state_ids[next_state]

    # Merge LR(1) states with same LR(0) core
    core_map = defaultdict(list)
    for state in C:
        core = frozenset((lhs, rhs) for lhs, rhs, _ in state)
        core_map[core].append(state)

    merged_states = []
    merged_map = dict()
    for states in core_map.values():
        merged = defaultdict(set)
        for state in states:
            for lhs, rhs, la in state:
                merged[(lhs, rhs)].add(la)
        items = frozenset((lhs, rhs, la) for (lhs, rhs), lookaheads in merged.items() for la in lookaheads)
        merged_states.append(items)

    state_id_map = {frozenset((lhs, rhs) for lhs, rhs, _ in state): i for i, state in enumerate(merged_states)}

    new_transitions = {}
    for (from_state, symbol), to_state in transitions.items():
        from_core = frozenset((lhs, rhs) for lhs, rhs, _ in C[from_state])
        to_core = frozenset((lhs, rhs) for lhs, rhs, _ in C[to_state])
        new_transitions[(state_id_map[from_core], symbol)] = state_id_map[to_core]

    return merged_states, new_transitions

# -------------------------------
# 5. Build LALR(1) Parsing Table
# -------------------------------

def build_lalr_parsing_table(states, transitions, grammar, augmented_start):
    ACTION = defaultdict(dict)
    GOTO = defaultdict(dict)
    productions = []
    prod_map = dict()

    for lhs in grammar:
        for rhs in grammar[lhs]:
            productions.append((lhs, rhs))
            prod_map[(lhs, rhs)] = len(productions) - 1

    for i, state in enumerate(states):
        for lhs, rhs, la in state:
            dot_pos = rhs.find(".")
            # Shift
            if dot_pos < len(rhs) - 1:
                a = rhs[dot_pos + 1]
                if (i, a) in transitions and not a.isupper():
                    ACTION[i][a] = ("shift", transitions[(i, a)])
            # Reduce or Accept
            elif dot_pos == len(rhs) - 1:
                if lhs == augmented_start:
                    ACTION[i]["$"] = ("accept",)
                else:
                    prod_num = prod_map[(lhs, rhs.replace(".", ""))]
                    ACTION[i][la] = ("reduce", prod_num)
        for symbol in grammar.keys():
            if (i, symbol) in transitions:
                GOTO[i][symbol] = transitions[(i, symbol)]

    return ACTION, GOTO, productions

# -------------------------------
# 6. Simulate Shift/Reduce Parsing
# -------------------------------

def simulate_parsing(input_string, ACTION, GOTO, productions):
    input_tokens = input_string.strip().split() + ["$"]
    stack = [0]
    steps = []

    idx = 0
    step = 1

    while True:
        current_state = stack[-1]
        current_token = input_tokens[idx]

        action = ACTION.get(current_state, {}).get(current_token)

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
            rhs_len = len(rhs) * 2
            if rhs:
                stack = stack[:-rhs_len]
            top_state = stack[-1]
            stack.append(lhs)
            stack.append(GOTO[top_state][lhs])

        elif action[0] == "accept":
            print("\n✅ String accepted by the grammar!\n")
            break

        step += 1

    print("\n=== PARSING STEPS ===")
    print(f"{'Step':<5} | {'Stack':<30} | {'Input':<15} | {'Action'}")
    print("-" * 70)
    for s in steps:
        print(f"{s[0]:<5} | {s[1]:<30} | {s[2]:<15} | {s[3]}")

# -------------------------------
# 7. Run Everything
# -------------------------------

states, transitions = build_lalr1_states(grammar, augmented_start)
follow = compute_follow(grammar, start_symbol)
ACTION, GOTO, productions = build_lalr_parsing_table(states, transitions, grammar, augmented_start)

# Print item sets
for i, state in enumerate(states):
    print(f"\nItem Set I{i}:")
    for lhs, rhs, la in sorted(state):
        print(f"  {lhs} -> {rhs}, {la}")

# Print parsing tables
print("\n=== ACTION TABLE ===")
for state in sorted(ACTION):
    for symbol in sorted(ACTION[state]):
        print(f"ACTION[{state}, '{symbol}'] = {ACTION[state][symbol]}")

print("\n=== GOTO TABLE ===")
for state in sorted(GOTO):
    for symbol in sorted(GOTO[state]):
        print(f"GOTO[{state}, '{symbol}'] = {GOTO[state][symbol]}")

print("\n=== PRODUCTIONS ===")
for i, (lhs, rhs) in enumerate(productions):
    print(f"{i}: {lhs} → {rhs}")

# Try parsing
test_string = "c d d"
simulate_parsing(test_string, ACTION, GOTO, productions)
