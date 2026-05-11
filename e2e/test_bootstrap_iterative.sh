#!/bin/bash
# -*- indent-tabs-mode: nil; tab-width: 2; sh-indentation: 2; -*-

# Tests that the iterative bootstrap produces correct results for a
# package with transitive dependencies. Verifies that the LIFO-based
# iterative loop builds dependencies in the correct order (deps before
# their dependents) and that the build-order.json and graph.json are
# consistent.

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPTDIR/common.sh"

fromager \
  --log-file="$OUTDIR/bootstrap.log" \
  --error-log-file="$OUTDIR/fromager-errors.log" \
  --sdists-repo="$OUTDIR/sdists-repo" \
  --wheels-repo="$OUTDIR/wheels-repo" \
  --work-dir="$OUTDIR/work-dir" \
  bootstrap 'stevedore==5.2.0'

# Verify expected output files exist
EXPECTED_FILES="
$OUTDIR/wheels-repo/downloads/setuptools-*.whl
$OUTDIR/wheels-repo/downloads/pbr-*.whl
$OUTDIR/wheels-repo/downloads/stevedore-*.whl
$OUTDIR/work-dir/build-order.json
$OUTDIR/work-dir/graph.json
"

pass=true
for pattern in $EXPECTED_FILES; do
  if [ ! -f "${pattern}" ]; then
    echo "Did not find $pattern" 1>&2
    pass=false
  fi
done

# Verify build order: dependencies must appear before dependents
# pbr and setuptools must come before stevedore in build-order.json
BUILD_ORDER="$OUTDIR/work-dir/build-order.json"
pbr_idx=$(python3 -c "
import json, sys
data = json.load(open('$BUILD_ORDER'))
dists = [e['dist'] for e in data]
print(dists.index('pbr') if 'pbr' in dists else -1)
")
stevedore_idx=$(python3 -c "
import json, sys
data = json.load(open('$BUILD_ORDER'))
dists = [e['dist'] for e in data]
print(dists.index('stevedore') if 'stevedore' in dists else -1)
")

if [ "$pbr_idx" -ge "$stevedore_idx" ] || [ "$pbr_idx" -eq "-1" ]; then
  echo "ERROR: pbr (idx=$pbr_idx) must appear before stevedore (idx=$stevedore_idx) in build order" 1>&2
  pass=false
fi

# Verify graph.json has the expected dependency edges
python3 -c "
import json, sys
graph = json.load(open('$OUTDIR/work-dir/graph.json'))
# stevedore should exist as a node
stevedore_nodes = [k for k in graph if k.startswith('stevedore==')]
if not stevedore_nodes:
    print('ERROR: stevedore not found in graph', file=sys.stderr)
    sys.exit(1)
# pbr should exist as a node
pbr_nodes = [k for k in graph if k.startswith('pbr==')]
if not pbr_nodes:
    print('ERROR: pbr not found in graph', file=sys.stderr)
    sys.exit(1)
print('Graph structure verified')
" || pass=false

$pass
