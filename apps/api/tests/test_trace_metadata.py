from app.api.documentary import _adapter_response_metadata, _json_trace_hash


class DummyClient:
    pass


def test_json_trace_hash_is_stable_for_key_order():
    first = _json_trace_hash({"query": "test", "top_k": 5})
    second = _json_trace_hash({"top_k": 5, "query": "test"})

    assert first == second
    assert len(first) == 64


def test_json_trace_hash_changes_when_payload_changes():
    first = _json_trace_hash({"query": "test", "top_k": 5})
    second = _json_trace_hash({"query": "test", "top_k": 10})

    assert first != second


def test_adapter_response_metadata_uses_client_class_name():
    metadata = _adapter_response_metadata(DummyClient())

    assert metadata == {"adapter": "DummyClient"}


def test_adapter_response_metadata_merges_provider_raw_metadata():
    metadata = _adapter_response_metadata(
        DummyClient(),
        {"adapter": "ProviderAdapter", "dimension": 1024},
    )

    assert metadata == {"adapter": "ProviderAdapter", "dimension": 1024}
