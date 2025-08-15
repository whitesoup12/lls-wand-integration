#!/bin/bash
if pgrep -f ir_wand_tracker.py > /dev/null; then
    echo "IR Wand Tracker is running"
else
    echo "IR Wand Tracker is not running"
fi