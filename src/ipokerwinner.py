import random
from itertools import combinations
from functools import lru_cache

# Emojis para os naipes
NAIPES = {'S': '♤', 'H': '♡', 'D': '♢', 'C': '♧'}

# Valor das cartas
CARTAS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

# Gerar todas as cartas possíveis
BARALHO = [f"{valor}{naipe}" for valor in CARTAS.keys() for naipe in NAIPES.keys()]

# Função para perguntar a ação de um jogador
def perguntar_acao(jogador, pot, aposta_atual, fase, usuario, num_jogadores, jogadores_ativos):
    while True:
        acao = input(f"\nQual foi a ação do jogador {jogador}? (fold, call, check, raise): ").lower()
        if acao in ['fold', 'call', 'check', 'raise']:
            break
        print("Ação inválida. Escolha entre fold, call, check ou raise.")
    
    # Verifica se o jogador é o usuário e dá sugestão de ação
    if jogador == usuario:
        print("Sugestão: Escolha entre 'fold', 'call', 'check' ou 'raise'.")
    
    if acao == 'fold':
        if jogador != usuario:
            jogadores_ativos.remove(jogador)
        return acao, pot, aposta_atual, jogadores_ativos

    if acao == 'call':
        pot += aposta_atual
        return acao, pot, aposta_atual, jogadores_ativos

    if acao == 'raise':
        valor_raise = int(input(f"Qual foi o valor do raise do jogador {jogador}? $"))
        pot += valor_raise
        aposta_atual = valor_raise
        return acao, pot, aposta_atual, jogadores_ativos

    return acao, pot, aposta_atual, jogadores_ativos

# Simulação de Monte Carlo para calcular equidade
def calcular_equidade(hand, board, num_oponentes, iteracoes=5000):
    cartas_conhecidas = set(hand + board)
    baralho_disponivel = [carta for carta in BARALHO if carta not in cartas_conhecidas]

    vitorias = 0
    total_simulacoes = 0

    for _ in range(iteracoes):
        random.shuffle(baralho_disponivel)
        cartas_comunitarias = board[:]
        cartas_faltantes = 5 - len(cartas_comunitarias)
        cartas_comunitarias.extend(baralho_disponivel[:cartas_faltantes])

        minha_mao = hand + cartas_comunitarias
        mao_oponente = random.sample(baralho_disponivel[cartas_faltantes:], 2) + cartas_comunitarias

        if avaliar_forca(tuple(minha_mao)) > avaliar_forca(tuple(mao_oponente)):
            vitorias += 1

        total_simulacoes += 1

    equidade = (vitorias / total_simulacoes) * 100
    return round(equidade, 2)

# Avaliação de força da mão
@lru_cache(None)
def avaliar_forca(mao):
    valores = sorted([CARTAS[carta[0]] for carta in mao], reverse=True)
    naipes = [carta[1] for carta in mao]

    is_flush = len(set(naipes)) == 1
    is_straight = all(valores[i] == valores[i+1] + 1 for i in range(len(valores)-1))

    if is_flush and is_straight and valores[0] == 14:
        return 10  # Royal Flush
    elif is_flush and is_straight:
        return 9   # Straight Flush
    elif any(valores.count(val) == 4 for val in valores):
        return 8   # Quadra
    elif any(valores.count(val) == 3 for val in valores) and any(valores.count(val) == 2 for val in valores):
        return 7   # Full House
    elif is_flush:
        return 6   # Flush
    elif is_straight:
        return 5   # Sequência
    elif any(valores.count(val) == 3 for val in valores):
        return 4   # Trinca
    elif list(valores.count(val) for val in valores).count(2) == 2:
        return 3   # Dois Pares
    elif any(valores.count(val) == 2 for val in valores):
        return 2   # Par
    else:
        return 1   # Carta Alta

# Recomendar jogada com base na equidade e apostas
def recomendar_jogada(equidade, aposta_atual, pot, ultimo_raise=None):
    if equidade < 20:
        return "Fold"
    elif equidade < 40:
        return "Call" if aposta_atual > 0 else "Check"
    else:
        if ultimo_raise is None:
            base = pot
        else:
            base = ultimo_raise
        
        sugestoes = {
            "1/4x": int(base * 0.25),
            "1/2x": int(base * 0.5),
            "1x": base,
            "2x": base * 2,
            "3x": base * 3,
            "All-in": pot  # Supondo que o all-in seja o valor total do pote
        }
        
        print("\nSugestões de Raise:")
        for opcao, valor in sugestoes.items():
            print(f"{opcao}: ${valor}")
        
        return "Raise"

