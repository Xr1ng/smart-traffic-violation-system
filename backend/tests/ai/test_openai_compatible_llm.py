from pathlib import Path

import pytest

from app.ai.adapters.base import LLMReportError


def test_openai_compatible_provider_parses_json_response():
    from app.ai.adapters.openai_compatible import OpenAICompatibleLLMProvider

    def fake_post_json(url, headers, payload, timeout):
        assert url == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        assert payload["model"] == "glm-5.1"
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"conclusion":"need_review","ai_confidence":0.61,'
                            '"reason":"证据需要人工复核","risk_points":["plate blurry"],'
                            '"missing_evidence":[]}'
                        )
                    }
                }
            ]
        }

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        text_model="glm-5.1",
        vision_model="glm-5v-turbo",
        post_json=fake_post_json,
    )

    result = provider.review({"rule": {"rule_matched": True}})

    assert result.conclusion == "need_review"
    assert result.ai_confidence == 0.61
    assert result.risk_points == ["plate blurry"]
    assert result.prompt_version == "openai-compatible-review-v1"


def test_openai_compatible_provider_uses_vision_model_for_existing_image(tmp_path):
    from app.ai.adapters.openai_compatible import OpenAICompatibleLLMProvider

    image_path = tmp_path / "evidence.jpg"
    image_path.write_bytes(b"fake-jpeg")
    captured = {}

    def fake_post_json(url, headers, payload, timeout):
        captured["payload"] = payload
        return {"choices": [{"message": {"content": '{"conclusion":"suggest_approve"}'}}]}

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        text_model="glm-5.1",
        vision_model="glm-5v-turbo",
        mode="vision",
        post_json=fake_post_json,
    )

    provider.review({"image_path": str(image_path)})

    assert captured["payload"]["model"] == "glm-5v-turbo"
    content = captured["payload"]["messages"][1]["content"]
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_openai_compatible_provider_generates_structured_report():
    from app.ai.adapters.openai_compatible import OpenAICompatibleLLMProvider

    captured = {}

    def fake_post_json(url, headers, payload, timeout):
        captured["payload"] = payload
        return {"choices": [{"message": {"content": """```json
        {"summary":"本期共 2 起违章","trend_analysis":"总体平稳",\
        "hotspot_analysis":"人民路较集中","risk_alerts":["晚高峰风险"],\
        "recommendations":["加强巡查"]}
        ```"""}}]}

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        base_url="https://example.com/v1",
        text_model="report-model",
        vision_model="vision-model",
        post_json=fake_post_json,
    )

    result = provider.generate_report({"overview": {"total_violations": 2}})

    assert result.summary == "本期共 2 起违章"
    assert result.recommendations == ["加强巡查"]
    assert captured["payload"]["model"] == "report-model"
    assert captured["payload"]["temperature"] == 0.2
    assert "不得编造" in captured["payload"]["messages"][0]["content"]
    assert "total_violations" in captured["payload"]["messages"][1]["content"]


@pytest.mark.parametrize(
    "response",
    [
        {"choices": [{"message": {"content": "not-json"}}]},
        {"choices": [{"message": {"content": '{"summary":"字段不完整"}'}}]},
    ],
)
def test_openai_compatible_provider_rejects_invalid_report(response):
    from app.ai.adapters.openai_compatible import OpenAICompatibleLLMProvider

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        base_url="https://example.com/v1",
        text_model="report-model",
        vision_model="vision-model",
        post_json=lambda *_args: response,
    )

    with pytest.raises(LLMReportError, match="报告生成失败"):
        provider.generate_report({"overview": {"total_violations": 0}})


def test_openai_compatible_provider_wraps_report_transport_error():
    from app.ai.adapters.openai_compatible import OpenAICompatibleLLMProvider

    def fail(*_args):
        raise TimeoutError("upstream timeout")

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        base_url="https://example.com/v1",
        text_model="report-model",
        vision_model="vision-model",
        post_json=fail,
    )

    with pytest.raises(LLMReportError, match="报告生成失败"):
        provider.generate_report({"overview": {"total_violations": 0}})
