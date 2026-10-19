cd "$(dirname "$0")/.."
python -X utf8 tools/direct.py && python -X utf8 tools/chunkfix.py && python -X utf8 tools/calendar.py && python -X utf8 tools/bgedit.py && python -X utf8 tools/build.py | tail -2
