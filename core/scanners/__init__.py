from . import surfaces, docs, deps, contracts, tools, uuids

# The Plugin Registry
# Add new scanners here to automatically expose them to the CLI
SCANNERS = {
    "surfaces": surfaces.scan,
    "docs": docs.scan,
    "deps": deps.scan,
    "contracts": contracts.scan,
    "tools": tools.scan,
    "uuids": uuids.scan,
}
