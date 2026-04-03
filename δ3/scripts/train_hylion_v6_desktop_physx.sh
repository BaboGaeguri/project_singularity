#!/bin/bash
# External desktop: PhysX-only v6 training entrypoint.

set -e
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
exec "$PROJECT_ROOT/δ3/scripts/launch_desktop_physx_v6.sh"
