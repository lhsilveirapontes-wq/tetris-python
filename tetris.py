import os
import random
import tkinter as tk

# Tenta importar o módulo de som nativo do Windows
try:
    import winsound
except ImportError:
    winsound = None

# Configurações do Jogo
LARGURA_GRID = 10
ALTURA_GRID = 20
TAMANHO_BLOCO = 30

# Tamanho do painel lateral expandido
LARGURA_PAINEL = 180
LARGURA_TELA = (LARGURA_GRID * TAMANHO_BLOCO) + LARGURA_PAINEL
ALTURA_TELA = ALTURA_GRID * TAMANHO_BLOCO

CORES = {
    "I": "#00f0f0",
    "J": "#0000f0",
    "L": "#f0a000",
    "O": "#f0f000",
    "S": "#00f000",
    "T": "#a000f0",
    "Z": "#f00000",
    "FUNDO": "#121212",
    "PAINEL": "#181818",
    "GRADE": "#222222",
    "TEXTO": "#ffffff",
    "GHOST": "#333333",
    "BRANCO": "#ffffff",
}

PECAS = {
    "I": [
        [(-1, 0), (0, 0), (1, 0), (2, 0)],
        [(0, -1), (0, 0), (0, 1), (0, 2)],
    ],
    "J": [
        [(0, -1), (0, 0), (0, 1), (-1, 1)],
        [(-1, 0), (0, 0), (1, 0), (1, 1)],
        [(0, -1), (0, 0), (0, 1), (1, -1)],
        [(-1, -1), (-1, 0), (0, 0), (1, 0)],
    ],
    "L": [
        [(0, -1), (0, 0), (0, 1), (1, 1)],
        [(-1, 0), (0, 0), (1, 0), (-1, 1)],
        [(-1, -1), (0, -1), (0, 0), (0, 1)],
        [(-1, -1), (1, -1), (0, 0), (1, 0)],
    ],
    "O": [[(0, 0), (0, 1), (1, 0), (1, 1)]],
    "S": [
        [(0, 0), (0, 1), (1, -1), (1, 0)],
        [(-1, 0), (0, 0), (0, 1), (1, 1)],
    ],
    "T": [
        [(0, -1), (0, 0), (0, 1), (1, 0)],
        [(-1, 0), (0, 0), (0, 1), (1, 0)],
        [(-1, 0), (0, -1), (0, 0), (0, 1)],
        [(-1, 0), (0, -1), (0, 0), (1, 0)],
    ],
    "Z": [
        [(0, -1), (0, 0), (1, 0), (1, 1)],
        [(-1, 1), (0, 0), (0, 1), (1, 0)],
    ],
}


class Peca:

    def __init__(self, x, y, tipo=None):
        self.x = x
        self.y = y
        self.pixel_x = x * TAMANHO_BLOCO
        self.pixel_y = y * TAMANHO_BLOCO
        self.tipo = tipo if tipo else random.choice(list(PECAS.keys()))
        self.rotacao = 0
        self.formas = PECAS[self.tipo]

    def atualizar_pixels_alvo(self):
        return self.x * TAMANHO_BLOCO, self.y * TAMANHO_BLOCO


