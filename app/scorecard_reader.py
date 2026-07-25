"""Golf scorecard image extraction via the OpenAI Responses API.

This module is intentionally an adapter only.  It extracts aggregate cells from
uploaded scorecard images, but it does not calculate or correct any score.
"""

from __future__ import annotations

import base64
from difflib import SequenceMatcher
from io import BytesIO
import os
import unicodedata
from typing import List, Optional, Sequence

from openai import OpenAI
from PIL import Image, ImageOps
from pydantic import BaseModel, Field


SCORECARD_READER_PROMPT = """
# スコアカード画像の読み取りロジック

あなたはゴルフスコアカード画像の集計欄専用OCRです。複数画像は同じ
スコアカードを左右に分けたスクリーンショットの場合があります。同じ氏名の
情報を1人分にまとめてください。ただし、見えていない値を計算・推測・補正
してはいけません。

## 読み取り対象

各プレーヤーについて、ホールごとの数値は読み取らず、OUT、IN、EXTRA
（表示がある場合）、GROSS／合計欄だけを読み取ります。各集計欄から、
スコア、パット数、ゲームポイントを取得します。

通常ゲームはOUTとINです。EXTRAは独立して追加した9ホールであり、
OUT＋INの合計欄ではありません。EXTRAがなければnullにしてください。
EXTRAをOUT、IN、GROSSへ加算してはいけません。

## 数値の配置

例:
49 ₁₅
-12

上段左の大きい数字がスコア、右横の小さい数字がパット数、下段の符号付き
整数がゲームポイントです。-12と12、-10と10を明確に区別してください。

## 画像の扱い

EXIF方向と90度回転を考慮し、表を横向きとして解釈してください。氏名欄を
基準にプレーヤー行を特定し、上段（スコア・パット数）と下段
（ゲームポイント）を1セットとして扱ってください。人数を4名に固定しては
いけません。OUT、IN、EXTRA、GROSSの集計セルだけを対象にしてください。

## セル内の読み分け

- スコア: 上段左、大きい1〜3桁整数
- パット数: 上段右、小さい1〜2桁整数。スコアと連結しない
- ゲームポイント: 下段、符号付き整数。マイナス記号を必ず保持

Unicodeのマイナス記号・全角マイナス・長音は、数値領域に限り半角ハイフン
へ正規化してください。全角数字は半角へ、空白・改行・カンマは除去して
ください。数値だけの領域では O/o→0、I/l/|→1、S→5、B→8 を補正候補に
できますが、不確かな場合は低信頼度にしてください。

## GROSS／合計欄

GROSSまたは合計欄も、スコア・合計パット数・合計ゲームポイントを画像から
直接読み取ってください。OUTやINから再計算してはいけません。読み取り処理
では既存ロジックによる計算や整合補正を一切行いません。

## 信頼度

各値に0〜1のconfidenceを付けてください。セル境界への重なり、小さく不鮮明
なパット数、不鮮明なマイナス、数字の連結、複数候補がある場合は低信頼度と
し、review_reasonに短い理由を記録してください。値を勝手に確定・補正せず、
読めない値はnullにしてください。

## 読み取り対象外

各ホールのスコア・パット数・ゲームポイント、Par、距離、色、バーディー等
の判定、NET、HDCP、ティー名称は読み取りません。

出力スキーマに厳密に従い、画像に実際に表示された集計値だけを返してください。
""".strip()


class OCRInteger(BaseModel):
    value: Optional[int]
    confidence: float = Field(ge=0.0, le=1.0)
    review_reason: Optional[str]


class AggregateCell(BaseModel):
    score: OCRInteger
    putts: OCRInteger
    game_point: OCRInteger


class PlayerScorecardTotals(BaseModel):
    player_name: str
    out: Optional[AggregateCell]
    in_: Optional[AggregateCell] = Field(alias="in")
    extra: Optional[AggregateCell]
    total: Optional[AggregateCell]

    model_config = {"populate_by_name": True}


class ScorecardExtraction(BaseModel):
    players: List[PlayerScorecardTotals]
    warnings: List[str]


