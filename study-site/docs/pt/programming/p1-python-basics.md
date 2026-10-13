# P1. Python básico

<p class="meta">Trilha de programação · junto do nível básico · cerca de 10 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Guardar números e textos em variáveis e saber o tipo de cada um.
    - Organizar dados em listas (períodos) e dicionários (parâmetros de uma estrela).
    - Repetir contas com laços `for` e decidir com `if`.
    - Escrever funções que calculam profundidade de trânsito e raio do planeta.
    - Separar seu código em módulos e importá-los.

Antes de começar, prepare o computador como explicado na [página da trilha](index.md). Crie cada exemplo como um arquivo `.py` na pasta `estudos-exoplanetas` e rode com `uv run python nome_do_arquivo.py`.

## Variáveis e tipos

Uma **variável** é um nome que aponta para um valor. Pense numa etiqueta colada numa caixa: a etiqueta é o nome, o conteúdo é o valor.

```python
periodo_dias = 3.7            # número com casas decimais (float)
n_transitos = 7               # número inteiro (int)
nome_estrela = "Pi Mensae"    # texto (str, de "string")
tem_transito = True           # verdadeiro ou falso (bool)

print(periodo_dias, n_transitos, nome_estrela, tem_transito)
print(type(periodo_dias))     # <class 'float'>
```

O sinal `=` não é "igual" da matemática. Ele quer dizer "guarde o valor da direita no nome da esquerda". Tudo depois de `#` é **comentário**: o Python ignora, serve para você.

Regras práticas para nomes: só letras sem acento, números e `_`; não comece com número; use nomes que digam a unidade. `raio_rsun` é melhor que `r`. O PlanetHunter segue essa regra: `period_days`, `depth_ppm`, `duration_hours`.

### Contas

```python
raio_sol_km = 696_000      # o _ só separa os milhares para facilitar a leitura
raio_terra_km = 6_371

razao = raio_terra_km / raio_sol_km   # divisão
profundidade = razao ** 2             # ** é potência
print(profundidade)                   # 8.379...e-05
```

O resultado `8.379e-05` é notação científica: $8{,}379 \times 10^{-5}$. É a fração da luz do Sol que a Terra bloqueia. Isso vem da regra da [aula B2](../basic/b2-transit-method.md):

$$\delta \approx \left(\frac{R_p}{R_\star}\right)^2$$

onde $\delta$ é a profundidade, $R_p$ o raio do planeta e $R_\star$ o raio da estrela.

### Converter para ppm e por cento

**ppm** quer dizer partes por milhão. Para passar de fração para ppm, multiplique por um milhão. Para por cento, por cem.

```python
profundidade_ppm = profundidade * 1e6     # 1e6 = 1 000 000
profundidade_pct = profundidade * 100
print(f"Terra: {profundidade_ppm:.0f} ppm = {profundidade_pct:.4f} %")
# Terra: 84 ppm = 0.0084 %
```

O `f` antes das aspas cria uma **f-string**: o que está entre chaves é calculado e inserido no texto. O `:.0f` diz "mostre com zero casas decimais".

!!! warning "Armadilha: vírgula decimal"
    Em Python, `3,7` não é o número três vírgula sete. É um par de números, 3 e 7. Sempre use ponto: `3.7`.

## Listas

Uma **lista** guarda vários valores em ordem, entre colchetes.

```python
periodos_dias = [0.94, 3.7, 6.27, 11.4]

print(len(periodos_dias))      # 4 elementos
print(periodos_dias[0])        # 0.94  (a contagem começa em ZERO)
print(periodos_dias[-1])       # 11.4  (índice -1 é o último)
print(periodos_dias[1:3])      # [3.7, 6.27]  (fatia: do 1 até antes do 3)

periodos_dias.append(25.0)     # acrescenta no fim
print(min(periodos_dias), max(periodos_dias), sum(periodos_dias))
print(sorted(periodos_dias, reverse=True))
```

Começar a contar do zero parece estranho no início. Pense no índice como "quantos passos andar a partir do começo".

## Dicionários

Um **dicionário** guarda pares chave e valor, entre chaves. É ótimo para descrever uma coisa com vários atributos, como uma estrela.

```python
estrela = {
    "nome": "WASP-18",
    "tic_id": 100100827,
    "raio_rsun": 1.35,     # raio em raios solares
    "tmag": 8.83,          # brilho na banda do TESS (menor = mais brilhante)
}

print(estrela["raio_rsun"])        # 1.35
estrela["teff_k"] = 6226           # acrescenta uma chave nova
for chave, valor in estrela.items():
    print(chave, "=", valor)
```

Os valores de WASP-18 vêm do arquivo que o PlanetHunter gravou para o setor 69. Você vai abrir esse arquivo na [aula P3](p3-lightkurve-in-practice.md).

## Decisões com `if`

