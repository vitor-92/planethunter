# Glossário

<p class="meta">Termos do curso, em ordem alfabética · consulte sempre que precisar</p>

Cada termo traz uma definição curta e, entre parênteses, a aula em que ele é explicado com calma. Termos com nome em inglês aparecem como são usados na área, com a tradução ao lado. Os nomes em `fonte de código` são colunas, testes ou comandos do PlanetHunter.

## A

**Alias.** Período errado que é múltiplo ou fração do verdadeiro (P/2, 2P, P/3, 3P...). Aparece porque, com poucos trânsitos e lacunas nos dados, vários períodos "encaixam" quase igualmente bem. O PlanetHunter testa aliases na busca (`refine_alias`) e no crossmatch. (B2, M3)

**Ano-luz.** Distância que a luz percorre em um ano: cerca de 9,46 trilhões de km. Apesar do nome, mede distância, não tempo. (B1)

**Anã vermelha.** Estrela do tipo espectral M: pequena (0,1 a 0,6 R☉), fria e pouco brilhante. É o tipo mais comum de estrela da galáxia e o melhor para achar planetas pequenos por trânsito. (B1, B2)

**Aprendizado de máquina.** Programas que aprendem padrões a partir de exemplos rotulados em vez de regras escritas à mão. Na área, redes neurais classificam sinais de trânsito como planeta ou falso positivo; as revisões feitas com `planethunter review` são os rótulos do futuro classificador do projeto. (A4)

## B

**Benchmark.** Teste padronizado que mede o desempenho do sistema sempre do mesmo jeito, para comparar versões. O benchmark de recall do PlanetHunter usa 135 TOIs detectáveis do setor 69. (A5)

**Binária de fundo.** Binária eclipsante fraca que fica quase na mesma direção do alvo, no mesmo pixel ou em pixels vizinhos. Os eclipses dela aparecem diluídos na luz total e imitam o trânsito raso de um planeta no alvo. (B4)

**Binária eclipsante (EB).** Duas estrelas que orbitam uma à outra com a órbita alinhada conosco, de modo que uma eclipsa a outra. É o falso positivo mais comum; denuncia-se por formato em V, eclipses ímpares e pares diferentes e eclipse secundário. (B4)

**Biweight.** Filtro robusto usado no detrending: estima a tendência lenta do brilho numa janela móvel, sem se deixar levar por pontos fora do padrão como os do próprio trânsito. O PlanetHunter usa a versão da biblioteca wotan, com janela de 1 dia (janelas mais curtas só para estrelas que variam depressa). (M4, A1)

**Blend.** Mistura da luz de duas ou mais estrelas na mesma medida. Ver **contaminação**. (B3, B4)

**BLS (Box Least Squares).** Algoritmo clássico de busca de trânsitos: testa muitos períodos e, para cada um, ajusta uma "caixa" (queda retangular) aos dados dobrados. Proposto por Kovács, Zucker e Mazeh em 2002. (M3, A1)

**Borda de órbita.** Início ou fim de cada órbita de 13,7 dias do TESS, onde aparecem rampas de brilho ligadas a mudanças de temperatura. Rampas mal removidas imitam trânsitos; o teste `edges_dumps` desconfia de trânsitos que caem nelas. (B4)

**BTJD (Barycentric TESS Julian Date).** Unidade de tempo do TESS: dias desde uma data de referência (BJD − 2 457 000), corrigidos para o centro de massa do Sistema Solar. Todos os tempos do PlanetHunter estão em BTJD. (B3)

## C

**Cadência.** Intervalo entre duas medidas seguidas de brilho. O TESS fornece curvas de 20 s e de 2 min para estrelas selecionadas, e imagens completas a cada 200 s (antes, 10 e 30 min). (B3)

**Candidato.** Sinal que sobreviveu ao vetting e merece atenção, mas não é planeta. Na escada do curso: sinal → candidato → CTOI → TOI → validado → confirmado. (B3)

**CBV (Cotrending Basis Vectors).** Padrões de variação comuns a muitas estrelas do mesmo detector, causados pelo instrumento. Subtraí-los remove sistemáticos compartilhados sem apagar a variação própria de cada estrela. (M4)

