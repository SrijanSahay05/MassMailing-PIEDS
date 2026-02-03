import re

def extract_emails(email_str):
    """Find all valid email patterns within a string."""
    if not email_str:
        return []
    import re
    # Robust regex specifically for finding emails in text
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    found = re.findall(email_pattern, str(email_str))
    # Cleanup trailing dots often caught by regex in text contexts
    return [e.rstrip('.') for e in found if e]

test_cases = [
    "amal@blume.vc (amal05vats@gmail.com personal)",
    "test@abc.com, test2@abc.com",
    "test@abc.com;test2@abc.com",
    "test@abc.com / test2@abc.com",
    "Multiple: a@b.com, c@d.com ; e@f.com/g@h.com (note: info@i.com)",
    "  onlyone@abc.com  ",
    "invalid-email",
    "",
    None
]

for tc in test_cases:
    print(f"Input: {tc} -> Result: {extract_emails(tc)}")
