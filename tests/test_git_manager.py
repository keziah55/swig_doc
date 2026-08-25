from swig_doc.swig_markdown_generator import GitManager

import pytest


@pytest.fixture(scope="session")
def swig_path(tmp_path_factory):

    tmp_path = tmp_path_factory.mktemp("tmp_swig_")
    assert tmp_path.exists()
    _, err_msg = GitManager._git_command("clone", "https://github.com/swig/swig.git", tmp_path)
    assert err_msg is None

    git_manager = GitManager(tmp_path)
    git_manager.setup()

    return git_manager.repo_path


@pytest.mark.parametrize(
    "branch, expected",
    [
        ("main", "main"),
        ("123-branch_name/4.5", "123-branch_name/4.5"),
        ("(HEAD detached at v4.4.1)", "v4.4.1"),
    ],
)
def test_get_branch(branch, expected, monkeypatch, swig_path):

    def mock_response(*args):
        return "\n".join(["a-branch", f"* {branch}", "another_branch"])

    monkeypatch.setattr(GitManager, "_git_repo_command", mock_response)

    git_manager = GitManager(target_dir=swig_path)
    git_manager.setup()

    assert git_manager._get_git_branch() == expected


def test_git_repo_command_static_error(monkeypatch, swig_path):

    git_manager = GitManager(target_dir=swig_path)
    git_manager.setup()

    with pytest.raises(
        Exception,
        match=(
            r"git this_is_not_a_command a b c failed with error "
            r"'git: 'this_is_not_a_command' is not a git command. See 'git --help'."
        ),
    ):
        git_manager._git_repo_command("this_is_not_a_command", "a", "b", "c")
