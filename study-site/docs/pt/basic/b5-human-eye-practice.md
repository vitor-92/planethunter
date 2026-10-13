# B5. Prática com olhos humanos

<p class="meta">Nível básico · semanas 5–6 · cerca de 6 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Como participar do Planet Hunters TESS no Zooniverse e o que observar em cada curva de luz.
    - Como rodar o PlanetHunter num planeta conhecido, Pi Men c, e encontrar o sinal dele.
    - Como ler um dossiê do PlanetHunter seção por seção.
    - Como revisar as três histórias reais do setor 69 identificando o teste que resolveu cada uma.

## Por que treinar o olho

As aulas anteriores deram as ideias. Esta é de prática. Algoritmos são rápidos e incansáveis, mas o olho humano treinado ainda é muito bom em perceber quando algo "não tem cara" de trânsito: um degrau estranho, uma queda colada numa lacuna, eclipses alternados. Toda decisão final sobre um candidato do PlanetHunter passa por uma pessoa olhando o dossiê. Essa pessoa vai ser você.

## Parte 1. Planet Hunters TESS

O **Planet Hunters TESS** é um projeto de ciência cidadã na plataforma **Zooniverse**, criado em 2018 por pesquisadores da Universidade de Oxford. Voluntários olham curvas de luz reais do TESS e marcam os trânsitos que veem. Cada curva é vista por várias pessoas, e as marcações combinadas apontam os sinais que merecem atenção dos cientistas.

Não é brincadeira: voluntários desse projeto já tiveram candidatos que viraram planetas. O primeiro foi TOI-813 b, um planeta do tamanho de Saturno com período de cerca de 84 dias, publicado por Eisner e colaboradores em 2020. Períodos longos assim, com poucos trânsitos, são justamente os que os algoritmos têm mais dificuldade de achar.

### Como participar

