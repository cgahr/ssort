from __future__ import annotations

import ast

from ._node_visitor import SmartNodeVisitor

__all__ = ["get_bindings"]


class Bindings(SmartNodeVisitor):
    def _store_name_visit_rest(
        self, node: ast.ExceptHandler | ast.MatchAs | ast.MatchStar
    ):
        for field, child in ast.iter_fields(node):
            if field == "name" and node.name:
                self.stack.add(node.name)
            else:
                self.smart_visit(child)

    visit_ExceptHandler = _store_name_visit_rest
    visit_MatchAs = _store_name_visit_rest
    visit_MatchStar = _store_name_visit_rest

    def _store_names(self, node: ast.Global | ast.Nonlocal):
        self.stack |= set(node.names)

    visit_Global = _store_names
    visit_Nonlocal = _store_names

    def _store_name_skip_body_visit_rest(
        self,
        node: ast.AsyncFunctionDef
        | ast.ClassDef
        | ast.FunctionDef
        | ast.Lambda,
    ):
        for field, child in ast.iter_fields(node):
            if field == "name":
                self.stack.add(child)
            elif field != "body":
                self.smart_visit(child)

    visit_FunctionDef = _store_name_skip_body_visit_rest
    visit_AsyncFunctionDef = _store_name_skip_body_visit_rest
    visit_ClassDef = _store_name_skip_body_visit_rest

    def visit_Lambda(self, node: ast.Lambda):
        self.smart_visit(node.args)

    def visit_Import(self, node):
        self.stack |= set(
            n.asname if n.asname else n.name.split(".")[0] for n in node.names
        )

    def visit_ImportFrom(self, node):
        self.stack |= set(n.asname if n.asname else n.name for n in node.names)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.stack.add(node.id)

    def visit_MatchMapping(self, node: ast.MatchMapping):
        for field, child in ast.iter_fields(node):
            if field == "rest":
                self.stack.add(child)
            else:
                self.smart_visit(child)


def get_bindings(node: ast.AST) -> set[str]:
    bindings = Bindings()
    bindings.visit(node)
    return bindings.stack