**Centróide.** Posição média da luz de uma estrela na imagem, como o "centro de gravidade" do brilho. Se ele se desloca durante o trânsito, a queda provavelmente vem de uma estrela vizinha; é o teste `centroid`. (B4, M5)

**Classe do crossmatch.** Resultado da pergunta "já existe?": `KNOWN_PLANET` (planeta confirmado), `KNOWN_TOI` e `KNOWN_CTOI` (já é candidato do TESS), `KNOWN_PUBLISHED` (está numa lista publicada de candidatos, como os KOIs do Kepler ou o DIAmante), `KNOWN_FP` (falso positivo ou binária catalogada), `NEARBY_KNOWN` (vizinho conhecido com o mesmo período), `NEW` (nada casou) e `UNVERIFIED` (seria novo, mas algum catálogo está ausente ou velho). (B3, B5)

**Completude.** Fração dos planetas reais, de certo tamanho e período, que o sistema consegue achar. Mede-se com injection-recovery. (A5)

**Contaminação.** Luz de outras estrelas misturada à do alvo na mesma medida, consequência do pixel grande do TESS. Um sinal "do alvo" pode vir de uma estrela contaminante. (B3, B4)

**Crossmatch.** Comparação de cada sinal com os catálogos de objetos conhecidos, para saber se ele já foi registrado. O PlanetHunter casa por estrela (número TIC ou posição até 21″) e por sinal (período com aliases e trânsito a trânsito). (B3, B4)

**CROWDSAP.** Número entre 0 e 1, calculado pelo pipeline SPOC, que estima a fração da luz na abertura que vem do próprio alvo. Valores bem abaixo de 1 indicam muita contaminação. Aparece na seção Parâmetros do dossiê. (B5, M4)

**CTOI (Community TOI).** Candidato submetido ao ExoFOP por alguém de fora da equipe do TESS. Pode ser promovido a TOI. É o destino de um bom candidato do PlanetHunter. (B3, A6)

**Curva de luz.** Gráfico do brilho de uma estrela ao longo do tempo. É o dado bruto de toda a busca por trânsitos. (B2)

## D

**Densidade estelar.** Massa da estrela dividida pelo volume. Junto com o período, ela determina quanto um trânsito deveria durar; um trânsito longo ou curto demais para a estrela sugere que o sinal vem de outra estrela. É a base do teste `duration`. (M2)

**Desvio padrão (σ).** Medida de quanto os valores se espalham em torno da média. Em curvas de luz, o desvio padrão dos pontos fora do trânsito é o ruído. (M1)

**Detrending.** Remoção da variação lenta do brilho (rotação, manchas, efeitos do instrumento) para deixar os trânsitos visíveis. Se a janela do filtro for curta demais, ele "come" o trânsito: com 0,5 dia, um trânsito de 5 h perde 40 % da profundidade; com 1 dia, 6 %. (B4, M4, A1)

**Disposição do TFOPWG.** Situação de um TOI registrada pelo grupo de acompanhamento: PC (candidato a planeta), APC (candidato ambíguo), CP (planeta confirmado), KP (planeta já conhecido), FP (falso positivo), FA (falso alarme). (B3)

**Dobrar (phase-fold).** Sobrepor todos os trânsitos alinhando-os pelo período, como empilhar folhas transparentes. O ruído aleatório se cancela em parte e o trânsito se soma. Gráfico "Trânsito dobrado" do dossiê. (B2, B5)

**Dossiê.** Relatório HTML que o PlanetHunter gera para um sinal, com parâmetros, gráficos, tabela de vetting, crossmatch e proveniência. Fica em `data/dossiers/`. (B5)

**Duotrânsito.** Sinal com só dois trânsitos separados por um intervalo longo (por exemplo, em setores observados com anos de diferença). O período fica ambíguo entre vários aliases. (A1)

**Duração (T14).** Tempo do início ao fim de um trânsito, em horas. Depende do período, do tamanho e da densidade da estrela e do parâmetro de impacto. (B2, M2)

