#!/usr/bin/env bash

set -e

mkdir -p "$HOME/.local/bin"
wget -O- https://github.com/koalaman/shellcheck/releases/download/v0.7.1/shellcheck-v0.7.1.linux.x86_64.tar.xz | \
  tar -xJC "$HOME/.local/bin" --strip-components 1 shellcheck-v0.7.1/shellcheck

pip --disable-pip-version-check --no-cache-dir install --user poetry

mkdir -p "$HOME/.config/pypoetry"
cp .devcontainer/poetry-config.toml "$HOME/.config/pypoetry/config.toml"

poetry install
