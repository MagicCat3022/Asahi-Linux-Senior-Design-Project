#!/usr/bin/env bash
# Compatibility entry point; the reusable workflow owns machine configuration.
set -euo pipefail
if [[ -f "$(dirname "${BASH_SOURCE[0]}")/tools/asahi" ]]; then
    ASAHI_PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    ASAHI_PROJECT="${ASAHI_PROJECT:-$HOME/Github/Asahi-Linux-Senior-Design-Project}"
fi
exec python3 "$ASAHI_PROJECT/tools/asahi" boot "$@"
