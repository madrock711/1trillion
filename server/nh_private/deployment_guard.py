"""Static launch contract plus the full injected failure/race test suite.

Does not contact NH, issue a token, or prove live provider availability.
An initialized shared record is still mandatory at runtime.
"""

from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    groups = ['test_token_store.py', 'test_nh_transport.py', 'test_runtime_service.py', 'test_flow_integration.py', 'test_flow_archive.py', 'test_closing_collector.py']
    for group in groups:
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(root), '-p', group],
                                capture_output=True)
        if result.returncode:
            raise SystemExit('NH 공유 토큰 안전성 검증 실패: ' + group)
    print('NH shared-state failure/race and no-retry transport checks passed. Live approval and initialization are separate.')


if __name__ == "__main__":
    main()
