import ast
import sys
import textwrap

import pytest


@pytest.fixture()
def parse():
    def _parse(source):
        source = textwrap.dedent(source)
        root = ast.parse(source)
        assert len(root.body) == 1
        node = root.body[0]
        if sys.version_info >= (3, 9):
            print(ast.dump(node, include_attributes=True, indent=2))
        else:
            print(ast.dump(node, include_attributes=True))
        return node

    return _parse
