import sqlite3
from datetime import datetime

conn = sqlite3.connect('banco.db')
cursor = conn.cursor()

# Criar tabela de usuários
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nascimento TEXT NOT NULL,
        cpf TEXT NOT NULL UNIQUE,
        endereco TEXT NOT NULL,
        n TEXT NOT NULL,
        bairro TEXT NOT NULL,
        cidade TEXT NOT NULL
    )
''')

# Criar tabela de contas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero INTEGER NOT NULL,
        agencia TEXT NOT NULL,
        saldo REAL NOT NULL,
        limite REAL NOT NULL,
        numero_saques INTEGER NOT NULL,
        LIMITE_SAQUES INTEGER NOT NULL,
        usuario_id INTEGER NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
''')

# Criar tabela de movimentações
cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL,
        data TEXT NOT NULL,
        conta_id INTEGER NOT NULL,
        FOREIGN KEY (conta_id) REFERENCES contas(id)
    )
''')

conn.commit()


class Usuario:
    def __init__(self, nome, data_nascimento, cpf, endereco, n, bairro, cidade):
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf
        self.endereco = endereco
        self.n = n
        self.bairro = bairro
        self.cidade = cidade
        self.conta = None  # Inicialmente, o usuário não tem conta


class Conta:
    def __init__(self, numero, agencia='0001'):
        self.numero = numero
        self.agencia = agencia
        self.saldo = 0
        self.limite = 500
        self.numero_saques = 0
        self.LIMITE_SAQUES = 3


def depositar(conta, valor):
    conta.saldo += valor
    registrar_movimentacao(conta, 'Depósito', valor)


def sacar(conta, valor):
    excedeu_saldo = valor > conta.saldo
    excedeu_limite = valor > conta.limite
    excedeu_saques = conta.numero_saques >= conta.LIMITE_SAQUES

    if excedeu_saldo:
        print("\nOperação falhou! Saldo insuficiente.")
    elif excedeu_limite:
        print("\nOperação falhou! O valor do saque excede o limite diário de 3 saques de R$ 500.00.")
    elif excedeu_saques:
        print("\nOperação falhou! Número de 3 saques diários atingidos.")
    else:
        conta.saldo -= valor
        conta.numero_saques += 1
        registrar_movimentacao(conta, 'Saque', valor)


def extrato(conta):
    cursor.execute('SELECT * FROM movimentacoes WHERE conta_id = ?', (conta.id,))
    movimentacoes = cursor.fetchall()

    print("\n=================== EXTRATO =====================")
    for movimentacao in movimentacoes:
        print(f"{movimentacao[3]} - {movimentacao[1]}: R$ {movimentacao[2]:.2f}")
    print(f'\nSaldo: R$ {conta.saldo:.2f}')
    print("\n=================== EXTRATO =====================")


def criar_usuario():
    nome = input("Nome completo: ")
    data_nascimento = input("Data de Nascimento (dd/mm/aaaa): ")
    cpf = input("CPF: ")
    endereco = input("Endereço: ")
    n = input("Número: ")
    bairro = input("Bairro: ")
    cidade = input("Cidade - Estado: ")

    try:
        cursor.execute('INSERT INTO usuarios (nome, data_nascimento, cpf, endereco, n, bairro, cidade) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (nome, data_nascimento, cpf, endereco, n, bairro, cidade))
        conn.commit()
        print("Usuário criado com sucesso!")
    except sqlite3.IntegrityError:
        print("CPF já cadastrado.")
        return None

    usuario = Usuario(nome, data_nascimento, cpf, endereco, n, bairro, cidade)
    return usuario


def criar_conta(usuario):
    cursor.execute('SELECT * FROM contas WHERE usuario_id = ?', (usuario.id,))
    conta_info = cursor.fetchone()

    if conta_info:
        print("Usuário já possui uma conta associada.")
    else:
        cursor.execute('INSERT INTO contas (numero, agencia, saldo, limite, numero_saques, LIMITE_SAQUES, usuario_id) '
                       'VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (usuario.id, '0001', 0, 500, 0, 3, usuario.id))
        conn.commit()
        print("Nova conta criada com sucesso!")


def excluir_conta(cpf):
    cursor.execute('SELECT * FROM usuarios WHERE cpf = ?', (cpf,))
    usuario_info = cursor.fetchone()

    if usuario_info:
        usuario_id = usuario_info[0]
        cursor.execute('SELECT * FROM contas WHERE usuario_id = ?', (usuario_id,))
        conta_info = cursor.fetchone()

        if conta_info:
            conta_id = conta_info[0]
            if conta_info[3] != 0:
                print("A conta não pode ser excluída pois ainda possui saldo.")
            else:
                cursor.execute('DELETE FROM contas WHERE id = ?', (conta_id,))
                conn.commit()
                print("Conta excluída com sucesso!")
        else:
            print("Usuário não possui uma conta associada.")
    else:
        print("Usuário não encontrado.")


def entrar_na_conta(usuario):
    cursor.execute('SELECT * FROM contas WHERE usuario_id = ?', (usuario.id,))
    conta_info = cursor.fetchone()

    if conta_info:
        conta = Conta(numero=conta_info[1], agencia=conta_info[2])
        conta.id = conta_info[0]
        conta.saldo = conta_info[3]
        conta.limite = conta_info[4]
        conta.numero_saques = conta_info[5]
        conta.LIMITE_SAQUES = conta_info[6]

        menu_conta = """
[D] Depositar
[E] Extrato
[S] Saque
[X] Excluir Conta
[Q] Sair

=> """

        while True:
            opcao = str(input(menu_conta))

            if opcao.lower() == 'd':
                try:
                    valor = float(input("\nInforme o valor do depósito: R$ "))
                    if valor > 0:
                        depositar(conta, valor)
                    else:
                        print("\nOperação falhou! O valor informado é inválido.")
                except ValueError:
                    print("\nOperação falhou! Valor inválido. Certifique-se de inserir um número válido.")

            elif opcao.lower() == 's':
                try:
                    valor = float(input("\nInforme o valor do saque: R$ "))
                    sacar(conta, valor)
                except ValueError:
                    print("\nOperação falhou! Valor inválido. Certifique-se de inserir um número válido.")

            elif opcao.lower() == 'e':
                extrato(conta)

            elif opcao.lower() == 'x':
                excluir_conta(usuario.cpf)
                break

            elif opcao.lower() == 'q':
                print("\nSaindo da conta.")
                sair_da_conta(conta)
                break

            else:
                print("\nOperação inválida! Escolha uma opção válida.")

    else:
        print("Usuário não possui uma conta associada.")
        opcao = input("Deseja criar uma conta agora? (s/n): ")
        if opcao.lower() == 's':
            criar_conta(usuario)


def listar_contas():
    cursor.execute('SELECT * FROM contas')
    contas_info = cursor.fetchall()

    print("\n=================== LISTA DE CONTAS =====================")
    for conta_info in contas_info:
        print(f"Conta {conta_info[1]} - Agência: {conta_info[2]} - Saldo: R$ {conta_info[3]:.2f}")
    print("===========================================================")


def registrar_movimentacao(conta, tipo, valor):
    data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO movimentacoes (tipo, valor, data, conta_id) VALUES (?, ?, ?, ?)',
                   (tipo, valor, data, conta.id))
    conn.commit()


def sair_da_conta(conta):
    cursor.execute('UPDATE contas SET saldo = ?, numero_saques = ? WHERE id = ?',
                   (conta.saldo, conta.numero_saques, conta.id))
    conn.commit()


menu_principal = """
[C] Criar Usuário
[L] Listar Contas
[E] Entrar na Conta
[Q] Sair

=> """

while True:
    opcao_principal = str(input(menu_principal))

    if opcao_principal.lower() == 'c':
        usuario = criar_usuario()

    elif opcao_principal.lower() == 'l':
        listar_contas()

    elif opcao_principal.lower() == 'e':
        cpf = input("Informe o CPF do usuário para entrar na conta: ")
        cursor.execute('SELECT * FROM usuarios WHERE cpf = ?', (cpf,))
        usuario_info = cursor.fetchone()

        if usuario_info:
            usuario = Usuario(usuario_info[1], usuario_info[2], usuario_info[3], usuario_info[4], usuario_info[5], usuario_info[6], usuario_info[7])
            usuario.id = usuario_info[0]
            entrar_na_conta(usuario)
        else:
            print("Usuário não encontrado.")

    elif opcao_principal.lower() == 'q':
        print("\nLogoff realizado")
        break

    else:
        print("\nOperação inválida! Escolha uma opção válida.")

conn.close()
