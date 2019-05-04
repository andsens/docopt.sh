#!/usr/bin/env bash

unset_params() {
  while [[ $# -gt 0 ]]; do
    unset $$1
    shift
  done
}
