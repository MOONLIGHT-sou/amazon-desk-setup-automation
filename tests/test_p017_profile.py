import json
from pathlib import Path
import main
def test_p017_is_first_unused_and_has_facts():
    products = main.load_products(); p017 = next(p for p in products if p['product_id'] == 'P017')
    assert p017['used'] == 'No'; assert products[0]['used'] == 'Yes'
    facts = json.loads(Path('product_facts.json').read_text())['facts']['P017']
    assert facts['asin'] == 'B00EU6TXC6'; assert 'Current price' in facts['do_not_claim_as_current_fact']
def test_p017_uses_laptop_stand_profile():
    products = main.load_products(); p017 = next(p for p in products if p['product_id'] == 'P017')
    profile_name, _ = main.infer_profile(p017); assert profile_name == 'laptop_stand'
def test_p017_content_generation_is_safe():
    products = main.load_products(); p017 = next(p for p in products if p['product_id'] == 'P017')
    content = main.build_content(p017); text = '\n'.join(str(v) for v in content.values()) if isinstance(content, dict) else str(content); lower = text.lower()
    assert '₹' not in text; assert 'guaranteed posture improvement' not in lower; assert 'i tested' not in lower
    assert 'as an amazon associate i earn from qualifying purchases.' in lower
