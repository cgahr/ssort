import sys

import pytest

from ssort._statements._method_requirements import get_method_requirements

match_statement = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="match statements were introduced in python 3.10",
)


def test_staticmethod_requirements(parse):
    reqs = parse(
        """
        @staticmethod
        def function():
            return Class.attr
        """
    )
    assert get_method_requirements(reqs) == set()


def test_classmethod_requirements(parse):
    reqs = parse(
        """
        @classmethod
        def function(cls, arg, **kwargs):
            return cls.attr + arg.argattr
        """
    )
    assert get_method_requirements(reqs) == {"attr"}


def testparse(parse):
    reqs = parse(
        """
        def function(self, something):
            return self.a + self.b - something.other
        """
    )
    assert get_method_requirements(reqs) == {"a", "b"}


def test_assignparse_none(parse):
    """
    ..code:: python

        Assign(expr* targets, expr value, string? type_comment)
    """
    reqs = parse(
        """
        def fun(self):
            a = b
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assignparse_target(parse):
    """
    ..code:: python

        Assign(expr* targets, expr value, string? type_comment)
    """
    reqs = parse(
        """
        def fun(self):
            self.a = b
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assignparse_value(parse):
    """
    ..code:: python

        Assign(expr* targets, expr value, string? type_comment)
    """
    reqs = parse(
        """
        def fun(self):
            a = self.b
        """
    )
    assert get_method_requirements(reqs) == {"b"}


def test_assign_method_attribute_requirements_none(parse):
    reqs = parse(
        """
        def fun(self):
            a.b = c
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assign_method_attribute_requirements(parse):
    reqs = parse(
        """
        def fun(self):
            self.a.b = c
        """
    )
    assert get_method_requirements(reqs) == {"a"}


def test_assign_method_star_requirements_none(parse):
    reqs = parse(
        """
        def fun(self):
            *a = c
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assign_method_star_requirements(parse):
    reqs = parse(
        """
        def fun(self):
            *self.a = c
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assign_method_star_attribute_requirements_none(parse):
    reqs = parse(
        """
        def fun(self):
            *a.b = c
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assign_method_star_attribute_requirements(parse):
    reqs = parse(
        """
        def fun(self):
            *self.a.b = c
        """
    )
    assert get_method_requirements(reqs) == {"a"}


def test_assign_method_subscript_requirements_none(parse):
    reqs = parse(
        """
        def fun(self):
            a[b] = c
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assign_method_subscript_requirements_source(parse):
    reqs = parse(
        """
        def fun(self):
            self.a[b] = c
        """
    )
    assert get_method_requirements(reqs) == {"a"}


def test_assign_method_subscript_requirements_key(parse):
    reqs = parse(
        """
        def fun(self):
            a[self.b] = c
        """
    )
    assert get_method_requirements(reqs) == {"b"}


def test_assign_method_tuple_requirements_none(parse):
    reqs = parse(
        """
        def fun(self):
            a, b[c], d.e, *f = g
        """
    )
    assert get_method_requirements(reqs) == set()


def test_assign_method_tuple_requirements(parse):
    reqs = parse(
        """
        def fun(self):
            self.a, self.b[self.c], self.d.e, *self.f = self.g
        """
    )
    assert get_method_requirements(reqs) == {"b", "c", "d", "g"}


def testparse_inner_function(parse):
    reqs = parse(
        """
        def fun(self):
            def inner():
                return self.a
            return inner()
        """
    )
    assert get_method_requirements(reqs) == {"a"}


def testparse_formatted_value(parse):
    reqs = parse(
        """
        def fun(self):
            return f"{self.a} {self.b} {self.c}"
        """
    )
    assert get_method_requirements(reqs) == {"a", "b", "c"}


def testparse_list_comp(parse):
    reqs = parse(
        """
        def fun(self):
            return [self.a for self.b.c in self.d]
        """
    )
    assert get_method_requirements(reqs) == {"a", "b", "d"}


def testparse_set_comp(parse):
    reqs = parse(
        """
        def fun(self):
            return {self.a for self.b.c in self.d}
        """
    )
    assert get_method_requirements(reqs) == {"a", "b", "d"}


def testparse_dict_comp(parse):
    reqs = parse(
        """
        def fun(self):
            return {self.a: self.b for self.c.d in self.e}
        """
    )
    assert get_method_requirements(reqs) == {"a", "b", "c", "e"}


def testparse_generator_exp(parse):
    reqs = parse(
        """
        def fun(self):
            return (self.a for self.b.c in self.d)
        """
    )
    assert get_method_requirements(reqs) == {"a", "b", "d"}


def testparse_lambda_default(parse):
    reqs = parse(
        """
        def fun(self):
            return lambda x=self.a: self.b
        """
    )
    assert get_method_requirements(reqs) == {"a", "b"}


def testparse_with(parse):
    reqs = parse(
        """
        def fun(self):
            with self.a as self.b.c:
                pass
        """
    )
    assert get_method_requirements(reqs) == {"a", "b"}


def testparse_ann_assign(parse):
    reqs = parse(
        """
        def fun(self):
            self.a: self.b = self.c
        """
    )
    assert get_method_requirements(reqs) == {"b", "c"}


@match_statement
def testparse_match_statement(parse):
    reqs = parse(
        """
        def fun(self):
            match self.a:
                case self.b:
                    pass
        """
    )
    assert get_method_requirements(reqs) == {"a", "b"}
