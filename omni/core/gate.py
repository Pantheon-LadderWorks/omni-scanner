def check(scan_data: dict, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Evaluates scan data against policy.
    Returns (Passed?, [Messages])
    """
    messages = []
    passed = True
    findings = scan_data.get("findings", {})
    
    # Docs Check
    docs = findings.get("docs", {})
    missing_docs = docs.get("missing", [])
    
    if missing_docs:
        # In strict mode, missing docs = fail. In partial, maybe just a warning?
        # Mega said: "Strict: Fail if Missing > 0"
        msg = f"Missing Documentation: {', '.join(missing_docs)}"
        messages.append(f"[FAIL] {msg}" if strict else f"[WARN] {msg}")
        if strict:
            passed = False
            
    # Surface Check
    surfaces_data = findings.get("surfaces", {})
    surfaces_items = surfaces_data.get("items", [])
    
    if surfaces_data.get("count", 0) == 0 and not surfaces_items:
         messages.append("[WARN] No surfaces found (Is this an empty project?)")
    
    missing_count = sum(1 for s in surfaces_items if s.get('status') == 'missing' and s.get('scope') != 'external_reference')
    
    if missing_count > 0:
        msg = f"Found {missing_count} MISSING surfaces."
        messages.append(f"[FAIL] {msg}" if strict else f"[WARN] {msg}")
        if strict:
            passed = False
    else:
        messages.append(f"[OK] Zero Missing contracts ({len(surfaces_items)} total)")

    if passed:
        messages.append("[PASS] Gate Passed")
    else:
        messages.append("[FAIL] Gate Failed")
        
    return passed, messages
