"""Do not deploy the NH quote endpoint while shared token safety is unresolved."""


def main():
    # This guard must be replaced, not bypassed with a runtime environment variable,
    # once the shared token state machine and its failure tests are implemented.
    raise SystemExit("배포 중단: NH 공유 토큰 발급 및 장애 복구가 아직 검증되지 않았습니다.")


if __name__ == "__main__":
    main()
