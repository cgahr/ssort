import ast
import sys
import textwrap

import pytest

from ssort._statements._bindings import get_bindings

# Most walrus operator syntax is valid in 3.8. Only use this decorator for the
# rare cases where it is not.
walrus_operator = pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="some walrus operator syntax is not valid prior to python 3.9",
)


match_statement = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="match statements were introduced in python 3.10",
)


def test_function_def_bindings(parse):
    node = parse(
        """
        def function():
            name
        """
    )
    assert get_bindings(node) == {"function"}


def test_function_def_bindings_walrus_default(parse):
    node = parse(
        """
        def function(a, b = (b_binding := 2)):
            pass
        """
    )
    assert get_bindings(node) == {"function", "b_binding"}


def test_function_def_bindings_walrus_kw_default(parse):
    node = parse(
        """
        def function(*, kw1 = (kw1_binding := 1), kw2):
            pass
        """
    )
    assert get_bindings(node) == {"function", "kw1_binding"}


def test_function_def_bindings_walrus_type(parse):
    node = parse(
        """
        def function(
            posonly: (posonly_type := int), / ,
            arg: (arg_type := int),
            *args: (args_type := int),
            kwarg: (kwarg_type := int),
            **kwargs: (kwargs_type := int)
        ) -> (return_type := int):
            pass
        """
    )
    assert get_bindings(node) == {
        "function",
        "posonly_type",
        "arg_type",
        "args_type",
        "kwarg_type",
        "kwargs_type",
        "return_type",
    }


@walrus_operator
def test_function_def_bindings_walrus_decorator(parse):
    node = parse(
        """
        @(p := property)
        def prop(self):
            pass
        """
    )
    assert get_bindings(node) == {"p", "prop"}


def test_async_function_def_bindings(parse):
    """
    ..code:: python

        AsyncFunctionDef(
            identifier name,
            arguments args,
            stmt* body,
            expr* decorator_list,
            expr? returns,
            string? type_comment,
        )

    """
    node = parse(
        """
        async def function():
            name
        """
    )
    assert get_bindings(node) == {"function"}


def test_async_function_def_bindings_walrus_kw_default(parse):
    node = parse(
        """
        async def function(*, kw1 = (kw1_binding := 1), kw2):
            pass
        """
    )
    assert get_bindings(node) == {"function", "kw1_binding"}


def test_async_function_def_bindings_walrus_type(parse):
    node = parse(
        """
        async def function(
            posonly: (posonly_type := int), / ,
            arg: (arg_type := int),
            *args: (args_type := int),
            kwarg: (kwarg_type := int),
            **kwargs: (kwargs_type := int)
        ) -> (return_type := int):
            pass
        """
    )
    assert get_bindings(node) == {
        "function",
        "posonly_type",
        "arg_type",
        "args_type",
        "kwarg_type",
        "kwargs_type",
        "return_type",
    }


@walrus_operator
def test_async_function_def_bindings_walrus_decorator(parse):
    node = parse(
        """
        @(p := property)
        async def prop(self):
            pass
        """
    )
    assert get_bindings(node) == {"p", "prop"}


def test_class_def_bindings(parse):
    """
    ..code:: python

        ClassDef(
            identifier name,
            expr* bases,
            keyword* keywords,
            stmt* body,
            expr* decorator_list,
        )
    """
    node = parse(
        """
        @decorator
        class ClassName:
            a = 1
            def b(self):
                pass
        """
    )
    assert get_bindings(node) == {"ClassName"}


@walrus_operator
def test_class_def_bindings_walrus_decorator(parse):
    node = parse(
        """
        @(d := decorator())
        class ClassName:
            pass
        """
    )
    assert get_bindings(node) == {"d", "ClassName"}


def test_class_def_bindings_walrus_base(parse):
    node = parse(
        """
        class ClassName(BaseClass, (OtherBase := namedtuple())):
            pass
        """
    )
    assert get_bindings(node) == {"OtherBase", "ClassName"}


def test_class_def_bindings_walrus_metaclass(parse):
    node = parse(
        """
        class Class(metaclass=(class_meta := MetaClass)):
            pass
        """
    )
    assert get_bindings(node) == {"class_meta", "Class"}


