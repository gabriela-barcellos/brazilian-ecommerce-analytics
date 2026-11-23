"""
BRAZILIAN E-COMMERCE | PIPELINE COMPLETO

Executa, em ordem, e para na primeira falha:
  1. Bronze   (ingestion.py)              CSV -> bronze.*
  2. Silver   (silver_transformation.py)  bronze.* -> silver.*
  3. Gold     (gold_build.py)             silver.* -> gold.*
  4. Qualidade (quality_checks.py)        verificações críticas e alertas

Uso:
  python Scripts\\run_pipeline.py              # tudo
  python Scripts\\run_pipeline.py --from silver # a partir de uma etapa
"""

import argparse
import time

from gold_build import build_gold
from ingestion import ingest_bronze
from quality_checks import run_quality_checks
from silver_transformation import transform_silver

STEPS = [
    ("bronze", ingest_bronze),
    ("silver", transform_silver),
    ("gold", build_gold),
    ("quality", run_quality_checks),
]


def main():
    parser = argparse.ArgumentParser(description="Pipeline Brazilian E-commerce")
    parser.add_argument("--from", dest="start", choices=[s for s, _ in STEPS],
                        default="bronze", help="etapa inicial (padrão: bronze)")
    args = parser.parse_args()

    names = [s for s, _ in STEPS]
    steps = STEPS[names.index(args.start):]

    started = time.perf_counter()

    for name, step in steps:
        print(f"\n>>> ETAPA: {name.upper()}\n")
        try:
            step()
        except SystemExit as exc:
            if exc.code not in (0, None):
                print(f"\nPIPELINE INTERROMPIDO NA ETAPA: {name.upper()}")
                raise

    elapsed = time.perf_counter() - started
    print("\n" + "#" * 60)
    print(f"PIPELINE CONCLUÍDO: {' -> '.join(n for n, _ in steps)}")
    print(f"Tempo total: {elapsed:.1f} s")
    print("#" * 60)


if __name__ == "__main__":
    main()
