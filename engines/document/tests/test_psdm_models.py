import sys
sys.path.insert(0, "/home/sjfs/autogen_project/multi_agent_infra")

import pytest

from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.psdm_models import (
    Animation, AnimationType, CustomShow, CustomShowCollection, HandoutMaster,
    HyperlinkAction, MediaReference, NotesMaster, NotesSlide, PSDMDocument,
    Placeholder, PlaceholderType, PresentationProperties, PresentationSection,
    PresentationTransition, ShowType, Slide, SlideComment, SlideLayout,
    SlideMaster, Theme, TransitionType, TriggerType,
)
from engines.document.models.usdm_models import (
    RichTextContent, ShapeContent,
)

pytestmark = pytest.mark.asyncio


class TestPSDMModelImports:
    def test_import_all_model_classes(self):
        assert PSDMDocument is not None
        assert Slide is not None
        assert SlideMaster is not None

    def test_model_instantiation(self):
        props = PresentationProperties(slide_width=9144000, slide_height=6858000)
        assert props.slide_width == 9144000
        assert props.slide_height == 6858000

    def test_psdm_document_creation(self):
        doc = PSDMDocument(
            title="Test Presentation",
            document_id="test-psdm-001",
            media_type=MEDIA_TYPES["pptx"],
        )
        assert doc.title == "Test Presentation"
        assert doc.slides == []
        assert doc.slide_masters == {}
        assert doc.handout_master is None
        assert doc.notes_master is None
        assert doc.theme is None
        assert doc.custom_shows.shows == []
        assert doc.sections == []


class TestPresentationProperties:
    def test_default_values(self):
        props = PresentationProperties()
        assert props.slide_width is None
        assert props.slide_height is None
        assert props.auto_advance is False
        assert props.show_type == ShowType.DEFAULT
        assert props.loop is False

    def test_print_settings(self):
        props = PresentationProperties(
            paper_size="letter",
            orientation="landscape",
            scale=100,
            first_slide_number=1,
            paper_source="default",
        )
        assert props.paper_size == "letter"
        assert props.orientation == "landscape"
        assert props.scale == 100
        assert props.first_slide_number == 1

    def test_sync_settings(self):
        props = PresentationProperties(
            sync_id="sync-001",
            scroll_outside=True,
            zoom_outside=False,
        )
        assert props.sync_id == "sync-001"
        assert props.scroll_outside is True
        assert props.zoom_outside is False


class TestSlideModel:
    def test_slide_creation(self):
        slide = Slide(slide_id="slide1")
        assert slide.slide_id == "slide1"
        assert slide.elements == []
        assert slide.transition == PresentationTransition()
        assert slide.animations == []
        assert slide.notes is None
        assert slide.comments == []
        assert slide.media_references == []

    def test_slide_with_properties(self):
        slide = Slide(
            slide_id="slide1",
            name="Title Slide",
            background_color="#FFFFFF",
            show_header=True,
            show_footer=False,
            show_date=True,
            show_slide_number=True,
        )
        assert slide.name == "Title Slide"
        assert slide.background_color == "#FFFFFF"
        assert slide.show_header is True
        assert slide.show_footer is False
        assert slide.show_date is True
        assert slide.show_slide_number is True

    def test_slide_transition(self):
        slide = Slide(
            slide_id="slide1",
            transition=PresentationTransition(
                type=TransitionType.FADE,
                duration_ms=1000.0,
                advance_after_ms=3000.0,
            ),
        )
        assert slide.transition.type == TransitionType.FADE
        assert slide.transition.duration_ms == 1000.0
        assert slide.transition.advance_after_ms == 3000.0


