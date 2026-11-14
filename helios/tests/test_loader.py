from helios.data import loader


def test_load_config_keys_present():
    cfg = loader.load_config()
    assert "latitude" in cfg
    assert "longitude" in cfg
    assert "pid" in cfg


def test_load_metadata_content():
    meta = loader.load_metadata()
    assert meta.get("project_name") == "Helios"
    assert "version" in meta
    assert isinstance(meta.get("authors"), list)