1. Acesse o projeto: [Planet Hunters TESS no Zooniverse](https://www.zooniverse.org/projects/nora-dot-eisner/planet-hunters-tess). Criar conta é opcional, mas com conta suas classificações ficam registradas e você pode comentar.
2. Faça o **tutorial** que aparece na primeira vez. Ele mostra a interface e exemplos.
3. Abra o **guia de campo** (*Field Guide*), na lateral. Ele tem exemplos de trânsitos, binárias, variabilidade e defeitos, com as mesmas categorias da aula B4.
4. Para cada curva, marque as quedas que parecem trânsitos e confirme. Se não houver nada, confirme sem marcar: "nada aqui" também é uma resposta útil.
5. Use o fórum **Talk** para perguntar sobre curvas estranhas. Lá voluntários experientes e cientistas conversam.

!!! note "Se a interface mudar"
    Projetos do Zooniverse evoluem e, às vezes, entram em pausa entre lotes de dados. Se o Planet Hunters TESS estiver pausado quando você chegar, explore o guia de campo e os fóruns Talk, que continuam abertos, e volte quando houver dados novos.

### O que observar em cada curva

| Você vê | Provavelmente é | Lembra o teste |
|---|---|---|
| Quedas iguais, com fundo plano, repetidas em intervalos regulares | trânsito de planeta | — |
| Quedas fundas e pontudas (V) | binária eclipsante | `shape` |
| Quedas que alternam: uma funda, uma rasa | binária eclipsante | `odd_even` |
| Uma queda menor exatamente entre duas maiores | eclipse secundário de binária | `secondary` |
| Ondas suaves de vários dias | manchas e rotação da estrela | detrending |
| Picos rápidos para **cima** | flares | corte de picos |
| Queda ou rampa colada numa lacuna dos dados | borda de órbita (defeito) | `edges_dumps` |
| Uma única queda, sem repetição | monotrânsito, ou defeito | `n_transits` |

**Meta do plano:** classifique pelo menos **200 curvas**. Parece muito, mas cada uma leva menos de um minuto depois de pegar o jeito. Lá pela centésima, você vai notar que o olho já separa trânsito, binária e defeito sem pensar.

!!! tip "Dica de estudo"
    Mantenha um caderno. Anote o número das curvas que te deixaram em dúvida e o que você decidiu. Depois, compare com as discussões no Talk. Esse caderno é o começo do "caderno de revisões" que o plano recomenda para o resto do curso.

## Parte 2. Pi Men c no PlanetHunter

Agora você vai rodar a ferramenta num planeta que já sabemos que existe. Isso tem um objetivo: aprender a ler a saída quando a resposta é conhecida, antes de olhar sinais desconhecidos.

**Pi Mensae** (TIC 261136679) é uma estrela brilhante, parecida com o Sol, no céu do hemisfério sul. Ela tem dois planetas conhecidos:

- **Pi Men b**: um gigante com órbita de vários anos, achado por velocidade radial em 2001. Não transita.
- **Pi Men c**: uma super-Terra de cerca de 2 R⊕, com período de **6,27 dias** e profundidade de **cerca de 300 ppm**. Foi o **primeiro** planeta em trânsito anunciado a partir dos dados do TESS, em 2018, e é o TOI-144.01.

A estrela fica perto do polo sul da eclíptica, então foi observada em muitos setores.

### Passo a passo

Antes de começar, instale o projeto (uma vez só) e atualize os espelhos dos catálogos. Sem espelhos atualizados, o sistema não consegue dizer se um sinal é conhecido.

```bash
uv sync
uv run planethunter mirrors sync
uv run planethunter mirrors status
```

O `mirrors status` mostra a idade de cada catálogo e o seu limite. Cada um precisa estar dentro do próprio limite (48 horas para os TOIs, os CTOIs e o arquivo da NASA; mais tempo para catálogos que mudam devagar), e toda linha precisa dizer `ok`.

**1. Rode a análise ponta a ponta para Pi Mensae.**

```bash
uv run planethunter run-target 261136679
```

Esse comando faz tudo para uma estrela só: baixa as curvas de luz do MAST, limpa, procura sinais juntando todos os setores, compara com os catálogos, roda o vetting básico e gera um dossiê para cada sinal forte. Na primeira vez, o download leva alguns minutos. Para algo mais rápido, limite a um setor com `--sectors 1`.

No fim, ele imprime uma linha `run_id=...`, uma tabela com uma linha por sinal (do mais forte para o mais fraco) e o caminho de cada dossiê. As colunas:

| Coluna | O que é | O que esperar para Pi Men c |
|---|---|---|
| `signal_id` | número do sinal no banco de dados | um número inteiro |
| `period_days` | período em dias | perto de 6,27 |
| `t0_btjd` | instante de um trânsito, em BTJD | um número com decimais |
| `depth_ppm` | profundidade | perto de 300 |
| `duration_hours` | duração | algumas horas |
| `sde`, `snr` | força do sinal | acima de 9 e de 7,1 |
| `n_transits` | trânsitos com dados | vários (muitos setores) |
| `match_class` | resultado do crossmatch | `KNOWN_PLANET` |
| `matched_name` | com quem casou | o nome de Pi Men c |
| `verdict`, `score` | resultado do vetting básico | `PASS_BASIC`, score perto de 1 |

Se aparecer ``WARNING: mirrors missing or stale; run `planethunter mirrors sync`.`` (espelhos ausentes ou velhos), rode `mirrors sync` de novo. Se aparecerem outros sinais fracos, é normal: depois de achar e apagar o sinal mais forte, a busca procura de novo e às vezes acha ruído.

**2. Abra o dossiê.** As últimas linhas dizem algo como:

```text
dossier for signal 1234: data/dossiers/tic261136679_sig1234.html
```

Abra o arquivo do sinal de ~6,27 dias no navegador. Se quiser gerar de novo mais tarde, use `uv run planethunter dossier <signal_id>`.

### Lendo o dossiê de Pi Men c, seção por seção

Percorra o dossiê de cima para baixo. Para cada seção, a primeira linha diz o que ela mostra; a segunda, o que procurar.

1. **Cabeçalho e pílulas.** O dossiê é gerado em inglês. As pílulas mostram a severidade (`severity`), a classe do crossmatch, o veredito do vetting com o score, e "host conhecido" (`known host`). Para Pi Men c: crossmatch `KNOWN_PLANET` e `known host: yes` (a estrela tem planetas catalogados). A severidade aparece como "—", porque sinais conhecidos não viram candidatos nem alertas. O título diz "Signal TIC ..." (sinal): a palavra "Candidate" (candidato) só aparece para sinais novos que passaram no vetting.
2. **Parameters** (parâmetros). Tabela com Tmag, temperatura, raio e massa da estrela, setores, período, profundidade ajustada, duração (T14), raio do planeta (Rp), SDE/SNR e número de trânsitos. **Confira:** o período perto de 6,27 dias, a profundidade perto de 300 ppm e Rp perto de 2 R⊕. Use a regra da aula B2: $R_p \approx R_\star\sqrt{\delta}$ com o R* da tabela. Bate? Repare também no Tmag: Pi Mensae é muito brilhante (Tmag em torno de 5), o que explica por que um trânsito tão raso é detectável.
3. **Light curve** (curva de luz). Todo o brilho ao longo do tempo, já limpo. Linhas **vermelhas** marcam os trânsitos; linhas **azuis pontilhadas**, os momentum dumps. **Procure:** os trânsitos em vermelho espalhados pelos setores, sem coincidir sistematicamente com as linhas azuis nem com as bordas das lacunas. Com 300 ppm, você provavelmente **não** vai enxergar cada trânsito individual a olho, e tudo bem.
4. **Folded transit** (trânsito dobrado). Todos os trânsitos sobrepostos, alinhados pelo período. Pontos cinza são medidas individuais; pontos pretos são médias; a curva vermelha é o modelo ajustado. **Procure:** um "U" claro nos pontos pretos, com a curva vermelha passando por eles. É aqui que o trânsito invisível na curva completa aparece: somar muitos trânsitos reduz o ruído (aula B2).
5. **Odd, even and secondary** (ímpar, par e secundário). Três painéis: trânsitos ímpares, pares e a fase 0,5. **Procure:** os dois primeiros com a mesma profundidade e o terceiro plano. É o que um planeta faz.
6. **Depth per transit** (profundidade por trânsito). Um ponto por trânsito, com a média como linha tracejada. **Procure:** pontos espalhados ao redor da linha, sem um muito mais fundo que os outros. Num sinal raso como esse, a dispersão entre os pontos é grande: é o ruído de cada trânsito isolado.
7. **TPF difference image** (imagem-diferença no TPF). Esta seção só aparece quando o vetting aprofundado rodou, e ele só roda para candidatos novos. Para Pi Men c, ela **não** aparece. Num candidato, o `x` vermelho (onde a luz sumiu) deve cair dentro do círculo laranja (a posição da estrela no catálogo).
8. **Vetting** (tabela de vetting). Um teste por linha, com valor (`value`), limite (`threshold`), resultado (`result`) e nota (`note`). **Procure:** quais passaram e, se algum falhou, leia a nota. Testes do vetting aprofundado podem aparecer como "pending" (pendente).
9. **Crossmatch.** Classe, número de objetos conhecidos na estrela e vizinhos, com quem o sinal casou, e a idade de cada catálogo no momento da comparação. **Procure:** casamento com Pi Men c e todos os catálogos dentro do seu limite de idade (48 horas para os TOIs, os CTOIs e o arquivo da NASA).
10. **Next action** (próxima ação). Para Pi Men c: "None: known signal or failed vetting." (nenhuma: sinal conhecido ou reprovado no vetting). Para um candidato novo aprovado, aqui aparece a sugestão de vetting aprofundado e submissão como CTOI.

No rodapé, a **Provenance** (proveniência) registra o `run_id`, a versão do pipeline e a janela de detrending usada em cada setor. É o que permite reproduzir a análise depois.

!!! tip "Na ferramenta"
    O roteiro completo de uso, com mais comandos, está no [manual prático do PlanetHunter](../lab/using-planethunter.md). Os dossiês ficam em `data/dossiers/`. Há dossiês de outros sinais do setor 69 nessa pasta; depois de ler o de Pi Men c, abra dois ou três deles e compare.

!!! example "Exercício 1"
    Depois de rodar Pi Men c, responda com os números do **seu** dossiê:

    a) Qual o período e a profundidade encontrados? Quão perto estão de 6,27 dias e 300 ppm?

    b) Use o R* do dossiê e a profundidade para calcular Rp. O resultado bate com o Rp que o dossiê mostra?

    c) Quantos trânsitos com dados o sistema contou? Por que esse número é bem maior que os 4 trânsitos de um único setor?

    ??? success "Ver resposta"
        a) O período deve sair muito próximo de 6,27 dias (a diferença costuma estar na terceira ou quarta casa decimal) e a profundidade na casa de algumas centenas de ppm, perto de 300. Diferenças de dezenas de ppm são normais: a profundidade depende do modelo ajustado e da limpeza dos dados.

        b) Com R* em torno de 1,1 R☉ e profundidade de 300 ppm: $\sqrt{0{,}0003} \times 1{,}1 \times 109 \approx 2{,}1$ R⊕. O dossiê calcula exatamente assim ($R_p = R_\star\sqrt{\delta} \times 109{,}076$), então deve bater, com diferença só de arredondamento.

        c) O `run-target` junta **todos os setores** em que a estrela foi observada. Pi Mensae fica perto do polo sul da eclíptica e tem muitos setores de dados, cada um com cerca de 4 trânsitos. Mais trânsitos somados dão um SNR muito maior, e é por isso que um sinal de só 300 ppm sai tão claro no trânsito dobrado.