class Tetris:

    def __init__(self, root):
        self.root = root
        self.root.title("Tetris Arcade Definitivo - Python")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=LARGURA_TELA,
            height=ALTURA_TELA,
            bg=CORES["FUNDO"],
            highlightthickness=0,
        )
        self.canvas.pack()

        # High Score
        self.arquivo_highscore = "tetris_highscore.txt"
        self.high_score = self.carregar_high_score()

        # Controles
        self.root.bind("<Left>", lambda e: self.tentar_mover(-1, 0))
        self.root.bind("<Right>", lambda e: self.tentar_mover(1, 0))
        self.root.bind("<Down>", lambda e: self.tentar_mover(0, 1))
        self.root.bind("<Up>", lambda e: self.tentar_rotacionar())
        self.root.bind("<space>", lambda e: self.cair_rapido())
        self.root.bind("c", lambda e: self.guardar_peca())
        self.root.bind("C", lambda e: self.guardar_peca())
        self.root.bind("r", lambda e: self.reiniciar_jogo())
        self.root.bind("R", lambda e: self.reiniciar_jogo())

        self.reiniciar_jogo(iniciar=True)
        self.loop_jogo()

    def tocar_som(self, tipo):
        if not winsound:
            return
        try:
            if tipo == "mover":
                winsound.Beep(800, 30)
            elif tipo == "rotacionar":
                winsound.Beep(1000, 40)
            elif tipo == "drop":
                winsound.Beep(400, 60)
            elif tipo == "linha":
                winsound.Beep(1200, 120)
            elif tipo == "game_over":
                winsound.Beep(200, 400)
        except RuntimeError:
            pass

    def carregar_high_score(self):
        if os.path.exists(self.arquivo_highscore):
            try:
                with open(self.arquivo_highscore, "r") as f:
                    return int(f.read().strip())
            except ValueError:
                return 0
        return 0

    def salvar_high_score(self):
        if self.pontos > self.high_score:
            self.high_score = self.pontos
            try:
                with open(self.arquivo_highscore, "w") as f:
                    f.write(str(self.high_score))
            except IOError:
                pass

    def reiniciar_jogo(self, iniciar=False):
        self.grid = [[CORES["FUNDO"] for _ in range(LARGURA_GRID)] for _ in range(ALTURA_GRID)]
        self.pontos = 0
        self.linhas_limpas = 0
        self.nivel = 1
        self.velocidade_queda = 500
        self.game_over = False

        self.proxima_peca = Peca(0, 0)
        self.peca_atual = Peca(LARGURA_GRID // 2, 0)

        # Variáveis de Hold e Animação
        self.hold_tipo = None
        self.pode_guardar = True
        self.linhas_animando = []
        self.contador_animacao = 0

        self.tempo_queda = 0
        if not iniciar:
            self.desenhar()

    def verificar_colisao(self, peca, dx, dy, nova_rotacao=None):
        rot = nova_rotacao if nova_rotacao is not None else peca.rotacao
        forma = peca.formas[rot % len(peca.formas)]

        for px, py in forma:
            novo_x = peca.x + px + dx
            novo_y = peca.y + py + dy

            if novo_x < 0 or novo_x >= LARGURA_GRID or novo_y >= ALTURA_GRID:
                return True
            if novo_y >= 0 and self.grid[novo_y][novo_x] != CORES["FUNDO"]:
                return True
        return False

    def fixar_peca(self):
        forma = self.peca_atual.formas[self.peca_atual.rotacao % len(self.peca_atual.formas)]
        for px, py in forma:
            x = self.peca_atual.x + px
            y = self.peca_atual.y + py
            if y < 0:
                self.game_over = True
                self.tocar_som("game_over")
                self.salvar_high_score()
                return
            self.grid[y][x] = CORES[self.peca_atual.tipo]

        # Verifica se há linhas completas para animação
        linhas_completas = []
        for y in range(ALTURA_GRID):
            if all(self.grid[y][x] != CORES["FUNDO"] for x in range(LARGURA_GRID)):
                linhas_completas.append(y)

        if linhas_completas:
            self.linhas_animando = linhas_completas
            self.contador_animacao = 4  # Quadros de animação de flash
            self.tocar_som("linha")
        else:
            self.proxima_rodada()

    def proxima_rodada(self):
        self.peca_atual = Peca(LARGURA_GRID // 2, 0, self.proxima_peca.tipo)
        self.proxima_peca = Peca(0, 0)
        self.pode_guardar = True

        if self.verificar_colisao(self.peca_atual, 0, 0):
            self.game_over = True
            self.tocar_som("game_over")
            self.salvar_high_score()

    def processar_linhas_completas(self):
        novas_linhas = [
            linha for i, linha in enumerate(self.grid) if i not in self.linhas_animando
        ]
        removidas = len(self.linhas_animando)
        for _ in range(removidas):
            novas_linhas.insert(0, [CORES["FUNDO"] for _ in range(LARGURA_GRID)])
        self.grid = novas_linhas

        self.linhas_limpas += removidas
        self.pontos += removidas * 100 * self.nivel
        self.nivel = 1 + (self.linhas_limpas // 3)
        self.velocidade_queda = max(100, 500 - (self.nivel - 1) * 50)
        self.salvar_high_score()

        self.linhas_animando = []
        self.proxima_rodada()

    def guardar_peca(self):
        if self.game_over or not self.pode_guardar:
            return

        tipo_atual = self.peca_atual.tipo
        if self.hold_tipo is None:
            self.hold_tipo = tipo_atual
            self.peca_atual = Peca(LARGURA_GRID // 2, 0, self.proxima_peca.tipo)
            self.proxima_peca = Peca(0, 0)
        else:
            self.hold_tipo, self.peca_atual = tipo_atual, Peca(
                LARGURA_GRID // 2, 0, self.hold_tipo
            )

        self.pode_guardar = False
        self.tocar_som("rotacionar")

    def tentar_mover(self, dx, dy):
        if self.game_over or self.linhas_animando:
            return
        if not self.verificar_colisao(self.peca_atual, dx, dy):
            self.peca_atual.x += dx
            self.peca_atual.y += dy
            if dx != 0:
                self.tocar_som("mover")
        elif dy > 0:
            self.fixar_peca()

    def tentar_rotacionar(self):
        if self.game_over or self.linhas_animando:
            return
        nova_rot = (self.peca_atual.rotacao + 1) % len(self.peca_atual.formas)
        if not self.verificar_colisao(self.peca_atual, 0, 0, nova_rotacao=nova_rot):
            self.peca_atual.rotacao = nova_rot
            self.tocar_som("rotacionar")

    def cair_rapido(self):
        if self.game_over or self.linhas_animando:
            return
        while not self.verificar_colisao(self.peca_atual, 0, 1):
            self.peca_atual.y += 1
        self.peca_atual.pixel_x, self.peca_atual.pixel_y = self.peca_atual.atualizar_pixels_alvo()
        self.tocar_som("drop")
        self.fixar_peca()

    def calcular_ghost_y(self):
        ghost_y = self.peca_atual.y
        while not self.verificar_colisao(self.peca_atual, 0, ghost_y - self.peca_atual.y + 1):
            ghost_y += 1
        return ghost_y

    def desenhar(self):
        self.canvas.delete("all")

        # Fundo do Painel Lateral
        self.canvas.create_rectangle(
            LARGURA_GRID * TAMANHO_BLOCO,
            0,
            LARGURA_TELA,
            ALTURA_TELA,
            fill=CORES["PAINEL"],
            outline="",
        )

        # 1. Desenhar grade e blocos fixados (com animação de flash se houver)
        for y in range(ALTURA_GRID):
            for x in range(LARGURA_GRID):
                cor = self.grid[y][x]
                if y in self.linhas_animando and self.contador_animacao % 2 == 0:
                    cor = CORES["BRANCO"]

                self.canvas.create_rectangle(
                    x * TAMANHO_BLOCO,
                    y * TAMANHO_BLOCO,
                    (x + 1) * TAMANHO_BLOCO,
                    (y + 1) * TAMANHO_BLOCO,
                    fill=cor,
                    outline=CORES["GRADE"],
                )

        if not self.game_over and not self.linhas_animando:
            # 2. Ghost Piece
            ghost_y = self.calcular_ghost_y()
            forma = self.peca_atual.formas[self.peca_atual.rotacao % len(self.peca_atual.formas)]
            for px, py in forma:
                gx = (self.peca_atual.x + px) * TAMANHO_BLOCO
                gy = (ghost_y + py) * TAMANHO_BLOCO
                if gy >= 0:
                    self.canvas.create_rectangle(
                        gx,
                        gy,
                        gx + TAMANHO_BLOCO,
                        gy + TAMANHO_BLOCO,
                        fill=CORES["FUNDO"],
                        outline=CORES["GHOST"],
                        width=2,
                    )

            # 3. Peça Atual com interpolação suave
            alvo_x, alvo_y = self.peca_atual.atualizar_pixels_alvo()
            self.peca_atual.pixel_x += (alvo_x - self.peca_atual.pixel_x) * 0.4
            self.peca_atual.pixel_y += (alvo_y - self.peca_atual.pixel_y) * 0.4

            if abs(alvo_x - self.peca_atual.pixel_x) < 0.5:
                self.peca_atual.pixel_x = alvo_x
            if abs(alvo_y - self.peca_atual.pixel_y) < 0.5:
                self.peca_atual.pixel_y = alvo_y

            for px, py in forma:
                bloco_x = self.peca_atual.pixel_x + (px * TAMANHO_BLOCO)
                bloco_y = self.peca_atual.pixel_y + (py * TAMANHO_BLOCO)
                if bloco_y + TAMANHO_BLOCO > 0:
                    self.canvas.create_rectangle(
                        bloco_x,
                        bloco_y,
                        bloco_x + TAMANHO_BLOCO,
                        bloco_y + TAMANHO_BLOCO,
                        fill=CORES[self.peca_atual.tipo],
                        outline=CORES["GRADE"],
                    )

        # 4. Painel Lateral (Hold, Próxima, Pontos, High Score)
        inicio_painel = LARGURA_GRID * TAMANHO_BLOCO + 15

        # Seção HOLD
        self.canvas.create_text(
            inicio_painel,
            15,
            anchor="nw",
            text="GUARDAR [C]:",
            fill=CORES["TEXTO"],
            font=("Arial", 10, "bold"),
        )
        self.canvas.create_rectangle(
            inicio_painel, 35, inicio_painel + 90, c_y := 95, outline=CORES["GRADE"], fill="#101010"
        )
        if self.hold_tipo:
            for px, py in PECAS[self.hold_tipo][0]:
                bx = inicio_painel + 45 + (px * 15)
                by = 65 + (py * 15)
                self.canvas.create_rectangle(
                    bx, by, bx + 15, by + 15, fill=CORES[self.hold_tipo], outline=CORES["GRADE"]
                )

        # Seção PRÓXIMA
        self.canvas.create_text(
            inicio_painel,
            110,
            anchor="nw",
            text="PRÓXIMA:",
            fill=CORES["TEXTO"],
            font=("Arial", 10, "bold"),
        )
        self.canvas.create_rectangle(
            inicio_painel, 130, inicio_painel + 90, 190, outline=CORES["GRADE"], fill="#101010"
        )
        for px, py in self.proxima_peca.formas[0]:
            bx = inicio_painel + 45 + (px * 15)
            by = 160 + (py * 15)
            self.canvas.create_rectangle(
                bx,
                by,
                bx + 15,
                by + 15,
                fill=CORES[self.proxima_peca.tipo],
                outline=CORES["GRADE"],
            )

        # Estatísticas
        self.canvas.create_text(
            inicio_painel,
            205,
            anchor="nw",
            text=f"RECORDES:\n{self.high_score}",
            fill="#ffcc00",
            font=("Arial", 10, "bold"),
        )
        self.canvas.create_text(
            inicio_painel,
            265,
            anchor="nw",
            text=f"PONTOS:\n{self.pontos}",
            fill=CORES["TEXTO"],
            font=("Arial", 10, "bold"),
        )
        self.canvas.create_text(
            inicio_painel,
            325,
            anchor="nw",
            text=f"NÍVEL: {self.nivel}",
            fill=CORES["TEXTO"],
            font=("Arial", 10, "bold"),
        )

        self.canvas.create_text(
            inicio_painel,
            380,
            anchor="nw",
            text="[R] Reiniciar\n[C] Guardar Peça",
            fill="#888888",
            font=("Arial", 8),
        )

        # 5. Game Over
        if self.game_over:
            largura_jogo = LARGURA_GRID * TAMANHO_BLOCO
            self.canvas.create_rectangle(
                0, ALTURA_TELA // 3, largura_jogo, ALTURA_TELA // 1.6, fill="#000000"
            )
            self.canvas.create_text(
                largura_jogo // 2,
                ALTURA_TELA // 2.3,
                text="GAME OVER",
                fill="#ff4444",
                font=("Arial", 20, "bold"),
                anchor="center",
            )
            self.canvas.create_text(
                largura_jogo // 2,
                ALTURA_TELA // 1.9,
                text="Pressione [ R ] para Jogar de Novo",
                fill="#ffffff",
                font=("Arial", 9),
                anchor="center",
            )

    def loop_jogo(self):
        if not self.game_over:
            if self.linhas_animando:
                self.contador_animacao -= 1
                if self.contador_animacao <= 0:
                    self.processar_linhas_completas()
            else:
                self.tempo_queda += 20
                if self.tempo_queda >= self.velocidade_queda:
                    self.tentar_mover(0, 1)
                    self.tempo_queda = 0

            self.desenhar()
            self.root.after(20, self.loop_jogo)
        else:
            self.desenhar()


if __name__ == "__main__":
    root = tk.Tk()
    app = Tetris(root)
    root.mainloop()