def test_class_def_bindings_walrus_body(parse):
    node = parse(
        """
        class Class:
            a = (prop := 2)
        """
    )
    assert get_bindings(node) == {"Class"}


def test_return_bindings(parse):
    """
    ..code:: python

        Return(expr? value)

    """
    node = parse("return x")
    assert get_bindings(node) == set()


def test_return_bindings_walrus(parse):
    node = parse("return (x := 1)")
    assert get_bindings(node) == {"x"}


def test_delete_bindings(parse):
    """
    ..code:: python

        Delete(expr* targets)
    """
    node = parse("del something")
    assert get_bindings(node) == set()


def test_delete_bindings_multiple(parse):
    node = parse("del a, b")
    assert get_bindings(node) == set()


def test_delete_bindings_subscript(parse):
    node = parse("del a[b:c]")
    assert get_bindings(node) == set()


def test_delete_bindings_attribute(parse):
    node = parse("del obj.attr")
    assert get_bindings(node) == set()


def test_assign_bindings(parse):
    """
    ..code:: python

        Assign(expr* targets, expr value, string? type_comment)
    """
    node = parse("a = b")
    assert get_bindings(node) == {"a"}


def test_assign_bindings_star(parse):
    node = parse("a, *b = c")
    assert get_bindings(node) == {"a", "b"}


def test_assign_bindings_attribute(parse):
    node = parse("obj.attr = value")
    assert get_bindings(node) == set()


def test_assign_bindings_list(parse):
    node = parse("[a, b, [c, d]] = value")
    assert get_bindings(node) == {"a", "b", "c", "d"}


def test_assign_bindings_list_star(parse):
    node = parse("[first, *rest] = value")
    assert get_bindings(node) == {"first", "rest"}


def test_assign_bindings_walrus_value(parse):
    node = parse("a = (b := c)")
    assert get_bindings(node) == {"a", "b"}


def test_aug_assign_bindings(parse):
    """
    ..code:: python

        AugAssign(expr target, operator op, expr value)
    """
    node = parse("a += b")
    assert get_bindings(node) == {"a"}


def test_aug_assign_bindings_attribute(parse):
    node = parse("obj.attr /= value")
    assert get_bindings(node) == set()


def test_aug_assign_bindings_walrus_value(parse):
    node = parse("a ^= (b := c)")
    assert get_bindings(node) == {"a", "b"}


def test_ann_assign_bindings(parse):
    """
    ..code:: python

        # 'simple' indicates that we annotate simple name without parens
        AnnAssign(expr target, expr annotation, expr? value, int simple)

    """
    node = parse("a: int = b")
    assert get_bindings(node) == {"a"}


def test_ann_assign_bindings_no_value(parse):
    # TODO this expression doesn't technically bind `a`.
    node = parse("a: int")
    assert get_bindings(node) == {"a"}


def test_ann_assign_bindings_walrus_value(parse):
    node = parse("a: int = (b := c)")
    assert get_bindings(node) == {"a", "b"}


def test_ann_assign_bindings_walrus_type(parse):
    node = parse("a: (a_type := int) = 4")
    assert get_bindings(node) == {"a", "a_type"}


def test_for_bindings(parse):
    """
    ..code:: python

        # use 'orelse' because else is a keyword in target languages
        For(
            expr target,
            expr iter,
            stmt* body,
            stmt* orelse,
            string? type_comment,
        )
    """
    node = parse(
        """
        for i in range(10):
            a += i
        else:
            b = 4
        """
    )
    assert get_bindings(node) == {"i", "a", "b"}


def test_for_bindings_walrus(parse):
    node = parse(
        """
        for i in (r := range(10)):
            pass
        """
    )
    assert get_bindings(node) == {"i", "r"}


def test_async_for_bindings(parse):
    """
    ..code:: python

        AsyncFor(
            expr target,
            expr iter,
            stmt* body,
            stmt* orelse,
            string? type_comment,
        )
    """
    node = parse(
        """
        async for i in range(10):
            a += i
        else:
            b = 4
        """
    )
    assert get_bindings(node) == {"i", "a", "b"}


def test_async_for_bindings_walrus(parse):
    node = parse(
        """
        async for i in (r := range(10)):
            pass
        """
    )
    assert get_bindings(node) == {"i", "r"}


