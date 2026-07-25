from io import BytesIO
from pathlib import Path
import sys
from types import SimpleNamespace

from PIL import Image

APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from scorecard_reader import (
    AggregateCell,
    OCRInteger,
    PlayerScorecardTotals,
    SCORECARD_READER_PROMPT,
    ScorecardExtraction,
    extraction_to_review_rows,
    match_participant_name,
    read_scorecard_images,
)


def reading(value, confidence=0.95):
    return OCRInteger(value=value, confidence=confidence, review_reason=None)


def cell(score, putts, point, confidence=0.95):
    return AggregateCell(
        score=reading(score, confidence),
        putts=reading(putts, confidence),
        game_point=reading(point, confidence),
    )


def test_name_matching_normalizes_spaces_and_handles_small_ocr_errors():
    names = ["荒巻 典芳", "吉井 孝樹", "福澤 忠"]
    assert match_participant_name("荒巻　典芳", names) == "荒巻 典芳"
    assert match_participant_name("吉井 孝樹", names) == "吉井 孝樹"
    assert match_participant_name("", names) is None


def test_review_rows_keep_extra_and_total_separate_from_out_and_in():
    extraction = ScorecardExtraction(
        players=[
            PlayerScorecardTotals(
                player_name="荒巻 典芳",
                out=cell(49, 15, -12),
                in_=cell(48, 13, -13),
                extra=cell(45, 14, 8),
                total=cell(97, 28, -25),
            )
        ],
        warnings=[],
    )

    row = extraction_to_review_rows(extraction, ["荒巻 典芳"])[0]

    assert row["OUTスコア"] == 49
    assert row["INスコア"] == 48
    assert row["EXTRAスコア"] == 45
    assert row["GROSS"] == 97
    assert row["OUTスコア"] + row["INスコア"] == row["GROSS"]
    assert row["GROSS"] != row["GROSS"] + row["EXTRAスコア"]


def test_prompt_forbids_recalculation_and_hole_level_ocr():
    assert "再計算してはいけません" in SCORECARD_READER_PROMPT
    assert "EXTRAをOUT、IN、GROSSへ加算してはいけません" in SCORECARD_READER_PROMPT
    assert "各ホールのスコア・パット数・ゲームポイント" in SCORECARD_READER_PROMPT
    assert "NET" in SCORECARD_READER_PROMPT


def test_api_adapter_sends_images_and_returns_structured_result():
    expected = ScorecardExtraction(
        players=[
            PlayerScorecardTotals(
                player_name="荒巻 典芳",
                out=cell(49, 15, -12),
                in_=cell(48, 13, -13),
                extra=None,
                total=cell(97, 28, -25),
            )
        ],
        warnings=[],
    )
    calls = []

    class FakeResponses:
        def parse(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_parsed=expected)

    fake_client = SimpleNamespace(responses=FakeResponses())
    image = Image.new("RGB", (360, 805), color="white")
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")

    result = read_scorecard_images(
        [image_bytes.getvalue()],
        ["荒巻 典芳"],
        client=fake_client,
        model="test-vision-model",
    )

    assert result == expected
    assert calls[0]["model"] == "test-vision-model"
    content = calls[0]["input"][0]["content"]
    assert content[0]["type"] == "input_text"
    assert content[1]["type"] == "input_image"
    assert content[1]["detail"] == "high"
    assert content[1]["image_url"].startswith("data:image/jpeg;base64,")