```python
rp_rearth = 15.1   # raio do planeta em raios terrestres

if rp_rearth < 4:
    classe = "rochoso a mini-Netuno"
elif rp_rearth < 8:
    classe = "tamanho de Netuno"
elif rp_rearth <= 20:
    classe = "gigante"
else:
    classe = "grande demais: provavelmente não é planeta"

print(classe)
```

Repare na **indentação**: os 4 espaços no começo das linhas dizem ao Python o que está "dentro" de cada `if`. Em Python, indentação não é enfeite, é regra. As faixas de tamanho seguem a tabela de leitura de candidatos do guia do projeto.

## Laços `for`

Um **laço** repete um bloco para cada elemento de uma lista.

```python
raio_sol_km = 696_000
planetas_km = {"Terra": 6_371, "Netuno": 24_622, "Júpiter": 69_911}

for nome, raio_km in planetas_km.items():
    prof_ppm = (raio_km / raio_sol_km) ** 2 * 1e6
    print(f"{nome:8s} {prof_ppm:8.0f} ppm")
```

Saída:

```text
Terra          84 ppm
Netuno       1251 ppm
Júpiter     10090 ppm
```

Compare com a tabela da aula B2 (84, ~1 300 e ~10 000 ppm). O guia arredonda Netuno para 1 300.

Para repetir um número fixo de vezes, use `range`:

```python
periodo = 0.9416     # dias
t0 = 3182.758        # instante do primeiro trânsito, em BTJD
for n in range(5):   # n = 0, 1, 2, 3, 4
    print(f"trânsito {n}: BTJD {t0 + n * periodo:.3f}")
```

**BTJD** é a contagem de dias que o TESS usa (dias desde uma data de referência). Esse cálculo é uma **efeméride**: a previsão de quando os próximos trânsitos acontecem.

## Funções

Uma **função** é uma receita com nome. Você define uma vez e usa quantas vezes quiser. Ela recebe **parâmetros** (entradas) e devolve um resultado com `return`.

```python
RSUN_EM_REARTH = 109.1   # um raio solar vale 109,1 raios terrestres


def profundidade_ppm(rp_rearth: float, rs_rsun: float) -> float:
    """Profundidade de trânsito em ppm. Rp em R_terra, R* em R_sol."""
    razao = rp_rearth / (rs_rsun * RSUN_EM_REARTH)
    return razao**2 * 1e6


def raio_planeta(prof_ppm: float, rs_rsun: float) -> float:
    """Raio do planeta em R_terra a partir da profundidade (ppm) e de R* (R_sol)."""
    return (prof_ppm / 1e6) ** 0.5 * rs_rsun * RSUN_EM_REARTH


print(profundidade_ppm(1.0, 1.0))     # Terra no Sol: ~84 ppm
print(raio_planeta(84, 1.0))          # volta para ~1 R_terra
print(raio_planeta(84, 0.2))          # mesma queda numa anã vermelha: ~0,2 R_terra
```

Detalhes:

- `rp_rearth: float` é uma **anotação de tipo**. Avisa quem lê que se espera um número. O Python não obriga, mas o PlanetHunter usa em todas as funções.
- O texto entre `"""` logo abaixo do `def` é a **docstring**: explica o que a função faz e as unidades.
- `raio_planeta` é a conta inversa de `profundidade_ppm`: raiz quadrada da profundidade (`** 0.5`) vezes o raio da estrela.

A última linha mostra uma ideia importante do básico: a mesma queda de 84 ppm numa estrela cinco vezes menor corresponde a um planeta cinco vezes menor. Por isso é mais fácil achar planetas pequenos em estrelas pequenas.

!!! tip "Na ferramenta"
    O PlanetHunter faz exatamente a conta de `raio_planeta` para mostrar a coluna `rp_rearth` na lista de candidatos. Está em `src/planethunter/pipeline.py`, na função `candidate_table`, escrita em SQL: `sqrt(fit_depth_ppm * 1e-6) * radius_rsun * 109.076`. Outro exemplo: em `src/planethunter/cli.py`, a função `_parse_ints` transforma o texto `"1,4,8"` da opção `--sectors` na lista `[1, 4, 8]`, usando `split(",")` e um laço compacto.

## Módulos

Um **módulo** é um arquivo `.py` cujas funções você reaproveita em outros arquivos com `import`.

O Python já vem com muitos módulos. O `math` tem raiz quadrada, pi e outras funções:

```python
import math

print(math.sqrt(10_583e-6))   # raiz quadrada de 0,010583 = 0,1029
print(math.pi)
```

Você também pode criar o seu. Salve as duas funções acima num arquivo `transito.py`. Em outro arquivo, na mesma pasta:

```python
from transito import raio_planeta

rp = raio_planeta(10_583, 1.3466)
print(f"WASP-18 b: {rp:.1f} raios terrestres")   # 15.1
```

