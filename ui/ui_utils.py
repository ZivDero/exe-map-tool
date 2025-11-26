
def parse_hex(text):
    s = str(text).strip()
    if not s:
        raise ValueError("Value required.")
    if s.endswith(("h", "H")): s = s[:-1]
    if s.lower().startswith("0x"): s = s[2:]
    return int(s, 16)