# Função para perguntar as ações dos jogadores na ordem correta
def perguntar_acoes_jogadores(total_jogadores, posicao_usuario, pot, aposta_atual, fase, usuario, jogadores_ativos, ultimo_raise=None):
    # Ordem de ação: jogadores antes do usuário, usuário, jogadores após o usuário, e finalmente os blinds
    for i in range(1, total_jogadores + 1):  # Todos os jogadores, incluindo Small Blind e Big Blind
        if i in jogadores_ativos:
            acao, pot, aposta_atual, jogadores_ativos = perguntar_acao(i, pot, aposta_atual, fase, usuario, total_jogadores, jogadores_ativos)
            if acao == 'raise':
                ultimo_raise = aposta_atual
    
    # Fechar o ciclo: garantir que todos os jogadores ativos tenham a oportunidade de agir novamente
    for i in range(1, total_jogadores + 1):
        if i in jogadores_ativos:
            acao, pot, aposta_atual, jogadores_ativos = perguntar_acao(i, pot, aposta_atual, fase, usuario, total_jogadores, jogadores_ativos)
            if acao == 'raise':
                ultimo_raise = aposta_atual
    
    return pot, aposta_atual, jogadores_ativos, ultimo_raise

# Função principal
def main():
    print("Bem-vindo ao Simulador de Texas Hold'em!")

    num_jogadores = int(input("Quantos jogadores estão na mesa (excluindo você)? "))
    total_jogadores = num_jogadores + 1
    posicao_usuario = int(input(f"Qual é a sua posição de jogada após os blinds? (1 a {total_jogadores}): "))

    pot = 150  # Small Blind ($50) + Big Blind ($100)
    aposta_atual = 100  # Big Blind

    print("\nSmall Blind ($50) e Big Blind ($100) são postados.")

    # Cartas do jogador
    global hand
    hand = [input(f"Digite a carta {i+1} da sua mão (ex: AH para Ás de Copas): ").upper() for i in range(2)]
    print(f"\nSua mão: {[carta + NAIPES[carta[-1]] for carta in hand]}")

    # Lista de jogadores ativos
    jogadores_ativos = list(range(1, total_jogadores + 1))

    # *** PRÉ-FLOP ***

    print("\n--- Ações Pré-Flop ---")
    fase = 'pré-flop'
    ultimo_raise = None

    # Perguntar ações dos jogadores na ordem correta
    pot, aposta_atual, jogadores_ativos, ultimo_raise = perguntar_acoes_jogadores(total_jogadores, posicao_usuario, pot, aposta_atual, fase, posicao_usuario, jogadores_ativos, ultimo_raise)

    # *** FLOP ***
    print("\n--- Fase do Flop ---")
    board = [input(f"Digite a carta {i+1} do flop: ").upper() for i in range(3)]
    print(f"\nBoard (Flop): {[carta + NAIPES[carta[-1]] for carta in board]}")

    fase = 'flop'
    pot, aposta_atual, jogadores_ativos, ultimo_raise = perguntar_acoes_jogadores(total_jogadores, posicao_usuario, pot, aposta_atual, fase, posicao_usuario, jogadores_ativos, ultimo_raise)

    equidade = calcular_equidade(hand, board, num_jogadores)
    print(f"\nEquidade (flop): {equidade}%")
    print(f"\nRecomendação: {recomendar_jogada(equidade, aposta_atual, pot, ultimo_raise)}")

    # *** TURN ***
    print("\n--- Fase do Turn ---")
    board.append(input("Digite a carta do turn: ").upper())
    print(f"\nBoard (Turn): {[carta + NAIPES[carta[-1]] for carta in board]}")

    fase = 'turn'
    pot, aposta_atual, jogadores_ativos, ultimo_raise = perguntar_acoes_jogadores(total_jogadores, posicao_usuario, pot, aposta_atual, fase, posicao_usuario, jogadores_ativos, ultimo_raise)

    equidade = calcular_equidade(hand, board, num_jogadores)
    print(f"\nEquidade (turn): {equidade}%")
    print(f"\nRecomendação: {recomendar_jogada(equidade, aposta_atual, pot, ultimo_raise)}")

    # *** RIVER ***
    print("\n--- Fase do River ---")
    board.append(input("Digite a carta do river: ").upper())
    print(f"\nBoard (River): {[carta + NAIPES[carta[-1]] for carta in board]}")

    fase = 'river'
    pot, aposta_atual, jogadores_ativos, ultimo_raise = perguntar_acoes_jogadores(total_jogadores, posicao_usuario, pot, aposta_atual, fase, posicao_usuario, jogadores_ativos, ultimo_raise)

    equidade = calcular_equidade(hand, board, num_jogadores)
    print(f"\nEquidade (river): {equidade}%")
    print(f"\nRecomendação: {recomendar_jogada(equidade, aposta_atual, pot, ultimo_raise)}")

    print("\n--- Showdown ---")
    print("Fim da rodada! Revelem suas cartas!")

if __name__ == "__main__":
    main()