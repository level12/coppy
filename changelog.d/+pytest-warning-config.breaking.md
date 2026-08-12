Add a `pytest.ini` to generated project roots and move pytest warning configuration there
from `tests/conftest.py` so the filters apply during every pytest lifecycle phase,
including configuration and collection
([#96](https://github.com/level12/coppy/issues/96)).

This makes the intended warnings-as-errors policy effective. After updating, warnings that
previously appeared only in pytest's warning summary may fail the test run.

**Manual update required:** migrate any project-specific `warnings.filterwarnings()` calls
from `tests/conftest.py` to `pytest.ini`'s `filterwarnings` list. Put the general `error`
rule first and more specific `ignore` rules afterward because the last matching rule takes
precedence.
