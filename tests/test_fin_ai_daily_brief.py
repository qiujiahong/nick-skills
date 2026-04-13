import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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

    def test_load_input_results_limits_candidates_to_first_15(self):
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
            input_path = Path(tmpdir) / "results.json"
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
            input_path = Path(tmpdir) / "results.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            loaded = module.load_input_results(input_path, limit=15)

        self.assertEqual(loaded[0]["title"], "生成式 AI 在银行业中的应用")
        self.assertEqual(loaded[0]["summary"], "中文摘要")

    def test_load_search_results_uses_tavily_when_no_input_file(self):
        fake_search = {
            "ok": True,
            "query": "金融 AI",
            "topic": "news",
            "response": {
                "results": [
                    {
                        "title": "某银行落地 AI 风控",
                        "url": "https://example.com/a",
                        "content": "银行在风控流程中引入 AI 提升审批效率。",
                        "published_date": "2026-04-14",
                    }
                ]
            },
        }
        with patch.object(module, "multi_search", return_value=fake_search):
            loaded, search_result = module.load_search_results("", "金融 AI", "news", candidate_limit=15)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], "某银行落地 AI 风控")
        self.assertEqual(search_result["topic"], "news")

    def test_build_html_renders_tavily_candidates_and_selected_sections(self):
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
                "title": "Tavily 候选资讯",
                "summary": "来自 Tavily 前 15 条结果。",
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

        self.assertNotIn("Tavily 搜索前 15 条结果", html)
        self.assertNotIn("精选 10 条高价值资讯", html)
        self.assertNotIn("Tavily 候选资讯", html)
        self.assertIn("某银行部署 AI 风控", html)
        self.assertIn("金融 AI", html)

    def test_build_html_hides_candidate_section_meta_and_read_more_link(self):
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
        html = module.build_html(
            date_str="2026-04-13",
            overview="今天重点关注金融企业中的 AI 落地。",
            items=selected,
            fun_facts=["事实1", "事实2", "事实3"],
            candidate_items=[],
            search_query="金融 AI",
        )
        self.assertNotIn("Tavily 搜索前 15 条结果", html)
        self.assertNotIn("精选 10 条高价值资讯", html)
        self.assertNotIn("从前 15 条候选里筛选出对金融企业更有价值的内容", html)
        self.assertNotIn("查看原文", html)
        self.assertNotIn("精选 #1", html)

    def test_shorten_summary_returns_chinese_text_with_max_80_chars(self):
        long_text = "这是一个很长的英文摘要 mixed with English context about AI in banking and risk control that should be summarized into concise Chinese text for executives."
        shortened = module.shorten_summary(long_text, max_chars=80)
        self.assertLessEqual(len(shortened), 80)
        self.assertTrue(module.contains_chinese(shortened))

    def test_build_candidate_items_only_keeps_yesterday_items(self):
        items = [
            {
                "title": "昨天的金融 AI 资讯",
                "summary": "银行用 AI 做风控。",
                "url": "https://example.com/yesterday",
                "source": "example.com",
                "published_date": "Mon, 13 Apr 2026 09:57:31 GMT",
            },
            {
                "title": "前天的金融 AI 资讯",
                "summary": "银行用 AI 做客服。",
                "url": "https://example.com/older",
                "source": "example.com",
                "published_date": "Sun, 12 Apr 2026 09:57:31 GMT",
            },
        ]
        filtered = module.filter_items_for_date(items, "2026-04-14")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], "昨天的金融 AI 资讯")

    def test_translate_title_makes_english_titles_chinese_friendly(self):
        translated = module.translate_title_for_cn("AI fintech startup Round raises $6 million")
        self.assertTrue(module.contains_chinese(translated))
        self.assertNotEqual(translated, "AI fintech startup Round raises $6 million")

    def test_shorten_summary_prefers_business_focused_chinese(self):
        source = "The startup helps banks automate compliance reviews, reduce manual underwriting work, and improve customer onboarding efficiency with AI agents."
        shortened = module.shorten_summary(source, max_chars=80)
        self.assertLessEqual(len(shortened), 80)
        self.assertTrue(any(term in shortened for term in ["银行", "合规", "风控", "效率", "业务"]))
        self.assertNotIn("该资讯涉及", shortened)

    def test_build_html_uses_single_column_with_number_icons_and_no_score(self):
        selected = [
            {
                "title": "某银行部署 AI 风控",
                "summary": "帮助信贷审批团队提升风控识别效率，并减少人工复核压力。",
                "url": "https://example.com/selected",
                "source": "example.com",
                "published_date": "2026-04-13",
                "score": 42,
            },
            {
                "title": "某券商升级投研智能体",
                "summary": "帮助研究团队更快汇总财报信息，并缩短日报产出时间。",
                "url": "https://example.com/selected2",
                "source": "example.com",
                "published_date": "2026-04-13",
                "score": 35,
            },
        ]
        html = module.build_html(
            date_str="2026-04-13",
            overview="今天重点关注金融企业中的 AI 落地。",
            items=selected,
            fun_facts=["事实1", "事实2", "事实3"],
            candidate_items=[],
            search_query="金融 AI",
        )
        self.assertNotIn("价值分", html)
        self.assertTrue(any(marker in html for marker in ["1", "①", "#1"]))
        self.assertIn("某银行部署 AI 风控", html)
        self.assertIn("某券商升级投研智能体", html)


if __name__ == "__main__":
    unittest.main()
