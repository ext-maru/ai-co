import pytest

from bs4.element import (
    CData,
    Comment,
    Declaration,
    Doctype,
    NavigableString,
    RubyParenthesisString,
    RubyTextString,
    Script,
    Stylesheet,

)

from . import SoupTest

class TestNavigableString(SoupTest):
    def test_text_acquisition_methods(self):
        # These methods are intended for use against Tag, but they
        # work on NavigableString as well,

        s = NavigableString("fee ")
        cdata = CData("fie ")
        comment = Comment("foe ")

        assert "fee " == s.get_text()
        assert "fee " == s.string
        assert "fee" == s.get_text(strip=True)
        assert ["fee "] == list(s.strings)
        assert ["fee"] == list(s.stripped_strings)
        assert ["fee "] == list(s._all_strings())

        assert "fie " == cdata.get_text()
        assert "fie " == cdata.string
        assert "fie" == cdata.get_text(strip=True)
        assert ["fie "] == list(cdata.strings)
        assert ["fie"] == list(cdata.stripped_strings)
        assert ["fie "] == list(cdata._all_strings())

        # Since a Comment isn't normally considered 'text',
        # these methods generally do nothing.
        assert "" == comment.get_text()
        assert [] == list(comment.strings)
        assert [] == list(comment.stripped_strings)
        assert [] == list(comment._all_strings())

        # Unless you specifically say that comments are okay.
        assert "foe" == comment.get_text(strip=True, types=Comment)
        assert "foe " == comment.get_text(types=(Comment, NavigableString))

    def test_string_has_immutable_name_property(self):
        # string.name is defined as None and can't be modified
        string = self.soup("s").string
        assert None is string.name
        with pytest.raises(AttributeError):
            string.name = "foo"

        string = self.soup("the string").string

        # Try to access an HTML attribute of a NavigableString and get a helpful exception.
        with pytest.raises(TypeError) as e:
            string["attr"]
        assert str(e.value) == "string indices must be integers, not 'str'. Are you treating a NavigableString like a Tag?"

        # Normal string access works.
        assert string[2] == "e"
        assert string[2:5] == "e s"

class TestNavigableStringSubclasses(SoupTest):
    def test_cdata(self):
        # None of the current builders turn CDATA sections into CData
        # objects, but you can create them manually.
        soup = self.soup("")
        cdata = CData("foo")
        soup.insert(1, cdata)
        assert str(soup) == "<![CDATA[foo]]>"
        assert soup.find(string="foo") == "foo"
        assert soup.contents[0] == "foo"

    def test_cdata_is_never_formatted(self):
        """Text inside a CData object is passed into the formatter.

        But the return value is ignored.
        """

        self.count = 0

        def increment(*args):
            self.count += 1
            return "BITTER FAILURE"

        soup = self.soup("")
        cdata = CData("<><><>")
        soup.insert(1, cdata)
        assert b"<![CDATA[<><><>]]>" == soup.encode(formatter=increment)
        assert 1 == self.count

    def test_doctype_ends_in_newline(self):
        # Unlike other NavigableString subclasses, a DOCTYPE always ends
        # in a newline.
        doctype = Doctype("foo")
        soup = self.soup("")
        soup.insert(1, doctype)
        assert soup.encode() == b"<!DOCTYPE foo>\n"

    def test_declaration(self):
        d = Declaration("foo")
        assert "<?foo?>" == d.output_ready()

    def test_default_string_containers(self):
        # In some cases, we use different NavigableString subclasses for
        # the same text in different tags.
        soup = self.soup("<div>text</div><script>text</script><style>text</style>")
        assert [NavigableString, Script, Stylesheet] == [
            x.__class__ for x in soup.find_all(string=True)
        ]

        soup = self.soup(

        )
        assert all(

        )

        # NavigableString.

        assert isinstance(outside, NavigableString)

        # NavigableString subclasses of _other_ types, such as
        # Comment.

        soup = self.soup(markup)

    def test_ruby_strings(self):
        markup = "<ruby>漢 <rp>(</rp><rt>kan</rt><rp>)</rp> 字 <rp>(</rp><rt>ji</rt><rp>)</rp></ruby>"
        soup = self.soup(markup)
        assert isinstance(soup.rp.string, RubyParenthesisString)
        assert isinstance(soup.rt.string, RubyTextString)

        # Just as a demo, here's what this means for get_text usage.
        assert "漢字" == soup.get_text(strip=True)
        assert "漢(kan)字(ji)" == soup.get_text(
            strip=True, types=(NavigableString, RubyTextString, RubyParenthesisString)
        )
