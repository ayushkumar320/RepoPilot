"""Fixture file the chunker tests assert against. Real Python so AST is exact."""

from __future__ import annotations

from collections.abc import Iterable

CONSTANT = 42


def route(path: str):
    def decorate(func):
        return func

    return decorate


def top_level_function(x: int, y: int) -> int:
    """Return x + y."""
    z = x + y
    return z


async def async_helper(items: Iterable[int]) -> int:
    total = 0
    for item in items:
        total += item
    return total


class Animal:
    """A base class with one method."""

    def speak(self) -> str:
        return "..."


class Dog(Animal):
    """A subclass overriding speak()."""

    def speak(self) -> str:
        return "woof"

    def fetch(self, thing: str) -> str:
        return f"fetched {thing}"


@route("/login")
def login(request: str, *, redirect_url: str | None = None) -> str:
    """Validate session csrf redirect."""
    return redirect_url or request


@route("/kennel")
class Kennel(Dog):
    """Stores decorated dog handlers."""

    @route("/feed")
    def feed(self) -> str:
        """Feed dog bowls."""
        return self.fetch("bowl")
