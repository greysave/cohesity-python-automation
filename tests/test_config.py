import unittest
from typing import ClassVar

from cohesity_automation import ConfigError, Settings


class ConfigTests(unittest.TestCase):
    base: ClassVar[dict[str, str]] = {
        "EXAMPLE_API_URL": "https://h.example.test/",
        "EXAMPLE_API_KEY": "k",
    }

    def test_defaults_and_trailing_slash(self) -> None:
        s = Settings.from_env(self.base)
        self.assertEqual(s.base_url, "https://h.example.test")
        self.assertTrue(s.verify_tls)

    def test_overrides(self) -> None:
        s = Settings.from_env(
            {
                **self.base,
                "EXAMPLE_API_VERIFY_TLS": "false",
                "EXAMPLE_API_MAX_RETRIES": "2",
                "EXAMPLE_API_PAGE_SIZE": "10",
            }
        )
        self.assertFalse(s.verify_tls)
        self.assertEqual((s.max_retries, s.page_size), (2, 10))

    def test_missing(self) -> None:
        with self.assertRaises(ConfigError):
            Settings.from_env({})

    def test_bad_values(self) -> None:
        for k, v in [
            ("EXAMPLE_API_VERIFY_TLS", "maybe"),
            ("EXAMPLE_API_TIMEOUT", "x"),
            ("EXAMPLE_API_PAGE_SIZE", "0"),
            ("EXAMPLE_API_MAX_RETRIES", "-1"),
        ]:
            with self.assertRaises(ConfigError, msg=k):
                Settings.from_env({**self.base, k: v})
        with self.assertRaises(ConfigError):
            Settings.from_env({"EXAMPLE_API_URL": "ftp://x", "EXAMPLE_API_KEY": "k"})

    def test_repr_hides_key(self) -> None:
        self.assertNotIn("secret-value", repr(Settings("https://a.test", "secret-value")))
