# A6. Do candidato à comunidade

<p class="meta">Nível avançado · semanas 13–16 · cerca de 16 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Quem decide cada degrau da escada sinal → candidato → CTOI → TOI → validado → confirmado.
    - Como usar o ExoFOP: páginas de alvo, notas da comunidade, arquivos de acompanhamento.
    - Quais campos uma submissão de CTOI precisa e como calcular as incertezas da efeméride.
    - O que faz cada subgrupo do programa de acompanhamento do TESS (TFOP).
    - Como buscar literatura no ADS e no arXiv antes de submeter qualquer coisa.
    - As regras de ética e o checklist de um pacote de submissão completo.

Até aqui, tudo aconteceu dentro do seu computador. Esta aula é sobre o momento em que um candidato sai dele. A partir daí, outras pessoas vão gastar tempo de telescópio com o que você enviou. Isso exige cuidado, honestidade e um pacote de informação que permita a qualquer pessoa refazer o seu raciocínio.

## 1. A escada e quem decide cada degrau

| Degrau | O que significa | Quem decide |
|---|---|---|
| **Sinal** | Uma queda periódica que passou dos limites de detecção | O pipeline (SDE ≥ 9, SNR ≥ 7,1, ≥ 2 trânsitos) |
| **Candidato** | Um sinal novo que sobreviveu ao vetting e à revisão humana | Você, com o PlanetHunter |
| **CTOI** | Candidato registrado no ExoFOP pela comunidade | Você submete |
| **TOI** | Objeto de interesse oficial do TESS | A equipe de TOIs do TESS, que pode promover o CTOI |
| **Planeta validado** | Probabilidade de falso positivo muito baixa, com dados de acompanhamento (em geral imagem de alta resolução e fotometria em solo) | Um artigo revisado por pares |
| **Planeta confirmado** | Natureza planetária demonstrada por medida independente, em geral a massa por velocidade radial ou variação no tempo dos trânsitos | Um artigo revisado por pares |

O PlanetHunter vai, no máximo, até o segundo degrau. Submeter o CTOI é o seu ato. Todos os degraus seguintes dependem de outras pessoas e de outros telescópios. Por isso nenhum texto seu, em nenhum lugar, deve usar a palavra "descoberta" para um candidato.

## 2. O ExoFOP

O **ExoFOP** (exofop.ipac.caltech.edu/tess) é o ponto de encontro de quem acompanha os alvos do TESS. É ali que a equipe do TESS publica os TOIs, a comunidade submete CTOIs e os observadores do programa de acompanhamento registram o que fizeram.

### A página de um alvo

Digite o número TIC na busca do ExoFOP. A página do alvo reúne, em geral:

- **Parâmetros da estrela** do TIC (raio, massa, temperatura, Tmag, distância) e nomes alternativos (HD, Gaia, 2MASS).
- **TOIs e CTOIs** associados à estrela, com período, época, profundidade, disposição e histórico.
- **Notas** (observing notes) escritas por membros da equipe e da comunidade: "secundário visível no setor X", "binária visual a 3″", "trânsito confirmado em solo". **Leia todas** antes de qualquer decisão.
- **Arquivos enviados** por observadores: curvas de luz de telescópios em solo, imagens de alta resolução com curvas de contraste, espectros.
- **Resumo das observações** já feitas: imagem, espectroscopia, séries temporais.
- **Links** para os relatórios do Data Validation do SPOC (aula A2).

Para submeter CTOIs ou escrever notas, é preciso criar uma conta no ExoFOP.

!!! info "O PlanetHunter já lê o ExoFOP"
    Os espelhos `toi` e `ctoi` do projeto são cópias das tabelas públicas do ExoFOP, sincronizadas por `uv run planethunter mirrors sync`. O crossmatch se recusa a classificar um sinal como `NEW` se algum espelho estiver ausente ou velho demais para o seu próprio limite (48 horas para as tabelas de TOIs, de CTOIs e do NASA Exoplanet Archive), e o comando de alerta verifica de novo logo antes de enviar. O projeto também espelha algumas listas publicadas de candidatos (classe `KNOWN_PUBLISHED`), mas longe de todas. E as **notas** e os **arquivos** da página de alvo não estão nos espelhos. Essa leitura é sempre sua.

## 3. Antes de submeter: busca de literatura

Os catálogos atrasam. Um planeta pode estar num artigo aceito há duas semanas e ainda não estar no NASA Exoplanet Archive. Um candidato pode aparecer na tabela de um artigo sobre outra coisa. A busca de literatura é a última linha de defesa contra submeter algo já conhecido.

### No ADS

O ADS (ui.adsabs.harvard.edu) indexa praticamente toda a literatura de astronomia. Estratégias:

