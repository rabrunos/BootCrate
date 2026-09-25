# Changelog

## v0.9 — Adoção e validação

- A adoção em código existente agora começa em uma cópia isolada e aplica ao original somente o delta aprovado após conferir a base.
- A verificação pós-materialização agora rejeita perfis ausentes ou incompletos, versões e referências inválidas.
- O Setup agora diferencia produto novo, repositório existente e integração externa sem oferecer opções que desligam GitHub Issues.
- Adicionados os perfis de consumo Padrão e Econômico, mantendo o mesmo esforço obrigatório e os mesmos critérios de aceitação.
- Adicionado um Project Console estático e opcional para consultar configuração e exportar um resumo local sem segredos.
- A preparação de entrega agora distingue candidato, notas e confirmação de cada destino, bloqueando duplicatas divergentes e resultados desconhecidos.
- A atualização de arquivos gerenciados antes da materialização agora preserva customizações e interrompe conflitos.
- Ampliados os cenários de regressão e os contratos de avaliação para registrar evidência efetivamente observada.
- Corrigidos os achados A01–A09 da auditoria em atualização gerenciada, validação/materialização, guidance, entrega, adoção e Console, com regressões nos módulos atuais.
- O Intake agora preserva uma identidade canônica de repositório e a origem versionada do BootCrate no handoff.
- Adicionados três perfis independentes de permissões de execução, com default protegido/manual, opt-in de risco para Acesso Total e adaptadores Codex/Claude que distinguem solicitado de efetivo.

## v0.8 — Setup guiado

- Adicionado um Setup local com perguntas condicionais, revisão das respostas e handoff inicial para GitHub e ChatGPT.

## v0.7 — Segurança e validação

- Adicionados controles de segurança por superfície e um validador estrutural para o template.

## v0.6 — Versão do pacote

- Atualizada a fonte canônica de versão do BootCrate para 0.6, sem mudança funcional nesse commit.

## v0.5 — Descoberta e esforço

- Adicionadas rotas de descoberta adaptativa e níveis de esforço para o Main.

## v0.4 — Identidade de versão

- Adicionada uma fonte canônica de versão para o próprio BootCrate.
