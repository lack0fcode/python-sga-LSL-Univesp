#!/usr/bin/env python3
"""
Script para executar Bandit em todos os apps Django separadamente
e combinar os resultados em um único relatório.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def run_bandit_on_app(app_name):
    """Executa Bandit em um app específico."""
    print(f"Executando Bandit no app: {app_name}")

    cmd = [
        "bandit",
        "--ini",
        ".bandit",
        "-r",
        app_name,
        "-f",
        "json",
        "-o",
        f"bandit_{app_name}_report.json",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )  # 10 minutos timeout
        if (
            result.returncode == 0 or result.returncode == 1
        ):  # 0 = sem issues, 1 = com issues
            print(f"✓ {app_name} concluído")
            return True
        else:
            print(f"✗ Erro no {app_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout no {app_name} (10 minutos)")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado no {app_name}: {e}")
        return False


def combine_reports() -> None:
    """Combina todos os relatórios individuais em um único."""
    combined: Dict[str, Any] = {
        "generated_at": "2025-11-03T16:08:12Z",
        "metrics": {"_totals": {"loc": 0, "nosec": 0, "skipped_tests": 0}},
        "results": [],
        "errors": [],
    }

    apps = [
        "core",
        "administrador",
        "guiche",
        "recepcionista",
        "profissional_saude",
        "api",
        "sga",
    ]

    for app in apps:
        report_file = f"bandit_{app}_report.json"
        if os.path.exists(report_file):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Combinar métricas
                if "_totals" in data.get("metrics", {}):
                    totals: Dict[str, int] = data["metrics"]["_totals"]
                    for key, value in totals.items():
                        if key in combined["metrics"]["_totals"]:
                            combined["metrics"]["_totals"][key] += value
                        else:
                            combined["metrics"]["_totals"][key] = value

                # Combinar resultados
                results: List[Dict[str, Any]] = data.get("results", [])
                errors: List[str] = data.get("errors", [])
                combined["results"].extend(results)
                combined["errors"].extend(errors)

                # Combinar métricas por arquivo
                for file_key, file_metrics in data.get("metrics", {}).items():
                    if file_key != "_totals":
                        combined["metrics"][file_key] = file_metrics

            except Exception as e:
                print(f"Erro ao processar {report_file}: {e}")

    # Salvar relatório combinado
    with open("bandit_full_report.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"Relatório combinado salvo em bandit_full_report.json")
    print(f"Total de vulnerabilidades encontradas: {len(combined['results'])}")


if __name__ == "__main__":
    print("Iniciando análise de segurança com Bandit...")

    apps = [
        "core",
        "administrador",
        "guiche",
        "recepcionista",
        "profissional_saude",
        "api",
        "sga",
    ]

    success_count = 0
    for app in apps:
        if run_bandit_on_app(app):
            success_count += 1

    print(f"\nConcluído: {success_count}/{len(apps)} apps processados com sucesso")

    if success_count == 0:
        print(
            "ERRO: Nenhum app foi processado com sucesso. Abortando combinação de relatórios."
        )
        exit(1)

    if success_count < len(apps):
        print(
            f"AVISO: Apenas {success_count} de {len(apps)} apps foram processados. Combinando relatórios disponíveis."
        )

    combine_reports()
    print("✅ Análise de segurança Bandit concluída com sucesso!")
    exit(0)