1. **Pelo nome do objeto**: `object:"HD 23472"`. O ADS resolve nomes conhecidos pelos bancos de objetos astronômicos e acha artigos que citam a estrela.
2. **Pelo número TIC no texto completo**: `full:"TIC 261136679"`. Pega tabelas e apêndices.
3. **Por todos os nomes**: repita com o nome HD, o identificador Gaia DR3 e o 2MASS da página do ExoFOP. Artigos antigos não usam TIC.
4. **Ordene por data** e leia pelo menos os resumos dos resultados dos últimos dois anos.

### No arXiv

Artigos recentes aparecem primeiro no arXiv (arxiv.org), na seção **astro-ph.EP** (planetas). A busca do arXiv procura em título, autores e resumo, não no texto completo. Por isso, além de buscar pelo nome, percorra a listagem das últimas semanas de astro-ph.EP procurando trabalhos sobre o mesmo campo, a mesma missão ou o mesmo tipo de objeto (por exemplo, "TESS single transits").

### O que registrar

Data da busca, consultas usadas, número de resultados, artigos relevantes e conclusão. No projeto, o agente `research-scout` faz essa varredura antes de qualquer P0. Mas o registro escrito é parte do pacote de submissão.

## 4. A submissão de CTOI

O formulário do ExoFOP muda de tempos em tempos. Confira sempre a página de ajuda antes de submeter. Os campos usuais, visíveis nas colunas da tabela pública de CTOIs, são:

| Campo | Unidade | De onde vem no PlanetHunter |
|---|---|---|
| TIC ID | — | `tic_id` |
| Período e erro | dias | `period_days` e incerteza do ajuste |
| Época do trânsito e erro | BJD (TDB), completo | `t0_btjd` + 2 457 000 |
| Profundidade e erro | ppm | `depth_ppm` do ajuste |
| Duração e erro | horas | `t14_h` do ajuste |
| Raio do planeta (opcional) | R⊕ | `rp_rearth`, com o raio estelar do TIC |
| Disposição do usuário | por exemplo PC | sua decisão de revisão |
| Notas | texto livre | resumo do dossiê |

### Cuidados com a efeméride

- **BTJD não é BJD.** O TESS usa BTJD = BJD − 2 457 000. O ExoFOP espera o BJD completo. Erro clássico: submeter 3180,45 em vez de 2 460 180,45.
- **Escolha a época no meio dos dados.** Período e época saem correlacionados de um ajuste. Uma época no centro do intervalo observado minimiza essa correlação e dá o menor erro de época.
- **Incertezas reais.** O passo da grade do TLS não é incerteza. Use um ajuste de modelo de trânsito com estimativa de erro (por exemplo, amostragem por MCMC ou bootstrap), ou pelo menos a largura do pico do periodograma, e diga qual usou.
- **Propagação.** A incerteza de um trânsito futuro, $n$ órbitas depois, cresce com $n$:

$$
\sigma_{T}(n) = \sqrt{\sigma_{T_0}^2 + n^2\, \sigma_P^2} .
$$

Isso decide se observadores em solo conseguem planejar uma observação, e é o mesmo motivo pelo qual o crossmatch do projeto ignora efemérides com incerteza propagada acima de 1 dia.

### As notas

As notas são lidas por pessoas ocupadas. Devem dizer, em poucas linhas: como o sinal foi achado (dados, setores, pipeline), o que foi testado e com que resultado, o que **não** foi testado, e qual observação ajudaria. Números, não adjetivos.

## 5. O programa de acompanhamento do TESS (TFOP)

O **TFOP** (TESS Follow-up Observing Program) organiza os observadores que acompanham TOIs. O grupo de trabalho (TFOPWG) se divide em subgrupos. Cada um ataca cenários de falso positivo diferentes, e vale ler a tabela com a aula A3 aberta:

| Subgrupo | O que faz | Cenários que elimina |
|---|---|---|
| **SG1** fotometria em solo | Observa um trânsito previsto com telescópio em solo, com pixels muito menores que os do TESS | Vizinhas (NEB, NTP): mostra em qual estrela o trânsito acontece; checa se a profundidade muda com a cor (binárias tendem a mudar) |
| **SG2** espectroscopia de reconhecimento | Espectros de resolução moderada | Binárias espectroscópicas, estrelas gigantes ou de rotação rápida; refina os parâmetros estelares |
| **SG3** imagem de alta resolução | Óptica adaptativa ou speckle, produz curva de contraste | Companheiras próximas não resolvidas (PEB, SEB, STP, BEB) |
| **SG4** velocidade radial precisa | Mede a oscilação da estrela causada pelo planeta | Mede a massa: é o caminho da confirmação |
| **SG5** fotometria espacial | Observações com outros telescópios espaciais | Refina efeméride e forma do trânsito |

