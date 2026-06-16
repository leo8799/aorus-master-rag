from aorus_rag.pipeline import RagPipeline


def test_retrieval_keeps_byh_gpu_separate():
    pipeline = RagPipeline.from_spec_path()
    docs = pipeline.retrieve("BYH 的顯卡和 VRAM 是多少？", top_k=3)
    assert docs[0].document.metadata["model"] == "AORUS MASTER 16 BYH"
    assert docs[0].document.metadata["field"] == "顯示晶片"
    assert "RTX 5080" in docs[0].document.content
    assert "16GB GDDR7" in docs[0].document.content


def test_retrieval_finds_ports_for_english_question():
    pipeline = RagPipeline.from_spec_path()
    docs = pipeline.retrieve("How many Thunderbolt ports are listed and which versions are they?", top_k=5)
    joined = "\n".join(doc.document.content for doc in docs)
    assert "Thunderbolt 5" in joined
    assert "Thunderbolt 4" in joined


def test_retrieval_finds_battery_and_adapter():
    pipeline = RagPipeline.from_spec_path()
    docs = pipeline.retrieve("電池容量和變壓器瓦數？", top_k=6)
    fields = {doc.document.metadata["field"] for doc in docs}
    assert "電池" in fields
    assert "變壓器" in fields


def test_retrieval_compares_gpu_memory_before_system_memory():
    pipeline = RagPipeline.from_spec_path()
    docs = pipeline.retrieve("Compare BXH, BYH and BZH GPU memory.", top_k=5)
    joined = "\n".join(doc.document.content for doc in docs)
    assert "24GB GDDR7" in joined
    assert "16GB GDDR7" in joined
    assert "12GB GDDR7" in joined


def test_retrieval_deduplicates_common_specs_without_variant_intent():
    pipeline = RagPipeline.from_spec_path()
    docs = pipeline.retrieve("How many Thunderbolt ports are listed and which versions are they?", top_k=5)
    port_docs = [doc for doc in docs if doc.document.metadata["field"] == "連接埠"]
    assert len(port_docs) == 1
    assert "Thunderbolt 5" in port_docs[0].document.content
    assert "Thunderbolt 4" in port_docs[0].document.content
