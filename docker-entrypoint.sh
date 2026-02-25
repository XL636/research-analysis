#!/bin/sh
# Fix ownership of mounted volumes (they may be created as root)
# Run this as root, then exec the main command as appuser

for dir in /app/knowledge_base /app/uploads /app/output /app/.uv-cache; do
    if [ -d "$dir" ] && [ "$(stat -c '%u' "$dir")" != "1000" ]; then
        chown -R appuser:appuser "$dir"
    fi
done

exec gosu appuser "$@"
