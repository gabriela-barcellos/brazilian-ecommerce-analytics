"""
BRAZILIAN E-COMMERCE | TESTE DA API

Chama a API em execução e compara as respostas com os valores da
dashboard.html (KPIs fixos das páginas 2 e 3 e totais recalculados a
partir dos dados embutidos na página 1, com a regra correta de pagamento).

Uso (com a API rodando em outro terminal):
    python Scripts\\test_api.py
    python Scripts\\test_api.py --url http://127.0.0.1:8000
Sem dependências extras (só biblioteca padrão).
"""

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request

results = []


def get(base, path, **params):
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{base}{path}" + (f"?{query}" if query else "")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, None


def check(name, got, expected):
    ok = got == expected
    results.append(ok)
    print(f"  {'OK' if ok else 'FAIL':<5} {name:<52} {got if ok else f'obtido={got} esperado={expected}'}")


def r2(x):
    return None if x is None else round(x, 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    base = parser.parse_args().url.rstrip("/")

    print("=" * 70)
    print(f"BRAZILIAN E-COMMERCE | TESTE DA API  ({base})")
    print("=" * 70)

    # ---------------- saúde ----------------
    print("\n[HEALTH]")
    status, body = get(base, "/api/health")
    check("status HTTP", status, 200)
    check("banco", body and body["database"], "ok")
    check("última qualidade sem falhas críticas",
          body and body["last_quality"] and body["last_quality"]["critical_failures"], 0)

    # ---------------- filtros ----------------
    print("\n[FILTROS]")
    _, f = get(base, "/api/filters")
    check("meses", len(f["periods"]), 24)
    check("estados", len(f["states"]), 27)
    check("categorias", len(f["categories"]), 74)
    check("tipos de pagamento (pedidos com itens)", f["payment_types"],
          ["boleto", "credit_card", "debit_card", "voucher"])

    # ---------------- comercial ----------------
    print("\n[COMERCIAL]")
    cases = [  # filtros -> (receita, pedidos, clientes)
        ({}, (13591643.70, 98666, 95420)),
        ({"period": "2018-05"}, (996517.68, 6853, 6795)),
        ({"state": "SP", "category": "beleza_saude"}, (462305.22, 3789, 3718)),
        ({"payment": "voucher"}, (416938.30, 3766, 3673)),
        ({"period": "2017-11", "state": "RJ", "payment": "boleto"}, (20402.18, 175, 173)),
        ({"category": "Sem categoria"}, (179535.28, 1451, 1445)),
    ]
    for params, expected in cases:
        _, c = get(base, "/api/commercial", **params)
        k = c["kpis"]
        check(f"KPIs {params or 'sem filtro'}",
              (r2(k["revenue"]), k["orders"], k["customers"]), expected)

    _, c = get(base, "/api/commercial")
    check("ticket médio", r2(c["kpis"]["average_ticket"]), 137.75)
    check("categoria líder", c["categories"][0]["category_label"], "Beleza Saude")
    check("estado líder", c["states"][0]["state"], "SP")
    check("pagamento predominante", c["payments"][0]["payment_type"], "credit_card")
    check("receita mensal soma o total", r2(sum(m["revenue"] for m in c["monthly"])), 13591643.70)

    _, c = get(base, "/api/commercial", period="2018-05")
    check("comparação 2018-05 vs mês anterior",
          (c["comparison"]["previous_period"], r2(c["comparison"]["previous_revenue"])),
          ("2018-04", 996647.75))
    _, c = get(base, "/api/commercial", period="2018-09")
    check("set/2018 parcial sem comparação", c["comparison"], None)

    status, _ = get(base, "/api/commercial", period="2018-5")
    check("período inválido rejeitado (422)", status, 422)
    status, _ = get(base, "/api/commercial", period="", state="", category="", payment="")
    check("filtros vazios aceitos", status, 200)

    # ---------------- logística ----------------
    print("\n[LOGÍSTICA]")
    _, lg = get(base, "/api/logistics")
    k = lg["kpis"]
    check("pedidos entregues com data válida", k["orders"], 96470)
    check("tempo médio (dias)", r2(k["avg_days"]), 12.56)
    check("mediana (dias)", r2(k["median_days"]), 10.22)
    check("no prazo (%)", r2(k["on_time_pct"]), 91.89)
    check("em atraso (%)", r2(k["late_pct"]), 8.11)
    check("antecipação média (dias)", r2(k["early_days"]), 11.18)
    check("meses na evolução", len(lg["monthly"]), 23)
    check("estado com menor pontualidade", (lg["states"][0]["customer_state"],
          r2(lg["states"][0]["on_time"] * 100)), ("AL", 76.07))
    check("estados listados", len(lg["states"]), 12)
    check("status delivered", lg["status"][0]["order_status"], "delivered")
    check("total de pedidos (status)", lg["total_orders"], 99441)
    check("delivered (% de todos os pedidos)", r2(lg["status"][0]["share_pct"]), 97.02)

    # ---------------- investigação ----------------
    print("\n[INVESTIGAÇÃO]")
    _, inv = get(base, "/api/investigation")
    k = inv["kpis"]
    check("pedidos com distância", k["orders_with_distance"], 95994)
    check("Spearman distância x tempo", round(k["spearman_distance_days"], 3), 0.543)
    check("Spearman distância x (real - estimada)", round(k["spearman_distance_delay"], 3), -0.179)
    check("atraso acima de 2.000 km (%)", r2(k["late_pct_over_2000km"]), 13.66)
    check("frete médio acima de 2.000 km", r2(k["avg_freight_over_2000km"]), 39.88)
    check("faixas: dias", [r2(b["avg_days"]) for b in inv["distance_bands"]],
          [6.51, 9.96, 12.63, 14.72, 17.95, 21.18])
    check("faixas: atraso (%)", [r2(b["late_pct"]) for b in inv["distance_bands"]],
          [6.43, 6.37, 7.77, 8.45, 10.76, 13.66])
    check("faixas: frete", [r2(b["avg_freight"]) for b in inv["distance_bands"]],
          [13.35, 18.83, 22.39, 24.85, 33.09, 39.88])
    check("cortes de frete", [r2(c) for c in inv["freight_cuts"]], [12.83, 15.64, 18.59, 27.38])
    check("frete médio por faixa", [r2(b["avg_freight"]) for b in inv["freight_bands"]],
          [9.75, 14.48, 17.19, 22.23, 50.36])
    check("atraso por faixa de frete (%)", [r2(b["late_pct"]) for b in inv["freight_bands"]],
          [6.08, 7.24, 8.86, 9.05, 9.35])
    check("estados com mais atraso", [(s["customer_state"], r2(s["late_pct"])) for s in inv["states"]],
          [("AL", 23.93), ("MA", 19.67), ("PI", 15.97), ("CE", 15.32),
           ("SE", 15.22), ("BA", 14.04), ("RJ", 13.47), ("TO", 12.77)])

    failed = results.count(False)
    print("\n" + "=" * 70)
    print(f"Testes: {len(results)} | falhas: {failed}")
    print("API TESTS PASSED" if not failed else "API TESTS FAILED")
    print("=" * 70)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
