import pytest

from bazel_compile_commands.cli import _action_to_compile_command


# Parametrized test for action to compile command for both Linux and MSVC:
@pytest.mark.parametrize(
    "action, expected",
    [
        # Linux/gcc
        (
            {
                "arguments": [
                    "gcc",
                    "-iquote",
                    "external/foo",
                    "-isystem",
                    "external/bar",
                    "-c",
                    "src/foo.cc",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "gcc",
                    "-iquote",
                    "bazel-project/external/foo",
                    "-isystem",
                    "bazel-project/external/bar",
                    "-c",
                    "src/foo.cc",
                ],
                "file": "src/foo.cc",
            },
        ),
        # Windows/MSVC
        (
            {
                "arguments": [
                    "cl.exe",
                    "/Iexternal/foo",
                    "/external:Iexternal/bar",
                    "/c",
                    "src/foo.cc",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "cl.exe",
                    "/Ibazel-project/external/foo",
                    "/external:Ibazel-project/external/bar",
                    "/c",
                    "src/foo.cc",
                ],
                "file": "src/foo.cc",
            },
        ),
    ],
)
def test_action_to_compile_command(action, expected):
    result = _action_to_compile_command(
        "/good/project",
        "project",
        action,
    )
    assert result == expected
