from __future__ import annotations

import ast
from typing import Sequence


class SmartNodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.stack: set[str] = set()

    def smart_visit(self, node: Sequence[ast.AST] | ast.AST | None):
        if node is None:
            return

        if isinstance(node, Sequence):
            for n in node:
                self.smart_visit(n)
        else:
            self.visit(node)
