# bazel-compile-commands

A tool that generates a `compile_commands.json` file from Bazel build
configurations, enabling IDE support for C/C++ projects built with Bazel.

## Installation

<!-- # TODO(robinlinden): Tag a release. Consider publishing to PyPI. -->

```bash
pipx install git+https://github.com/robinlinden/bazel-compile-commands.git@master
```

## Usage

Navigate to your Bazel workspace root and run:

```bash
bccommand
```

The script will:
1. Query your Bazel workspace for C/C++ compilation actions.
1. Extract and normalize compilation commands.
1. Generate a `compile_commands.json` file in your workspace root.

### Custom Arguments

You can pass additional arguments to `bazel aquery`, such as configuration
options:

```bash
bccommand --config=myconfig
```
