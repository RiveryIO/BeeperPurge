#!/bin/bash
# Run Ruff to check for linting and formating issues
echo "Running Ruff to check for issues"
output="$(ruff check .)"
exit_code=$?

if [[ $exit_code -eq 0 ]]
then
    printf "Ruff completed successfully. No issues found.\n"
elif [[ $exit_code -eq 1 ]]
then
    printf "Ruff found issues:\n"
    printf "%s\n" "$output"
    exit 1
else
    printf "Ruff encountered an error:\n"
    printf "%s\n" "$output"
    exit $exit_code
fi