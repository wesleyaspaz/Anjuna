import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify

# Inicializa a aplicação Flask
app = Flask(__name__)

# Define o caminho para o arquivo CSV
# O Flask espera que este arquivo esteja no mesmo diretório que o app.py
CSV_FILE_PATH = "hfmea2.csv"

@app.route('/api/hfmea_graph')
def get_hfmea_graph_data():
    """
    Endpoint da API para ler o CSV do HFMEA e formatá-lo para o sigma.js.
    """
    try:
        # Verifica se o arquivo CSV existe
        if not os.path.exists(CSV_FILE_PATH):
            raise FileNotFoundError(f"Arquivo CSV '{CSV_FILE_PATH}' não encontrado no diretório.")

        # --- NOVA LÓGICA DE LEITURA MANUAL ---
        # Em vez de usar pd.read_csv e falhar, lemos o arquivo
        # e processamos linha por linha para corrigir erros de formatação.
        
        all_rows_data = []
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
            # Pula a linha do cabeçalho
            header_line = next(f)
            
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Separa a linha por vírgulas
                fields = line.split(',')
                
                row_data = {}
                
                if len(fields) == 9:
                    # Linha BOA (9 campos)
                    row_data['Etapa do Processo'] = fields[0]
                    row_data['Modo de Falha'] = fields[1]
                    row_data['Causa'] = fields[2]
                    row_data['Efeito Potencial'] = fields[3]
                    row_data['Controles Atuais'] = fields[4]
                    row_data['S'] = fields[5]
                    row_data['O'] = fields[6]
                    row_data['D'] = fields[7]
                    row_data['NPR'] = fields[8]
                elif len(fields) == 10:
                    # Linha RUIM (10 campos) - A vírgula extra está no campo 3 (Efeito)
                    print(f"Linha malformada detectada, corrigindo: {line}")
                    row_data['Etapa do Processo'] = fields[0]
                    row_data['Modo de Falha'] = fields[1]
                    row_data['Causa'] = fields[2]
                    # Junta a 3ª e 4ª colunas para formar o "Efeito Potencial"
                    row_data['Efeito Potencial'] = f"{fields[3]}, {fields[4]}"
                    # Desloca o resto das colunas
                    row_data['Controles Atuais'] = fields[5]
                    row_data['S'] = fields[6]
                    row_data['O'] = fields[7]
                    row_data['D'] = fields[8]
                    row_data['NPR'] = fields[9]
                else:
                    # Ignora linhas com número inesperado de colunas
                    print(f"Ignorando linha com formato inesperado ({len(fields)} campos): {line}")
                    continue
                    
                all_rows_data.append(row_data)
        
        # --- FIM DA NOVA LÓGICA ---

        nodes = []
        edges = []
        node_id_counter = 0
        y_pos = 0  # Posição vertical para cada linha do HFMEA

        # Itera sobre a lista de dicionários que acabamos de criar
        for row_data in all_rows_data:
            
            # Extrai os metadados (S, O, D, NPR) para adicionar aos nós
            node_metadata = {
                "S": row_data.get('S'),
                "O": row_data.get('O'),
                "D": row_data.get('D'),
                "NPR": row_data.get('NPR')
            }

            # 1. Nó de Processo
            processo_id = f"node_{node_id_counter}"
            nodes.append({
                "id": processo_id,
                "label": str(row_data.get('Etapa do Processo', 'N/A')),
                "tipo": "Processo",
                "x": 0,  # Posição X (coluna 0)
                "y": y_pos,
                **node_metadata  # Adiciona S, O, D, NPR
            })
            node_id_counter += 1

            # 2. Nó de Modo de Falha
            falha_id = f"node_{node_id_counter}"
            nodes.append({
                "id": falha_id,
                "label": str(row_data.get('Modo de Falha', 'N/A')),
                "tipo": "Modo de Falha",
                "x": 2,  # Posição X (coluna 2)
                "y": y_pos,
                **node_metadata
            })
            node_id_counter += 1

            # 3. Nó de Causa
            causa_id = f"node_{node_id_counter}"
            nodes.append({
                "id": causa_id,
                "label": str(row_data.get('Causa', 'N/A')),
                "tipo": "Causa",
                "x": 4,  # Posição X (coluna 4)
                "y": y_pos,
                **node_metadata
            })
            node_id_counter += 1

            # 4. Nó de Efeito
            efeito_id = f"node_{node_id_counter}"
            nodes.append({
                "id": efeito_id,
                "label": str(row_data.get('Efeito Potencial', 'N/A')),
                "tipo": "Efeito",
                "x": 6,  # Posição X (coluna 6)
                "y": y_pos,
                **node_metadata
            })
            node_id_counter += 1

            # 5. Nó de Controle
            controle_id = f"node_{node_id_counter}"
            nodes.append({
                "id": controle_id,
                "label": str(row_data.get('Controles Atuais', 'N/A')),
                "tipo": "Controle",
                "x": 8,  # Posição X (coluna 8)
                "y": y_pos,
                **node_metadata
            })
            node_id_counter += 1

            # Adiciona as arestas (ligações) para esta linha
            edges.append({"source": processo_id, "target": falha_id})
            edges.append({"source": falha_id, "target": causa_id})
            edges.append({"source": causa_id, "target": efeito_id})
            edges.append({"source": efeito_id, "target": controle_id})

            # Move a posição Y para a próxima linha do HFMEA
            y_pos -= 2.5  # Aumentei o espaçamento vertical

        # Monta o objeto de dados final
        graph_data = {
            "nome": "HFMEA - Análise de Processo (CSV)",
            "nodes": nodes,
            "edges": edges
        }
        
        return jsonify(graph_data)

    except FileNotFoundError as fnf_error:
        print(f"Erro: {fnf_error}")
        return jsonify({"error": str(fnf_error)}), 404
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Erro ao processar o arquivo: {str(e)}"}), 500

@app.route('/')
def index():
    """
    Serve a página HTML principal.
    """
    return render_template('index.html')

if __name__ == '__main__':
    # Garante que a pasta 'templates' exista
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Pasta 'templates' criada. Por favor, adicione seu 'index.html' nela.")

    # Verifica se o hfmea2.csv está presente
    if not os.path.exists(CSV_FILE_PATH):
        print(f"AVISO: O arquivo '{CSV_FILE_PATH}' não foi encontrado.")
        print("Por favor, coloque o arquivo 'hfmea2.csv' no mesmo diretório que 'app.py'.")

    # Executa a aplicação
    # O host='0.0.0.0' torna a aplicação acessível na sua rede local
    app.run(debug=True, host='0.0.0.0', port=5000)

