"""
Script auxiliar para gerenciar o banco de dados EFD-REINF
Útil para visualizar, limpar ou exportar declarações
"""

import sqlite3
import csv
import json
import os
from datetime import datetime

def conectar():
    """Conecta ao banco de dados"""
    return sqlite3.connect('cadastros.db')


def limpar_checkpoint():
    """Remove o arquivo de checkpoint para reiniciar o processamento."""
    if os.path.exists('checkpoint.txt'):
        try:
            os.remove('checkpoint.txt')
            print("🧹 Checkpoint removido. Processamento reiniciará do primeiro grupo.")
        except OSError as exc:
            print(f"⚠️ Não foi possível remover o checkpoint: {exc}")


def estatisticas():
    """Mostra estatísticas das declarações EFD-REINF"""
    conn = conectar()
    cursor = conn.cursor()
    
    # Total de declarações
    cursor.execute('SELECT COUNT(*) FROM efd_declaracoes')
    total = cursor.fetchone()[0]
    
    # Total de dependentes
    cursor.execute('SELECT dependentes FROM efd_declaracoes WHERE dependentes IS NOT NULL AND dependentes != "[]"')
    dependentes_data = cursor.fetchall()
    total_dependentes = 0
    for dep_data in dependentes_data:
        if dep_data[0]:
            dependentes = json.loads(dep_data[0])
            total_dependentes += len(dependentes)
    
    # Total de planos de saúde
    cursor.execute('SELECT planos_saude FROM efd_declaracoes WHERE planos_saude IS NOT NULL AND planos_saude != "[]"')
    planos_data = cursor.fetchall()
    total_planos = 0
    for plano_data in planos_data:
        if plano_data[0]:
            planos = json.loads(plano_data[0])
            total_planos += len(planos)
    
    # Total de informações de dependentes
    cursor.execute('SELECT dependentes_planos FROM efd_declaracoes WHERE dependentes_planos IS NOT NULL AND dependentes_planos != "[]"')
    dep_planos_data = cursor.fetchall()
    total_dep_planos = 0
    for dp_data in dep_planos_data:
        if dp_data[0]:
            dep_planos = json.loads(dp_data[0])
            total_dep_planos += len(dep_planos)
    
    conn.close()
    
    print("\n" + "="*80)
    print("📊 ESTATÍSTICAS EFD-REINF")
    print("="*80)
    
    print(f"\n📈 Total de declarações: {total}")
    print(f"👥 Total de dependentes: {total_dependentes}")
    print(f"🏥 Total de planos de saúde: {total_planos}")
    print(f"💰 Total de informações de dependentes: {total_dep_planos}")
    
    if total > 0:
        print(f"\n📊 Médias por declaração:")
        print(f"  • Dependentes: {total_dependentes/total:.1f}")
        print(f"  • Planos de saúde: {total_planos/total:.1f}")
        print(f"  • Informações de dependentes: {total_dep_planos/total:.1f}")
    
    print("\n" + "="*80 + "\n")

def buscar_por_cpf(cpf):
    """Busca declarações por CPF"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM efd_declaracoes WHERE cpf LIKE ?', (f'%{cpf}%',))
    resultados = cursor.fetchall()
    conn.close()
    
    if not resultados:
        print(f"\n❌ Nenhuma declaração encontrada com CPF '{cpf}'\n")
        return
    
    print(f"\n🔍 {len(resultados)} declaração(ões) encontrada(s):\n")
    for dec in resultados:
        print(f"🆔 #{dec[0]} - CPF: {dec[3]} - CNPJ: {dec[2]} - Data: {dec[1]}")

def limpar_banco():
    """Limpa todos os registros do banco"""
    resposta = input("⚠️  ATENÇÃO: Isso irá APAGAR TODAS as declarações EFD-REINF. Confirma? (sim/não): ")
    
    if resposta.lower() == 'sim':
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM efd_declaracoes')
        linhas_afetadas = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"\n✅ {linhas_afetadas} declaração(ões) removida(s)\n")
        limpar_checkpoint()
    else:
        print("\n❌ Operação cancelada\n")

def exportar_csv():
    """Exporta declarações EFD-REINF para CSV"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM efd_declaracoes')
    declaracoes = cursor.fetchall()
    conn.close()
    
    if not declaracoes:
        print("\n❌ Nenhuma declaração para exportar\n")
        return
    
    nome_arquivo = f"efd_declaracoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo:
        writer = csv.writer(arquivo)
        
        # Cabeçalho
        writer.writerow([
            'ID', 'Data', 'CNPJ', 'CPF', 'Dependentes', 
            'Planos_Saude', 'Dependentes_Planos', 'Data_Cadastro'
        ])
        
        # Dados
        writer.writerows(declaracoes)
    
    print(f"\n✅ Dados exportados para: {nome_arquivo}\n")

