import csv
import json
import sys
from pathlib import Path

from candidate_selector import select_candidate
from main import load_products, verify_content
from selection_intelligence import build_report

TARGET_FILE = Path('/tmp/intelligent-target.txt')


def choose() -> None:
    products = load_products()
    report = build_report()
    selection = select_candidate(products, report)
    if selection is None:
        selected_id = ''
        print('TEST_MODE intelligent candidate: NONE — safe stop expected')
    else:
        product = selection['product']
        result = selection['selection']
        selected_id = product['product_id']
        print(
            f"TEST_MODE intelligent candidate: {selected_id} — {product['product_name']} "
            f"decision={result['decision']} score={result['opportunity_score']} "
            f"coverage={result['evidence_coverage']} confidence={result['confidence']}"
        )
    TARGET_FILE.write_text(selected_id, encoding='utf-8')
    Path('/tmp/selection-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def verify() -> None:
    target_id = TARGET_FILE.read_text(encoding='utf-8').strip()
    if not target_id:
        output_dir = Path('.test-output')
        files = [p for p in output_dir.rglob('*') if p.is_file()] if output_dir.exists() else []
        if files:
            raise SystemExit('SAFETY FAILURE: no eligible candidate was reported, but TEST_MODE generated output.')
        print('No eligible candidate: safe TEST_MODE stop verified.')
        return

    output_file = Path('.test-output') / target_id / 'package.txt'
    if not output_file.is_file():
        raise SystemExit(f'SAFETY FAILURE: expected output missing: {output_file}')
    content = output_file.read_text(encoding='utf-8')
    required = [target_id, 'Amazon Link:', 'MEDIUM', 'PINTEREST MAIN PIN', 'PINTEREST PRODUCT PIN', 'CONTENT QUALITY', '(paid link)', 'As an Amazon Associate I earn from qualifying purchases.', 'Human review before publication: REQUIRED']
    for marker in required:
        if marker not in content:
            raise SystemExit(f'SAFETY FAILURE: missing content marker: {marker}')
    with open('products.csv', newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    target = next(row for row in rows if row['product_id'] == target_id)
    verify_content(content, target)
    if target['used'].strip().lower() != 'no':
        raise SystemExit(f"SAFETY FAILURE: {target_id} changed to {target['used']!r} during TEST_MODE.")
    print(f'Independent TEST_MODE quality/compliance verification: PASS ({target_id})')


if __name__ == '__main__':
    verify() if len(sys.argv) == 2 and sys.argv[1] == '--verify' else choose()
