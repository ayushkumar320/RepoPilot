import asyncio
from repopilot_core.settings import Settings
from repopilot_core.llm.provider import LLMProvider
from repopilot_ingestion.pipeline import index_repo

async def main():
    settings = Settings()
    settings.ingestion_embed_concurrency = 1
    provider = LLMProvider.build(settings=settings)
    repos = [
        ("https://github.com/tiangolo/fastapi", "0.103.1"),
        ("https://github.com/encode/httpx", "0.25.0"),
        ("https://github.com/pallets/flask", "2.3.3"),
    ]
    for url, version in repos:
        print(f"Indexing {url} @ {version}")
        await index_repo(url, provider=provider, settings=settings)

if __name__ == "__main__":
    asyncio.run(main())
