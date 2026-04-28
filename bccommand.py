#!/usr/bin/env python3

import subprocess
import json
import time
import sys
import pathlib
import os


def main():
    start_time = time.time()

    project_root = subprocess.check_output(
        ["bazel", "info", "workspace"], text=True
    ).strip()

    project_name = project_root.rsplit("/")[-1]

    # Bazel's compile commands are based from bazel-<project_name>, and that's a
    # mirror of the workspace root, except it also has all external dependencies
    # in an external/ subdirectory. To make the compile commands work without
    # modification, we need to create a symlink from external/ to
    # bazel-<project_name>/external.
    # TODO(robinlinden): Patch the paths in the compile commands instead.
    is_windows = os.name == "nt"
    src = pathlib.Path("external")
    dst = pathlib.Path(project_root) / f"bazel-{project_name}" / "external"
    if not pathlib.Path("external").exists():
        if is_windows:
            subprocess.run(f'mklink /J "{src}" "{dst}"', check=True, shell=True)
        else:
            src.symlink_to(dst)
        print(f"Created symlink from '{src}' to '{dst}'", file=sys.stderr)
    else:
        # Check if the symlink points to the correct location, and warn if it doesn't.
        symlink_ok = False
        if is_windows:
            # Check that src/ and dst/ contain the same folders. Windows doesn't like symlinks. :(
            src_folders = set(p.name for p in src.iterdir())
            dst_folders = set(p.name for p in dst.iterdir())
            symlink_ok = src_folders == dst_folders
        else:
            symlink_ok = src.is_symlink() and src.resolve() == dst.resolve()

        if not symlink_ok:
            print(
                f"Warning: 'external' already exists, but does not point to '{dst}'. You'll probably have issues w/ external dependencies.",
                file=sys.stderr,
            )

    command = [
        "bazel",
        "aquery",
        # --include_param_files is broken on CppCompile actions, so we have to
        # disable the feature instead.
        # See: https://github.com/bazelbuild/bazel/issues/23293
        # "--include_param_files",
        "--features=-compiler_param_file",
        # layering_check adds a lot of '-fmodule-map-file'-arguments that aren't
        # useful for compile_commands.json.
        "--features=-layering_check",
        # In my projects, tooling is included in the target configuration as
        # well, and including the same file twice doesn't make much sense.
        "--notool_deps",
        "--output=jsonproto",
        # Allow the user to pass additional arguments, e.g. if they want a
        # --config or whatever.
        *sys.argv[1:],
        'mnemonic("CppCompile", deps(...))',
    ]

    print(f"Running '{' '.join(command)}'", file=sys.stderr)

    result = subprocess.run(command, capture_output=True, text=True, check=True)

    aquery_output = json.loads(result.stdout)
    actions = aquery_output.get("actions", [])

    compile_commands = []

    print(f"Found {len(actions)} actions in aquery output", file=sys.stderr)
    for action in actions:
        arguments = action.get("arguments", [])
        for i, arg in enumerate(arguments):
            if arg in ("-c", "/c") and i + 1 < len(arguments):
                source_file = arguments[i + 1]
                compile_commands.append(
                    {
                        "directory": project_root,
                        "arguments": arguments,
                        "file": source_file,
                    }
                )
                break
        else:
            print(
                f"No source file found for action with arguments: {arguments}",
                file=sys.stderr,
            )

    with open(f"{project_root}/compile_commands.json", "w") as f:
        json.dump(compile_commands, f, indent=2)

    end_time = time.time()
    print(
        f"Wrote {len(compile_commands)} compile commands to {project_root}/compile_commands.json after {end_time - start_time:.2f} seconds",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
