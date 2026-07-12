import os
import unittest

from marble.llms.text_embedding import text_embedding


class TestTextEmbedding(unittest.TestCase):
    def test_text_embedding(self) -> None:
        content = "This is a test sentence."
        model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        emebedding = text_embedding(
            model=model,
            input=content,
        )
        self.assertIsInstance(emebedding, list)
        for entry in emebedding:
            self.assertIsInstance(entry, float)


if __name__ == "__main__":
    unittest.main()