## E

**Eclipse secundário.** Segunda queda de brilho de uma binária, quando a companheira passa atrás da estrela principal; numa órbita circular, ocorre na fase 0,5. O teste `secondary` só veta se ele for pelo menos 10 % do principal. Se o "secundário" for tão fundo e tão longo quanto a queda principal, ele é só mais um trânsito: o sinal foi achado com o dobro do período verdadeiro, e o PlanetHunter o testa de novo com metade do período (`period_halved`). (B4, M5)

**Eclíptica.** Plano em que a Terra e os outros planetas orbitam o Sol. Os setores do TESS se organizam ao redor dos polos da eclíptica. (B3)

**Efeito Doppler.** Mudança na cor (comprimento de onda) da luz de uma fonte que se aproxima ou se afasta, como o tom da sirene de uma ambulância. É a base do método de velocidade radial. (B1)

**Efeméride.** Previsão de quando os próximos trânsitos acontecem: um período e um instante de trânsito ($T_0$). (B2)

**Escurecimento de borda.** A borda do disco de uma estrela parece mais escura que o centro, porque ali vemos camadas mais altas e mais frias. Isso arredonda o fundo do trânsito. (B2, M2)

**Espelho (de catálogo).** Cópia local de um catálogo de objetos conhecidos. O PlanetHunter mantém 12 espelhos: o NASA Exoplanet Archive, os TOIs, os CTOIs, o exoplanet.eu, os KOIs do Kepler, o K2, dois catálogos de binárias do TESS e quatro listas publicadas de candidatos. Cada um tem o seu próprio limite de validade: 48 h para os TOIs, os CTOIs e o Archive, 7 dias para o exoplanet.eu e o K2, 30 dias para os KOIs; tabelas publicadas fixas nunca expiram. Se algum espelho estiver ausente ou velho demais, nenhum sinal pode ser classificado como novo. (B3, B5)

**ExoFOP.** Portal de acompanhamento de exoplanetas (exofop.ipac.caltech.edu), com páginas de cada estrela, listas de TOIs e CTOIs, notas da comunidade e submissão de CTOIs. (B3, A6)

**ExoMiner.** Rede neural da NASA para classificar sinais de trânsito, descrita por Valizadegan e colaboradores em 2022. (A4)

**Exoplaneta.** Planeta que orbita outra estrela que não o Sol. Em 2026 são conhecidos cerca de 6 400 confirmados. (B1)

**exoplanet.eu.** Catálogo europeu de exoplanetas, mais inclusivo que o da NASA (cerca de 8 300 objetos). É um dos espelhos do PlanetHunter. (B3)

## F

**Falha grave (hard fail).** Falha do vetting séria o bastante para reprovar o sinal sozinha, sem zerar o score: `shape`, `secondary_scan`, `tpf_difference_image` e `fpp_triceratops`. Compare com **falha leve** e **veto**. (M5)

**Falha leve (soft fail).** Falha do vetting que, sozinha, só reduz o score. Uma falha leve é tolerada; duas ou mais reprovam o sinal. (M5)

**Falso alarme (FA).** Sinal que não tem origem astrofísica: ruído ou defeito instrumental. (B3, B4)

**Falso positivo (FP).** Sinal real, astrofísico, que parece planeta mas não é: binária eclipsante, binária de fundo, contaminação. Em uso geral, qualquer sinal que parece planeta e não é. (B4)

**Fase.** Posição dentro de uma órbita, de 0 a 1. O trânsito fica na fase 0; o meio do caminho entre dois trânsitos, na fase 0,5. (B4)

**FFI (Full-Frame Image).** Imagem completa de uma câmera do TESS, com todas as estrelas do campo. Cadência atual de 200 s. Permite estudar estrelas fora da lista de 2 minutos. (B3)

**Flare.** Explosão na superfície de uma estrela que produz um pico rápido de brilho para cima. O PlanetHunter corta picos para cima, mas nunca para baixo. (B4)