def test_while_bindings(parse):
    """
    ..code:: python

        While(expr test, stmt* body, stmt* orelse)
    """
    node = parse(
        """
        while test():
            a = 1
        else:
            b = 2
        """
    )
    assert get_bindings(node) == {"a", "b"}


def test_while_bindings_walrus_test(parse):
    node = parse(
        """
        while (value := test):
            pass
        """
    )
    assert get_bindings(node) == {"value"}


def test_if_bindings(parse):
    """
    ..code:: python

        If(expr test, stmt* body, stmt* orelse)
    """
    node = parse(
        """
        if predicate_one():
            a = 1
        elif predicate_two():
            b = 2
        else:
            c = 3
        """
    )
    assert get_bindings(node) == {"a", "b", "c"}


def test_if_bindings_walrus_test(parse):
    node = parse(
        """
        if (result := predicate()):
            pass
        """
    )
    assert get_bindings(node) == {"result"}


def test_with_bindings(parse):
    """
    ..code:: python

        With(withitem* items, stmt* body, string? type_comment)
    """
    node = parse(
        """
        with A() as a:
            b = 4
        """
    )
    assert get_bindings(node) == {"a", "b"}


def test_with_bindings_requirements_example(parse):
    node = parse(
        """
        with chdir(os.path.dirname(path)):
            requirements = parse_requirements(path)
            for req in requirements.values():
                if req.name:
                    results.append(req.name)
        """
    )
    assert get_bindings(node) == {"requirements", "req"}


def test_with_bindings_multiple(parse):
    node = parse(
        """
        with A() as a, B() as b:
            pass
        """
    )
    assert get_bindings(node) == {"a", "b"}


def test_with_bindings_unbound(parse):
    node = parse(
        """
        with A():
            pass
        """
    )
    assert get_bindings(node) == set()


def test_with_bindings_tuple(parse):
    node = parse(
        """
        with A() as (a, b):
            pass
        """
    )
    assert get_bindings(node) == {"a", "b"}


def test_with_bindings_walrus(parse):
    node = parse(
        """
        with (ctx := A()) as a:
            pass
        """
    )
    assert get_bindings(node) == {"ctx", "a"}


def test_async_with_bindings(parse):
    """
    ..code:: python

        AsyncWith(withitem* items, stmt* body, string? type_comment)
    """
    node = parse(
        """
        async with A() as a:
            b = 4
        """
    )
    assert get_bindings(node) == {"a", "b"}


def test_async_with_bindings_multiple(parse):
    node = parse(
        """
        async with A() as a, B() as b:
            pass
        """
    )
    assert get_bindings(node) == {"a", "b"}


def test_async_with_bindings_unbound(parse):
    node = parse(
        """
        async with A():
            pass
        """
    )
    assert get_bindings(node) == set()


def test_async_with_bindings_tuple(parse):
    node = parse(
        """
        async with A() as (a, b):
            pass
        """
    )
    assert get_bindings(node) == {"a", "b"}


def test_async_with_bindings_walrus(parse):
    node = parse(
        """
        async with (ctx := A()) as a:
            pass
        """
    )
    assert get_bindings(node) == {"ctx", "a"}


def test_raise_bindings(parse):
    """
    ..code:: python

        Raise(expr? exc, expr? cause)
    """
    node = parse("raise TypeError()")
    assert get_bindings(node) == set()


def test_raise_bindings_reraise(parse):
    node = parse("raise")
    assert get_bindings(node) == set()


def test_raise_bindings_with_cause(parse):
    node = parse("raise TypeError() from exc")
    assert get_bindings(node) == set()


def test_raise_bindings_walrus(parse):
    node = parse("raise (exc := TypeError())")
    assert get_bindings(node) == {"exc"}


def test_raise_bindings_walrus_in_cause(parse):
    node = parse("raise TypeError() from (original := exc)")
    assert get_bindings(node) == {"original"}


def test_try_bindings(parse):
    """
    ..code:: python

        Try(
            stmt* body,
            excepthandler* handlers,
            stmt* orelse,
            stmt* finalbody,
        )
    """
    node = parse(
        """
        try:
            a = something_stupid()
        except Exception as exc:
            b = recover()
        else:
            c = otherwise()
        finally:
            d = finish()
        """
    )
    assert get_bindings(node) == {"a", "exc", "b", "c", "d"}


