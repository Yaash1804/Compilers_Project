from collections import defaultdict, OrderedDict

class LL1Parser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.non_terminals = set(grammar.keys())
        self.terminals = set()
        self.start_symbol = next(iter(grammar.keys()))
        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.parsing_table = defaultdict(dict)
        self.epsilon = 'ε'
        
        # Initialize terminals
        for nt, prods in grammar.items():
            for prod in prods:
                for symbol in prod:
                    if symbol not in self.non_terminals and symbol != self.epsilon:
                        self.terminals.add(symbol)
        self.terminals.add('$')

    def remove_left_recursion(self):
        new_grammar = OrderedDict()
        ordered_nts = list(self.grammar.keys())
        
        for i, nt in enumerate(ordered_nts):
            alpha = []
            beta = []
            # Separate productions into recursive and non-recursive
            for prod in self.grammar[nt]:
                if prod and prod[0] == nt:
                    alpha.append(prod[1:])
                else:
                    beta.append(prod)
            
            if alpha:  # Has left recursion
                new_nt = nt + "'"
                new_grammar[nt] = [prod + [new_nt] for prod in beta]
                new_grammar[new_nt] = [prod + [new_nt] for prod in alpha] + [[self.epsilon]]
            else:
                new_grammar[nt] = self.grammar[nt]
        
        self.grammar = new_grammar
        self.non_terminals = set(new_grammar.keys())

    def compute_first(self):
        for nt in self.grammar:
            self._first(nt)

    def _first(self, symbol):
        if symbol in self.terminals:
            return {symbol}
        
        if symbol in self.first and self.first[symbol]:
            return self.first[symbol]
        
        for production in self.grammar[symbol]:
            if production[0] == self.epsilon:
                self.first[symbol].add(self.epsilon)
            else:
                for s in production:
                    s_first = self._first(s) if s in self.non_terminals else {s}
                    self.first[symbol].update(s_first - {self.epsilon})
                    if self.epsilon not in s_first:
                        break
                else:
                    self.first[symbol].add(self.epsilon)
        return self.first[symbol]

    def compute_follow(self):
        self.follow[self.start_symbol].add('$')
        updated = True
        
        while updated:
            updated = False
            for nt in self.grammar:
                for prod in self.grammar[nt]:
                    for i, symbol in enumerate(prod):
                        if symbol in self.non_terminals:
                            next_symbols = prod[i+1:]
                            first_of_next = self._compute_sequence_first(next_symbols)
                            before_size = len(self.follow[symbol])
                            
                            self.follow[symbol].update(first_of_next - {self.epsilon})
                            if self.epsilon in first_of_next or not next_symbols:
                                self.follow[symbol].update(self.follow[nt])
                            
                            if len(self.follow[symbol]) > before_size:
                                updated = True

    def _compute_sequence_first(self, sequence):
        first_set = set()
        for s in sequence:
            if s == self.epsilon:  # Add this check
                first_set.add(self.epsilon)
                break
            if s in self.terminals:
                first_set.add(s)
                break
            s_first = self.first[s]
            first_set.update(s_first - {self.epsilon})
            if self.epsilon not in s_first:
                break
        else:
            first_set.add(self.epsilon)
        return first_set
    def build_parsing_table(self):
        for nt in self.grammar:
            for prod in self.grammar[nt]:
                first_alpha = self._compute_sequence_first(prod)
                for terminal in first_alpha - {self.epsilon}:
                    self.parsing_table[nt][terminal] = prod
                
                if self.epsilon in first_alpha:
                    for terminal in self.follow[nt]:
                        self.parsing_table[nt][terminal] = prod

    def print_grammar(self, title):
        print(f"\n{title}:")
        for nt, prods in self.grammar.items():
            print(f"{nt} -> {' | '.join([' '.join(p) for p in prods])}")

    def print_first_follow(self):
        print("\nFIRST Sets:")
        for nt in self.grammar:
            print(f"FIRST({nt}) = {{{', '.join(self.first[nt])}}}")
        
        print("\nFOLLOW Sets:")
        for nt in self.grammar:
            print(f"FOLLOW({nt}) = {{{', '.join(self.follow[nt])}}}")

    def print_parsing_table(self):
        print("\nParsing Table:")
        header = ["Non-Terminal"] + list(self.terminals)
        print("{:<15}".format(header[0]), end="")
        for term in header[1:]:
            print("{:<20}".format(term), end="")
        print()
        
        for nt in self.grammar:
            print("{:<15}".format(nt), end="")
            for term in self.terminals:
                prod = self.parsing_table.get(nt, {}).get(term, "")
                print("{:<20}".format(f"{nt}->{' '.join(prod)}" if prod else ""), end="")
            print()

    def parse(self, input_string):
        stack = ['$', self.start_symbol]
        input = list(input_string.split()) + ['$']
        print("\nParsing Steps:")
        step = 1
        
        while stack:
            print(f"\nStep {step}:")
            print(f"Stack: {' '.join(stack)}")
            print(f"Input: {' '.join(input)}")
            
            top = stack[-1]
            current_input = input[0]
            
            if top == current_input == '$':
                print("Accepted!")
                return True
            
            if top == current_input:
                stack.pop()
                input.pop(0)
                print(f"Matched {top}")
                step += 1
                continue
                
            if top in self.terminals:
                print(f"Error: Mismatch between stack ({top}) and input ({current_input})")
                return False
                
            production = self.parsing_table.get(top, {}).get(current_input, None)
            if not production:
                print(f"Error: No production found for {top} on input {current_input}")
                return False
                
            stack.pop()
            if production[0] != self.epsilon:
                stack.extend(reversed(production))
            print(f"Applied {top} -> {' '.join(production)}")
            step += 1
        
        return False

# Input processing
def get_grammar():
    grammar = defaultdict(list)
    print("Enter grammar rules (e.g., 'E -> E + T | T', empty line to finish):")
    while True:
        line = input().strip()
        if not line:
            break
        nt, prods = line.split('->')
        nt = nt.strip()
        for prod in prods.split('|'):
            grammar[nt].append([s.strip() for s in prod.split() if s.strip()])
    return grammar

# Example usage
if __name__ == "__main__":
    # Sample input grammar (uncomment to use)
    # grammar = {
    #     'E': [['E', '+', 'T'], ['T']],
    #     'T': [['T', '*', 'F'], ['F']],
    #     'F': [['(', 'E', ')'], ['id']]
    # }
    
    grammar = get_grammar()
    parser = LL1Parser(grammar)
    
    # Step 1: Remove left recursion
    parser.remove_left_recursion()
    parser.print_grammar("Grammar after removing left recursion")
    
    # Step 2: Compute FIRST and FOLLOW
    parser.compute_first()
    parser.compute_follow()
    parser.print_first_follow()
    
    # Step 3: Build parsing table
    parser.build_parsing_table()
    parser.print_parsing_table()
    
    # Step 4: Parse input string
    input_str = input("\nEnter input string to parse: ")
    parser.parse(input_str)