## Parte 3. Revisão das três histórias

Releia a seção "Três histórias reais do setor 69" da [aula B4](b4-false-positives.md). Para cada história, responda no caderno, com suas palavras, antes de abrir a resposta:

1. O que o sistema viu?
2. Por que parecia bom?
3. Que pista revelou o problema?
4. Qual teste ou mudança resolveu?

!!! example "Exercício 2"
    Preencha a tabela para as três histórias.

    | Caso | O que parecia | O que era | Teste ou mudança que resolveu |
    |---|---|---|---|
    | HD 23472 | ? | ? | ? |
    | WASP-18 b | ? | ? | ? |
    | HD 271883 | ? | ? | ? |

    ??? success "Ver resposta"
        | Caso | O que parecia | O que era | Teste ou mudança que resolveu |
        |---|---|---|---|
        | HD 23472 | um planeta novo de 10,29 dias | um trânsito do planeta b e um do planeta c, juntados num período falso | crossmatch **trânsito a trânsito**: se pelo menos metade das quedas coincide com trânsitos previstos de planetas conhecidos, e isso dificilmente é acaso, o sinal é conhecido |
        | WASP-18 b | uma binária eclipsante (queda na fase 0,5) | um planeta tão quente que a luz dele some quando passa atrás da estrela (ocultação, cerca de 340 ppm) | veto do teste `secondary` só quando o secundário é pelo menos **10 %** do principal |
        | HD 271883 | o candidato perfeito: 6,61 dias, 4 900 ppm, passou em tudo | defeito de um único setor | teste `other_sectors`: o sinal não reapareceu com a força esperada (SNR 45–64) nos setores 67, 68 e 97 |

        Repare no padrão. No primeiro caso, o erro foi do **crossmatch** (achou "novo" o que era conhecido). No segundo, o vetting era **rigoroso demais** (reprovou um planeta real). No terceiro, o vetting básico era **frouxo demais** para esse tipo de defeito e precisou de uma etapa extra. Um sistema confiável tem de errar pouco nas três direções.

