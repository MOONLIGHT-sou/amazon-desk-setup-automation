from affiliate_link import build_affiliate_link, extract_asin, validate_affiliate_link

TAG = "moonlight0adc-21"
CANONICAL = "https://www.amazon.in/dp/B0GL2ZFVR1"
EXPECTED = "https://www.amazon.in/dp/B0GL2ZFVR1?tag=moonlight0adc-21"

assert extract_asin(CANONICAL) == "B0GL2ZFVR1"
assert build_affiliate_link(CANONICAL, TAG) == EXPECTED
validate_affiliate_link(EXPECTED, "B0GL2ZFVR1", TAG)

try:
    validate_affiliate_link(
        "https://www.amazon.in/dp/B0GL2ZFVR1?tag=wrong-21",
        "B0GL2ZFVR1",
        TAG,
    )
except ValueError:
    pass
else:
    raise AssertionError("Invalid Associate tag was accepted")

try:
    build_affiliate_link("https://www.amazon.in/dp/WRONG12345", TAG)
except ValueError:
    pass
else:
    raise AssertionError("Invalid ASIN was accepted")

try:
    build_affiliate_link("https://example.com/dp/B0GL2ZFVR1", TAG)
except ValueError:
    pass
else:
    raise AssertionError("Non-Amazon URL was accepted")

print("Affiliate link safety checks: PASS")