def test_try_bindings_walrus(parse):
    node = parse(
        """
        try:
            pass
        except (x := Exception):
            pass
        """
    )
    assert get_bindings(node) == {"x"}


def test_assert_bindings(parse):
    """
    ..code:: python

        Assert(expr test, expr? msg)

    """
    node = parse("assert condition()")
    assert get_bindings(node) == set()


def test_assert_bindings_with_message(parse):
    node = parse('assert condition(), "message"')
    assert get_bindings(node) == set()


def test_assert_bindings_walrus_condition(parse):
    node = parse("assert (result := condition())")
    assert get_bindings(node) == {"result"}


def test_assert_bindings_walrus_message(parse):
    node = parse('assert condition, (message := "message")')
    assert get_bindings(node) == {"message"}


def test_import_bindings(parse):
    """
    ..code:: python

        Import(alias* names)
    """
    node = parse("import something")
    assert get_bindings(node) == {"something"}


def test_import_bindings_as(parse):
    node = parse("import something as something_else")
    assert get_bindings(node) == {"something_else"}


def test_import_bindings_nested(parse):
    node = parse("import module.submodule")
    assert get_bindings(node) == {"module"}


def test_import_from_bindings(parse):
    """
    ..code:: python

        ImportFrom(identifier? module, alias* names, int? level)

    """
    node = parse("from module import a, b")
    assert get_bindings(node) == {"a", "b"}


def test_import_from_bindings_as(parse):
    node = parse("from module import something as something_else")
    assert get_bindings(node) == {"something_else"}


def test_global_bindings(parse):
    """
    ..code:: python

        Global(identifier* names)
    """
    node = parse("global name")
    assert get_bindings(node) == {"name"}


def test_global_bindings_multiple(parse):
    node = parse("global a, b")
    assert get_bindings(node) == {"a", "b"}


def test_non_local_bindings(parse):
    """
    ..code:: python

        Nonlocal(identifier* names)
    """
    node = parse("nonlocal name")
    assert get_bindings(node) == {"name"}


def test_nonlocal_bindings_multiple(parse):
    node = parse("nonlocal a, b")
    assert get_bindings(node) == {"a", "b"}


def test_pass_bindings(parse):
    """
    ..code:: python

        Pass

    """
    node = parse("pass")
    assert get_bindings(node) == set()


def test_break_bindings(parse):
    """
    ..code:: python

        Break

    """
    node = parse("break")
    assert get_bindings(node) == set()


def test_continue_bindings(parse):
    """
    ..code:: python

        Continue

    """
    node = parse("continue")
    assert get_bindings(node) == set()


def test_bool_op_bindings(parse):
    """
    ..code:: python

        # BoolOp() can use left & right?
        # expr
        BoolOp(boolop op, expr* values)
    """
    node = parse("a and b")
    assert get_bindings(node) == set()


def test_named_expr_bindings(parse):
    """
    ..code:: python

        NamedExpr(expr target, expr value)
    """
    node = parse("(a := b)")
    assert get_bindings(node) == {"a"}


def test_named_expr_bindings_recursive(parse):
    """
    ..code:: python

        NamedExpr(expr target, expr value)
    """
    node = parse("(a := (b := (c := d)))")
    assert get_bindings(node) == {"a", "b", "c"}


def test_bool_op_bindings_walrus_left(parse):
    node = parse("(left := a) and b")
    assert get_bindings(node) == {"left"}


def test_bool_op_bindings_walrus_right(parse):
    node = parse("a or (right := b)")
    assert get_bindings(node) == {"right"}


def test_bool_op_bindings_walrus_both(parse):
    node = parse("(left := a) and (right := b)")
    assert get_bindings(node) == {"left", "right"}


def test_bool_op_bindings_walrus_multiple(parse):
    node = parse("(a := 1) and (b := 2) and (c := 3)")
    assert get_bindings(node) == {"a", "b", "c"}


def test_bin_op_bindings(parse):
    """
    ..code:: python

        BinOp(expr left, operator op, expr right)
    """
    node = parse("a and b")
    assert get_bindings(node) == set()