**Formato em U e em V.** Trânsito de planeta tem fundo quase plano (U); eclipse rasante de binária é pontudo (V). Planetas rasantes também fazem V. Mesmo assim, o teste `shape` é uma falha grave: um formato em V reprova o sinal sozinho, ao custo de alguns planetas rasantes reais. (B4, M5)

**FPP (False Positive Probability).** Probabilidade, calculada por um modelo estatístico, de o sinal ser um falso positivo. Abaixo de 0,5, candidato plausível; abaixo de 0,015 (com NFPP abaixo de 0,001 e imagem de alta resolução), nível usado para validar um planeta. O PlanetHunter calcula com triceratops, e o teste falha se FPP ≥ 0,5 ou NFPP > 0,1. (A3)

**Fusão nuclear.** Junção de núcleos leves (hidrogênio) em mais pesados (hélio), com liberação de energia. É o que faz as estrelas brilharem. (B1)

## G

**Gaia.** Missão espacial europeia que mediu posição, distância e brilho de mais de um bilhão de estrelas. O PlanetHunter usa o catálogo Gaia DR3 para listar estrelas vizinhas e binárias eclipsantes conhecidas. (A2)

**Gigante.** Estrela que esgotou o hidrogênio do centro e inchou até dezenas ou centenas de R☉. Esconde planetas pequenos, porque a profundidade cai com o quadrado do raio da estrela. (B1)

**GP (processo gaussiano).** Modelo estatístico flexível que descreve variações correlacionadas no tempo. É uma alternativa ao biweight para o detrending de estrelas muito variáveis. (A1)

## I

**IC 95 % (intervalo de confiança).** Faixa de valores compatíveis com uma medida, dada a quantidade de dados. O recall de 91,1 % do PlanetHunter, medido com 135 objetos, tem IC 95 % de 85,1 % a 94,8 % (intervalo de Wilson). (A5)

**Imagem direta.** Método de detecção que fotografa o próprio planeta, bloqueando a luz da estrela. Funciona só para planetas gigantes, jovens e distantes da estrela. (B1)

**Imagem-diferença.** Subtração da imagem fora do trânsito da imagem durante o trânsito. O que "apagou" aparece na diferença e mostra de onde veio a queda. Teste `tpf_difference_image`. (B4, A2)

**Ímpar/par (odd-even).** Comparação entre a profundidade dos trânsitos ímpares e dos pares. Se diferem, provavelmente é uma binária com o dobro do período encontrado. Teste `odd_even`. (B4)

**Ingestão.** Etapa que baixa as curvas de luz do MAST e as grava em Parquet. Comando `planethunter ingest`. (B3)

**Injection-recovery.** Técnica que injeta trânsitos sintéticos em curvas reais, roda o pipeline e conta quantos ele recupera. É como se mede a completude. (A5)

## J

**Júpiter quente.** Planeta gigante gasoso em órbita de poucos dias, muito perto da estrela. Foram os primeiros exoplanetas encontrados em estrelas tipo Sol (51 Pegasi b, 1995). (B1)

## K

**Kepler (lei).** A terceira lei de Kepler relaciona período e tamanho da órbita: para uma estrela de 1 M☉, $a^3 = P^2$ com $a$ em UA e $P$ em anos. (B2, M2)

**Kepler (telescópio).** Telescópio espacial da NASA que observou uma região do céu de 2009 a 2018 e mostrou que planetas são comuns. Antecessor do TESS. (B1, B3)

## L

**Lightkurve.** Biblioteca Python para baixar, limpar e analisar curvas de luz do Kepler e do TESS. Base da trilha de programação. (M4, P3)

**Luz espalhada.** Luz da Terra e da Lua que entra nas câmeras do TESS em certas partes da órbita e muda o fundo das imagens. Um dos sistemáticos que imitam trânsitos. (B4)

## M

**M☉ (massa solar).** Massa do Sol, cerca de 2 × 10³⁰ kg, usada como unidade para estrelas. (B1)

**Magnitude.** Escala de brilho invertida: número menor, objeto mais brilhante. Cinco magnitudes correspondem a um fator de 100 em brilho. Ver **Tmag**. (B3)

