from lark import Lark, Transformer
from nltk import Tree
from collections import deque  # For level-order traversal

# Define a simple grammar for arithmetic expressions
grammar = """
    ?start: expr
    ?expr: expr "+" term   -> add
         | expr "-" term   -> sub
         | term
    ?term: term "*" factor -> mul
         | term "/" factor -> div
         | factor
    ?factor: NUMBER        -> number
           | "(" expr ")"  -> paren
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

# Transformer to convert parse tree into NLTK Tree
class TreeTransformer(Transformer):
    def add(self, children):
        return Tree('+', children)
    
    def sub(self, children):
        return Tree('-', children)
    
    def mul(self, children):
        return Tree('*', children)
    
    def div(self, children):
        return Tree('/', children)
    
    def number(self, children):
        return Tree(str(children[0]), [])  # Convert token to string
    
    def paren(self, children):
        return children[0]

# Parse the input expression and return the parse tree
def parse_expression(expression):
    parser = Lark(grammar, parser='lalr', transformer=TreeTransformer())
    try:
        parse_tree = parser.parse(expression)
        return parse_tree  # Return the parse tree
    except Exception as e:
        print("Syntax Error:", e)
        return None

# Function to perform preorder traversal
def preorder_traversal(tree, result):
    if isinstance(tree, Tree):
        result.append(tree.label())  # Root (operator or number)
        for child in tree:  # Recursively visit children
            preorder_traversal(child, result)

# Function to perform level-order traversal
def level_order_traversal(tree, result):
    if not isinstance(tree, Tree):
        return
    
    queue = deque([tree])  # Initialize queue with root node
    
    while queue:
        node = queue.popleft()  # Dequeue the front element
        result.append(node.label())  # Store the label
        
        # Enqueue all children (left to right)
        for child in node:
            if isinstance(child, Tree):
                queue.append(child)

# Example usage
expr = "6 + 9 - 9 + (51*9)/8"
parse_tree = parse_expression(expr)

if parse_tree:
    print("Parse Tree:")
    parse_tree.pretty_print()

    # Store preorder traversal
    preorder_result = []
    preorder_traversal(parse_tree, preorder_result)
    print("Preorder Traversal:", preorder_result)

    # Store level-order traversal
    level_order_result = []
    level_order_traversal(parse_tree, level_order_result)
    print("Level-Order Traversal:", level_order_result)
