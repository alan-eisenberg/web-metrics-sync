from automation.state_store import RunState, load_state, save_state


def test_save_and_load_state_roundtrip(tmp_path):
    state_path = tmp_path / "run_state.json"
    original = RunState(run_id="r1", state="PROMPT_ONE", email="a@b.c")
    save_state(state_path, original)

    loaded = load_state(state_path)
    assert loaded is not None
    assert loaded.run_id == "r1"
    assert loaded.state == "PROMPT_ONE"
    assert loaded.email == "a@b.c"
