"""
Script para verificar disponibilidade de dados NYC Taxi
Útil para validar quais meses têm dados disponíveis antes de executar a DAG
"""
import sys
import requests
from datetime import datetime, timedelta
import argparse

def check_nyc_taxi_data_availability(year: int, month: int) -> dict:
    """
    Verifica se os dados NYC Taxi estão disponíveis para um determinado mês

    Returns:
        dict com informações sobre disponibilidade
    """
    # URL base do NYC TLC
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data"

    # Formato do arquivo: yellow_tripdata_YYYY-MM.parquet
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"{base_url}/{filename}"

    print(f"Verificando: {url}")

    try:
        # HEAD request para verificar se o arquivo existe sem baixá-lo
        response = requests.head(url, timeout=10)

        if response.status_code == 200:
            size_mb = int(response.headers.get('Content-Length', 0)) / (1024 * 1024)
            return {
                'available': True,
                'url': url,
                'size_mb': round(size_mb, 2),
                'year': year,
                'month': month
            }
        else:
            return {
                'available': False,
                'url': url,
                'status_code': response.status_code,
                'year': year,
                'month': month
            }
    except Exception as e:
        return {
            'available': False,
            'url': url,
            'error': str(e),
            'year': year,
            'month': month
        }

def check_date_range(start_year: int, start_month: int, end_year: int = None, end_month: int = None):
    """
    Verifica disponibilidade de dados para um range de datas
    """
    if end_year is None or end_month is None:
        now = datetime.now()
        end_year = now.year
        end_month = now.month

    results = []
    current_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)

    print("=" * 80)
    print("VERIFICAÇÃO DE DISPONIBILIDADE DE DADOS NYC TAXI")
    print("=" * 80)
    print(f"Período: {start_year}-{start_month:02d} até {end_year}-{end_month:02d}\n")

    while current_date <= end_date:
        result = check_nyc_taxi_data_availability(current_date.year, current_date.month)
        results.append(result)

        if result['available']:
            print(f"[OK] {current_date.year}-{current_date.month:02d}: Disponivel ({result['size_mb']} MB)")
        else:
            error_msg = result.get('error', f"HTTP {result.get('status_code', 'N/A')}")
            print(f"[X] {current_date.year}-{current_date.month:02d}: Nao disponivel ({error_msg})")

        # Próximo mês
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)

    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)
    available_count = sum(1 for r in results if r['available'])
    total_size = sum(r.get('size_mb', 0) for r in results if r['available'])

    print(f"Total de meses verificados: {len(results)}")
    print(f"Meses disponíveis: {available_count}")
    print(f"Meses não disponíveis: {len(results) - available_count}")
    print(f"Tamanho total estimado: {round(total_size, 2)} MB (~{round(total_size/1024, 2)} GB)")

    if available_count < len(results):
        print("\n[!] ATENCAO: Alguns meses nao estao disponiveis!")
        print("Recomendacao: Ajuste a start_date da DAG para evitar falhas.")
    else:
        print("\n[OK] Todos os meses estao disponiveis!")

    return results

def main():
    parser = argparse.ArgumentParser(
        description='Verifica disponibilidade de dados NYC Taxi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Verificar apenas janeiro de 2024
  python check_data_availability.py --year 2024 --month 1

  # Verificar de janeiro de 2023 até hoje
  python check_data_availability.py --start-year 2023 --start-month 1

  # Verificar range específico
  python check_data_availability.py --start-year 2023 --start-month 1 --end-year 2024 --end-month 6
        """
    )

    parser.add_argument('--year', type=int, help='Ano único para verificar')
    parser.add_argument('--month', type=int, help='Mês único para verificar')
    parser.add_argument('--start-year', type=int, help='Ano inicial do range')
    parser.add_argument('--start-month', type=int, help='Mês inicial do range')
    parser.add_argument('--end-year', type=int, help='Ano final do range (default: hoje)')
    parser.add_argument('--end-month', type=int, help='Mês final do range (default: hoje)')

    args = parser.parse_args()

    # Verificação de mês único
    if args.year and args.month:
        result = check_nyc_taxi_data_availability(args.year, args.month)
        print("=" * 80)
        if result['available']:
            print(f"[OK] Dados disponiveis para {args.year}-{args.month:02d}")
            print(f"  URL: {result['url']}")
            print(f"  Tamanho: {result['size_mb']} MB")
        else:
            print(f"[X] Dados NAO disponiveis para {args.year}-{args.month:02d}")
            if 'error' in result:
                print(f"  Erro: {result['error']}")
            else:
                print(f"  Status HTTP: {result.get('status_code', 'N/A')}")
        print("=" * 80)
        return

    # Verificação de range
    if args.start_year and args.start_month:
        check_date_range(args.start_year, args.start_month, args.end_year, args.end_month)
        return

    # Default: verificar últimos 3 meses
    print("Nenhum parâmetro fornecido. Verificando últimos 3 meses...\n")
    now = datetime.now()
    start_date = now - timedelta(days=90)
    check_date_range(start_date.year, start_date.month, now.year, now.month)

if __name__ == "__main__":
    main()