**MAST (Mikulski Archive for Space Telescopes).** Arquivo público da NASA onde ficam os dados do TESS. (B3)

**Mediana.** Valor do meio quando os dados são ordenados. Menos sensível a valores extremos que a média. (M1)

**Microlente gravitacional.** Método de detecção em que a gravidade de uma estrela em primeiro plano amplia a luz de outra ao fundo; um planeta causa um desvio breve. O evento não se repete. (B1)

**Mini-Netuno.** Planeta entre cerca de 2 e 4 R⊕, com atmosfera espessa. Não existe no Sistema Solar, mas é muito comum na galáxia. (B1)

**Momentum dump.** Acionamento de pequenos propulsores do TESS para descarregar a rotação acumulada nas rodas de reação. O apontamento treme e o brilho salta; no dossiê, aparecem como linhas azuis pontilhadas. (B4)

**Monotrânsito.** Sinal com um único trânsito observado; o período fica desconhecido. O PlanetHunter veta sinais com menos de 2 trânsitos; monotrânsitos exigem um detector próprio, previsto no plano. (B4, A1)

**Multi-setor.** Análise que junta os dados de vários setores da mesma estrela. Aumenta o número de trânsitos e permite verificar se um sinal se repete. (B3, M5)

## N

**NFPP (Nearby False Positive Probability).** Probabilidade de o sinal vir de uma estrela vizinha conhecida, e não do alvo. Para validar um planeta, a literatura usa NFPP abaixo de 0,001; acima de 0,1, o sinal é um provável falso positivo de vizinha e o teste de FPP do PlanetHunter falha. (A3)

**Normal (distribuição).** Distribuição em forma de sino que descreve bem o ruído aleatório de muitas medidas. Cerca de 99,7 % dos valores ficam a menos de 3σ da média. (M1)

## O

**Ocultação.** Passagem do planeta **atrás** da estrela. Em planetas muito quentes, como WASP-18 b, a luz do planeta some e aparece uma queda pequena na fase 0,5. (B4, M2)

## P

**P0, P1, P2 (severidade).** Prioridade de um candidato novo no PlanetHunter. P1: passou no vetting, score ≥ 0,8 **e**, quando o modelo existe, `p_rank` igual ou acima do limiar de P1 do modelo. P0: tudo o que P1 exige, mais vetting aprofundado completo (imagem-diferença e vizinhos Gaia aprovados, FPP calculado) com FPP < 0,1, NFPP < 0,001, planeta menor que 8 R⊕, SNR ≥ 15 e dados de 2 minutos. P2: passou no vetting mas ficou abaixo dos limiares de P1; ou falhou no vetting sem veto, mas foi resgatado por um `p_rank` igual ou acima do limiar de P2 do modelo; ou foi limitado por um aviso (a estrela é binária catalogada ou não tem raio conhecido, NFPP > 0,1, o sinal é a fonte de um sinal compartilhado com um vizinho, ou os trânsitos coincidem em parte com um objeto conhecido). Sem severidade: um veto, trânsitos em picos de época, ou um sinal que pertence a um vizinho. O modelo só baixa a prioridade, nunca a sobe. (B5, A3, A4)

**p_planet, p_rank e p_abs.** `p_rank` (guardado na coluna `p_planet`) é a probabilidade de um sinal ser planeta, aprendida com `planethunter calibrate` a partir de sinais conhecidos: planetas confirmados contra falsos positivos catalogados e os alarmes falsos das rodadas nulas. A severidade a usa só para baixar a prioridade, por dois limiares escolhidos medindo quantos planetas conhecidos eles mantêm. `p_abs` é a mesma probabilidade corrigida por quão raros são os planetas entre os sinais novos; essa correção depende de uma suposição (5 %), por isso `p_abs` serve só para leitura. (A4)

**Parâmetro de impacto (b).** Distância do caminho do planeta ao centro do disco da estrela, em unidades do raio da estrela: 0 é central, perto de 1 é rasante. Trânsitos com $b$ alto são mais curtos e em V. (B2, M2)

