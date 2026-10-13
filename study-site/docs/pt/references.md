# Referências

Bibliografia completa do curso, organizada por nível e por tema. Cada item tem uma frase dizendo por que vale a pena. Para artigos, a citação traz autores, ano, revista e volume; com isso você acha qualquer um deles no ADS (ui.adsabs.harvard.edu) e, quase sempre, uma versão gratuita no arXiv (arxiv.org).

!!! tip "Como ler os artigos desta lista"
    Na primeira vez, leia resumo, figuras e conclusão. Volte às equações quando precisar delas. O método está explicado no [índice do nível avançado](advanced/index.md#como-ler-um-artigo-cientifico).

## Livros

- Tasker, E. (2017). *The Planet Factory*. Bloomsbury. Divulgação de alto nível sobre formação e diversidade de planetas; o melhor ponto de partida do nível básico.
- Seager, S. (ed.) (2010). *Exoplanets*. University of Arizona Press. Livro de referência do nível avançado, com capítulos escritos pelos especialistas de cada técnica.
- Haswell, C. A. (2010). *Transiting Exoplanets*. Cambridge University Press. Livro-texto dedicado ao método de trânsito, com exercícios; ponte entre o nível médio e o avançado.
- Perryman, M. (2018). *The Exoplanet Handbook*, 2ª ed. Cambridge University Press. Enciclopédia da área, para consulta quando um artigo citar algo que você não conhece.
- Sivia, D. S. (2006). *Data Analysis: A Bayesian Tutorial*, 2ª ed. Oxford University Press. Introdução curta e clara ao raciocínio bayesiano usado na aula A3.
- Ivezić, Ž., Connolly, A. J., VanderPlas, J. T. & Gray, A. *Statistics, Data Mining, and Machine Learning in Astronomy*. Princeton University Press. Estatística e aprendizado de máquina com exemplos astronômicos e código em Python.
- VanderPlas, J. (2016). *Python Data Science Handbook*. O'Reilly. NumPy, pandas, Matplotlib e scikit-learn em um só livro; há versão gratuita online.

## Nível básico

### O céu, os planetas e o método de trânsito

- NASA, site de exoplanetas (science.nasa.gov/exoplanets). Seções de introdução e "how we find"; explicações visuais dos métodos de detecção.
- Página da missão TESS no site da NASA e guia do TESS no HEASARC (heasarc.gsfc.nasa.gov/docs/tess). O que o TESS observa, setores, câmeras e cadências.
- Guia para leigos do PlanetHunter, em `docs/BEGINNERS_GUIDE.md` no repositório do projeto. Explica a ferramenta passo a passo, com glossário e três histórias reais.
- Plano de estudos do PlanetHunter, em `docs/STUDY_PLAN.md`. A estrutura que este curso segue, com checklists por módulo.

### Prática

- Planet Hunters TESS (zooniverse.org). Classificar curvas de luz reais é o melhor treino de olho que existe, e voluntários do projeto já tiveram candidatos promovidos.

## Nível médio

### Estatística para sinais

- Khan Academy em português (pt.khanacademy.org), trilha de estatística. Estatística descritiva e distribuição normal, base de SNR e "sigma".
- Pont, F., Zucker, S. & Queloz, D. (2006). *Monthly Notices of the RAS* 373, 231. O artigo que mostrou o efeito do ruído vermelho em trânsitos; base do erro por blocos (`BlockNoise`) usado no vetting.
- Hogg, D. W., Bovy, J. & Lang, D. (2010). "Data analysis recipes: Fitting a model to data", arXiv:1008.4686. Guia prático e opinativo sobre ajustar modelos com honestidade estatística.

### Física do trânsito

- Winn, J. N. (2010). "Transits and Occultations", arXiv:1001.2010. O texto clássico sobre geometria, duração, forma e eclipse secundário; seções 1 a 3 cobrem o nível médio.
- Seager, S. & Mallén-Ornelas, G. (2003). *The Astrophysical Journal* 585, 1038. Relações analíticas entre forma do trânsito, densidade estelar e período; base do teste `duration`.
- Mandel, K. & Agol, E. (2002). *The Astrophysical Journal* 580, L171. O modelo analítico de trânsito com escurecimento de borda usado por quase todo software da área.

### Periodogramas

- Documentação do Astropy sobre Box Least Squares (docs.astropy.org, seção timeseries). Exemplo prático de BLS em Python.
- Hippke, M. & Heller, R. (2019). *Astronomy & Astrophysics* 623, A39. O TLS usado pelo PlanetHunter; no nível médio, introdução e figuras.
- VanderPlas, J. T. (2018). *The Astrophysical Journal Supplement Series* 236, 16. Explicação didática de periodogramas e aliases (no caso, Lomb-Scargle), útil para entender picos falsos.

### Python e dados do TESS

- *Curso em Vídeo — Python*, de Gustavo Guanabara, mundos 1, 2 e 3. Curso gratuito em português, do zero ao intermediário.
- Documentação introdutória do NumPy (numpy.org) e do pandas (pandas.pydata.org), seções "getting started". Arrays e tabelas, a base de todo o código do projeto.
- Tutoriais da Lightkurve (lightkurve.github.io). Baixar, limpar, achatar e dobrar curvas do TESS; o caminho para reproduzir Pi Men c.

### Cursos complementares

- *Super-Earths and Life* (Harvard, plataforma edX). Módulos acessíveis sobre detecção e caracterização de exoplanetas.
- *Astrobiology and the Search for Extraterrestrial Life* (Universidade de Edimburgo, Coursera). Contexto científico mais amplo, também acessível.

## Nível avançado

### Como ler artigos

- Keshav, S. (2007). "How to Read a Paper", *ACM SIGCOMM Computer Communication Review* 37. O método das três passadas adaptado no índice do nível avançado.

### A1. Algoritmos de detecção

- Kovács, G., Zucker, S. & Mazeh, T. (2002). *Astronomy & Astrophysics* 391, 369. O artigo original do BLS; contém toda a estatística da aula A1.
- Hippke, M. & Heller, R. (2019). *Astronomy & Astrophysics* 623, A39. O TLS completo, com equações e comparação com o BLS.
- Ofir, A. (2014). *Astronomy & Astrophysics* 561, A138. Amostragem ótima da grade de períodos, usada pelo TLS.
- Hippke, M. et al. (2019). *The Astronomical Journal* 158, 143. O wotan e a comparação de métodos de detrending que justifica o biweight com janela de cerca de três durações.
- Foreman-Mackey, D. et al. (2017). *The Astronomical Journal* 154, 220. O celerite, para processos gaussianos rápidos em séries temporais.
- Aigrain, S. & Foreman-Mackey, D. (2023). *Annual Review of Astronomy and Astrophysics* 61, 329. Revisão sobre processos gaussianos em séries temporais astronômicas; leitura de fôlego para quem quiser testar GP no projeto.
- Kipping, D. M. (2010). *Monthly Notices of the RAS* 408, 1758. Os efeitos de integrar e agrupar pontos na forma do trânsito; ajuda a pensar o `bin_minutes`.
- Osborn, H. P. et al. (2016). *Monthly Notices of the RAS* 457, 2273. Trânsitos únicos no K2 e estimativa de período a partir de um só evento.

### A2. Vetting das missões

- Jenkins, J. M. et al. (2010). *The Astrophysical Journal Letters* 713, L87. Visão geral do pipeline científico do Kepler, ancestral do SPOC.
- Twicken, J. D. et al. (2018). *Publications of the Astronomical Society of the Pacific* 130, 064502. O Data Validation: imagem-diferença, centróides e demais diagnósticos.
- Coughlin, J. L. et al. (2016). *The Astrophysical Journal Supplement Series* 224, 12. O catálogo DR24 do Kepler e a primeira versão do Robovetter.
- Thompson, S. E. et al. (2018). *The Astrophysical Journal Supplement Series* 235, 38. O DR25 e o Robovetter, com confiabilidade medida por curvas invertidas e embaralhadas.
- Guerrero, N. M. et al. (2021). *The Astrophysical Journal Supplement Series* 254, 39. O catálogo de TOIs da missão principal e o processo de vetting da equipe do TESS.
- Prša, A. et al. (2022). *The Astrophysical Journal Supplement Series* 258, 16. O catálogo de binárias eclipsantes do TESS, espelhado pelo projeto (e que contém hot Jupiters).
- Bryson, S. T. et al. (2013). *Publications of the Astronomical Society of the Pacific* 125, 889. Identificação de falsos positivos de fundo com imagens-diferença.
- Coughlin, J. L. et al. (2014). *The Astronomical Journal* 147, 119. Casamento de efemérides no campo do Kepler; base conceitual do `NEARBY_KNOWN`.

### A3. Probabilidade de falso positivo

- Morton, T. D. (2012). *The Astrophysical Journal* 761, 6. O método de validação estatística implementado no vespa.
- Morton, T. D. & Johnson, J. A. (2011). *The Astrophysical Journal* 738, 170. Estimativa da taxa de falsos positivos esperada entre candidatos do Kepler.
- Morton, T. D. et al. (2016). *The Astrophysical Journal* 822, 86. Validação em massa de planetas do Kepler; mostra o que "validado" significa.
- Giacalone, S. et al. (2021). *The Astronomical Journal* 161, 24. O triceratops, usado pelo PlanetHunter; cenários, FPP, NFPP e limiares.
- Torres, G. et al. (2011). *The Astrophysical Journal* 727, 24. O BLENDER e a validação do Kepler-9 d; outra escola de validação estatística.
- Fressin, F. et al. (2013). *The Astrophysical Journal* 766, 81. Taxa de falsos positivos do Kepler por tipo de cenário; ajuda a calibrar a intuição sobre priors.
- Lissauer, J. J. et al. (2012). *The Astrophysical Journal* 750, 112. Por que candidatos em sistemas múltiplos são quase sempre planetas.
- Raghavan, D. et al. (2010). *The Astrophysical Journal Supplement Series* 190, 1. Multiplicidade de estrelas tipo Sol; de onde vem a ideia de que cerca de metade delas tem companheira.

### A4. Aprendizado de máquina

- Shallue, C. J. & Vanderburg, A. (2018). *The Astronomical Journal* 155, 94. Rede neural com visões global e local para sinais do Kepler.
- Yu, L. et al. (2019). *The Astronomical Journal* 158, 25. Adaptação dessa rede ao TESS, com triagem e vetting.
- Valizadegan, H. et al. (2022). *The Astrophysical Journal* 926, 120. O ExoMiner e a validação de 301 planetas do Kepler.
- Armstrong, D. J. et al. (2021). *Monthly Notices of the RAS* 504, 5327. Validação de planetas com vários algoritmos de ML e probabilidades calibradas.
- Guo, C. et al. (2017). "On Calibration of Modern Neural Networks", *Proceedings of the 34th International Conference on Machine Learning*. Redes profundas são confiantes demais; o temperature scaling corrige.

### A5. Medir o sistema

- Wilson, E. B. (1927). *Journal of the American Statistical Association* 22, 209. O intervalo de confiança usado em todos os relatórios de benchmark.
- Brown, L. D., Cai, T. T. & DasGupta, A. (2001). *Statistical Science* 16, 101. Por que o intervalo ingênuo falha e Wilson funciona.
- McNemar, Q. (1947). *Psychometrika* 12, 153. O teste para comparar proporções medidas nos mesmos objetos, base da comparação antes/depois.
- Christiansen, J. L. et al. (2013). *The Astrophysical Journal Supplement Series* 207, 35. Injeção de trânsitos no Kepler para medir recuperação; modelo do injection-recovery.
- Burke, C. J. et al. (2015). *The Astrophysical Journal* 809, 8. Completude do Kepler aplicada a taxas de ocorrência de planetas.
- Kreidberg, L. (2015). *Publications of the Astronomical Society of the Pacific* 127, 1161. O `batman`, que gera os trânsitos sintéticos.

### A6. Do candidato à comunidade

- Eisner, N. L. et al. (2021). *Monthly Notices of the RAS* 501, 4669. Resultados do Planet Hunters TESS; como voluntários chegam a CTOIs, muitos de trânsito único.
- Collins, K. A. et al. (2017). *The Astronomical Journal* 153, 77. O AstroImageJ, ferramenta padrão da fotometria em solo do TFOP.
- Avaliação dos CTOIs da comunidade (Zenodo, registro 5130660). Os 168 TOIs nascidos de CTOIs até 2021 e por que se concentram em estrelas fracas e trânsitos únicos; evidência para os nichos do projeto.
- Página do TFOP no HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html). Estrutura do programa de acompanhamento e como participar.

