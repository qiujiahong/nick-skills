import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "skills" / "fin-ai-daily-brief" / "scripts" / "generate_fin_ai_brief.py"

spec = importlib.util.spec_from_file_location("fin_ai_daily_brief", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FinAiDailyBriefTests(unittest.TestCase):
    def test_parse_recipients_supports_subscribers_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subscriber_file = Path(tmpdir) / "subscribers.txt"
            subscriber_file.write_text("alpha@example.com\nbeta@example.com\n", encoding="utf-8")
            old_file = os.environ.get("FIN_AI_SUBSCRIBERS_FILE")
            old_raw = os.environ.get("FIN_AI_SUBSCRIBERS")
            os.environ["FIN_AI_SUBSCRIBERS_FILE"] = str(subscriber_file)
            os.environ["FIN_AI_SUBSCRIBERS"] = "beta@example.com,gamma@example.com"
            try:
                recipients = module.parse_recipients(["delta@example.com"])
            finally:
                if old_file is None:
                    os.environ.pop("FIN_AI_SUBSCRIBERS_FILE", None)
                else:
                    os.environ["FIN_AI_SUBSCRIBERS_FILE"] = old_file
                if old_raw is None:
                    os.environ.pop("FIN_AI_SUBSCRIBERS", None)
                else:
                    os.environ["FIN_AI_SUBSCRIBERS"] = old_raw

        self.assertEqual(
            recipients,
            [
                "alpha@example.com",
                "beta@example.com",
                "gamma@example.com",
                "delta@example.com",
            ],
        )

    def test_load_input_results_limits_google_candidates_to_first_15(self):
        payload = {
            "query": "金融 AI",
            "results": [
                {
                    "title": f"结果 {i}",
                    "url": f"https://example.com/{i}",
                    "summary": f"摘要 {i}",
                    "source": "example.com",
                }
                for i in range(1, 19)
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "google-results.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            loaded = module.load_input_results(input_path, limit=15)

        self.assertEqual(len(loaded), 15)
        self.assertEqual(loaded[0]["title"], "结果 1")
        self.assertEqual(loaded[-1]["title"], "结果 15")

    def test_load_input_results_prefers_chinese_fields(self):
        payload = {
            "query": "金融 AI",
            "results": [
                {
                    "title": "Generative AI in banking",
                    "zh_title": "生成式 AI 在银行业中的应用",
                    "url": "https://example.com/a",
                    "summary": "English summary",
                    "zh_summary": "中文摘要",
                    "source": "example.com",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "google-results.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            loaded = module.load_input_results(input_path, limit=15)

        self.assertEqual(loaded[0]["title"], "生成式 AI 在银行业中的应用")
        self.assertEqual(loaded[0]["summary"], "中文摘要")

    def test_load_google_results_requires_input_file(self):
        with self.assertRaises(RuntimeError):
            module.load_google_results("", candidate_limit=15)

    def test_build_html_renders_google_candidates_and_selected_sections(self):
        selected = [
            {
                "title": "某银行部署 AI 风控",
                "summary": "提升审批效率与风险识别能力。",
                "url": "https://example.com/selected",
                "source": "example.com",
                "published_date": "2026-04-13",
                "score": 42,
            }
        ]
        candidates = [
            {
                "title": "Google 候选资讯",
                "summary": "来自 Google 前 15 条结果。",
                "url": "https://example.com/candidate",
                "source": "example.com",
                "published_date": "2026-04-13",
                "score": 12,
            }
        ]

        html = module.build_html(
            date_str="2026-04-13",
            overview="今天重点关注金融企业中的 AI 落地。",
            items=selected,
            fun_facts=["事实1", "事实2", "事实3"],
            candidate_items=candidates,
            search_query="金融 AI",
        )

        self.assertIn("Google 前 15 条结果", html)
        self.assertIn("精选 10 条高价值资讯", html)
        self.assertIn("Google 候选资讯", html)
        self.assertIn("某银行部署 AI 风控", html)
        self.assertIn("金融 AI", html)


if __name__ == "__main__":
    unittest.main()