Os números são reais: 10 583 ppm é a profundidade que o PlanetHunter mediu para WASP-18 b no setor 69, e 1,3466 R☉ é o raio da estrela no catálogo do TESS.

Bibliotecas como NumPy e Lightkurve são módulos feitos por outras pessoas. Você as instala com `uv add` e importa do mesmo jeito.

## Erros: leia a última linha

Errar faz parte. Quando o Python encontra um problema, ele mostra um **traceback**. A informação mais útil está na **última linha**:

| Mensagem | Causa mais comum |
|---|---|
| `NameError: name 'periodo' is not defined` | Nome digitado errado ou variável criada depois de usada |
| `IndentationError` | Espaços do começo da linha desalinhados |
| `TypeError: can't multiply sequence by non-int of type 'float'` | Tentou multiplicar uma lista por um número (isso só funciona com NumPy, aula P2) |
| `KeyError: 'raio'` | Chave que não existe no dicionário |
| `IndexError: list index out of range` | Pediu um elemento além do fim da lista |

## Exercícios

!!! example "Exercício 1. Conversões"
    O PlanetHunter mediu 10 583 ppm para WASP-18 b. Escreva um script que mostre esse valor como fração e como porcentagem.

    ??? success "Ver resposta"
        ```python
        prof_ppm = 10_583
        fracao = prof_ppm / 1e6
        pct = prof_ppm / 1e4        # 1 % = 10 000 ppm
        print(f"{fracao:.6f}  {pct:.4f} %")
        ```
        Saída: `0.010583  1.0583 %`. Um trânsito de cerca de 1 %, típico de um Júpiter quente diante de uma estrela parecida com o Sol.

!!! example "Exercício 2. Função de classificação"
    Escreva a função `classifica(prof_ppm, rs_rsun)` que use `raio_planeta` e devolva o texto da classe de tamanho (use o `if` da seção "Decisões"). Teste com WASP-18 b (10 583 ppm, 1,3466 R☉) e com uma queda de 40 000 ppm numa estrela de 1,5 R☉.

    ??? success "Ver resposta"
        ```python
        from transito import raio_planeta


        def classifica(prof_ppm: float, rs_rsun: float) -> str:
            """Classe de tamanho a partir da profundidade (ppm) e de R* (R_sol)."""
            rp = raio_planeta(prof_ppm, rs_rsun)
            if rp < 4:
                return f"{rp:.1f} R_terra: rochoso a mini-Netuno"
            elif rp < 8:
                return f"{rp:.1f} R_terra: tamanho de Netuno"
            elif rp <= 20:
                return f"{rp:.1f} R_terra: gigante"
            return f"{rp:.1f} R_terra: grande demais, desconfie de binária"


        print(classifica(10_583, 1.3466))   # 15.1 R_terra: gigante
        print(classifica(40_000, 1.5))      # 32.7 R_terra: grande demais...
        ```
        O segundo caso daria um "planeta" de quase 33 raios terrestres, três vezes Júpiter. É o que o teste `radius` do vetting desconfia: provavelmente uma estrela pequena eclipsando outra (aula B4).

!!! example "Exercício 3. Caçando aliases"
    Uma busca devolveu estes períodos para a mesma estrela: `[0.9416, 1.8832, 0.4708, 2.8248]`. Use um laço para dividir cada um pelo primeiro e diga quais são **aliases** (múltiplos ou frações do período verdadeiro).

    ??? success "Ver resposta"
        ```python
        periodos = [0.9416, 1.8832, 0.4708, 2.8248]
        base = periodos[0]
        for p in periodos:
            razao = p / base
            print(f"{p:.4f} d  ->  {razao:.2f} x o primeiro")
        ```
        As razões são 1,00, 2,00, 0,50 e 3,00. Os três últimos são aliases: $2P$, $P/2$ e $3P$. Picos assim aparecem no periodograma (aula M3), e o crossmatch do PlanetHunter testa essas razões ao comparar um sinal com planetas conhecidos.

## Checklist da aula

- [ ] Criei variáveis de cada tipo e conferi com `type()`
- [ ] Converti uma profundidade entre fração, ppm e por cento
- [ ] Usei lista e dicionário com dados de uma estrela
- [ ] Escrevi um laço que calcula profundidades de vários planetas
- [ ] Escrevi as funções `profundidade_ppm` e `raio_planeta` com docstring e unidades
- [ ] Importei minhas funções de um módulo `transito.py`
- [ ] Resolvi os três exercícios

## Para ir além

- Curso em Vídeo — Python, mundos 1 e 2 (Gustavo Guanabara). Cobre com calma tudo desta aula, com exercícios corrigidos em vídeo.
- Tutorial oficial do Python, que tem tradução para o português no site docs.python.org. Bom para consultar um assunto específico, como dicionários.
- Seção sobre o método de trânsito no site da NASA ([science.nasa.gov/exoplanets](https://science.nasa.gov/exoplanets/)). Para revisar a física por trás das contas que você programou.