def deletar_por_id(id_declaracao):
    """Deleta uma declaração específica"""
    conn = conectar()
    cursor = conn.cursor()
    
    # Verificar se existe
    cursor.execute('SELECT cpf, cnpj FROM efd_declaracoes WHERE id = ?', (id_declaracao,))
    resultado = cursor.fetchone()
    
    if not resultado:
        print(f"\n❌ Declaração #{id_declaracao} não encontrada\n")
        conn.close()
        return
    
    cpf = resultado[0]
    cnpj = resultado[1]
    resposta = input(f"⚠️  Deseja deletar a declaração #{id_declaracao} (CPF: {cpf}, CNPJ: {cnpj})? (sim/não): ")
    
    if resposta.lower() == 'sim':
        cursor.execute('DELETE FROM efd_declaracoes WHERE id = ?', (id_declaracao,))
        conn.commit()
        print(f"\n✅ Declaração #{id_declaracao} deletada com sucesso\n")
    else:
        print("\n❌ Operação cancelada\n")
    
    conn.close()

def mostrar_status_ids():
    """Mostra o status atual dos IDs"""
    print("📊 Status dos IDs do banco de dados:")
    
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT COUNT(*) FROM efd_declaracoes')
        total = cursor.fetchone()[0]
        
        if total == 0:
            print("📭 Nenhuma declaração encontrada.")
        else:
            cursor.execute('SELECT MIN(id), MAX(id) FROM efd_declaracoes')
            min_id, max_id = cursor.fetchone()
            print(f"📈 Total de declarações: {total}")
            print(f"🆔 ID mínimo: {min_id}")
            print(f"🆔 ID máximo: {max_id}")
            
            # Verificar se há gaps
            cursor.execute('SELECT id FROM efd_declaracoes ORDER BY id')
            ids = [row[0] for row in cursor.fetchall()]
            ids_esperados = list(range(1, total + 1))
            
            if ids == ids_esperados:
                print("✅ IDs estão sequenciais (1, 2, 3, ...)")
            else:
                print("⚠️ IDs não estão sequenciais")
                print(f"   IDs atuais: {ids}")
                print(f"   IDs esperados: {ids_esperados}")
    
    except Exception as e:
        print(f"❌ Erro ao verificar status: {str(e)}")
    finally:
        conn.close()