**Parquet.** Formato de arquivo compacto para tabelas, usado pelo PlanetHunter para guardar curvas de luz em `data/parquet/`. O banco DuckDB (`data/planethunter.duckdb`) guarda sinais, vetting e candidatos. (B3, P2)

**Parsec (pc).** Unidade de distância usada por astrônomos, igual a 3,26 anos-luz. (B1)

**PDCSAP e SAP.** Dois tipos de fluxo nas curvas do pipeline SPOC. SAP é a soma simples da luz numa abertura; PDCSAP é o SAP corrigido de sistemáticos e de contaminação. (M4)

**Período (P).** Tempo entre dois trânsitos seguidos, em dias. (B2)

**Periodograma.** Gráfico que testa milhares de períodos e mostra quanto cada um "encaixa" nos dados. Um pico destacado indica um sinal periódico. (M3)

**Pico de época (epoch spike).** Momento em que muito mais estrelas sem relação entre si mostram um "trânsito" do que o acaso permite. A causa é o telescópio, não as estrelas. O PlanetHunter procura esses picos em toda rodada; um sinal com metade ou mais dos trânsitos em picos de época nunca gera alerta. (A2)

**Pixel do TESS.** Cada pixel cobre 21″ × 21″ do céu. É grande: cabem várias estrelas, o que causa contaminação. (B3)

**Planet Hunters TESS.** Projeto de ciência cidadã no Zooniverse em que voluntários marcam trânsitos em curvas de luz reais do TESS. (B5)

**Planeta confirmado.** Planeta com evidência independente do trânsito, em geral massa medida por velocidade radial. Último degrau da escada. (B3)

**Planeta validado.** Planeta cuja probabilidade de falso positivo foi mostrada como muito pequena, por análise estatística apoiada em imagens de alta resolução, sem massa medida. (B3, A3)

**ppm (partes por milhão).** Unidade de profundidade de trânsito. 10 000 ppm = 1 %. (B2)

**Profundidade (δ).** Quanto o brilho cai no trânsito, em ppm. Aproximadamente $(R_p/R_\star)^2$. (B2)

**Proveniência.** Registro de onde veio cada resultado: setor, autor dos dados, versão do pipeline e `run_id`. Permite reproduzir qualquer análise. (B5)

## Q

**QLP (Quick Look Pipeline).** Pipeline do MIT que extrai curvas de luz das imagens completas (FFI) do TESS, alcançando muito mais estrelas que as curvas de 2 minutos. (B3)

**Qui-quadrado (χ²).** Teste estatístico que mede se várias medidas concordam com um modelo, levando em conta os erros. O teste `consistency` usa essa ideia para ver se todos os trânsitos têm a mesma profundidade. (M1)

## R

**R⊕ (raio terrestre).** Raio da Terra, 6 371 km, usado como unidade para planetas. Júpiter tem cerca de 11 R⊕. (B1)

**R☉ (raio solar).** Raio do Sol, 696 000 km (cerca de 109 R⊕), usado como unidade para estrelas. (B1)

**Razão de raios (Rp/R*).** Raio do planeta dividido pelo raio da estrela. A profundidade é aproximadamente o quadrado dela. (B2)

**Recall.** Fração de objetos conhecidos que o sistema recupera. No setor 69, o PlanetHunter recupera 123 de 135 TOIs detectáveis: 91,1 %. (A5)

**Robovetter.** Sistema automático de vetting do Kepler (catálogo DR25), descrito por Thompson e colaboradores em 2018. Referência para comparar com o vetting do PlanetHunter. (A2)

**Rodada nula (null run).** Busca em curvas de luz viradas de cabeça para baixo (invertidas) ou com cada órbita deslocada no tempo (embaralhadas). Todo "trânsito" achado nelas é falso por construção, e contá-los mede a taxa de alarmes falsos. O Kepler usou esse método (Thompson et al. 2018); no PlanetHunter, é `planethunter search --null inverted` ou `--null scrambled`. (A1, A2)

**Ruído.** Flutuações nas medidas que não vêm do sinal procurado. Esconde trânsitos rasos. (B2, M1)