def test_bin_op_bindings_walrus_left(parse):
    node = parse("(left := a) | b")
    assert get_bindings(node) == {"left"}


def test_bin_op_bindings_walrus_right(parse):
    node = parse("a ^ (right := b)")
    assert get_bindings(node) == {"right"}


def test_bin_op_bindings_walrus_both(parse):
    node = parse("(left := a) + (right := b)")
    assert get_bindings(node) == {"left", "right"}


def test_unary_op_bindings(parse):
    """
    ..code:: python

        UnaryOp(unaryop op, expr operand)
    """
    node = parse("-a")
    assert get_bindings(node) == set()


def test_unary_op_bindings_walrus(parse):
    node = parse("-(a := b)")
    assert get_bindings(node) == {"a"}


def test_lambda_bindings(parse):
    """
    ..code:: python

        Lambda(arguments args, expr body)
    """
    pass


def test_lambda_bindings_walrus_default(parse):
    node = parse("(lambda a, b = (b_binding := 2): None)")
    assert get_bindings(node) == {"b_binding"}


def test_lambda_bindings_walrus_kw_default(parse):
    node = parse("(lambda *, kw1 = (kw1_binding := 1), kw2: None)")
    assert get_bindings(node) == {"kw1_binding"}


def test_lambda_bindings_walrus_body(parse):
    node = parse("(lambda : (a := 1) + a)")
    assert get_bindings(node) == set()


def test_if_exp_bindings(parse):
    """
    ..code:: python

        IfExp(expr test, expr body, expr orelse)
    """
    node = parse("subsequent() if predicate() else alternate()")
    assert get_bindings(node) == set()


def test_if_exp_bindings_walrus_subsequent(parse):
    node = parse("(a := subsequent()) if predicate() else alternate()")
    assert get_bindings(node) == {"a"}


def test_if_exp_bindings_walrus_predicate(parse):
    node = parse("subsequent() if (a := predicate()) else alternate()")
    assert get_bindings(node) == {"a"}


def test_if_exp_bindings_walrus_alternate(parse):
    node = parse("subsequent() if predicate() else (a := alternate())")
    assert get_bindings(node) == {"a"}


def test_if_exp_bindings_walrus(parse):
    node = parse(
        "(a := subsequent()) if (b := predicate()) else (c := alternate())"
    )
    assert get_bindings(node) == {"b", "a", "c"}


def test_dict_bindings(parse):
    """
    ..code:: python

        Dict(expr* keys, expr* values)
    """
    node = parse("{key: value}")
    assert get_bindings(node) == set()


def test_dict_bindings_empty(parse):
    node = parse("{}")
    assert get_bindings(node) == set()


def test_dict_bindings_unpack(parse):
    node = parse("{**values}")
    assert get_bindings(node) == set()


def test_dict_bindings_walrus_key(parse):
    node = parse("{(key := genkey()): value}")
    assert get_bindings(node) == {"key"}


def test_dict_bindings_walrus_value(parse):
    node = parse("{key: (value := genvalue())}")
    assert get_bindings(node) == {"value"}


def test_dict_bindings_walrus_unpack(parse):
    node = parse("{key: value, **(rest := other)}")
    assert get_bindings(node) == {"rest"}


def test_set_bindings(parse):
    """
    ..code:: python

        Set(expr* elts)
    """
    node = parse("{a, b, c}")
    assert get_bindings(node) == set()


def test_set_bindings_unpack(parse):
    node = parse("{a, b, *rest}")
    assert get_bindings(node) == set()


@walrus_operator
def test_set_bindings_walrus(parse):
    node = parse("{a, {b := genb()}, c}")
    assert get_bindings(node) == {"b"}


def test_set_bindings_walrus_py38(parse):
    node = parse("{a, {(b := genb())}, c}")
    assert get_bindings(node) == {"b"}


def test_set_bindings_walrus_unpack(parse):
    node = parse("{a, b, *(rest := other)}")
    assert get_bindings(node) == {"rest"}


def test_list_comp_bindings(parse):
    """
    ..code:: python

        comprehension = (expr target, expr iter, expr* ifs, int is_async)
        ListComp(expr elt, comprehension* generators)
    """
    node = parse("[item for item in iterator if condition(item)]")
    assert get_bindings(node) == {"item"}


