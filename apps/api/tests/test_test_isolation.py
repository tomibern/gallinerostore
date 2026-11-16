"""Cada worktree corre los tests contra su propia base y su propio bucket.

Si dos worktrees comparten la base de tests, sus transacciones se bloquean entre sí
al cargar el seed; si comparten el bucket, una corrida le vacía las imágenes a la otra.
"""

from pathlib import Path

from tests.isolation import checkout_name, isolated_bucket, isolated_database_url

URL = "postgresql+asyncpg://catalog:catalog@localhost:5433/gallinero_test"


def test_main_clone_has_no_checkout_name(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()

    assert checkout_name(tmp_path) is None


def test_worktree_is_named_after_its_folder(tmp_path: Path) -> None:
    root = tmp_path / "laughing-bouman-03008d"
    root.mkdir()
    (root / ".git").write_text("gitdir: /somewhere/.git/worktrees/laughing-bouman-03008d\n")

    assert checkout_name(root) == "laughing-bouman-03008d"


def test_without_checkout_name_resources_stay_the_same() -> None:
    assert isolated_database_url(URL, None) == URL
    assert isolated_bucket("test-media", None) == "test-media"


def test_worktree_gets_its_own_database() -> None:
    url = isolated_database_url(URL, "Laughing-Bouman.03008d")

    assert (
        url
        == "postgresql+asyncpg://catalog:catalog@localhost:5433/gallinero_test_laughing_bouman_03008d"
    )


def test_worktree_gets_its_own_bucket() -> None:
    bucket = isolated_bucket("test-media", "Laughing_Bouman.03008d")

    assert bucket == "test-media-laughing-bouman-03008d"


def test_names_fit_postgres_and_s3_limits() -> None:
    name = "x" * 100

    database = isolated_database_url(URL, name).rsplit("/", 1)[1]
    bucket = isolated_bucket("test-media", name)

    assert len(database) <= 63
    assert len(bucket) <= 63
    assert not bucket.endswith("-")


def test_password_survives_the_rename() -> None:
    url = isolated_database_url("postgresql+asyncpg://u:p%40ss@db:5432/t", "wt")

    assert url == "postgresql+asyncpg://u:p%40ss@db:5432/t_wt"
