import json

from app import main


def test_latest_eval_report_returns_newest_file(client, monkeypatch, tmp_path) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir(parents=True)

    old = reports / 'eval_report_20260101T000000Z.json'
    new = reports / 'eval_report_20260101T000100Z.json'

    old.write_text(
        json.dumps(
            {
                'generated_at': '2026-01-01T00:00:00Z',
                'summary': {
                    'total': 1,
                    'passed': 1,
                    'failed': 0,
                    'pass_rate': 100.0,
                    'failed_ids': [],
                    'violations_by_rule': {}
                },
                'results': []
            }
        )
    )

    new.write_text(
        json.dumps(
            {
                'generated_at': '2026-01-01T00:01:00Z',
                'summary': {
                    'total': 2,
                    'passed': 1,
                    'failed': 1,
                    'pass_rate': 50.0,
                    'failed_ids': ['x'],
                    'violations_by_rule': {'safety_first': 1}
                },
                'results': [
                    {
                        'id': 'x',
                        'expected_outcome': 'allow',
                        'actual_outcome': 'refuse',
                        'expected_violated_rules': [],
                        'actual_violated_rules': ['safety_first'],
                        'passed': False,
                        'confidence': 0.84,
                        'final_answer': 'blocked'
                    }
                ]
            }
        )
    )

    monkeypatch.setattr(main.settings, 'eval_reports_dir', str(reports))

    response = client.get('/eval/reports/latest')
    assert response.status_code == 200

    body = response.json()
    assert body['source_file'] == new.name
    assert body['summary']['total'] == 2


def test_latest_eval_report_404_when_missing(client, monkeypatch, tmp_path) -> None:
    empty = tmp_path / 'empty_reports'
    empty.mkdir(parents=True)

    monkeypatch.setattr(main.settings, 'eval_reports_dir', str(empty))

    response = client.get('/eval/reports/latest')
    assert response.status_code == 404