**Ruído branco.** Ruído aleatório e independente de uma medida para outra; diminui com a raiz do número de pontos quando se faz a média. (M1)

**Ruído vermelho.** Ruído correlacionado no tempo (vizinhos parecidos entre si), que não some ao fazer média. Por isso o PlanetHunter estima erros por blocos de dados, como em Pont, Zucker e Queloz (2006). (M1)

**run_id.** Código único de cada execução do PlanetHunter, impresso pelos comandos e usado em `vet`, `candidates` e no dossiê. (B5)

## S

**Score de vetting.** Nota de 0 a 1 do vetting. Começa em 1,0; cada teste que falha multiplica por um peso (0,3 a 0,6) e cada teste sem dados, por 0,95; um veto zera. Não decide aprovação ou reprovação (ver **veredito**): ele ordena os sinais, e P0 e P1 exigem score de pelo menos 0,8. É uma ordenação útil, não uma probabilidade (para uma probabilidade, ver **p_planet, p_rank e p_abs**). (B4, M5)

**SDE (Signal Detection Efficiency).** Quanto o pico mais alto do periodograma se destaca do resto, em unidades de desvio padrão. O PlanetHunter exige SDE ≥ 9, que corresponde a uma chance de alarme falso de cerca de 1 em 10 000 segundo Hippke e Heller (2019). (M3)

**Segundo de arco (″).** Unidade de ângulo: 1/3 600 de grau. A Lua cheia mede cerca de 1 800″; um pixel do TESS, 21″. (B3)

**Sequência principal.** Fase estável da vida de uma estrela, em que ela queima hidrogênio no centro. O Sol está nela. (B1)

**Setor.** Bloco de cerca de 27 dias em que o TESS observa a mesma faixa de 24° × 96° do céu. (B3)

**Sigma (σ).** Símbolo do desvio padrão. "3σ" quer dizer três desvios padrão acima ou abaixo da média: improvável por acaso, mas não impossível quando se fazem muitas tentativas. (M1)

**SIMBAD.** Banco de dados astronômico (Estrasburgo, França) que diz que tipo de objeto é cada estrela conhecida. O teste `simbad_type` o consulta. (A2)

**Sinal.** Queda de brilho periódica encontrada pela busca. Primeiro degrau da escada: ainda não passou por nenhum teste. (B3)

**Sinal compartilhado.** O mesmo período e o mesmo instante de trânsito em duas estrelas a menos de 2′: a luz de uma vaza para os pixels da outra. A estrela que consegue de fato produzir a queda é a `source` (no máximo P2); a outra é a `victim` (sem alerta). Duas entradas do TIC a menos de 2″ uma da outra são um `duplicate` da mesma estrela (sem alerta). (A2)

**Sistemático.** Variação causada pelo instrumento ou pelo processamento, não pela estrela. Exemplos: momentum dumps, bordas de órbita, luz espalhada. (B4)

**S/N_pink.** Razão sinal-ruído que também conta o ruído vermelho, medido na escala de tempo do trânsito (Pont, Zucker e Queloz, 2006). O pipeline de visão rápida do TESS (QLP) exige pelo menos 9; no PlanetHunter, ficar abaixo de 9 é uma falha leve. (M1, M5)

**SNR (razão sinal-ruído).** Tamanho do trânsito comparado ao ruído, considerando quantas medidas há dentro dos trânsitos. O PlanetHunter exige SNR ≥ 7,1. (B2, M1)

**SPOC (Science Processing Operations Center).** Pipeline oficial da NASA que produz as curvas de luz de 2 minutos e 20 segundos do TESS. É o "author" mais usado pelo PlanetHunter. (B3)

**Super-Terra.** Planeta rochoso maior que a Terra, de cerca de 1 a 2 R⊕. (B1)

## T

**T0.** Instante do meio de um trânsito de referência, em BTJD. Com o período, forma a efeméride. (B2)

**T14.** Ver **duração**.

**Teff.** Temperatura efetiva, ou temperatura da superfície da estrela, em kelvin. O Sol tem 5 772 K. (B1)

