"""
Script de inicialização do dbt
Verifica se o dbt está configurado corretamente e testa a conexão com o banco
"""
import os
import sys
import subprocess
from pathlib import Path

def check_dbt_installation():
    """Verifica se o dbt está instalado"""
    try:
        result = subprocess.run(['dbt', '--version'], capture_output=True, text=True)
        print("✓ dbt instalado:")
        print(result.stdout)
        return True
    except FileNotFoundError:
        print("✗ dbt não encontrado. Execute: pip install dbt-core dbt-postgres")
        return False

def check_environment_variables():
    """Verifica se as variáveis de ambiente necessárias estão configuradas"""
    required_vars = [
        'NYC_POSTGRES_HOST',
        'NYC_POSTGRES_PORT',
        'NYC_POSTGRES_USER',
        'NYC_POSTGRES_PASSWORD',
        'NYC_POSTGRES_DB'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"✗ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("  Certifique-se de que o arquivo .env está configurado corretamente")
        return False
    else:
        print("✓ Todas as variáveis de ambiente necessárias estão configuradas")
        return True

def test_dbt_connection():
    """Testa a conexão do dbt com o banco de dados"""
    dbt_project_dir = Path(__file__).parent.parent / 'dbt_project'

    if not dbt_project_dir.exists():
        print(f"✗ Diretório do projeto dbt não encontrado: {dbt_project_dir}")
        return False

    print(f"\nTestando conexão com o banco de dados...")
    print(f"Diretório do projeto: {dbt_project_dir}")

    try:
        result = subprocess.run(
            ['dbt', 'debug', '--profiles-dir', str(dbt_project_dir), '--project-dir', str(dbt_project_dir)],
            capture_output=True,
            text=True,
            cwd=str(dbt_project_dir)
        )

        print(result.stdout)

        if result.returncode == 0:
            print("✓ Conexão com o banco de dados bem-sucedida!")
            return True
        else:
            print("✗ Falha ao conectar com o banco de dados")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Erro ao testar conexão: {e}")
        return False

def run_dbt_models(select=None):
    """Executa os modelos dbt"""
    dbt_project_dir = Path(__file__).parent.parent / 'dbt_project'

    cmd = ['dbt', 'run', '--profiles-dir', str(dbt_project_dir), '--project-dir', str(dbt_project_dir)]

    if select:
        cmd.extend(['--select', select])

    print(f"\nExecutando modelos dbt...")
    if select:
        print(f"Seleção: {select}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(dbt_project_dir),
            capture_output=True,
            text=True
        )

        print(result.stdout)

        if result.returncode == 0:
            print("✓ Modelos dbt executados com sucesso!")
            return True
        else:
            print("✗ Falha ao executar modelos dbt")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Erro ao executar modelos: {e}")
        return False

def main():
    print("=" * 60)
    print("NYC Taxi Pipeline - Inicialização do dbt")
    print("=" * 60)
    print()

    # Verifica instalação do dbt
    if not check_dbt_installation():
        sys.exit(1)

    # Verifica variáveis de ambiente
    if not check_environment_variables():
        sys.exit(1)

    # Testa conexão
    if not test_dbt_connection():
        sys.exit(1)

    # Pergunta se deseja executar os modelos
    print("\n" + "=" * 60)
    response = input("Deseja executar os modelos dbt agora? (s/N): ").strip().lower()

    if response in ['s', 'sim', 'y', 'yes']:
        # Primeiro cria a estrutura Silver
        print("\n1. Criando estrutura Silver...")
        if run_dbt_models(select='silver'):
            # Depois cria a estrutura Gold (depende do Silver)
            print("\n2. Criando estrutura Gold...")
            run_dbt_models(select='gold')

    print("\n" + "=" * 60)
    print("Inicialização concluída!")
    print("=" * 60)
    print("\nPróximos passos:")
    print("1. Execute a DAG no Airflow para processar os dados")
    print("2. Visualize a documentação: cd dbt_project && dbt docs serve")
    print("3. Execute testes: cd dbt_project && dbt test")

if __name__ == "__main__":
    main()