!!! example "Exercício 3"
    Na curva de luz de um dossiê, você vê três trânsitos marcados em vermelho. Dois deles caem exatamente sobre linhas azuis pontilhadas, e o terceiro cai no fim de um trecho de dados, logo antes de uma lacuna. O trânsito dobrado mostra um "U" bonito. O que você conclui?

    ??? success "Ver resposta"
        Desconfie fortemente de **defeito do telescópio**. As linhas azuis pontilhadas são momentum dumps, e o fim de um trecho de dados é uma borda de órbita, onde aparecem rampas. Todas as três quedas coincidem com momentos problemáticos. O "U" bonito no trânsito dobrado não salva o sinal: ele só mostra que as quedas se parecem entre si, não de onde vieram. O teste `edges_dumps` deve ter falhado; confira na tabela de vetting. O próximo passo seria ver se a estrela tem outros setores e se o sinal aparece neles.

## Checklist da aula

- [ ] Fiz o tutorial do Planet Hunters TESS e li o guia de campo.
- [ ] Classifiquei pelo menos 200 curvas de luz no Zooniverse.
- [ ] Rodei `uv run planethunter run-target 261136679` e encontrei o sinal de 6,27 dias com classe `KNOWN_PLANET`.
- [ ] Rodei o vetting e gerei o dossiê de Pi Men c.
- [ ] Achei no dossiê o período, a profundidade e os trânsitos marcados em vermelho.
- [ ] Percorri as dez seções do dossiê sabendo o que procurar em cada uma.
- [ ] Expliquei, com minhas palavras, qual teste resolveu cada uma das três histórias.
- [ ] Fiz os três exercícios sem olhar a resposta.

## Para ir além

- Eisner et al. (2021), "Planet Hunters TESS II: findings from the first two years of TESS", *Monthly Notices of the Royal Astronomical Society* 501, 4669. O que os voluntários acharam nos primeiros dois anos. Veja as figuras com exemplos de curvas.
- Eisner et al. (2020), "Planet Hunters TESS I: TOI 813, a subgiant hosting a transiting Saturn-sized planet on an 84 day orbit", *Monthly Notices of the Royal Astronomical Society* 494, 750. O primeiro planeta do projeto, com a história de como voluntários o encontraram.
- Huang et al. (2018), "TESS Discovery of a Transiting Super-Earth in the pi Mensae System", *The Astrophysical Journal Letters* 868, L39. O artigo de Pi Men c. Compare os números do resumo com os do seu dossiê.
- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/): procure "pi Men c" e compare período, raio e profundidade com o seu dossiê, como sugere o guia do projeto.