**TESS (Transiting Exoplanet Survey Satellite).** Telescópio espacial da NASA lançado em 2018 que observa quase o céu inteiro em busca de trânsitos. Fonte dos dados do PlanetHunter. (B3)

**TFOP e TFOPWG.** TFOP é o programa de observações de acompanhamento dos TOIs com outros telescópios. TFOPWG é o grupo de trabalho que registra a disposição de cada TOI. (B3, A6)

**Threshold (limite).** Valor de corte de um teste, como SNR ≥ 7,1. No PlanetHunter, todos vivem em `config/thresholds.yaml`, versionados e comentados. (B4, A5)

**TIC (TESS Input Catalog).** Catálogo com mais de 1,7 bilhão de objetos; cada estrela tem um número, como TIC 261136679 (Pi Mensae). Traz também raio, massa e temperatura estimados. (B3)

**Tipo espectral.** Classificação das estrelas pela temperatura: O, B, A, F, G, K, M, da mais quente para a mais fria. O Sol é G2. (B1)

**TLS (Transit Least Squares).** Algoritmo de busca de trânsitos que, em vez de uma caixa, usa um modelo realista de trânsito. Publicado por Hippke e Heller em 2019; é o que o PlanetHunter usa. (M3, A1)

**Tmag.** Brilho da estrela na escala de magnitudes do TESS. Número menor, estrela mais brilhante: 6 é muito brilhante, 13 é fraca. (B3)

**TOI (TESS Object of Interest).** Candidato oficial anunciado pela equipe do TESS, com número como TOI-144.01. Ainda pode ser falso positivo. (B3)

**TPF (Target Pixel File).** Arquivo com os pixels ao redor de uma estrela, em cada instante. Permite fazer imagem-diferença e medir centróides. (A2)

**Trânsito.** Passagem de um planeta (ou outro corpo) na frente de uma estrela, do nosso ponto de vista, causando uma queda de brilho. (B1, B2)

**Trânsito rasante.** Trânsito em que o planeta só raspa a borda da estrela ($b$ perto de 1). É curto e em V, e por isso pode ser confundido com uma binária. (B2, B4)

**Triceratops.** Programa que calcula FPP e NFPP considerando a estrela, os vizinhos do Gaia e o formato do trânsito. Descrito por Giacalone e colaboradores em 2021. (A3)

## U

**UA (unidade astronômica).** Distância média entre a Terra e o Sol, cerca de 150 milhões de km. Usada para o tamanho de órbitas. (B1, B2)

## V

**Variabilidade estelar.** Mudanças de brilho da própria estrela: manchas e rotação, pulsações, flares. Removida em parte pelo detrending. (B4)

**Velocidade radial.** Método de detecção que mede o vaivém da estrela causado pelo planeta, pelo efeito Doppler. Dá a massa do planeta e é o principal método de confirmação. (B1)

**Veredito.** Resultado do vetting: `FAIL` com qualquer veto, qualquer falha grave ou mais de uma falha leve; caso contrário, `PASS_BASIC`. (M5)

**Vetting.** Bateria de testes para descartar falsos positivos. No PlanetHunter há o vetting básico (sem internet, testes como `odd_even`, `secondary`, `shape`, `centroid`) e o aprofundado (com internet: imagem-diferença, vizinhos do Gaia, outros setores, FPP). (B4, M5)

**Veto.** Falha séria a ponto de eliminar o sinal na hora num teste do vetting, zerando o score. As outras falhas são graves ou leves. (B4, M5)

## W

**wotan.** Biblioteca Python de detrending, de Hippke e colaboradores, que o PlanetHunter usa com o filtro biweight. (M4, A1)

## Z

**Zona de visão contínua (CVZ).** Regiões a até cerca de 12° dos polos da eclíptica, observadas pelo TESS em todos os setores de um ano. Estrelas nelas têm muitos setores de dados: no setor 69, de 10 a 22. (B3)

**Zooniverse.** Plataforma de ciência cidadã que hospeda o Planet Hunters TESS e muitos outros projetos. (B5)
