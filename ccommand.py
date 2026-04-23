#!/usr/bin/env python3

import subprocess
import json
import time
import sys

if __name__ == "__main__":
    start_time = time.time()

    project_root = subprocess.check_output(
        ["bazel", "info", "workspace"], text=True
    ).strip()

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
        "--output=jsonproto",
        # Allow the user to pass additional arguments, e.g. if they want a
        # --config or whatever.
        *sys.argv[1:],
        'mnemonic("CppCompile", ...)',
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
