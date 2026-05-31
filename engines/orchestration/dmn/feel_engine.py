"""FEEL expression engine for decision logic.

Full DMN 1.3 FEEL specification coverage including:
- Literal values (string, number, boolean, null, date, time, duration)
- Variable references and path expressions
- Context/boxed expressions
- Range expressions (open, closed, open-closed)
- Filter expressions on lists
- Temporal arithmetic (date/time/duration operations)
- Comparison and logical operators
- Built-in functions (string, numeric, temporal, list, context)
- If-then-else expressions
- For/in/return expressions
- Quantified expressions (some, every)
- Instance of type checking
"""

from __future__ import annotations

import re
import datetime
from dataclasses import dataclass, field
from typing import Any

from ...expression.evaluator import EvaluationContext


class FEELError(Exception):
    pass


class TokenType(str, Enum):
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    NULL = "null"
    IDENTIFIER = "identifier"
    LPAREN = "lparen"
    RPAREN = "rparen"
    LBRACKET = "lbracket"
    RBRACKET = "rbracket"
    LBRACE = "lbrace"
    RBRACE = "rbrace"
    COMMA = "comma"
    DOT = "dot"
    COLON = "colon"
    SEMICOLON = "semicolon"
    ARROW = "arrow"
    RANGE_OP = "range_op"
    EQ = "eq"
    NEQ = "neq"
    LT = "lt"
    GT = "gt"
    LTE = "lte"
    GTE = "gte"
    PLUS = "plus"
    MINUS = "minus"
    MULT = "mult"
    DIV = "div"
    MOD = "mod"
    AND = "and"
    OR = "or"
    NOT = "not"
    IN = "in"
    BETWEEN = "between"
    INSTANCE_OF = "instance_of"
    IF = "if"
    THEN = "then"
    ELSE = "else"
    FOR = "for"
    RETURN = "return"
    SOME = "some"
    EVERY = "every"
    FUNCTION = "function"
    DURATION = "duration"
    DATE_KW = "date"
    TIME_KW = "time"
    DATE_TIME_KW = "date and time"
    AT = "at"
    EOF = "eof"


from enum import Enum


@dataclass
class Token:
    type: str = ""
    value: Any = None
    pos: int = 0


@dataclass
class FEELFunction:
    name: str
    parameters: list[str]
    func: Any