def _prepare_image(image_bytes: bytes) -> str:
    """Apply safe orientation/size normalization and return a JPEG data URL."""
    with Image.open(BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        # The supplied mobile screenshots contain a landscape table rotated inside
        # a portrait canvas. Rotate only that clearly portrait-shaped case.
        if image.height > image.width * 1.25:
            image = image.rotate(90, expand=True)
        image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="JPEG", quality=92, optimize=True)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def read_scorecard_images(
    image_payloads: Sequence[bytes],
    participant_names: Sequence[str],
    *,
    client: Optional[OpenAI] = None,
    model: Optional[str] = None,
) -> ScorecardExtraction:
    """Extract aggregate cells without performing score calculations."""
    if not image_payloads:
        raise ValueError("解析する画像がありません。")
    if len(image_payloads) > 4:
        raise ValueError("一度に解析できる画像は4枚までです。")
    if not os.getenv("OPENAI_API_KEY") and client is None:
        raise RuntimeError("OPENAI_API_KEY が設定されていません。")

    api_client = client or OpenAI()
    content = [
        {
            "type": "input_text",
            "text": (
                SCORECARD_READER_PROMPT
                + "\n\n今回の登録参加者候補:\n- "
                + "\n- ".join(participant_names)
                + "\n氏名候補は照合の参考にのみ使い、画像にない人物を作らないでください。"
            ),
        }
    ]
    for payload in image_payloads:
        content.append(
            {
                "type": "input_image",
                "image_url": _prepare_image(payload),
                "detail": "high",
            }
        )

    response = api_client.responses.parse(
        model=model or os.getenv("OPENAI_VISION_MODEL", "gpt-5.6"),
        input=[{"role": "user", "content": content}],
        text_format=ScorecardExtraction,
    )
    if response.output_parsed is None:
        raise RuntimeError("画像認識AIから読み取り結果を取得できませんでした。")
    return response.output_parsed


def normalize_player_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    return "".join(character for character in normalized if not character.isspace())


def match_participant_name(
    extracted_name: str,
    participant_names: Sequence[str],
    *,
    threshold: float = 0.58,
) -> Optional[str]:
    """Return a unique best participant match, or None when it is ambiguous."""
    needle = normalize_player_name(extracted_name)
    if not needle:
        return None
    exact = [name for name in participant_names if normalize_player_name(name) == needle]
    if len(exact) == 1:
        return exact[0]

    ranked = sorted(
        (
            SequenceMatcher(None, needle, normalize_player_name(name)).ratio(),
            name,
        )
        for name in participant_names
    )
    if not ranked or ranked[-1][0] < threshold:
        return None
    if len(ranked) > 1 and ranked[-1][0] - ranked[-2][0] < 0.08:
        return None
    return ranked[-1][1]


def confidence_floor(player: PlayerScorecardTotals) -> float:
    values = []
    for cell in (player.out, player.in_, player.extra, player.total):
        if cell is None:
            continue
        for field in (cell.score, cell.putts, cell.game_point):
            if field.value is not None:
                values.append(field.confidence)
    return min(values) if values else 0.0


def extraction_to_review_rows(
    extraction: ScorecardExtraction,
    participant_names: Sequence[str],
) -> List[dict]:
    """Flatten the OCR result for an editable Streamlit confirmation table."""

    def value(cell: Optional[AggregateCell], field: str):
        return getattr(cell, field).value if cell is not None else None

    rows = []
    for player in extraction.players:
        matched = match_participant_name(player.player_name, participant_names)
        rows.append(
            {
                "反映": matched is not None,
                "画像の氏名": player.player_name,
                "参加者": matched or "選択してください",
                "OUTスコア": value(player.out, "score"),
                "OUTパット": value(player.out, "putts"),
                "OUTゲームポイント": value(player.out, "game_point"),
                "INスコア": value(player.in_, "score"),
                "INパット": value(player.in_, "putts"),
                "INゲームポイント": value(player.in_, "game_point"),
                "EXTRAスコア": value(player.extra, "score"),
                "EXTRAパット": value(player.extra, "putts"),
                "EXTRAゲームポイント": value(player.extra, "game_point"),
                "GROSS": value(player.total, "score"),
                "合計パット": value(player.total, "putts"),
                "合計ゲームポイント": value(player.total, "game_point"),
                "最低信頼度": round(confidence_floor(player), 2),
            }
        )
    return rows

