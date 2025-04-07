from collections import defaultdict, deque
from lark import Lark, Transformer, Token
import json

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
        print(f"✅ Tree exported to {file_path}")
    return tree_json

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

        # Build GOTO table for non-terminals
        for symbol in grammar.keys():
            if (i, symbol) in transitions:
                GOTO[i][symbol] = transitions[(i, symbol)]

    return ACTION, GOTO, productions

# -------------------------------
# 5. Parse Tree Node Class & Print Function
# -------------------------------


def print_parse_tree(node, indent="", last=True):
    """Recursively print the parse tree with nice formatting."""
    marker = "└── " if last else "├── "
    print(indent + marker + node.symbol)
    indent += "    " if last else "│   "
    child_count = len(node.children)
    for i, child in enumerate(node.children):
        print_parse_tree(child, indent, i == child_count - 1)

# -------------------------------
# 6. Print Combined Parsing Table
# -------------------------------

# Build the canonical collection and parsing table.
states, transitions = build_canonical_collection(grammar, augmented_start)
ACTION, GOTO, productions = build_parsing_table(states, transitions, grammar, augmented_start)

print("\n=== COMBINED PARSING TABLE ===")

# Collect symbols: terminals then non-terminals
terminals = sorted(get_terminals(grammar))
non_terminals = sorted([nt for nt in grammar.keys() if nt != augmented_start])
columns = terminals + non_terminals

# Header formatting
header = ["State"] + columns
col_widths = [max(len(col), 12) for col in header]
header_line = '  '.join(f"{col:<{w}}" for col, w in zip(header, col_widths))
print(header_line)
print("-" * len(header_line))

# Print rows per state
for i in range(len(states)):
    row = [f"I{i}"]
    for sym in columns:
        cell = ""
        if sym in terminals:
            action = ACTION[i].get(sym)
            if action:
                if action[0] == "shift":
                    cell = f"s{action[1]}"  # Terminal: add "s" prefix for shift actions
                elif action[0] == "reduce":
                    lhs, rhs = productions[action[1]]
                    cell = f"r({lhs} -> {rhs})"
                elif action[0] == "accept":
                    cell = "acc"
        else:
            if sym in GOTO[i]:
                cell = str(GOTO[i][sym])
        row.append(cell)
    print('  '.join(f"{val:<{w}}" for val, w in zip(row, col_widths)))

# -------------------------------
# 7. Additional Displays (Optional)
# -------------------------------

# Print item sets
print("\n=== ITEM SETS ===")
for i, state in enumerate(states):
    print(f"\nItem Set I{i}:")
    for lhs, rhs in sorted(state):
        print(f"  {lhs} -> {rhs}")

# Print transitions
print("\n=== TRANSITIONS ===")
for (from_state, symbol), to_state in sorted(transitions.items()):
    print(f"  I{from_state} -- {symbol} --> I{to_state}")

# Print production rules
print("\n=== PRODUCTIONS ===")
for i, (lhs, rhs) in enumerate(productions):
    print(f"{i}: {lhs} → {rhs}")

# -------------------------------
# 8. Simulate LR(0) Parsing and Build Parse Tree
# -------------------------------

def simulate_lr0_parsing_with_tree(input_string, ACTION, GOTO, productions):
    input_tokens = input_string.strip().split() + ["$"]
    stack = [0]            # This is the state stack for LR parsing.
    tree_stack = []        # This holds TreeNode objects corresponding to grammar symbols.
    steps = []

    idx = 0  # pointer to input token
    step = 1

    while True:
        current_state = stack[-1]
        current_token = input_tokens[idx]
        action = ACTION.get(current_state, {}).get(current_token)

        # Record current step (for debugging)
        stack_repr = ' '.join(str(s) for s in stack)
        input_repr = ' '.join(input_tokens[idx:])
        action_repr = str(action) if action else "ERROR"
        steps.append((step, stack_repr, input_repr, action_repr))
        
        if not action:
            print("\n🚫 Parsing Error! String rejected.\n")
            return None

        if action[0] == "shift":
            # Shift the token: push it on the state stack and create a leaf node.
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
                    # Pop nodes from the tree_stack (maintaining left-to-right order).
                    children.insert(0, tree_stack.pop())
                # Remove corresponding items from the state stack (2 items per symbol)
                stack = stack[:-num_symbols*2]
            # Create a new node for the non-terminal and push it on the tree stack.
            new_node = TreeNode(lhs, children)
            tree_stack.append(new_node)
            top_state = stack[-1]
            stack.append(lhs)
            stack.append(GOTO[top_state][lhs])

        elif action[0] == "accept":
            print("\n✅ String accepted by the grammar!\n")
            break

        step += 1

    # The final parse tree is the single node remaining on the tree_stack.
        # The final parse tree is the single node remaining on the tree_stack.
    parse_tree = tree_stack[0] if tree_stack else None

    print("\n=== PARSE TREE ===")
    if parse_tree:
        print_parse_tree(parse_tree)

        # Export for React-D3-Tree
        tree_json = export_tree_to_json(parse_tree)
        print("\n=== D3 JSON TREE ===")
        print(json.dumps(tree_json, indent=2))

    return parse_tree


# 🔥 Try it with a test string:
test_string = "c d d"
simulate_lr0_parsing_with_tree(test_string, ACTION, GOTO, productions)