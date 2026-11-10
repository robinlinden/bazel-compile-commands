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
        (
            # -c src.cc before arguments that should be patched.
            {
                "arguments": [
                    "clang++",
                    "-c",
                    "external/foo/src.cc",
                    "-isystem",
                    "external/bar",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "clang++",
                    "-c",
                    "bazel-project/external/foo/src.cc",
                    "-isystem",
                    "bazel-project/external/bar",
                ],
                "file": "bazel-project/external/foo/src.cc",
            },
        ),
        (
            # compiler in external/, --sysroot, and -B.
            {
                "arguments": [
                    "external/some/compiler",
                    "--sysroot=external/sysroot",
                    "-Bexternal/toolchain",
                    "--sysroot",
                    "external/split-sysroot",
                    "-B",
                    "external/split-toolchain",
                    "-c",
                    "src/foo.cc",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "bazel-project/external/some/compiler",
                    "--sysroot=bazel-project/external/sysroot",
                    "-Bbazel-project/external/toolchain",
                    "--sysroot",
                    "bazel-project/external/split-sysroot",
                    "-B",
                    "bazel-project/external/split-toolchain",
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
