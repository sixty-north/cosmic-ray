"""Tests for `cosmic_ray.commands.new_config`."""

import importlib

new_config_command = importlib.import_module("cosmic_ray.commands.new_config")


def test_new_config_uses_click_prompts(monkeypatch):
    prompts = iter(
        [
            "tests/resources/example_project/adam",
            10.5,
            "python -m unittest discover tests",
            "local",
        ]
    )
    prompt_calls = []

    def fake_prompt(text, **kwargs):
        prompt_calls.append((text, kwargs))
        return next(prompts)

    monkeypatch.setattr(new_config_command.click, "prompt", fake_prompt)
    monkeypatch.setattr(new_config_command.click, "echo", lambda *args, **kwargs: None)
    monkeypatch.setattr(new_config_command, "distributor_names", lambda: ("http", "local"))

    config = new_config_command.new_config()

    assert config == {
        "module-path": "tests/resources/example_project/adam",
        "timeout": 10.5,
        "excluded-modules": [],
        "test-command": "python -m unittest discover tests",
        "distributor": {"name": "local"},
    }
    assert [call[0] for call in prompt_calls] == [
        "Top-level module path",
        "Test execution timeout (seconds)",
        "Test command",
        "Distributor",
    ]
