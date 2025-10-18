#!/usr/bin/env bash
#
# Quick Integration Test Runner
# Run this with your GitHub tokens set
#

# Set your tokens here (replace with actual values)
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

echo "Running integration tests with tokens set..."
echo ""

# Run the integration test
./integration_test_step7.sh
