from __future__ import annotations

import ast
from typing import Generic, Hashable, Sequence, TypeVar

__all__ = ["SmartNodeVisitor"]

T = TypeVar("T", bound=Hashable)


class SmartNodeVisitor(ast.NodeVisitor, Generic[T]):
    def __init__(self) -> None:
        self.stack: set[T] = set()

    def smart_visit(self, node: Sequence[ast.AST] | ast.AST | None) -> None:
        if node is None:
            return

        if isinstance(node, Sequence):
            for n in node:
                self.smart_visit(n)
        else:
            self.visit(node)
