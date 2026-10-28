#!/usr/bin/env bash
set -Eeo pipefail; shopt -s inherit_errexit

mkdir -p "$HOME/.local/bin"
shellcheck_version=v0.11.0
shellcheck_sha256=8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198
wget -O /tmp/shellcheck.tar.xz \
  "https://github.com/koalaman/shellcheck/releases/download/$shellcheck_version/shellcheck-$shellcheck_version.linux.x86_64.tar.xz"
sha256sum -c <<<"$shellcheck_sha256  /tmp/shellcheck.tar.xz"
tar -xJC "$HOME/.local/bin" --strip-components 1 -f /tmp/shellcheck.tar.xz "shellcheck-$shellcheck_version/shellcheck"
rm /tmp/shellcheck.tar.xz

pip --disable-pip-version-check --no-cache-dir install --user poetry
poetry install --no-root
