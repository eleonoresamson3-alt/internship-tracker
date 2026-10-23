from tracker import formations


def test_config_file_is_valid():
    items, problems = formations.load()
    assert problems == []
    assert {i["id"] for i in items} >= {"amf", "bmc", "cfa-1", "frm-1"}


def test_invalid_entries_are_reported(tmp_path):
    f = tmp_path / "f.yaml"
    f.write_text("""formations:
  - {id: a, nom: A, categorie: marches, priorite: 1, verifie_le: 2026-10-23}
  - {id: a, nom: B, categorie: sport, priorite: 5, heures: beaucoup, echeance: 31/12/2026, champ: x}
""", encoding="utf-8")
    items, problems = formations.load(f)
    text = " ".join(problems)
    assert items[0]["verifie_le"] == "2026-10-23"
    for word in ("used twice", "categorie", "priorite", "heures", "echeance", "unknown field"):
        assert word in text
