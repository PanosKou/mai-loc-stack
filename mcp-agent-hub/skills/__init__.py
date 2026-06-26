import importlib
import inspect
import pkgutil

from .base import AgentHubSkill


def discover_skills() -> list[AgentHubSkill]:
    """Discover and instantiate all Agent Hub skills in this package."""

    discovered: list[AgentHubSkill] = []
    package_name = __name__

    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name == "base" or module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{package_name}.{module_info.name}")

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is AgentHubSkill:
                continue

            if issubclass(obj, AgentHubSkill) and obj.__module__ == module.__name__:
                discovered.append(obj())

    return sorted(discovered, key=lambda skill: skill.name)
