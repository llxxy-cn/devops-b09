import unittest

from draft.autobuild import classify_failure, prepare_candidate


BROKEN = """FROM python:3.13-slim
WORKDIR /work
COPY main.c helper.c config.h extra.h unused.h Makefile ./
RUN make app
CMD ["./app"]
"""

CANDIDATE = """FROM python:3.13-slim@sha256:{digest}
WORKDIR /work
COPY main.c helper.c config.h extra.h unused.h Makefile ./
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN make app
CMD ["./app"]
""".format(digest="0" * 64)


class B1DraftContractTests(unittest.TestCase):
    def test_missing_make_is_classified(self):
        log = "/bin/sh: 1: make: not found\n"
        self.assertEqual(classify_failure(log), "MISSING_MAKE")

    def test_candidate_cannot_change_required_runtime_instruction(self):
        changed = CANDIDATE.replace(
            'CMD ["./app"]',
            'CMD ["echo", "wrong"]',
        )
        with self.assertRaisesRegex(
            ValueError,
            "changed required project/build/runtime instructions",
        ):
            prepare_candidate(BROKEN, changed)


if __name__ == "__main__":
    unittest.main()
