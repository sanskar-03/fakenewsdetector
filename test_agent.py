import asyncio
import json
import httpx

TEST_CASES = [
    {"label": "FAKE", "claim": "Pope Francis endorsed Donald Trump for President in 2016."},
    {"label": "REAL", "claim": "Joe Biden won the 2020 US Presidential Election."},
    {"label": "FAKE", "claim": "COVID-19 vaccines contain trackable microchips inserted by Bill Gates."},
    {"label": "UNVERIFIED", "claim": "A massive undiscovered pyramid was just found under Central Park in New York yesterday."},
    {"label": "REAL", "claim": "India successfully landed the Chandrayaan-3 mission near the Moon's south pole in 2023."},
    {"label": "FAKE", "claim": "UNESCO has officially declared Narendra Modi as the best Prime Minister in the world."},
    {"label": "REAL", "claim": "The Japanese passport allows visa-free or visa-on-arrival access to over 190 destinations."},
    {"label": "FAKE", "claim": "If you type your PIN backwards at an ATM, it will secretly call the police."},
    {"label": "FAKE", "claim": "NASA has confirmed that the Earth will experience 15 days of total darkness this November."},
    {"label": "REAL", "claim": "The Great Wall of China is generally not visible to the naked eye from low Earth orbit."}
]

async def run_tests():
    print("==========================================")
    print("Fake News Detector - Automated 10-Case Test")
    print("==========================================\n")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, tc in enumerate(TEST_CASES, 1):
            print(f"[{i}/10] Testing claim: {tc['claim']}")
            print(f"Expected: {tc['label']}")
            
            try:
                resp = await client.post(
                    "http://127.0.0.1:8000/api/v1/verify",
                    json={"article": tc['claim'], "language": "en"}
                )
                resp.raise_for_status()
                data = resp.json()
                
                verdict = data.get("verdict", "UNKNOWN")
                conf = data.get("confidence", 0)
                print(f"Result: {verdict} (Confidence: {conf}%)")
                print(f"Reasoning: {data.get('reasoning', '')[:150]}...")
                
                if verdict == tc['label']:
                    print("✅ MATCH")
                else:
                    print("❌ MISMATCH")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(run_tests())
