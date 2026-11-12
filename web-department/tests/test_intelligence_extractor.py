from intelligence_extractor import extract_business_entities


def test_extracts_explicit_schema_org_business_and_address():
    html = b"""
    <html><head><title>Alpha Plumbing</title>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "PlumbingService",
      "name": "Alpha Plumbing",
      "url": "https://alpha.example.za/",
      "telephone": "+27 11 000 0000",
      "email": "hello@alpha.example.za",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "10 Main Road",
        "addressLocality": "Johannesburg",
        "addressRegion": "Gauteng"
      }
    }
    </script></head><body></body></html>
    """
    records = extract_business_entities(html, "https://directory.example.za/listing/alpha")
    assert len(records) == 1
    assert records[0]["business_name"] == "Alpha Plumbing"
    assert records[0]["city"] == "Johannesburg"
    assert records[0]["province"] == "Gauteng"
    assert records[0]["website"] == "https://alpha.example.za/"


def test_does_not_infer_business_from_plain_page_title():
    html = b"<html><head><title>Johannesburg Services</title></head><body></body></html>"
    assert extract_business_entities(html, "https://directory.example.za/") == []


def test_ignores_malformed_jsonld_without_crashing():
    html = b'<html><script type="application/ld+json">{broken</script></html>'
    assert extract_business_entities(html, "https://directory.example.za/") == []
