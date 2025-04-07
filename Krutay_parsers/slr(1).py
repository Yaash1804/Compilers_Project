from collections import defaultdict, deque
import json

# -------------------------------
# Tree Node Class for Parse Tree
# -------------------------------
class TreeNode:
    def __init__(self, symbol, children=None):
        self.symbol = symbol
        self.children = children if children is not None else []

    def __str__(self):
        return self.symbol

    def to_d3_json(self):
        return {
            "name": self.symbol,
            "children": [child.to_d3_json() for child in self.children] if self.children else []
        }

def export_tree_to_json(tree_node, file_path=None):
    if not tree_node:
        return None
    tree_json = tree_node.to_d3_json()
    if file_path:
        with open(file_path, 'w') as f:
            json.dump(tree_json, f, indent=2)
    return tree_json

def print_parse_tree(node, indent="", last=True):
    marker = "└── " if last else "├── "
    print(indent + marker + node.symbol)
    indent += "    " if last else "│   "
    child_count = len(node.children)
    for i, child in enumerate(node.children):
        print_parse_tree(child, indent, i == child_count - 1)

# -------------------------------
# Input Grammar & Augmentation
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
# Utility Functions
# -------------------------------
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
            if next_symbol.isupper():
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

def get_terminals(grammar):
    symbols = set()
    for rhs_list in grammar.values():
        for prod in rhs_list:
            for symbol in prod:
                if not symbol.isupper():
                    symbols.add(symbol)
    symbols.add("$")
    return symbols

# -------------------------------
# Canonical Collection
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
    symbols.update(grammar.keys())

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
# FIRST & FOLLOW Sets
# -------------------------------
def first(grammar, symbol):
    if not symbol.isupper():
        return {symbol}
    result = set()
    for prod in grammar[symbol]:
        if not prod:
            result.add('ε')
        else:
            for char in prod:
                result.update(first(grammar, char))
                if 'ε' not in first(grammar, char):
                    break
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
                                    if 'ε' not in trailer:
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
# SLR Parsing Table Construction
# -------------------------------
def build_slr_parsing_table(states, transitions, grammar, augmented_start, follow):
    ACTION = defaultdict(dict)
    GOTO = defaultdict(dict)
    productions = []
    prod_map = dict()

    for lhs in grammar:
        for rhs in grammar[lhs]:
            productions.append((lhs, rhs))
            prod_map[(lhs, rhs)] = len(productions) - 1

    for i, state in enumerate(states):
        for lhs, rhs in state:
            dot_pos = rhs.find(".")
            if dot_pos < len(rhs) - 1:
                a = rhs[dot_pos + 1]
                if (i, a) in transitions and not a.isupper():
                    ACTION[i][a] = ("shift", transitions[(i, a)])
            elif dot_pos == len(rhs) - 1:
                if lhs == augmented_start:
                    ACTION[i]["$"] = ("accept",)
                else:
                    prod_num = prod_map[(lhs, rhs.replace(".", ""))]
                    for terminal in follow[lhs]:
                        if terminal not in ACTION[i]:
                            ACTION[i][terminal] = ("reduce", prod_num)
        for symbol in grammar.keys():
            if (i, symbol) in transitions:
                GOTO[i][symbol] = transitions[(i, symbol)]

    return ACTION, GOTO, productions

# -------------------------------
# SLR Parsing with Tree Construction
# -------------------------------
def simulate_slr_parsing_with_tree(input_string, ACTION, GOTO, productions):
    input_tokens = input_string.strip().split() + ["$"]
    stack = [0]
    tree_stack = []
    idx = 0
    step = 1

    while True:
        current_state = stack[-1]
        current_token = input_tokens[idx]
        action = ACTION.get(current_state, {}).get(current_token)

        if not action:
            print("\n🚫 Parsing Error! String rejected.\n")
            return None

        if action[0] == "shift":
            stack.append(current_token)
            stack.append(action[1])
            tree_stack.append(TreeNode(current_token))
            idx += 1

        elif action[0] == "reduce":
            prod_index = action[1]
            lhs, rhs = productions[prod_index]
            num_symbols = len(rhs) if rhs != "ε" else 0
            children = []
            if rhs != "ε":
                for _ in range(num_symbols):
                    children.insert(0, tree_stack.pop())
                stack = stack[:-num_symbols * 2]
            new_node = TreeNode(lhs, children)
            tree_stack.append(new_node)
            top_state = stack[-1]
            stack.append(lhs)
            stack.append(GOTO[top_state][lhs])

        elif action[0] == "accept":
            print("\n✅ String accepted by the grammar!\n")
            break

        step += 1

    parse_tree = tree_stack[0] if tree_stack else None
    print("\n=== PARSE TREE ===")
    print_parse_tree(parse_tree)
    print("\n=== D3 JSON TREE ===")
    print(json.dumps(export_tree_to_json(parse_tree), indent=2))
    return parse_tree

# -------------------------------
# Run Everything
# -------------------------------
states, transitions = build_canonical_collection(grammar, augmented_start)
follow = compute_follow(grammar, start_symbol)
ACTION, GOTO, productions = build_slr_parsing_table(states, transitions, grammar, augmented_start, follow)

print("\n=== PARSING TABLE ===")
terminals = sorted(get_terminals(grammar))
non_terminals = sorted([nt for nt in grammar if nt != augmented_start])
header = ["State"] + terminals + non_terminals
print('\t'.join(header))
for i in range(len(states)):
    row = [f"{i}"]
    for sym in terminals:
        a = ACTION[i].get(sym)
        if not a:
            row.append("")
        elif a[0] == "shift":
            row.append(f"s{a[1]}")
        elif a[0] == "reduce":
            lhs, rhs = productions[a[1]]
            row.append(f"r({lhs}->{rhs})")
        elif a[0] == "accept":
            row.append("acc")
    for sym in non_terminals:
        row.append(str(GOTO[i].get(sym, "")))
    print('\t'.join(row))

print("\n=== TEST PARSING ===")
simulate_slr_parsing_with_tree("c d d", ACTION, GOTO, productions)