O SG1 é o subgrupo mais aberto a observadores com telescópios modestos, inclusive amadores experientes, para alvos brilhantes com trânsitos profundos. A participação exige seguir as regras do programa. A página do TFOP no HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html) é o ponto de partida. O software AstroImageJ (Collins et al. 2017) é a ferramenta padrão para reduzir essas observações.

## 6. Ética

1. **Vocabulário.** Sinal, candidato, CTOI, TOI, validado, confirmado. Nunca "descoberta", nem em rede social, nem em conversa com jornalista, nem "entre amigos" num post público.
2. **Cite quem produziu os dados.** Toda apresentação, nota ou artigo cita: a missão TESS (Ricker et al. 2015), o pipeline da curva de luz usada (SPOC, Jenkins et al. 2016; ou QLP, Huang et al. 2020), o TIC (Stassun et al. 2019), o Gaia (Gaia Collaboration, Prusti et al. 2016; e Vallenari et al. 2023 para o DR3), o MAST, e as bibliotecas usadas (lightkurve, astropy, TLS, wotan, triceratops). Os dados são públicos porque muita gente trabalhou para isso.
3. **Dê crédito a quem viu antes.** Se uma nota do ExoFOP ou um voluntário do Planet Hunters TESS já apontou o sinal, cite. Se o sinal já está num artigo, ele não é seu para submeter como novo.
4. **Respeite os dados de acompanhamento.** Arquivos enviados por observadores ao ExoFOP têm regras de uso. Antes de usá-los num trabalho, leia a política e, na dúvida, pergunte aos autores.
5. **Não desperdice tempo de telescópio.** Cada CTOI fraco consome horas de voluntários e profissionais. Submeta poucos e bons. Um CTOI que vira falso positivo óbvio na primeira observação queima credibilidade.
6. **Relate o que falhou.** Um teste que você não conseguiu rodar, um FPP médio, um vizinho não excluído: tudo vai nas notas. Esconder um problema é pior que ter o problema.

!!! tip "Na ferramenta"
    - O dossiê (`uv run planethunter dossier <signal_id>`) já traz links para a página do alvo no ExoFOP, para o Exoplanet Archive e para o SIMBAD, além da seção "Próxima ação".
    - A tabela `signals` grava a proveniência de cada linha: setor, autor da curva, `pipeline_version` e `run_id`. Copie esses campos para o pacote.
    - `uv run planethunter review <signal_id> follow_up --note "..."` marca o candidato enquanto você prepara a submissão.

## 7. Checklist do pacote de submissão

- [ ] Dossiê HTML do candidato, revisado seção por seção.
- [ ] Classe `NEW` com todos os espelhos dentro do seu limite de idade na data do pacote (48 h para TOI, CTOI e o Archive; anote as idades).
- [ ] Página do alvo no ExoFOP lida, incluindo todas as notas e arquivos.
- [ ] Busca de literatura registrada: data, consultas no ADS e no arXiv, resultado.
- [ ] Efeméride: período ± erro (d), época BJD completa ± erro, com a época no meio dos dados e o método de erro declarado.
- [ ] Profundidade ± erro (ppm), duração ± erro (h), raio estimado (R⊕) e raio estelar usado.
- [ ] Tabela de vetting completa: cada teste com valor, limite e veredito, incluindo os "sem dados".
- [ ] Imagem-diferença, vizinhos Gaia e resultado de outros setores.
- [ ] FPP e NFPP com os cenários principais, ou a razão de não ter rodado.
- [ ] Proveniência: setores, autor da curva (SPOC/QLP), `pipeline_version`, `run_id`.
- [ ] Previsão dos próximos trânsitos com incerteza, para facilitar o SG1.
- [ ] Texto das notas, com números e limitações.
- [ ] Lista de citações.
- [ ] Revisão por uma segunda pessoa antes de enviar.

!!! example "Exercício 1. Efeméride para o ExoFOP"
    Seu ajuste deu época 3180,4512 ± 0,0011 BTJD e período 7,23492 ± 0,00004 d. (a) Qual a época em BJD? (b) Preveja o trânsito 50 órbitas depois, com incerteza em minutos. (c) E 1 000 órbitas depois?

    ??? success "Ver resposta"
        (a) $3180{,}4512 + 2\,457\,000 = 2\,460\,180{,}4512$ BJD.

        (b) $3180{,}4512 + 50 \times 7{,}23492 = 3180{,}4512 + 361{,}7460 = 3542{,}1972$ BTJD, ou $2\,460\,542{,}1972$ BJD. Incerteza: $\sqrt{0{,}0011^2 + (50 \times 0{,}00004)^2} = \sqrt{1{,}21 \times 10^{-6} + 4{,}0 \times 10^{-6}} = 0{,}00228$ d ≈ **3,3 min**. Ótimo para planejar uma observação.

        (c) $\sqrt{0{,}0011^2 + (1000 \times 0{,}00004)^2} \approx 0{,}040$ d ≈ **58 min**, cerca de 20 anos depois. A efeméride "envelhece": o termo do período domina. É por isso que novas observações de trânsito são valiosas mesmo para planetas já conhecidos.

