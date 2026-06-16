from aorus_rag.data import load_spec
from aorus_rag.query import QueryParser
from aorus_rag.text import normalize_traditional_output


def test_parser_detects_variant_and_gpu_field():
    parser = QueryParser(load_spec())
    intent = parser.parse("BYH 的顯卡和 VRAM 是多少？")
    assert intent.models == ("AORUS MASTER 16 BYH",)
    assert "顯示晶片" in intent.fields


def test_parser_detects_english_variant_alias():
    parser = QueryParser(load_spec())
    intent = parser.parse("Which model has RTX 5070 Ti and what is its maximum graphics power?")
    assert intent.models == ("AORUS MASTER 16 BZH",)
    assert "顯示晶片" in intent.fields


def test_parser_detects_multiple_fields():
    parser = QueryParser(load_spec())
    intent = parser.parse("電池容量和變壓器瓦數？")
    assert "電池" in intent.fields
    assert "變壓器" in intent.fields


def test_parser_treats_gpu_memory_as_graphics_field():
    parser = QueryParser(load_spec())
    intent = parser.parse("Compare BXH, BYH and BZH GPU memory.")
    assert "顯示晶片" in intent.fields
    assert "記憶體" not in intent.fields


def test_common_simplified_characters_are_normalized_for_traditional_output():
    assert normalize_traditional_output("显卡与变压器瓦数") == "顯卡與變壓器瓦數"