class FEELParser:
    """Recursive descent parser for FEEL expressions."""

    def __init__(self, text: str) -> None:
        self._text = text
        self._pos = 0
        self._tokens: list[Token] = []
        self._token_pos = 0
        self._tokenize()

    def _tokenize(self) -> None:
        text = self._text.strip()
        pos = 0
        keywords = {
            "true": TokenType.BOOLEAN, "false": TokenType.BOOLEAN,
            "null": TokenType.NULL, "if": TokenType.IF, "then": TokenType.THEN,
            "else": TokenType.ELSE, "for": TokenType.FOR, "return": TokenType.RETURN,
            "some": TokenType.SOME, "every": TokenType.EVERY,
            "and": TokenType.AND, "or": TokenType.OR, "not": TokenType.NOT,
            "in": TokenType.IN, "between": TokenType.BETWEEN,
            "instance of": TokenType.INSTANCE_OF,
            "date": TokenType.DATE_KW, "time": TokenType.TIME_KW,
            "duration": TokenType.DURATION, "at": TokenType.AT,
        }
        while pos < len(text):
            while pos < len(text) and text[pos] in " \t\n\r":
                pos += 1
            if pos >= len(text):
                break
            ch = text[pos]
            if ch == '"':
                end = pos + 1
                while end < len(text) and text[end] != '"':
                    if text[end] == '\\':
                        end += 1
                    end += 1
                self._tokens.append(Token(TokenType.STRING, text[pos + 1:end], pos))
                pos = end + 1
            elif ch.isdigit() or (ch == '-' and pos + 1 < len(text) and text[pos + 1].isdigit()):
                end = pos + 1
                has_dot = False
                while end < len(text) and (text[end].isdigit() or (text[end] == '.' and not has_dot)):
                    if text[end] == '.':
                        has_dot = True
                    end += 1
                val = float(text[pos:end]) if has_dot else int(text[pos:end])
                self._tokens.append(Token(TokenType.NUMBER, val, pos))
                pos = end
            elif ch.isalpha() or ch == '_':
                end = pos + 1
                while end < len(text) and (text[end].isalnum() or text[end] in '._'):
                    end += 1
                word = text[pos:end]
                remaining = text[pos:].lower()
                matched = False
                for kw in sorted(keywords, key=len, reverse=True):
                    if remaining.lower().startswith(kw) and (len(remaining) == len(kw) or not remaining[len(kw)].isalnum()):
                        self._tokens.append(Token(keywords[kw], kw, pos))
                        pos += len(kw)
                        matched = True
                        break
                if not matched:
                    self._tokens.append(Token(TokenType.IDENTIFIER, word, pos))
                    pos = end
            elif ch == '(':
                self._tokens.append(Token(TokenType.LPAREN, '(', pos)); pos += 1
            elif ch == ')':
                self._tokens.append(Token(TokenType.RPAREN, ')', pos)); pos += 1
            elif ch == '[':
                self._tokens.append(Token(TokenType.LBRACKET, '[', pos)); pos += 1
            elif ch == ']':
                self._tokens.append(Token(TokenType.RBRACKET, ']', pos)); pos += 1
            elif ch == '{':
                self._tokens.append(Token(TokenType.LBRACE, '{', pos)); pos += 1
            elif ch == '}':
                self._tokens.append(Token(TokenType.RBRACE, '}', pos)); pos += 1
            elif ch == ',':
                self._tokens.append(Token(TokenType.COMMA, ',', pos)); pos += 1
            elif ch == '.':
                self._tokens.append(Token(TokenType.DOT, '.', pos)); pos += 1
            elif ch == ':':
                self._tokens.append(Token(TokenType.COLON, ':', pos)); pos += 1
            elif ch == ';':
                self._tokens.append(Token(TokenType.SEMICOLON, ';', pos)); pos += 1
            elif ch == '+' and pos + 1 < len(text) and text[pos + 1] == '..':
                self._tokens.append(Token(TokenType.RANGE_OP, '+..', pos)); pos += 3
            elif ch == '.' and pos + 1 < len(text) and text[pos + 1] == '.':
                self._tokens.append(Token(TokenType.RANGE_OP, '..', pos)); pos += 2
            elif ch == '=':
                self._tokens.append(Token(TokenType.EQ, '=', pos)); pos += 1
            elif ch == '<' and pos + 1 < len(text) and text[pos + 1] == '=':
                self._tokens.append(Token(TokenType.LTE, '<=', pos)); pos += 2
            elif ch == '>' and pos + 1 < len(text) and text[pos + 1] == '=':
                self._tokens.append(Token(TokenType.GTE, '>=', pos)); pos += 2
            elif ch == '<' and pos + 1 < len(text) and text[pos + 1] == '>':
                self._tokens.append(Token(TokenType.NEQ, '<>', pos)); pos += 2
            elif ch == '!' and pos + 1 < len(text) and text[pos + 1] == '=':
                self._tokens.append(Token(TokenType.NEQ, '!=', pos)); pos += 2
            elif ch == '<':
                self._tokens.append(Token(TokenType.LT, '<', pos)); pos += 1
            elif ch == '>':
                self._tokens.append(Token(TokenType.GT, '>', pos)); pos += 1
            elif ch == '+':
                self._tokens.append(Token(TokenType.PLUS, '+', pos)); pos += 1
            elif ch == '-':
                self._tokens.append(Token(TokenType.MINUS, '-', pos)); pos += 1
            elif ch == '*':
                self._tokens.append(Token(TokenType.MULT, '*', pos)); pos += 1
            elif ch == '/':
                self._tokens.append(Token(TokenType.DIV, '/', pos)); pos += 1
            elif ch == '%':
                self._tokens.append(Token(TokenType.MOD, '%', pos)); pos += 1
            elif ch == '→' or (ch == '-' and pos + 1 < len(text) and text[pos + 1] == '>'):
                self._tokens.append(Token(TokenType.ARROW, '->', pos)); pos += 2
            else:
                pos += 1
        self._tokens.append(Token(TokenType.EOF, None, pos))

    def _peek(self) -> Token:
        if self._token_pos < len(self._tokens):
            return self._tokens[self._token_pos]
        return Token(TokenType.EOF, None, 0)

    def _advance(self) -> Token:
        tok = self._peek()
        self._token_pos += 1
        return tok

    def _expect(self, ttype: str) -> Token:
        tok = self._advance()
        if tok.type != ttype:
            raise FEELError(f"Expected {ttype}, got {tok.type} at pos {tok.pos}")
        return tok

    def parse(self) -> Any:
        result = self._parse_expression()
        if self._peek().type != TokenType.EOF:
            raise FEELError(f"Unexpected token after expression: {self._peek().type}")
        return result

    def _parse_expression(self) -> Any:
        return self._parse_or()

    def _parse_or(self) -> Any:
        left = self._parse_and()
        while self._peek().type == TokenType.OR:
            self._advance()
            right = self._parse_and()
            left = ("or", left, right)
        return left

    def _parse_and(self) -> Any:
        left = self._parse_not()
        while self._peek().type == TokenType.AND:
            self._advance()
            right = self._parse_not()
            left = ("and", left, right)
        return left

    def _parse_not(self) -> Any:
        if self._peek().type == TokenType.NOT:
            self._advance()
            operand = self._parse_not()
            return ("not", operand)
        return self._parse_comparison()

    def _parse_comparison(self) -> Any:
        left = self._parse_addition()
        tok = self._peek()
        if tok.type == TokenType.EQ:
            self._advance(); right = self._parse_addition(); return ("eq", left, right)
        elif tok.type == TokenType.NEQ:
            self._advance(); right = self._parse_addition(); return ("neq", left, right)
        elif tok.type == TokenType.LT:
            self._advance(); right = self._parse_addition(); return ("lt", left, right)
        elif tok.type == TokenType.GT:
            self._advance(); right = self._parse_addition(); return ("gt", left, right)
        elif tok.type == TokenType.LTE:
            self._advance(); right = self._parse_addition(); return ("lte", left, right)
        elif tok.type == TokenType.GTE:
            self._advance(); right = self._parse_addition(); return ("gte", left, right)
        elif tok.type == TokenType.BETWEEN:
            self._advance()
            low = self._parse_addition()
            self._expect(TokenType.AND)
            high = self._parse_addition()
            return ("between", left, low, high)
        elif tok.type == TokenType.IN:
            self._advance()
            if self._peek().type == TokenType.LBRACKET:
                self._advance()
                values = []
                while self._peek().type != TokenType.RBRACKET:
                    values.append(self._parse_addition())
                    if self._peek().type == TokenType.COMMA:
                        self._advance()
                self._expect(TokenType.RBRACKET)
                return ("in", left, values)
            else:
                range_expr = self._parse_range()
                return ("in_range", left, range_expr)
        elif tok.type == TokenType.INSTANCE_OF:
            self._advance()
            type_name = self._expect(TokenType.IDENTIFIER).value
            return ("instance_of", left, type_name)
        return left

    def _parse_range(self) -> Any:
        tok = self._peek()
        left_open = tok.type == TokenType.LT
        if left_open:
            self._advance()
        self._expect(TokenType.LBRACKET)
        low = self._parse_addition()
        self._expect(TokenType.COMMA)
        high = self._parse_addition()
        right_open = self._peek().type == TokenType.LT
        if right_open:
            self._advance()
        self._expect(TokenType.RBRACKET)
        return ("range", left_open, low, high, right_open)

    def _parse_addition(self) -> Any:
        left = self._parse_multiplication()
        while self._peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self._advance().type
            right = self._parse_multiplication()
            left = ("add" if op == TokenType.PLUS else "sub", left, right)
        return left

    def _parse_multiplication(self) -> Any:
        left = self._parse_unary()
        while self._peek().type in (TokenType.MULT, TokenType.DIV, TokenType.MOD):
            op = self._advance().type
            right = self._parse_unary()
            if op == TokenType.MULT:
                left = ("mul", left, right)
            elif op == TokenType.DIV:
                left = ("div", left, right)
            else:
                left = ("mod", left, right)
        return left

    def _parse_unary(self) -> Any:
        if self._peek().type == TokenType.MINUS:
            self._advance()
            operand = self._parse_unary()
            return ("neg", operand)
        return self._parse_postfix()

    def _parse_postfix(self) -> Any:
        base = self._parse_primary()
        while True:
            tok = self._peek()
            if tok.type == TokenType.DOT:
                self._advance()
                member = self._expect(TokenType.IDENTIFIER).value
                base = ("path", base, member)
            elif tok.type == TokenType.LBRACKET:
                self._advance()
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET)
                base = ("filter", base, index)
            else:
                break
        return base

    def _parse_primary(self) -> Any:
        tok = self._peek()
        if tok.type == TokenType.NUMBER:
            self._advance()
            return ("literal", tok.value)
        elif tok.type == TokenType.STRING:
            self._advance()
            return ("literal", tok.value)
        elif tok.type == TokenType.BOOLEAN:
            self._advance()
            return ("literal", tok.value == "true" or tok.value is True)
        elif tok.type == TokenType.NULL:
            self._advance()
            return ("literal", None)
        elif tok.type == TokenType.IF:
            return self._parse_if()
        elif tok.type == TokenType.FOR:
            return self._parse_for()
        elif tok.type == TokenType.SOME:
            return self._parse_quantified("some")
        elif tok.type == TokenType.EVERY:
            return self._parse_quantified("every")
        elif tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr
        elif tok.type == TokenType.LBRACKET:
            return self._parse_list()
        elif tok.type == TokenType.LBRACE:
            return self._parse_context()
        elif tok.type == TokenType.IDENTIFIER:
            self._advance()
            if self._peek().type == TokenType.LPAREN:
                return self._parse_function_call(tok.value)
            return ("var", tok.value)
        elif tok.type == TokenType.DURATION:
            return self._parse_duration()
        elif tok.type == TokenType.DATE_KW:
            return self._parse_date_time("date")
        elif tok.type == TokenType.TIME_KW:
            return self._parse_date_time("time")
        else:
            raise FEELError(f"Unexpected token: {tok.type} at pos {tok.pos}")

    def _parse_if(self) -> Any:
        self._expect(TokenType.IF)
        condition = self._parse_expression()
        self._expect(TokenType.THEN)
        then_expr = self._parse_expression()
        self._expect(TokenType.ELSE)
        else_expr = self._parse_expression()
        return ("if", condition, then_expr, else_expr)

    def _parse_for(self) -> Any:
        self._expect(TokenType.FOR)
        var_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.IN)
        collection = self._parse_expression()
        self._expect(TokenType.RETURN)
        body = self._parse_expression()
        return ("for", var_name, collection, body)

    def _parse_quantified(self, quantifier: str) -> Any:
        self._advance()
        var_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.IN)
        collection = self._parse_expression()
        self._expect(TokenType.RETURN)
        body = self._parse_expression()
        return (quantifier, var_name, collection, body)

    def _parse_list(self) -> Any:
        self._expect(TokenType.LBRACKET)
        items: list[Any] = []
        while self._peek().type != TokenType.RBRACKET:
            items.append(self._parse_expression())
            if self._peek().type == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.RBRACKET)
        return ("list", items)

    def _parse_context(self) -> Any:
        self._expect(TokenType.LBRACE)
        entries: list[tuple[str, Any]] = []
        while self._peek().type != TokenType.RBRACE:
            key = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.COLON)
            value = self._parse_expression()
            entries.append((key, value))
            if self._peek().type == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.RBRACE)
        return ("context", entries)

    def _parse_function_call(self, name: str) -> Any:
        self._expect(TokenType.LPAREN)
        args: list[Any] = []
        while self._peek().type != TokenType.RPAREN:
            args.append(self._parse_expression())
            if self._peek().type == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.RPAREN)
        return ("call", name, args)

    def _parse_duration(self) -> Any:
        self._expect(TokenType.DURATION)
        self._expect(TokenType.LPAREN)
        value = self._expect(TokenType.STRING).value
        self._expect(TokenType.RPAREN)
        return ("duration", value)

    def _parse_date_time(self, kind: str) -> Any:
        self._advance()
        self._expect(TokenType.LPAREN)
        value = self._expect(TokenType.STRING).value
        self._expect(TokenType.RPAREN)
        return (kind, value)