def resetar_ids():
    """Reseta os IDs da tabela efd_declaracoes"""
    print("🔄 Resetando IDs do banco de dados...")
    
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se há dados
        cursor.execute('SELECT COUNT(*) FROM efd_declaracoes')
        total = cursor.fetchone()[0]
        
        if total == 0:
            print("📭 Nenhuma declaração encontrada para resetar.")
            conn.close()
            return
        
        print(f"📊 Total de declarações: {total}")
        
        # Mostrar IDs atuais
        cursor.execute('SELECT id FROM efd_declaracoes ORDER BY id')
        ids_atuais = [row[0] for row in cursor.fetchall()]
        print(f"🆔 IDs atuais: {ids_atuais}")
        
        # Confirmar operação
        resposta = input(f"\n⚠️  Deseja resetar os IDs de {total} declarações? (sim/não): ")
        
        if resposta.lower() != 'sim':
            print("❌ Operação cancelada.")
            conn.close()
            return
        
        # Criar tabela temporária com dados
        cursor.execute('''
            CREATE TABLE efd_declaracoes_temp AS 
            SELECT * FROM efd_declaracoes ORDER BY data_cadastro
        ''')
        
        # Limpar tabela original
        cursor.execute('DELETE FROM efd_declaracoes')
        
        # Resetar sequência do ID
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="efd_declaracoes"')
        
        # Inserir dados com novos IDs sequenciais
        cursor.execute('''
            INSERT INTO efd_declaracoes (data, cnpj, cpf, dependentes, planos_saude, dependentes_planos, data_cadastro)
            SELECT data, cnpj, cpf, dependentes, planos_saude, dependentes_planos, data_cadastro
            FROM efd_declaracoes_temp
        ''')
        
        # Remover tabela temporária
        cursor.execute('DROP TABLE efd_declaracoes_temp')
        
        # Confirmar alterações
        conn.commit()
        
        # Verificar resultado
        cursor.execute('SELECT id FROM efd_declaracoes ORDER BY id')
        ids_novos = [row[0] for row in cursor.fetchall()]
        print(f"✅ IDs resetados: {ids_novos}")
        
        print(f"\n🎉 Reset concluído! {total} declarações com IDs sequenciais de 1 a {total}")
        
    except Exception as e:
        print(f"❌ Erro durante o reset: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def reset_completo():
    """Reseta completamente o banco (remove todos os dados)"""
    print("🗑️ Reset completo do banco de dados...")
    
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar dados
        cursor.execute('SELECT COUNT(*) FROM efd_declaracoes')
        total = cursor.fetchone()[0]
        
        if total == 0:
            print("📭 Banco já está vazio.")
            conn.close()
            return
        
        print(f"📊 Total de declarações: {total}")
        
        # Confirmar operação
        resposta = input(f"\n⚠️  ATENÇÃO: Isso irá APAGAR TODAS as {total} declarações! Confirma? (sim/não): ")
        
        if resposta.lower() != 'sim':
            print("❌ Operação cancelada.")
            conn.close()
            return
        
        # Limpar tabela
        cursor.execute('DELETE FROM efd_declaracoes')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="efd_declaracoes"')
        
        conn.commit()
        print(f"✅ {total} declarações removidas. Banco resetado!")
        limpar_checkpoint()
        
    except Exception as e:
        print(f"❌ Erro durante o reset: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def menu():
    """Menu principal"""
    while True:
        print("\n" + "="*70)
        print("🗄️  GERENCIADOR DE BANCO DE DADOS - EFD-REINF")
        print("="*70)
        print("\n1  - Buscar por CPF")
        print("2  - Ver estatísticas")
        print("3  - Exportar para CSV")
        print("4  - Deletar declaração por ID")
        print("5  - Limpar todas as declarações")
        print("6  - Ver status dos IDs")
        print("7  - Resetar IDs (reorganizar)")
        print("8  - Reset completo (apagar tudo)")
        print("0  - Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            cpf = input("Digite o CPF para buscar: ")
            buscar_por_cpf(cpf)
        elif opcao == "2":
            estatisticas()
        elif opcao == "3":
            exportar_csv()
        elif opcao == "4":
            id_dec = input("Digite o ID da declaração para deletar: ")
            deletar_por_id(int(id_dec))
        elif opcao == "5":
            limpar_banco()
        elif opcao == "6":
            mostrar_status_ids()
        elif opcao == "7":
            resetar_ids()
        elif opcao == "8":
            reset_completo()
        elif opcao == "0":
            print("\n👋 Até logo!\n")
            break
        else:
            print("\n❌ Opção inválida!\n")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\n👋 Programa encerrado pelo usuário\n")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}\n")