## Dados, missões e catálogos (citações obrigatórias)

Qualquer trabalho com dados do TESS deve citar as fontes abaixo, conforme o que foi usado.

- Ricker, G. R. et al. (2015). *Journal of Astronomical Telescopes, Instruments, and Systems* 1, 014003. A missão TESS.
- Jenkins, J. M. et al. (2016). *Proceedings of the SPIE* 9913. O SPOC, que produz as curvas de 2 minutos e os relatórios DV.
- Huang, C. X. et al. (2020). *Research Notes of the AAS* 4, 204. O QLP, pipeline das imagens completas.
- Stassun, K. G. et al. (2019). *The Astronomical Journal* 158, 138. O TESS Input Catalog (TIC v8), fonte dos parâmetros estelares.
- Gaia Collaboration, Prusti, T. et al. (2016). *Astronomy & Astrophysics* 595, A1. A missão Gaia.
- Gaia Collaboration, Vallenari, A. et al. (2023). *Astronomy & Astrophysics* 674, A1. O Gaia DR3, usado nos vizinhos e nas binárias do Gaia.
- Akeson, R. L. et al. (2013). *Publications of the Astronomical Society of the Pacific* 125, 989. O NASA Exoplanet Archive (exoplanetarchive.ipac.caltech.edu).
- Schneider, J. et al. (2011). *Astronomy & Astrophysics* 532, A79. A Encyclopaedia of Exoplanetary Systems (exoplanet.eu).
- ExoFOP-TESS (exofop.ipac.caltech.edu/tess). Tabelas de TOIs e CTOIs, notas e arquivos de acompanhamento; cite conforme a página de ajuda do serviço.