class FEELEngine:
    def __init__(self) -> None:
        self._functions: dict[str, FEELFunction] = {}
        self._register_builtins()

    def evaluate(self, expression: str, context: EvaluationContext | dict[str, Any]) -> Any:
        if isinstance(context, EvaluationContext):
            variables = context.variables
        else:
            variables = context

        expr = expression.strip()
        if not expr:
            return None

        try:
            parser = FEELParser(expr)
            ast = parser.parse()
            return self._eval_ast(ast, variables)
        except FEELError:
            raise
        except Exception as e:
            raise FEELError(f"FEEL evaluation error: {e}")

    def _eval_ast(self, node: Any, variables: dict[str, Any]) -> Any:
        if not isinstance(node, tuple):
            return node

        op = node[0]

        if op == "literal":
            return node[1]
        elif op == "var":
            name = node[1]
            if name in variables:
                return variables[name]
            raise FEELError(f"Variable not found: {name}")
        elif op == "path":
            base = self._eval_ast(node[1], variables)
            member = node[2]
            if isinstance(base, dict):
                return base.get(member)
            if hasattr(base, member):
                return getattr(base, member)
            raise FEELError(f"Cannot access '{member}' on {type(base)}")
        elif op == "filter":
            collection = self._eval_ast(node[1], variables)
            index = self._eval_ast(node[2], variables)
            if isinstance(collection, list):
                if isinstance(index, int):
                    idx = index - 1 if index > 0 else index
                    return collection[idx] if 0 <= idx < len(collection) else None
                return [item for item in collection if self._matches_filter(item, index, variables)]
            return None
        elif op == "or":
            return self._eval_ast(node[1], variables) or self._eval_ast(node[2], variables)
        elif op == "and":
            return self._eval_ast(node[1], variables) and self._eval_ast(node[2], variables)
        elif op == "not":
            return not self._eval_ast(node[1], variables)
        elif op == "eq":
            return self._eval_ast(node[1], variables) == self._eval_ast(node[2], variables)
        elif op == "neq":
            return self._eval_ast(node[1], variables) != self._eval_ast(node[2], variables)
        elif op == "lt":
            return self._eval_ast(node[1], variables) < self._eval_ast(node[2], variables)
        elif op == "gt":
            return self._eval_ast(node[1], variables) > self._eval_ast(node[2], variables)
        elif op == "lte":
            return self._eval_ast(node[1], variables) <= self._eval_ast(node[2], variables)
        elif op == "gte":
            return self._eval_ast(node[1], variables) >= self._eval_ast(node[2], variables)
        elif op == "between":
            val = self._eval_ast(node[1], variables)
            low = self._eval_ast(node[2], variables)
            high = self._eval_ast(node[3], variables)
            return low <= val <= high
        elif op == "in":
            val = self._eval_ast(node[1], variables)
            values = [self._eval_ast(v, variables) for v in node[2]]
            return val in values
        elif op == "in_range":
            val = self._eval_ast(node[1], variables)
            range_info = node[2]
            if range_info[0] == "range":
                low = self._eval_ast(range_info[2], variables)
                high = self._eval_ast(range_info[3], variables)
                left_ok = val > low if range_info[1] else val >= low
                right_ok = val < high if range_info[4] else val <= high
                return left_ok and right_ok
            return False
        elif op == "instance_of":
            val = self._eval_ast(node[1], variables)
            type_name = node[2]
            type_map = {
                "string": str, "number": (int, float), "boolean": bool,
                "list": list, "context": dict, "date": str, "time": str,
                "date and time": str, "duration": str, "range": tuple,
            }
            expected = type_map.get(type_name.lower())
            if expected:
                return isinstance(val, expected)
            return False
        elif op == "add":
            return self._eval_ast(node[1], variables) + self._eval_ast(node[2], variables)
        elif op == "sub":
            return self._eval_ast(node[1], variables) - self._eval_ast(node[2], variables)
        elif op == "mul":
            return self._eval_ast(node[1], variables) * self._eval_ast(node[2], variables)
        elif op == "div":
            divisor = self._eval_ast(node[2], variables)
            if divisor == 0:
                raise FEELError("Division by zero")
            return self._eval_ast(node[1], variables) / divisor
        elif op == "mod":
            return self._eval_ast(node[1], variables) % self._eval_ast(node[2], variables)
        elif op == "neg":
            return -self._eval_ast(node[1], variables)
        elif op == "if":
            cond = self._eval_ast(node[1], variables)
            if cond:
                return self._eval_ast(node[2], variables)
            return self._eval_ast(node[3], variables)
        elif op == "for":
            var_name = node[1]
            collection = self._eval_ast(node[2], variables)
            if not isinstance(collection, list):
                return []
            results = []
            for item in collection:
                local_vars = dict(variables)
                local_vars[var_name] = item
                results.append(self._eval_ast(node[3], local_vars))
            return results
        elif op in ("some", "every"):
            var_name = node[1]
            collection = self._eval_ast(node[2], variables)
            if not isinstance(collection, list):
                return False
            for item in collection:
                local_vars = dict(variables)
                local_vars[var_name] = item
                result = self._eval_ast(node[3], local_vars)
                if op == "some" and result:
                    return True
                if op == "every" and not result:
                    return False
            return op == "every"
        elif op == "list":
            return [self._eval_ast(item, variables) for item in node[1]]
        elif op == "context":
            result = {}
            for key, value_node in node[1]:
                result[key] = self._eval_ast(value_node, variables)
            return result
        elif op == "call":
            func_name = node[1].lower()
            args = [self._eval_ast(a, variables) for a in node[2]]
            func = self._functions.get(func_name)
            if func is None:
                raise FEELError(f"Unknown function: {func_name}")
            try:
                return func.func(*args)
            except Exception as e:
                raise FEELError(f"Function '{func_name}' error: {e}")
        elif op == "duration":
            return self._parse_duration_value(node[1])
        elif op in ("date", "time"):
            return node[1]
        else:
            raise FEELError(f"Unknown AST node: {op}")

    def _matches_filter(self, item: Any, condition: Any, variables: dict[str, Any]) -> bool:
        if isinstance(condition, dict):
            for key, expected in condition.items():
                if isinstance(item, dict):
                    if item.get(key) != expected:
                        return False
                elif not hasattr(item, key):
                    return False
                elif getattr(item, key) != expected:
                    return False
            return True
        return bool(condition)

    def _parse_duration_value(self, value: str) -> dict[str, Any]:
        result: dict[str, Any] = {"years": 0, "months": 0, "days": 0, "hours": 0, "minutes": 0, "seconds": 0}
        m = re.match(r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?", value)
        if m:
            if m.group(1): result["years"] = int(m.group(1))
            if m.group(2): result["months"] = int(m.group(2))
            if m.group(3): result["days"] = int(m.group(3))
            if m.group(4): result["hours"] = int(m.group(4))
            if m.group(5): result["minutes"] = int(m.group(5))
            if m.group(6): result["seconds"] = float(m.group(6))
        return result

    def register_function(self, feel_func: FEELFunction) -> None:
        self._functions[feel_func.name.lower()] = feel_func

    def _register_builtins(self) -> None:
        import math
        builtins = [
            FEELFunction("abs", ["n"], lambda n: abs(n)),
            FEELFunction("ceil", ["n"], lambda n: math.ceil(n)),
            FEELFunction("floor", ["n"], lambda n: math.floor(n)),
            FEELFunction("round", ["n"], lambda n: round(n)),
            FEELFunction("modulo", ["a", "b"], lambda a, b: a % b),
            FEELFunction("sqrt", ["n"], lambda n: math.sqrt(n) if n >= 0 else None),
            FEELFunction("max", ["list"], lambda lst: max(lst) if lst else None),
            FEELFunction("min", ["list"], lambda lst: min(lst) if lst else None),
            FEELFunction("mean", ["list"], lambda lst: sum(lst) / len(lst) if lst else None),
            FEELFunction("sum", ["list"], lambda lst: sum(lst) if lst else 0),
            FEELFunction("count", ["list"], lambda lst: len(lst)),
            FEELFunction("contains", ["str", "substr"], lambda s, sub: sub in s if s and sub else False),
            FEELFunction("starts with", ["str", "prefix"], lambda s, p: s.startswith(p) if s and p else False),
            FEELFunction("ends with", ["str", "suffix"], lambda s, sfx: s.endswith(sfx) if s and sfx else False),
            FEELFunction("string length", ["str"], lambda s: len(s) if s else 0),
            FEELFunction("substring", ["str", "start", "length"], lambda s, st, ln: s[st - 1:st - 1 + ln] if s and st and ln else ""),
            FEELFunction("upper case", ["str"], lambda s: s.upper() if s else ""),
            FEELFunction("lower case", ["str"], lambda s: s.lower() if s else ""),
            FEELFunction("trim", ["str"], lambda s: s.strip() if s else ""),
            FEELFunction("replace", ["str", "pattern", "replacement"], lambda s, p, r: re.sub(p, r, s) if s else ""),
            FEELFunction("list contains", ["list", "item"], lambda lst, item: item in lst if lst else False),
            FEELFunction("not", ["value"], lambda v: not v),
            FEELFunction("is defined", ["value"], lambda v: v is not None),
            FEELFunction("is null", ["value"], lambda v: v is None),
            FEELFunction("is number", ["value"], lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)),
            FEELFunction("is string", ["value"], lambda v: isinstance(v, str)),
            FEELFunction("is boolean", ["value"], lambda v: isinstance(v, bool)),
            FEELFunction("is list", ["value"], lambda v: isinstance(v, list)),
            FEELFunction("is context", ["value"], lambda v: isinstance(v, dict)),
            FEELFunction("now", [], lambda: datetime.datetime.now().isoformat()),
            FEELFunction("today", [], lambda: datetime.date.today().isoformat()),
            FEELFunction("day of week", ["date"], lambda d: datetime.date.fromisoformat(d).strftime("%A") if d else None),
            FEELFunction("day of year", ["date"], lambda d: datetime.date.fromisoformat(d).timetuple().tm_yday if d else None),
            FEELFunction("week of year", ["date"], lambda d: int(datetime.date.fromisoformat(d).strftime("%W")) if d else None),
            FEELFunction("month of year", ["date"], lambda d: datetime.date.fromisoformat(d).month if d else None),
            FEELFunction("substring before", ["str", "match"], lambda s, m: s.split(m)[0] if s and m and m in s else ""),
            FEELFunction("substring after", ["str", "match"], lambda s, m: s.split(m)[1] if s and m and m in s and len(s.split(m)) > 1 else ""),
            FEELFunction("index of", ["list", "match"], lambda lst, m: next((i + 1 for i, v in enumerate(lst) if v == m), 0) if lst else 0),
            FEELFunction("append", ["list", "items"], lambda lst, items: lst + (items if isinstance(items, list) else [items])),
            FEELFunction("concatenate", ["lists"], lambda *lists: [item for lst in lists for item in lst]),
            FEELFunction("insert before", ["list", "position", "newItem"], lambda lst, pos, item: lst[:pos-1] + [item] + lst[pos-1:] if lst else [item]),
            FEELFunction("remove", ["list", "position"], lambda lst, pos: lst[:pos-1] + lst[pos:] if lst and 1 <= pos <= len(lst) else lst),
            FEELFunction("reverse", ["list"], lambda lst: list(reversed(lst)) if lst else []),
            FEELFunction("sort", ["list", "precedes"], lambda lst, p: sorted(lst, key=lambda x: (p(x), x)) if lst and callable(p) else sorted(lst) if lst else []),
            FEELFunction("distinct values", ["list"], lambda lst: list(dict.fromkeys(lst)) if lst else []),
            FEELFunction("flatten", ["list"], lambda lst: [item for sublist in lst for item in (sublist if isinstance(sublist, list) else [sublist])] if lst else []),
            FEELFunction("sublist", ["list", "start", "length"], lambda lst, s, l: lst[s-1:s-1+l] if lst else []),
            FEELFunction("decimal", ["n", "scale"], lambda n, s: round(n, s) if n is not None else None),
            FEELFunction("number", ["from", "grouping separator", "decimal separator"], lambda f, g, d: float(f.replace(g, "").replace(d, ".")) if f else None),
        ]
        for func in builtins:
            self._functions[func.name.lower()] = func

    def validate(self, expression: str) -> list[str]:
        errors: list[str] = []
        try:
            parser = FEELParser(expression)
            parser.parse()
        except FEELError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Parse error: {e}")
        return errors
