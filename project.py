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

# Parse the input expression
def parse_expression(expression):
    parser = Lark(grammar, parser='lalr', transformer=TreeTransformer())
    try:
        parse_tree = parser.parse(expression)
        parse_tree.pretty_print()  # Print tree in terminal
        parse_tree.draw()  # Draw tree using NLTK GUI
    except Exception as e:
        print("Syntax Error:", e)

# Example usage
expr = "6 + 9 - 9 + (51*9)/8"
parse_expression(expr)