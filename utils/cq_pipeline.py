import asyncio
from agents.ontology_agent import OntologyBuilderAgent
from pathlib import Path
from typing import List, Tuple
import datetime
import time

class CQPipeline:
    def __init__(self, cq_file: str, output_dir: str = "outputs/ontology/", retries: int = 2):
        self.agent = OntologyBuilderAgent()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cq_list = self._load_cqs(cq_file)
        self.generated_axioms: List[Tuple[str, str]] = []
        self.retries = retries
        self.latencies = []

    def _load_cqs(self, file_path: str) -> List[str]:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines

    async def process_all(self):
        print(f"Processing {len(self.cq_list)} competency questions...")
        for i, cq in enumerate(self.cq_list, start=1):
            print(f"\nCQ {i}: {cq}")
            attempt = 0
            success = False
            axiom = ""
            start = time.time()
            while not success and attempt <= self.retries:
                try:
                    axiom = await self.agent.run(cq)
                    success = True
                except Exception as e:
                    attempt += 1
                    print(f"❌ Attempt {attempt} failed: {str(e)}")
                    await asyncio.sleep(2)

            if success:
                self.latencies.append(time.time() - start)
                self.generated_axioms.append((cq, axiom))
                print(axiom)
            else:
                self.generated_axioms.append((cq, "# ERROR: Generation failed after retries."))

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"ontology_axioms_{timestamp}.ttl"

        with open(output_path, "w", encoding="utf-8") as f:
            for cq, axiom in self.generated_axioms:
                f.write(f"# CQ: {cq}\n{axiom}\n\n")

        print(f"\n✅ Saved to: {output_path}")
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        print(f"⏱️ Avg Latency per CQ: {avg_latency:.2f}s")

# Run CLI
if __name__ == "__main__":
    input_file = "data/sample_cqs.txt"
    pipeline = CQPipeline(cq_file=input_file)
    asyncio.run(pipeline.process_all())
