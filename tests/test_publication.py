import unittest

from scripts.check_open_source import findings


class PublicationTests(unittest.TestCase):
    def test_template_values_are_scanned(self):
        credential = ('sk-' + 'z' * 24).encode()
        self.assertIn('API credential', findings('.env.example', b'LLM_API_KEY=' + credential))
        template = bytes([10]).join([b'LLM_API_KEY=', b'NEO4J_PASSWORD='])
        self.assertEqual(findings('.env.example', template), [])

    def test_private_paths_and_database_urls_are_flagged(self):
        path = '/'.join(['', 'Users', 'sample', 'work', 'document'])
        self.assertIn('personal home path', findings('README.md', path.encode()))
        connection = 'bolt://' + 'account:' + 'sample-value' + '@example.invalid'
        self.assertIn('credential in URL', findings('config.txt', connection.encode()))

    def test_environment_file_is_not_publishable(self):
        self.assertIn('environment file', findings('.env', b''))
