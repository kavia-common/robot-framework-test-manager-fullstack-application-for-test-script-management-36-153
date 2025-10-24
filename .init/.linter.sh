#!/bin/bash
cd /home/kavia/workspace/code-generation/robot-framework-test-manager-fullstack-application-for-test-script-management-36-153/BackendAPI
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

