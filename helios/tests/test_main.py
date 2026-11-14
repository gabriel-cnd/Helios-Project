import pytest


def test_main_entrypoint_skipped():
    pytest.skip("Entrée UI Qt non testée automatiquement (dépendance GUI manquante).")
