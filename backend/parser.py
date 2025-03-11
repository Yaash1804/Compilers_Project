from lark import Lark, Transformer, Token
import json

# Define the grammar
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

# Transformer to convert parse tree into JSON for react-d3-tree
class JsonTreeTransformer(Transformer):
    def add(self, children):
        # print("add children:", children)
        subtrees = [c for c in children if not isinstance(c, Token)]
        return {'name': '+', 'children': subtrees}
    
    def sub(self, children):
        # print("sub children:", children)
        subtrees = [c for c in children if not isinstance(c, Token)]
        return {'name': '-', 'children': subtrees}
    
    def mul(self, children):
        # print("mul children:", children)
        subtrees = [c for c in children if not isinstance(c, Token)]
        return {'name': '*', 'children': subtrees}
    
    def div(self, children):
        # print("div children:", children)
        subtrees = [c for c in children if not isinstance(c, Token)]
        return {'name': '/', 'children': subtrees}
    
    def number(self, children):
        # print("number children:", children)
        return {'name': children[0].value, 'children': []}
    
    def paren(self, children):
        # print("paren children:", children)
        return children[0]  # Just return the transformed expr
    
    # Handle pass-through rules
    def expr(self, children):
        # print("expr children:", children)
        return children[0]
    
    def term(self, children):
        # print("term children:", children)
        return children[0]
    
    def factor(self, children):
        # print("factor children:", children)
        return children[0]

# Parse the expression and output JSON
def parse_expression(expression):
    parser = Lark(grammar, parser='lalr', transformer=JsonTreeTransformer())
    try:
        parse_tree = parser.parse(expression)
        print("---------------------------------------------------------------------")
        print(json.dumps(parse_tree, indent=2))
        print("---------------------------------------------------------------------")
        return parse_tree
    except Exception as e:
        print("Syntax Error:", e)
        return None