def test_list_comp_bindings_walrus_target(parse):
    node = parse("[( a:= item) for item in iterator if condition(item)]")
    assert get_bindings(node) == {"a", "item"}


def test_list_comp_bindings_walrus_iter(parse):
    node = parse("[item for item in (it := iterator) if condition(item)]")
    assert get_bindings(node) == {"item", "it"}


def test_list_comp_bindings_walrus_condition(parse):
    node = parse("[item for item in iterator if (c := condition(item))]")
    assert get_bindings(node) == {"item", "c"}


def test_set_comp_bindings(parse):
    """
    ..code:: python

        comprehension = (expr target, expr iter, expr* ifs, int is_async)
        SetComp(expr elt, comprehension* generators)
    """
    node = parse("{item for item in iterator if condition(item)}")
    assert get_bindings(node) == {"item"}


def test_set_comp_bindings_walrus_target(parse):
    node = parse("{( a:= item) for item in iterator if condition(item)}")
    assert get_bindings(node) == {"a", "item"}


def test_set_comp_bindings_walrus_iter(parse):
    node = parse("{item for item in (it := iterator) if condition(item)}")
    assert get_bindings(node) == {"item", "it"}


def test_set_comp_bindings_walrus_condition(parse):
    node = parse("{item for item in iterator if (c := condition(item))}")
    assert get_bindings(node) == {"item", "c"}


def test_dict_comp_bindings(parse):
    """
    ..code:: python

        DictComp(expr key, expr value, comprehension* generators)
    """
    node = parse("{item[0]: item[1] for item in iterator if check(item)}")
    assert get_bindings(node) == {"item"}


def test_dict_comp_bindings_unpack(parse):
    node = parse("{key: value for key, value in iterator}")
    assert get_bindings(node) == {"key", "value"}


def test_dict_comp_bindings_walrus_key(parse):
    node = parse(
        "{(key := item[0]): item[1] for item in iterator if check(item)}"
    )
    assert get_bindings(node) == {"key", "item"}


def test_dict_comp_bindings_walrus_value(parse):
    node = parse(
        "{item[0]: (value := item[1]) for item in iterator if check(item)}"
    )
    assert get_bindings(node) == {"value", "item"}


def test_dict_comp_bindings_walrus_iter(parse):
    node = parse(
        "{item[0]: item[1] for item in (it := iterator) if check(item)}"
    )
    assert get_bindings(node) == {"item", "it"}


def test_dict_comp_bindings_walrus_condition(parse):
    node = parse(
        "{item[0]: item[1] for item in iterator if (c := check(item))}"
    )
    assert get_bindings(node) == {"item", "c"}


def test_generator_exp_bindings(parse):
    """
    ..code:: python

        GeneratorExp(expr elt, comprehension* generators)
    """
    node = parse("(item for item in iterator if condition(item))")
    assert get_bindings(node) == {"item"}


def test_generator_exp_bindings_walrus_target(parse):
    node = parse("(( a:= item) for item in iterator if condition(item))")
    assert get_bindings(node) == {"a", "item"}


def test_generator_exp_bindings_walrus_iter(parse):
    node = parse("(item for item in (it := iterator) if condition(item))")
    assert get_bindings(node) == {"item", "it"}


def test_generator_exp_bindings_walrus_condition(parse):
    node = parse("(item for item in iterator if (c := condition(item)))")
    assert get_bindings(node) == {"item", "c"}


def test_await_bindings(parse):
    """
    ..code:: python

        # the grammar constrains where yield expressions can occur
        Await(expr value)
    """
    node = parse("await fun()")
    assert get_bindings(node) == set()


def test_await_bindings_walrus(parse):
    node = parse("await (r := fun())")
    assert get_bindings(node) == {"r"}


def test_yield_bindings(parse):
    """
    ..code:: python

        Yield(expr? value)
    """
    node = parse("yield fun()")
    assert get_bindings(node) == set()


def test_yield_bindings_no_result(parse):
    node = parse("yield")
    assert get_bindings(node) == set()


def test_yield_bindings_walrus(parse):
    node = parse("yield (r := fun())")
    assert get_bindings(node) == {"r"}


