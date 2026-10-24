import pytest

from engine.config import Settings
from engine.llm.schemas import AskAnswer
from engine.pipeline.ask import ask
from engine.pipeline.frames import decode
from engine.pipeline.session import SessionPipeline
from tests.factories import candidate_code, candidate_sheet
from tests.fakes import ScriptedModel, sheet_frame


@pytest.mark.parametrize("refs", [[], ["invented"], ["cell", "invented"]])
async def test_unsupported_answer_is_not_read_as_fact(refs: list[str]) -> None:
    model = ScriptedModel()
    pipe = SessionPipeline(model, Settings(llm_mode="replay"))
    doc = candidate_sheet(["Value"], [["100"]])
    assert doc.sheet is not None
    doc.sheet.rows[0].cells[0].id = "cell"
    model.push("ask", AskAnswer(answer="It is 999.", refs=refs))
    answer = await ask(pipe.reader, decode(sheet_frame([["100"]])), doc, "What is the value?")
    assert "999" not in answer.text and answer.refs == []


async def test_unclear_reference_cannot_be_spoken_as_a_confident_answer() -> None:
    model = ScriptedModel()
    pipe = SessionPipeline(model, Settings(llm_mode="replay"))
    doc = candidate_code(["x = 100"])
    assert doc.code is not None
    doc.code.lines[0].id = "line"
    doc.code.lines[0].uncertain = True
    model.push("ask", AskAnswer(answer="The value is 100.", refs=["line"]))
    answer = await ask(pipe.reader, decode(sheet_frame([["100"]])), doc, "What is x?")
    assert "100" not in answer.text and "unclear" in answer.text and answer.refs == ["line"]
