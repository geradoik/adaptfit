import os
import json
import unittest
from unittest import mock
 
from app import llm_client as lc
 
try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None
 
 
@unittest.skipIf(httpx is None, "httpx not installed")
class GroqClientTests(unittest.TestCase):
    def client(self, handler):
        return lc.GroqClient("test-key", "test-model", timeout=1, transport=httpx.MockTransport(handler))
 
    def test_sends_key_model_system_and_question_and_returns_the_text(self):
        seen = {}
        def handler(request):
            seen["headers"], seen["body"] = request.headers, request.read().decode()
            return httpx.Response(200, json={"choices": [{"message": {"content": "Hello there"}}]})

        answer = self.client(handler).complete("Be brief.", "Hi")
        body = json.loads(seen["body"])
        self.assertEqual(answer, "Hello there")
        self.assertEqual(seen["headers"]["authorization"], "Bearer test-key")
        self.assertEqual(body["messages"][0], {"role": "system", "content": "Be brief."})
        self.assertEqual(body["messages"][1], {"role": "user", "content": "Hi"})
 
    def test_every_kind_of_failure_becomes_llm_unavailable(self):
        def server_error(request):
            return httpx.Response(500, json={"error": "boom"})
 
        def not_json(request):
            return httpx.Response(200, content=b"<html>oops</html>")
 
        def wrong_shape(request):
            return httpx.Response(200, json={"unexpected": True})
 
        def empty(request):
            return httpx.Response(200, json={"content": []})
 
        def no_internet(request):
            raise httpx.ConnectError("no route")
 
        for handler in (server_error, not_json, wrong_shape, empty, no_internet):
            with self.assertRaises(lc.LLMUnavailable):
                self.client(handler).complete("s", "u")
 
 
class ClientFactoryTests(unittest.TestCase):
    def test_no_key_means_no_client(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            self.assertIsNone(lc.get_client())
 
    def test_key_and_model_come_from_the_environment(self):
        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "abc", "ADAPTFIT_LLM_MODEL": "my-model"}):client = lc.get_client()
        self.assertEqual((client.api_key, client.model), ("abc", "my-model"))
 
    def test_fake_client_records_calls_and_can_fail(self):
        fake = lc.FakeClient("hi")
        self.assertEqual(fake.complete("s", "u"), "hi")
        self.assertEqual(fake.calls, [("s", "u")])
        with self.assertRaises(lc.LLMUnavailable):
            lc.FakeClient(error=lc.LLMUnavailable("down")).complete("s", "u")
 
 
if __name__ == "__main__":
    unittest.main()