def test_yield_from_bindings(parse):
    """
    ..code:: python

        YieldFrom(expr value)
    """
    node = parse("yield from fun()")
    assert get_bindings(node) == set()


def test_yield_from_bindings_walrus(parse):
    node = parse("yield from (r := fun())")
    assert get_bindings(node) == {"r"}


def test_compare_bindings(parse):
    """
    ..code:: python

        # need sequences for compare to distinguish between
        # x < 4 < 3 and (x < 4) < 3
        Compare(expr left, cmpop* ops, expr* comparators)
    """
    node = parse("0 < value < 5")
    assert get_bindings(node) == set()


def test_compare_bindings_walrus(parse):
    node = parse("(a := 0) < (b := value) < (c := 5)")
    assert get_bindings(node) == {"a", "b", "c"}


def test_call_bindings(parse):
    """
    ..code:: python

        keyword = (identifier? arg, expr value)
        Call(expr func, expr* args, keyword* keywords)
    """
    node = parse("fun(arg, *args, kwarg=kwarg, **kwargs)")
    assert get_bindings(node) == set()


def test_call_bindings_walrus_function(parse):
    node = parse("(f := fun)()")
    assert get_bindings(node) == {"f"}


def test_call_bindings_walrus_args(parse):
    node = parse(
        """
        fun(
            (arg_binding := arg),
            *(args_binding := args),
            kwarg=(kwarg_binding := kwarg),
            **(kwargs_binding := kwargs),
        )
        """
    )
    assert get_bindings(node) == {
        "arg_binding",
        "args_binding",
        "kwarg_binding",
        "kwargs_binding",
    }


def test_joined_str_bindings(parse):
    """
    ..code:: python

        JoinedStr(expr* values)
        FormattedValue(expr value, int? conversion, expr? format_spec)
    """
    node = parse('f"a: {a}"')
    assert get_bindings(node) == set()


def test_joined_str_bindings_walrus(parse):
    """
    ..code:: python

        JoinedStr(expr* values)
        FormattedValue(expr value, int? conversion, expr? format_spec)
    """
    node = parse('f"a: {(a := get_a())}"')
    assert get_bindings(node) == {"a"}


def test_constant_bindings(parse):
    """
    ..code:: python

        Constant(constant value, string? kind)
    """
    node = parse("1")
    assert get_bindings(node) == set()


def test_attribute_bindings(parse):
    """
    ..code:: python

        # the following expression can appear in assignment context
        Attribute(expr value, identifier attr, expr_context ctx)
    """
    node = parse("a.b.c")
    assert get_bindings(node) == set()


def test_attribute_bindings_walrus(parse):
    node = parse("(a_binding := a).b")
    assert get_bindings(node) == {"a_binding"}


def test_subscript_bindings(parse):
    """
    ..code:: python

        Subscript(expr value, expr slice, expr_context ctx)
    """
    node = parse("a[b]")
    assert get_bindings(node) == set()


def test_subscript_bindings_slice(parse):
    node = parse("a[b:c]")
    assert get_bindings(node) == set()


def test_subscript_bindings_slice_with_step(parse):
    node = parse("a[b:c:d]")
    assert get_bindings(node) == set()


def test_subscript_bindings_walrus_value(parse):
    node = parse("(a_binding := a)[b]")
    assert get_bindings(node) == {"a_binding"}


def test_subscript_bindings_walrus_index(parse):
    node = parse("a[(b_binding := b)]")
    assert get_bindings(node) == {"b_binding"}


def test_subscript_bindings_walrus_slice(parse):
    node = parse("a[(b_binding := b):(c_binding := c)]")
    assert get_bindings(node) == {"b_binding", "c_binding"}


def test_subscript_bindings_walrus_slice_with_step(parse):
    node = parse("a[(b_binding := b):(c_binding := c):(d_binding := d)]")
    assert get_bindings(node) == {"b_binding", "c_binding", "d_binding"}


def test_starred_bindings(parse):
    """
    ..code:: python

        Starred(expr value, expr_context ctx)
    """
    node = parse("*a")
    assert get_bindings(node) == set()


def test_starred_bindings_walrus(parse):
    node = parse("*(a_binding := a)")
    assert get_bindings(node) == {"a_binding"}


