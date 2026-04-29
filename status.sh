#!/usr/bin/env bash
echo "===== ZILFIT IP CORE STATUS ====="
echo
echo "Current path:"
pwd
echo
echo "Folders:"
find . -maxdepth 2 -type d | sort
echo
echo "Key files:"
find . -maxdepth 3 -type f | sort
echo
echo "Validation test:"
python3 validators/validate_agent_output.py reports/test_agent_output.json
echo
echo "Line counts:"
wc -l $(find . -type f | sort)