## Ferramentas

- Lightkurve Collaboration (2018), ascl:1812.013. Lightkurve, para baixar e manipular curvas do TESS.
- Astropy Collaboration (2022). *The Astrophysical Journal* 935, 167. Astropy, base de unidades, tempo e BLS.
- Ginsburg, A. et al. (2019). *The Astronomical Journal* 157, 98. Astroquery, para consultar MAST, Gaia, VizieR e SIMBAD.
- wotan (Hippke et al. 2019), TLS (Hippke & Heller 2019), batman (Kreidberg 2015), triceratops (Giacalone et al. 2021), vespa (Morton 2012) e celerite (Foreman-Mackey et al. 2017): cite os artigos listados acima.

## Sites e comunidades

- ADS (ui.adsabs.harvard.edu). Buscador da literatura astronômica; use `object:` e `full:` para buscar alvos.
- arXiv, seção astro-ph.EP (arxiv.org). Artigos novos sobre planetas, antes da publicação nas revistas.
- ExoFOP-TESS (exofop.ipac.caltech.edu/tess). Páginas de alvo, notas da comunidade e submissão de CTOI.
- NASA Exoplanet Archive (exoplanetarchive.ipac.caltech.edu). Planetas confirmados e tabela de TOIs com disposições.
- Planet Hunters TESS no Zooniverse (zooniverse.org). Classificação de curvas e fórum onde voluntários e profissionais discutem candidatos.
