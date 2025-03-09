from lark import Lark, Transformer
from nltk import Tree

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
        return Tree(children[0], [])
    
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

# Function to perform inorder traversal
def inorder_traversal(tree, result):
    if isinstance(tree, Tree):
        if len(tree) == 2:  # Operator nodes (binary operations)
            inorder_traversal(tree[0], result)  # Left subtree
            result.append(tree.label())  # Root (operator)
            inorder_traversal(tree[1], result)  # Right subtree
        else:  # Leaf nodes (numbers)
            result.append(tree.label())

# Example usage
expr = "6 + 9 - 9 + (51*9)/8"
parse_tree = parse_expression(expr)

if parse_tree:
    print("Parse Tree:")
    parse_tree.pretty_print()

    # Store inorder traversal
    inorder_result = []
    inorder_traversal(parse_tree, inorder_result)

    print("Inorder Traversal:", inorder_result)
