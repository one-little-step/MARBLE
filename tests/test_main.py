import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from marble.main import parse_args


def test_parse_args_resume_from():
    with patch.object(
        sys,
        "argv",
        ["marble", "--resume_from", "outputs/x/20260706-000000/checkpoints/latest"],
    ):
        args = parse_args()
    assert args.resume_from == "outputs/x/20260706-000000/checkpoints/latest"
