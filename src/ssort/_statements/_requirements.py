from __future__ import annotations

import ast
import dataclasses
import enum

from .._builtins import CLASS_BUILTINS
from ._bindings import get_bindings
from ._node_visitor import SmartNodeVisitor

__all__ = ["get_requirements", "Requirement"]


class Scope(enum.Enum):
    LOCAL = "LOCAL"
    NONLOCAL = "NONLOCAL"
    GLOBAL = "GLOBAL"


NamesInScope = set[str]


@dataclasses.dataclass(frozen=True)
class Requirement:
    name: str
    lineno: int
    col_offset: int
    deferred: bool = False
    scope: Scope = Scope.LOCAL


def get_scope_from_arguments(args: ast.arguments) -> NamesInScope:
    scope: NamesInScope = set()

    for field, child in ast.iter_fields(args):
        if field in {"posonlyargs", "args", "kwonlyargs"}:
            scope |= {argument.arg for argument in child}

        elif field in {"vararg", "kwarg"} and child is not None:
            scope.add(child.arg)

    return scope


def get_requirements(node: ast.AST):
    requirements = Requirements()
    requirements.visit(node)
    return requirements.stack


class Requirements(SmartNodeVisitor[Requirement]):
    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self.smart_visit(node.decorator_list)
        self.smart_visit(node.args)
        self.smart_visit(node.returns)

        scope = get_scope_from_arguments(node.args)

        requirements = set()
        for statement in node.body:
            scope |= get_bindings(statement)

            for requirement in get_requirements(statement):
                if not requirement.deferred:
                    requirement = dataclasses.replace(
                        requirement, deferred=True
                    )
                requirements.add(requirement)

        for requirement in requirements:
            if requirement.scope == Scope.GLOBAL:
                self.stack.add(requirement)
            elif requirement.scope == Scope.NONLOCAL:
                self.stack.add(
                    dataclasses.replace(requirement, scope=Scope.LOCAL)
                )
            elif requirement.name not in scope:
                self.stack.add(requirement)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef):
        self.smart_visit(node.decorator_list)
        self.smart_visit(node.bases)

        scope = set(CLASS_BUILTINS)

        for statement in node.body:
            for stmt_dep in get_requirements(statement):
                if stmt_dep.deferred or stmt_dep.name not in scope:
                    self.stack.add(stmt_dep)

            scope.update(get_bindings(statement))

    def visit_For(self, node: ast.For | ast.AsyncFor):
        bindings = get_bindings(node)

        self.smart_visit(node.target)
        self.smart_visit(node.iter)

        for stmt in node.body:
            for requirement in get_requirements(stmt):
                if requirement.name not in bindings:
                    self.stack.add(requirement)

        for stmt in node.orelse:
            for requirement in get_requirements(stmt):
                if requirement.name not in bindings:
                    self.stack.add(requirement)

    visit_AsyncFor = visit_For

    def visit_With(self, node: ast.With | ast.AsyncWith):
        bindings = get_bindings(node)

        self.smart_visit(node.items)

        for stmt in node.body:
            for requirement in get_requirements(stmt):
                if requirement.name not in bindings:
                    self.stack.add(requirement)

    visit_AsyncWith = visit_With

    def visit_Global(self, node: ast.Global):
        for name in node.names:
            self.stack.add(
                Requirement(
                    name=name,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    scope=Scope.GLOBAL,
                )
            )

    def visit_Nonlocal(self, node: ast.Nonlocal):
        for name in node.names:
            self.stack.add(
                Requirement(
                    name=name,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    scope=Scope.NONLOCAL,
                )
            )

    def visit_Lambda(self, node: ast.Lambda):
        self.smart_visit(node.args)

        scope = get_scope_from_arguments(node.args)
        scope |= get_bindings(node.body)

        for requirement in get_requirements(node.body):
            if requirement.name not in scope:
                self.stack.add(requirement)

    def visit_ListComp(
        self,
        node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
    ):
        bindings = get_bindings(node)

        for child in ast.iter_child_nodes(node):
            for requirement in get_requirements(child):
                if requirement.name not in bindings:
                    self.stack.add(requirement)

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, (ast.Load, ast.Del)):
            self.stack.add(
                Requirement(
                    name=node.id,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )
            )
