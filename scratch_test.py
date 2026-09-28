import asyncio
from backend.services.agent import verify_news

async def main():
    test_cases = [
        # Fake because no sources found
        {"claim": "The moon is made of blue cheese.", "url": None},
        # Fake because sources contradict
        {"claim": "Earth is flat.", "url": None},
        {"claim": "Vaccines cause autism.", "url": None},
        # Real because sources support
        {"claim": "Water is composed of hydrogen and oxygen.", "url": None},
        {"claim": "Barack Obama was the 44th president of the United States.", "url": None},
        # Unverified / Neutral
        {"claim": "The new iPhone will have a holographic display.", "url": None},
        {"claim": "A new species of alien was found on Mars.", "url": None},
        # Some URLs
        {"claim": "Global warming is a hoax.", "url": "http://example.com/fake-news"},
        {"claim": "The Eiffel Tower is in Paris.", "url": None},
        {"claim": "Albert Einstein developed the theory of relativity.", "url": None}
    ]

    for i, case in enumerate(test_cases):
        print(f"--- Case {i+1} ---")
        print(f"Claim: {case['claim']}")
        try:
            res = await verify_news(article=case['claim'], image_url=None, language='en', article_url=case['url'])
            print(f"Verdict: {res.get('verdict')}")
            print(f"Reasoning: {res.get('reasoning')}")
        except Exception as e:
            print(f"Error: {e}")
        print()

asyncio.run(main())