class TestSlideMasterAndLayout:
    def test_slide_layout_creation(self):
        layout = SlideLayout(name="Title Slide")
        assert layout.name == "Title Slide"
        assert layout.master_name is None
        assert layout.placeholders == []

    def test_slide_master_creation(self):
        master = SlideMaster(name="Office Theme")
        assert master.name == "Office Theme"
        assert master.layouts == {}
        assert master.default_text_style is None

    def test_placeholder_creation(self):
        shape = ShapeContent(shape_type="rectangle", x=0, y=0, width=100, height=100)
        ph = Placeholder(idx=0, type=PlaceholderType.TITLE, shape=shape)
        assert ph.idx == 0
        assert ph.type == PlaceholderType.TITLE
        assert ph.shape == shape

    def test_layout_with_placeholder(self):
        shape = ShapeContent(shape_type="rectangle", x=0, y=0, width=100, height=100)
        ph = Placeholder(idx=0, type=PlaceholderType.TITLE, shape=shape)
        layout = SlideLayout(name="Title", placeholders=[ph])
        assert len(layout.placeholders) == 1
        assert layout.placeholders[0].type == PlaceholderType.TITLE


class TestHandoutAndNotesMasters:
    def test_handout_master_creation(self):
        hm = HandoutMaster(name="Handout Master")
        assert hm.name == "Handout Master"
        assert hm.background_color is None

    def test_notes_master_creation(self):
        nm = NotesMaster(name="Notes Master")
        assert nm.name == "Notes Master"
        assert nm.default_text_style is None


class TestTheme:
    def test_theme_creation(self):
        theme = Theme(
            name="Office Theme",
            color_scheme={"dk1": "#000000", "lt1": "#FFFFFF"},
            major_font="Calibri",
            minor_font="Calibri",
        )
        assert theme.name == "Office Theme"
        assert theme.color_scheme["dk1"] == "#000000"
        assert theme.major_font == "Calibri"

    def test_theme_empty(self):
        theme = Theme()
        assert theme.name is None
        assert theme.color_scheme == {}
        assert theme.major_font is None


class TestCustomShows:
    def test_custom_show_creation(self):
        show = CustomShow(name="Intro", slide_ids=["slide1", "slide2"])
        assert show.name == "Intro"
        assert show.slide_ids == ["slide1", "slide2"]

    def test_custom_show_collection(self):
        collection = CustomShowCollection()
        assert collection.shows == []

        collection.shows.append(CustomShow(name="Intro", slide_ids=["slide1"]))
        assert len(collection.shows) == 1


class TestAnimations:
    def test_animation_creation(self):
        anim = Animation(
            target_shape_id="shape1",
            type=AnimationType.FADE_IN,
            duration_ms=500.0,
            delay_ms=0.0,
            trigger=TriggerType.ON_CLICK,
        )
        assert anim.target_shape_id == "shape1"
        assert anim.type == AnimationType.FADE_IN
        assert anim.trigger == TriggerType.ON_CLICK


class TestMediaAndNotes:
    def test_media_reference_creation(self):
        ref = MediaReference(
            relationship_id="rId1",
            media_type="audio",
            mime_type="audio/mp3",
            start_time=0.0,
            end_time=10.0,
            loop=False,
        )
        assert ref.relationship_id == "rId1"
        assert ref.media_type == "audio"
        assert ref.mime_type == "audio/mp3"

    def test_notes_slide_creation(self):
        notes = NotesSlide(
            text=RichTextContent(spans=[]),
            plain_text="",
        )
        assert notes.text.spans == []
        assert notes.plain_text == ""


class TestSlideComment:
    def test_comment_creation(self):
        comment = SlideComment(
            comment_id="1",
            author="John Doe",
            date="2026-01-01T00:00:00",
            text="This is a comment",
            position_x=100.0,
            position_y=200.0,
        )
        assert comment.comment_id == "1"
        assert comment.author == "John Doe"
        assert comment.text == "This is a comment"


class TestPresentationSection:
    def test_section_creation(self):
        section = PresentationSection(
            name="Section 1",
            first_slide_id="slide1",
        )
        assert section.name == "Section 1"
        assert section.first_slide_id == "slide1"


class TestHyperlinkAction:
    def test_hyperlink_creation(self):
        action = HyperlinkAction(
            target="https://example.com",
            tooltip="Click here",
            show_and_return=False,
        )
        assert action.target == "https://example.com"
        assert action.tooltip == "Click here"
