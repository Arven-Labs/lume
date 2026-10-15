# SPEC: Desmontagem do Lume

> Destinatário: agente que trabalha no repositório do Lume.
> Esta spec descreve **intenção e princípios**, não implementação.

## Regra número um para você (agente)

**Não presuma nada.** Nem estrutura de arquivos, nem código, nem convenções, nem o que existe no repositório. A conversa que originou esta spec foi de alto nível e a realidade do código pode ser diferente do que foi imaginado. Antes de propor qualquer coisa:

1. Explore o repositório e entenda o que realmente existe.
2. Apresente ao Fabio o que você encontrou.
3. Discuta as dúvidas e **confirme cada decisão de arquitetura com ele** antes de agir ("vai ser assim mesmo?").
4. Quando houver mais de um caminho razoável, apresente as opções com prós e contras e deixe ele escolher.

Itens marcados como **[DIREÇÃO]** são ideias a validar, não decisões.

## Contexto

O Lume (antes EasyBusiness) é hoje uma API de informações financeiras, consumida apenas pelo Anchor, embarcada como sidecar. Fabio percebeu que está trabalhando em dois repositórios dentro de um único projeto, o que gera desorganização. Nenhum dos projetos dele tem usuários ainda; ele está construindo primeiro para uso próprio, mas quer uma arquitetura que não exija retrabalho para escalar depois.

## Decisão tomada

**O Lume será desfeito.** O Anchor deve se tornar totalmente autossuficiente e não depender mais deste repositório. As capacidades de dados financeiros migram para dentro do Anchor (ver `SPEC-anchor-autossuficiencia.md`).

## Objetivo desta spec

Mapear com precisão o que existe no Lume e planejar, junto com Fabio, a migração do que for necessário para o Anchor, de modo que ao final o Lume possa ser descartado sem perda.

## O que fazer

- Inventariar o que o Lume faz hoje (capacidades, fontes de dados, cache/armazenamento, contratos expostos, configuração).
- Identificar o que o Anchor consome hoje e como (o mecanismo de sidecar, o fallback para instância compartilhada, etc.), sem presumir como funciona. Verifique.
- Propor, com opções e tradeoffs, o que migra, o que é reescrito e o que é descartado.
- Documentar a migração de forma que o agente do Anchor consiga executar a outra metade com contexto (alinhe com a spec do Anchor).

## Estado do repositório após a migração

- O repositório **permanece no GitHub por enquanto**.
- Fabio vai validar com o tempo que o Anchor funciona sem o Lume e **só então descartá-lo** (arquivar ou apagar, decisão dele).
- Nada deve ser deletado ou arquivado por você sem confirmação explícita.
- Considere deixar um aviso no README indicando que o projeto está em desmontagem e para onde as responsabilidades foram. **Confirme com ele antes.**

## Questões abertas (discuta com Fabio)

- Existe alguma ideia ou decisão antiga do Lume que deva ser preservada de alguma forma (padrão de `DataProvider` com fonte grátis, BYO-key e premium)?
- O que acontece com a renomeação EasyBusiness → Lume, que ainda não havia sido aplicada? Provavelmente perde o sentido, mas confirme.
- Há alguma outra coisa, além do Anchor, que dependa do Lume?

## Fora de escopo

- Qualquer mudança no Warden ou no TruthID.
- Criar novos repositórios.