def test_name_bindings(parse):
    """
    ..code:: python

        Name(identifier id, expr_context ctx)
    """
    node = parse("a")
    assert get_bindings(node) == set()


def test_list_bindings(parse):
    """
    ..code:: python

        List(expr* elts, expr_context ctx)
    """
    node = parse("[a, b, c]")
    assert get_bindings(node) == set()


def test_list_bindings_unpack(parse):
    node = parse("{a, b, *rest}")
    assert get_bindings(node) == set()


def test_list_bindings_walrus(parse):
    node = parse("[a, (b := genb()), c]")
    assert get_bindings(node) == {"b"}


def test_list_bindings_walrus_unpack(parse):
    node = parse("[a, b, *(rest := other)]")
    assert get_bindings(node) == {"rest"}


def test_tuple_bindings(parse):
    """
    ..code:: python

        Tuple(expr* elts, expr_context ctx)
    """
    node = parse("(a, b, c)")
    assert get_bindings(node) == set()


def test_tuple_bindings_unpack(parse):
    node = parse("(a, b, *rest)")
    assert get_bindings(node) == set()


def test_tuple_bindings_walrus(parse):
    node = parse("(a, (b := genb()), c)")
    assert get_bindings(node) == {"b"}


def test_tuple_bindings_walrus_unpack(parse):
    node = parse("(a, b, *(rest := other))")
    assert get_bindings(node) == {"rest"}


def test_formatted_value_bindings(parse):
    """
    ..code:: python

        FormattedValue(expr value, int conversion, expr? format_spec)
    """
    node = parse("f'{a} {b} {c}'")
    assert get_bindings(node) == set()


def test_formatted_value_bindings_walrus(parse):
    node = parse("f'{a} {1 + (b := 1)} {c}'")
    assert get_bindings(node) == {"b"}


def test_formatted_value_bindings_format_spec_walrus(parse):
    node = parse("f'{a} {b:{0 + (c := 0.3)}} {d}'")
    assert get_bindings(node) == {"c"}


@match_statement
def test_match_statement_bindings_literal(parse):
    node = parse(
        """
        match a:
            case True:
                pass
        """
    )
    assert get_bindings(node) == set()


@match_statement
def test_match_statement_bindings_capture(parse):
    node = parse(
        """
        match a:
            case b:
                pass
        """
    )
    assert get_bindings(node) == {"b"}


@match_statement
def test_match_statement_bindings_wildcard(parse):
    node = parse(
        """
        match a:
            case _:
                pass
        """
    )
    assert get_bindings(node) == set()


@match_statement
def test_match_statement_bindings_constant(parse):
    node = parse(
        """
        match a:
            case 1:
                pass
        """
    )
    assert get_bindings(node) == set()


@match_statement
def test_match_statement_bindings_named_constant(parse):
    node = parse(
        """
        match a:
            case MyEnum.CONSTANT:
                pass
        """
    )
    assert get_bindings(node) == set()


@match_statement
def test_match_statement_bindings_sequence(parse):
    node = parse(
        """
        match a:
            case [b, *c, d, _]:
                pass
        """
    )
    assert get_bindings(node) == {"b", "c", "d"}


@match_statement
def test_match_statement_bindings_sequence_wildcard(parse):
    node = parse(
        """
        match a:
            case [*_]:
                pass
        """
    )
    assert get_bindings(node) == set()


@match_statement
def test_match_statement_bindings_mapping(parse):
    node = parse(
        """
        match a:
            case {"k1": "v1", "k2": b, "k3": _, **c}:
                pass
        """
    )
    assert get_bindings(node) == {"b", "c"}


@match_statement
def test_match_statement_bindings_class(parse):
    node = parse(
        """
        match a:
            case MyClass(0, b, x=_, y=c):
                pass
        """
    )
    assert get_bindings(node) == {"b", "c"}


@match_statement
def test_match_statement_bindings_or(parse):
    node = parse(
        """
        match a:
            case b | c:
                pass
        """
    )
    assert get_bindings(node) == {"b", "c"}


@match_statement
def test_match_statement_bindings_as(parse):
    node = parse(
        """
        match a:
            case b as c:
                pass
        """
    )
    assert get_bindings(node) == {"b", "c"}