!!! example "Exercício 2. O que há de errado nesta nota?"
    "Descobrimos um novo planeta rochoso potencialmente habitável em TIC 123456789! Período 14,2 dias, FPP 0,02, o que confirma que é um planeta. Época 3201,77."

    ??? success "Ver resposta"
        1. "Descobrimos": vocabulário errado. É um candidato.
        2. "Rochoso": sem massa, não se sabe a composição. No máximo "raio estimado de X R⊕".
        3. "Potencialmente habitável": afirmação sem base e sensacionalista; não pertence a uma nota técnica.
        4. "FPP 0,02 confirma": FPP não confirma nada. Além disso, 0,02 está acima de 0,015 e não há menção a NFPP nem a imagem de alta resolução.
        5. "Época 3201,77": está em BTJD, sem erro, sem o período com erro.
        6. Falta: setores, autor da curva, testes feitos e limitações.

        Versão aceitável: "Candidato a trânsito em TIC 123456789, setores 68–69 (SPOC 2 min), P = 14,2031 ± 0,0012 d, T0 = 2 460 201,7712 ± 0,0018 BJD, profundidade 610 ± 70 ppm, duração 3,1 ± 0,2 h, Rp ≈ 2,3 R⊕ para R* = 0,86 R☉ (TIC). Ímpar/par e secundário consistentes com zero; imagem-diferença no alvo (deslocamento 0,2 ± 0,3 px); sem vizinhos Gaia capazes de produzir a queda fora do raio de exclusão de 6″. Triceratops: FPP 0,02, NFPP < 0,001, cenário principal PEB. Sem imagem de alta resolução. Sugere-se SG3 e SG1." (Números hipotéticos.)

!!! example "Exercício 3. Achei num preprint"
    Seu candidato passou em tudo e é `NEW`. Na busca de literatura, você acha no arXiv um preprint de três semanas atrás que lista a mesma estrela com período compatível com o seu, numa tabela de "candidatos de trânsito único resolvidos". Não há CTOI no ExoFOP. O que fazer?

    ??? success "Ver resposta"
        1. **Não submeter como novo.** O sinal já foi reportado. Submeter seria apropriar-se do trabalho de outra pessoa, mesmo sem intenção.
        2. Comparar com cuidado: o período é o mesmo, um alias, ou outro planeta da mesma estrela? Se for outro período incompatível, pode ser um planeta adicional, e a nota deve citar o preprint.
        3. Se for o mesmo: registrar no seu caderno, classificar como conhecido na revisão (`rejected --reason already_known`, com a referência na nota) e, se tiver algo a acrescentar (setores novos, efeméride melhor), escrever aos autores ou deixar uma nota no ExoFOP citando o trabalho deles.
        4. Para o projeto: abrir uma issue sugerindo que o espelho de literatura (ADS/arXiv) seja consultado antes do alerta, porque os catálogos ainda não refletem o preprint.

## Checklist da aula

- [ ] Sei quem decide cada degrau da escada até o planeta confirmado.
- [ ] Abri a página de pelo menos três alvos no ExoFOP e li as notas.
- [ ] Sei fazer buscas por objeto e por texto completo no ADS e percorrer o astro-ph.EP.
- [ ] Sei converter BTJD em BJD e propagar a incerteza de uma efeméride.
- [ ] Sei o que cada subgrupo do TFOP faz e qual cenário de falso positivo ele elimina.
- [ ] Montei um pacote de submissão completo para um candidato P1 (mesmo hipotético), sem enviar.

## Para ir além

- Guerrero et al. (2021), *The Astrophysical Journal Supplement Series* 254, 39. Releia a parte sobre CTOIs e a promoção a TOI, agora do ponto de vista de quem submete.
- Ricker et al. (2015), *Journal of Astronomical Telescopes, Instruments, and Systems* 1, 014003. O artigo da missão TESS; é a citação obrigatória de qualquer trabalho com os dados.
- Collins et al. (2017), *The Astronomical Journal* 153, 77. O AstroImageJ, ferramenta padrão do SG1; mostra o que a fotometria em solo consegue verificar.
- Eisner et al. (2021), *Monthly Notices of the RAS* 501, 4669. Resultados do Planet Hunters TESS: como uma comunidade de voluntários organiza a submissão de candidatos, com muitos trânsitos únicos.
- Página do TFOP no HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html). Estrutura do programa e como participar.
- Página de ajuda do ExoFOP (exofop.ipac.caltech.edu/tess). Formato atual de submissão de CTOI e regras de uso dos dados.
