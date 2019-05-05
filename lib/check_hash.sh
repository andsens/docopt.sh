#!/usr/bin/env bash

docopt_check() {
  local current_doc_hash
  current_doc_hash=$(printf "%s" "${{docname}}" | shasum -a 256 | cut -f 1 -d " ")
  if [[ $current_doc_hash != "{{digest}}" ]]; then
    printf "The current usage doc (%s) does not match what the parser was generated with ({{digest}})\n" "$current_doc_hash" >&2
    exit 1;
  fi
}
