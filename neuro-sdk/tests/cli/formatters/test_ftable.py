import pytest

from neuromation.cli.formatters.ftable import Align, ColumnWidth, _cell, _row, table


class TestColumnWidth:
    def test_negative_widths(self) -> None:
        with pytest.raises(ValueError, match="Width must be positive integer"):
            ColumnWidth(width=-1)
        with pytest.raises(ValueError, match="Min must be positive integer"):
            ColumnWidth(min=-1)
        with pytest.raises(ValueError, match="Max must be positive integer"):
            ColumnWidth(max=-1)


class TestCell:
    def test_align_left(self) -> None:
        assert list(_cell("text", 6, Align.LEFT)) == ["text  "]

    def test_align_right(self) -> None:
        assert list(_cell("text", 6, Align.RIGHT)) == ["  text"]

    def test_align_center(self) -> None:
        assert list(_cell("text", 6, Align.CENTER)) == [" text "]

    def test_align_none_is_left(self) -> None:
        assert list(_cell("text", 6, None)) == ["text  "]

    def test_align_unknown(self) -> None:
        with pytest.raises(ValueError, match=r"Unsupported align type:"):
            list(_cell("text", 6, "bottom"))  # type: ignore

    def test_empty_width(self) -> None:
        with pytest.raises(TypeError, match=r"positive integer"):
            list(_cell("text", 0, None)) == ["text"]

    def test_multiline(self) -> None:
        result = list(_cell("one two end", 4, None))
        assert result == ["one ", "two ", "end "]


class TestRow:
    def test_normal_case(self) -> None:
        result = list(_row(["one", "two"], [3, 3], [Align.LEFT, Align.LEFT], None, 3))
        assert result == ["one  two"]

    def test_partial_align(self) -> None:
        result = list(_row(["one", "two"], [3, 3], [Align.LEFT], None, 3))
        assert result == ["one  two"]

    def test_empty_align(self) -> None:
        result = list(_row(["one", "two"], [3, 3], (), None, 3))
        assert result == ["one  two"]

    def test_multiline(self) -> None:
        result = _row(["one", "two and more"], [3, 4], (), None, 3)
        assert result


class TestTable:
    def test_empty(self) -> None:
        result = list(table(()))
        assert result == []

    def test_simple(self) -> None:
        rows = [["a", "Alpha"], ["b", "Bravo"]]
        result = list(
            table(rows, widths=[ColumnWidth(width=10), ColumnWidth(width=10)])
        )
        print("\n" + "\n".join(result))
        assert len(result) == 2
        assert "a" in result[0]
        assert "Alpha" in result[0]
        assert "b" in result[1]
        assert "Bravo" in result[1]

    def test_multiline(self) -> None:
        rows = [
            ["a", "Alpha"],
            ["b", "Bravo and Delta And Epsilon"],
            ["two line here", "1213241324141413134"],
        ]
        result = list(
            table(
                rows,
                aligns=[Align.CENTER, Align.RIGHT],
                widths=[ColumnWidth(width=10), ColumnWidth(width=10)],
            )
        )
        assert len(result) == 6
        assert "a" in result[0]
        assert "Alpha" in result[0]
        assert "b" in result[1]
        assert "Bravo" in result[1]
        assert "Delta" in result[2]
        assert "Epsilon" in result[3]
        assert "here" in result[5]

    def test_no_any_width(self) -> None:
        rows = [["a", "Alpha"], ["b", "Bravo"]]
        result = list(table(rows))
        assert result == ["a  Alpha", "b  Bravo"]

    def test_max_table_width(self) -> None:
        rows = [["a", "Alpha"], ["b", "Bravo"]]
        result = list(table(rows, max_width=5))
        for line in result:
            assert len(line) == 5

    def test_partial_column_width(self) -> None:
        rows = [["a", "Alpha"], ["b", "Bravo"]]
        result = list(table(rows, widths=[ColumnWidth(), ColumnWidth(width=10)]))
        assert result == ["a  Alpha     ", "b  Bravo     "]

        result = list(table(rows, widths=[ColumnWidth(width=5)]))
        assert result == ["a      Alpha", "b      Bravo"]

        result = list(table(rows, widths=[ColumnWidth(width=5), ColumnWidth()]))
        assert result == ["a      Alpha", "b      Bravo"]

    def test_column_width_range_simple(self) -> None:
        rows = [["a", "Alpha"], ["b", "Bravo"]]
        result = list(table(rows, widths=[ColumnWidth(1, 1), ColumnWidth(1, 5)]))
        assert result == ["a  Alpha", "b  Bravo"]

    def test_column_width_range_violation(self) -> None:
        rows = [["12345"]]
        result = list(table(rows, widths=[ColumnWidth(2, 3)]))
        assert result == ["123", "45 "]

        rows = [["12"]]
        result = list(table(rows, widths=[ColumnWidth(3, 5)]))
        assert result == ["12".ljust(5)]

        rows = [["12"]]
        result = list(table(rows, widths=[ColumnWidth(min=3)]))
        assert result == ["12".ljust(3)]

        rows = [["123"]]
        result = list(table(rows, widths=[ColumnWidth(max=2)]))
        assert result == ["12", "3 "]

    def test_empty_first_columns(self) -> None:
        rows = [["a", "Alpha"], ["b", "Bravo"]]
        result = list(
            table(
                rows, max_width=2, widths=[ColumnWidth(width=1), ColumnWidth(width=2)]
            )
        )
        assert result == ["a ", "b "]
