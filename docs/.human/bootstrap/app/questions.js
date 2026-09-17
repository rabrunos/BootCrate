window.BOOTCRATE_QUESTIONS = [
  {
    "id": "project_name",
    "section": "identity",
    "type": "text",
    "required": true,
    "en": "What should the project be called?",
    "pt": "Como o projeto deve se chamar?"
  },
  {
    "id": "one_sentence",
    "section": "identity",
    "type": "textarea",
    "required": true,
    "en": "Describe the desired project in one sentence.",
    "pt": "Descreva o projeto desejado em uma frase."
  },
  {
    "id": "project_kind",
    "section": "identity",
    "type": "select",
    "required": true,
    "en": "What are you primarily building?",
    "pt": "O que você está construindo principalmente?",
    "options": [
      [
        "game",
        "Game",
        "Jogo"
      ],
      [
        "game_mod",
        "Game mod",
        "Mod de jogo"
      ],
      [
        "game_engine",
        "Game engine",
        "Engine de jogo"
      ],
      [
        "web_app",
        "Web application",
        "Aplicativo web"
      ],
      [
        "desktop_app",
        "Desktop application",
        "Aplicativo desktop"
      ],
      [
        "mobile_app",
        "Mobile application",
        "Aplicativo mobile"
      ],
      [
        "library",
        "Library/SDK",
        "Biblioteca/SDK"
      ],
      [
        "cli_tool",
        "CLI/tooling",
        "CLI/ferramenta"
      ],
      [
        "service",
        "Backend/service/API",
        "Backend/serviço/API"
      ],
      [
        "automation",
        "Automation",
        "Automação"
      ],
      [
        "other",
        "Other",
        "Outro"
      ]
    ]
  },
  {
    "id": "existing_or_new",
    "section": "identity",
    "type": "select",
    "required": true,
    "en": "Is this a new project or work on an existing codebase/product?",
    "pt": "É um projeto novo ou trabalho sobre um código/produto existente?",
    "options": [
      [
        "new",
        "New",
        "Novo"
      ],
      [
        "existing_code",
        "Existing codebase",
        "Código existente"
      ],
      [
        "external_target",
        "Extension/mod/integration with external product",
        "Extensão/mod/integração com produto externo"
      ],
      [
        "unknown",
        "Not sure",
        "Não sei"
      ]
    ]
  },
  {
    "id": "success",
    "section": "identity",
    "type": "textarea",
    "required": true,
    "en": "What would make the first meaningful version successful?",
    "pt": "O que faria a primeira versão significativa ser considerada bem-sucedida?"
  },
  {
    "id": "non_goals",
    "section": "identity",
    "type": "textarea",
    "en": "What is explicitly out of scope for now?",
    "pt": "O que está explicitamente fora de escopo por enquanto?"
  },
  {
    "id": "owner_role",
    "section": "owner",
    "type": "textarea",
    "en": "How do you want to participate (product, architecture, testing, coding, other)?",
    "pt": "Como você quer participar (produto, arquitetura, testes, código, outro)?"
  },
  {
    "id": "technical_level",
    "section": "owner",
    "type": "select",
    "en": "How technical do you consider yourself for this project?",
    "pt": "Qual é seu nível técnico para este projeto?",
    "options": [
      [
        "nontechnical",
        "Non-technical",
        "Não técnico"
      ],
      [
        "beginner",
        "Beginner",
        "Iniciante"
      ],
      [
        "intermediate",
        "Intermediate",
        "Intermediário"
      ],
      [
        "advanced",
        "Advanced",
        "Avançado"
      ],
      [
        "expert",
        "Expert",
        "Especialista"
      ]
    ]
  },
  {
    "id": "report_language",
    "section": "owner",
    "type": "select",
    "required": true,
    "en": "What language should implementation-agent final reports use?",
    "pt": "Qual idioma os relatórios finais dos agentes de implementação devem usar?",
    "options": [
      [
        "pt-BR",
        "Português (Brasil)",
        "Português (Brasil)"
      ],
      [
        "en",
        "English",
        "Inglês"
      ],
      [
        "other",
        "Other",
        "Outro"
      ]
    ]
  },
  {
    "id": "repo_language",
    "section": "owner",
    "type": "select",
    "required": true,
    "en": "What language should repository technical documentation/prompts use?",
    "pt": "Qual idioma a documentação técnica/prompts do repositório deve usar?",
    "options": [
      [
        "en",
        "English",
        "Inglês"
      ],
      [
        "pt-BR",
        "Português (Brasil)",
        "Português (Brasil)"
      ],
      [
        "other",
        "Other",
        "Outro"
      ]
    ]
  },
  {
    "id": "autonomy",
    "section": "owner",
    "type": "select",
    "en": "How much implementation autonomy should agents have?",
    "pt": "Quanta autonomia de implementação os agentes devem ter?",
    "options": [
      [
        "low",
        "Low — ask before meaningful choices",
        "Baixa — perguntar antes de decisões relevantes"
      ],
      [
        "medium",
        "Medium — decide within approved scope",
        "Média — decidir dentro do escopo aprovado"
      ],
      [
        "high",
        "High — broad autonomy within repository rules",
        "Alta — ampla autonomia dentro das regras"
      ]
    ]
  },
  {
    "id": "target_platforms",
    "section": "platform",
    "type": "multiselect",
    "en": "Target platforms?",
    "pt": "Plataformas alvo?",
    "options": [
      [
        "windows",
        "Windows",
        "Windows"
      ],
      [
        "linux",
        "Linux",
        "Linux"
      ],
      [
        "macos",
        "macOS",
        "macOS"
      ],
      [
        "web",
        "Web/browser",
        "Web/navegador"
      ],
      [
        "android",
        "Android",
        "Android"
      ],
      [
        "ios",
        "iOS",
        "iOS"
      ],
      [
        "console",
        "Console",
        "Console"
      ],
      [
        "server",
        "Server/cloud",
        "Servidor/cloud"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "primary_dev_os",
    "section": "platform",
    "type": "select",
    "en": "Primary development OS?",
    "pt": "Sistema operacional principal de desenvolvimento?",
    "options": [
      [
        "windows",
        "Windows",
        "Windows"
      ],
      [
        "linux",
        "Linux",
        "Linux"
      ],
      [
        "macos",
        "macOS",
        "macOS"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "distribution",
    "section": "platform",
    "type": "textarea",
    "en": "How do you expect users to receive/run the project?",
    "pt": "Como você espera que os usuários recebam/executem o projeto?"
  },
  {
    "id": "offline_requirement",
    "section": "platform",
    "type": "select",
    "en": "Must development/runtime work offline?",
    "pt": "O desenvolvimento/runtime precisa funcionar offline?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "partial",
        "Partially",
        "Parcialmente"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "language_known",
    "section": "stack",
    "type": "select",
    "en": "Do you already require a programming language?",
    "pt": "Você já exige alguma linguagem de programação?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "preference",
        "Preference only",
        "Apenas preferência"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "language_value",
    "section": "stack",
    "type": "text",
    "condition": {
      "id": "language_known",
      "in": [
        "yes",
        "preference"
      ]
    },
    "en": "Which language(s)?",
    "pt": "Qual(is) linguagem(ns)?"
  },
  {
    "id": "framework_known",
    "section": "stack",
    "type": "select",
    "en": "Do you already require a framework/engine/runtime?",
    "pt": "Você já exige algum framework/engine/runtime?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "preference",
        "Preference only",
        "Apenas preferência"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "framework_value",
    "section": "stack",
    "type": "text",
    "condition": {
      "id": "framework_known",
      "in": [
        "yes",
        "preference"
      ]
    },
    "en": "Which framework/engine/runtime?",
    "pt": "Qual framework/engine/runtime?"
  },
  {
    "id": "dependency_constraints",
    "section": "stack",
    "type": "textarea",
    "en": "Required or forbidden dependencies/libraries/licenses?",
    "pt": "Dependências/bibliotecas/licenças obrigatórias ou proibidas?"
  },
  {
    "id": "performance_constraints",
    "section": "stack",
    "type": "textarea",
    "en": "Any performance, memory, latency, startup, or size constraints?",
    "pt": "Há restrições de desempenho, memória, latência, inicialização ou tamanho?"
  },
  {
    "id": "external_product_name",
    "section": "external",
    "type": "text",
    "condition": {
      "id": "existing_or_new",
      "in": [
        "external_target"
      ]
    },
    "en": "What external product/game/system is being extended or modified?",
    "pt": "Qual produto/jogo/sistema externo será estendido ou modificado?"
  },
  {
    "id": "official_sdk_known",
    "section": "external",
    "type": "select",
    "condition": {
      "id": "existing_or_new",
      "in": [
        "external_target"
      ]
    },
    "en": "Is there an official SDK/modding API/plugin system?",
    "pt": "Existe SDK/API de modding/sistema de plugins oficial?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "community_tool_known",
    "section": "external",
    "type": "select",
    "condition": {
      "id": "existing_or_new",
      "in": [
        "external_target"
      ]
    },
    "en": "Are there community loaders/frameworks/tools?",
    "pt": "Existem loaders/frameworks/ferramentas da comunidade?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "community_tool_value",
    "section": "external",
    "type": "text",
    "condition": {
      "id": "community_tool_known",
      "in": [
        "yes"
      ]
    },
    "en": "Which ones do you already know? (optional)",
    "pt": "Quais você já conhece? (opcional)"
  },
  {
    "id": "target_engine_known",
    "section": "external",
    "type": "select",
    "condition": {
      "id": "existing_or_new",
      "in": [
        "external_target"
      ]
    },
    "en": "Do you know the external product's engine/runtime?",
    "pt": "Você conhece a engine/runtime do produto externo?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "target_engine_value",
    "section": "external",
    "type": "text",
    "condition": {
      "id": "target_engine_known",
      "in": [
        "yes"
      ]
    },
    "en": "Engine/runtime?",
    "pt": "Engine/runtime?"
  },
  {
    "id": "binary_access",
    "section": "external",
    "type": "select",
    "condition": {
      "id": "existing_or_new",
      "in": [
        "external_target"
      ]
    },
    "en": "Will the local environment have access to installed binaries/assets/logs?",
    "pt": "O ambiente local terá acesso a binários/assets/logs instalados?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "partial",
        "Partially",
        "Parcialmente"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "reverse_engineering_allowed",
    "section": "external",
    "type": "select",
    "condition": {
      "id": "existing_or_new",
      "in": [
        "external_target"
      ]
    },
    "en": "May the project use local inspection/decompilation/reverse-engineering tools when legally/technically appropriate?",
    "pt": "O projeto pode usar inspeção/decompilação/reverse engineering local quando legal e tecnicamente apropriado?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "conditional",
        "Only after owner approval",
        "Somente após aprovação do owner"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "game_engine_choice",
    "section": "game",
    "type": "select",
    "condition": {
      "id": "project_kind",
      "in": [
        "game",
        "game_engine"
      ]
    },
    "en": "For game work, is an existing engine required?",
    "pt": "Para o jogo, uma engine existente é obrigatória?",
    "options": [
      [
        "existing",
        "Use an existing engine",
        "Usar engine existente"
      ],
      [
        "custom",
        "Build custom engine/foundation",
        "Criar engine/fundação própria"
      ],
      [
        "undecided",
        "Undecided",
        "Indefinido"
      ]
    ]
  },
  {
    "id": "game_dimension",
    "section": "game",
    "type": "select",
    "condition": {
      "id": "project_kind",
      "in": [
        "game",
        "game_engine"
      ]
    },
    "en": "Primary presentation?",
    "pt": "Apresentação principal?",
    "options": [
      [
        "2d",
        "2D",
        "2D"
      ],
      [
        "3d",
        "3D",
        "3D"
      ],
      [
        "hybrid",
        "Hybrid",
        "Híbrido"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "multiplayer",
    "section": "game",
    "type": "select",
    "condition": {
      "id": "project_kind",
      "in": [
        "game",
        "game_mod",
        "game_engine"
      ]
    },
    "en": "Multiplayer/networking expected?",
    "pt": "Multiplayer/rede é esperado?",
    "options": [
      [
        "none",
        "No",
        "Não"
      ],
      [
        "local",
        "Local only",
        "Somente local"
      ],
      [
        "online",
        "Online",
        "Online"
      ],
      [
        "maybe",
        "Maybe later",
        "Talvez depois"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "save_system",
    "section": "game",
    "type": "select",
    "condition": {
      "id": "project_kind",
      "in": [
        "game",
        "game_mod"
      ]
    },
    "en": "Persistence/save data expected?",
    "pt": "Persistência/save é esperado?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "web_scope",
    "section": "web",
    "type": "multiselect",
    "condition": {
      "id": "project_kind",
      "in": [
        "web_app",
        "service"
      ]
    },
    "en": "Which web areas are expected?",
    "pt": "Quais áreas web são esperadas?",
    "options": [
      [
        "frontend",
        "Frontend",
        "Frontend"
      ],
      [
        "backend",
        "Backend/API",
        "Backend/API"
      ],
      [
        "database",
        "Database",
        "Banco de dados"
      ],
      [
        "auth",
        "Authentication",
        "Autenticação"
      ],
      [
        "realtime",
        "Realtime/WebSockets",
        "Realtime/WebSockets"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "hosting_known",
    "section": "web",
    "type": "select",
    "condition": {
      "id": "project_kind",
      "in": [
        "web_app",
        "service"
      ]
    },
    "en": "Is hosting/provider already chosen?",
    "pt": "Hospedagem/provedor já foi escolhido?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "hosting_value",
    "section": "web",
    "type": "text",
    "condition": {
      "id": "hosting_known",
      "in": [
        "yes"
      ]
    },
    "en": "Hosting/provider?",
    "pt": "Hospedagem/provedor?"
  },
  {
    "id": "sensitive_data",
    "section": "security",
    "type": "select",
    "en": "Will the project handle personal, secret, financial, health, authentication, or other sensitive data?",
    "pt": "O projeto lidará com dados pessoais, secretos, financeiros, saúde, autenticação ou outros dados sensíveis?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "secrets_needed",
    "section": "security",
    "type": "select",
    "en": "Will development require API keys/tokens/credentials?",
    "pt": "O desenvolvimento exigirá chaves de API/tokens/credenciais?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "log_privacy",
    "section": "security",
    "type": "select",
    "en": "Can runtime/build logs contain private or machine-specific data?",
    "pt": "Logs de runtime/build podem conter dados privados ou específicos da máquina?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "compliance",
    "section": "security",
    "type": "textarea",
    "en": "Any legal, license, privacy, compliance, or distribution restrictions already known?",
    "pt": "Há restrições legais, licença, privacidade, compliance ou distribuição já conhecidas?"
  },
  {
    "id": "automated_tests",
    "section": "validation",
    "type": "select",
    "en": "Do you expect automated tests from the beginning?",
    "pt": "Você espera testes automatizados desde o início?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "recommended",
        "Let the orchestrator recommend",
        "Deixar o orquestrador recomendar"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "manual_smoke",
    "section": "validation",
    "type": "select",
    "en": "Will some important behavior require human/manual smoke testing?",
    "pt": "Algum comportamento importante exigirá teste manual/humano?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "ci",
    "section": "validation",
    "type": "select",
    "en": "Should CI run on GitHub when useful?",
    "pt": "CI deve rodar no GitHub quando útil?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "recommended",
        "Let the orchestrator recommend",
        "Deixar o orquestrador recomendar"
      ]
    ]
  },
  {
    "id": "validation_priorities",
    "section": "validation",
    "type": "textarea",
    "en": "What failures are most important to catch automatically?",
    "pt": "Quais falhas são mais importantes de detectar automaticamente?"
  },
  {
    "id": "single_or_team",
    "section": "workflow",
    "type": "select",
    "required": true,
    "en": "Who will normally develop this repository?",
    "pt": "Quem normalmente desenvolverá este repositório?",
    "options": [
      [
        "single",
        "One owner/developer",
        "Um owner/desenvolvedor"
      ],
      [
        "small_team",
        "Small team",
        "Equipe pequena"
      ],
      [
        "team",
        "Team/multiple contributors",
        "Equipe/múltiplos contribuidores"
      ]
    ]
  },
  {
    "id": "issues_tracking",
    "section": "workflow",
    "type": "select",
    "required": true,
    "en": "Use GitHub Issues as the operational source for plans, bugs, decisions, acceptance and follow-up?",
    "pt": "Usar GitHub Issues como fonte operacional para planos, bugs, decisões, aceitação e follow-up?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "custom",
        "Custom approach",
        "Abordagem personalizada"
      ]
    ]
  },
  {
    "id": "commit_push_policy",
    "section": "workflow",
    "type": "select",
    "en": "After a validated implementation task, should Codex normally commit and push?",
    "pt": "Após uma tarefa validada, o Codex deve normalmente fazer commit e push?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "ask",
        "Ask/only when prompt says",
        "Perguntar/somente quando o prompt disser"
      ],
      [
        "no",
        "No",
        "Não"
      ]
    ]
  },
  {
    "id": "issue_closure_owner",
    "section": "workflow",
    "type": "select",
    "en": "Who should normally decide whether an Issue is closed?",
    "pt": "Quem normalmente deve decidir se uma Issue é fechada?",
    "options": [
      [
        "orchestrator",
        "ChatGPT/orchestrator after reviewing evidence",
        "ChatGPT/orquestrador após revisar evidências"
      ],
      [
        "codex",
        "Implementation agent when explicitly authorized",
        "Agente de implementação quando explicitamente autorizado"
      ],
      [
        "human",
        "Human owner manually",
        "Owner humano manualmente"
      ]
    ]
  },
  {
    "id": "release_approval",
    "section": "workflow",
    "type": "select",
    "en": "Who may authorize a real external release/publish?",
    "pt": "Quem pode autorizar uma publicação/release externa real?",
    "options": [
      [
        "owner_only",
        "Owner only",
        "Somente owner"
      ],
      [
        "task_explicit",
        "Explicit approved task",
        "Tarefa explicitamente aprovada"
      ],
      [
        "custom",
        "Custom",
        "Personalizado"
      ]
    ]
  },
  {
    "id": "primary_orchestration",
    "section": "ai",
    "type": "select",
    "required": true,
    "en": "What should be the normal primary orchestration workflow?",
    "pt": "Qual deve ser o fluxo normal principal de orquestração?",
    "options": [
      [
        "chatgpt",
        "ChatGPT orchestrates; implementation runs in Codex/Claude",
        "ChatGPT orquestra; implementação roda no Codex/Claude"
      ],
      [
        "local_planner",
        "Codex/Claude planning is primary",
        "Planejamento do Codex/Claude é principal"
      ],
      [
        "custom",
        "Custom",
        "Personalizado"
      ]
    ]
  },
  {
    "id": "claude_code",
    "section": "ai",
    "type": "select",
    "en": "Will Claude Code be used as an implementation harness?",
    "pt": "Claude Code será usado como harness/agente de implementação?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "maybe",
        "Maybe",
        "Talvez"
      ]
    ]
  },
  {
    "id": "planning_fallback",
    "section": "ai",
    "type": "multiselect",
    "en": "Which fallback planners should remain usable if ChatGPT is unavailable or limited?",
    "pt": "Quais planejadores fallback devem continuar utilizáveis se o ChatGPT estiver indisponível ou limitado?",
    "options": [
      [
        "codex_plan",
        "Codex Plan Mode",
        "Modo Plan do Codex"
      ],
      [
        "claude_plan",
        "Claude Code Plan Mode",
        "Modo Plan do Claude Code"
      ],
      [
        "none",
        "No fallback planning required",
        "Não é necessário fallback de planejamento"
      ]
    ]
  },
  {
    "id": "codex_local",
    "section": "ai",
    "type": "select",
    "en": "Will Codex Local/IDE be used?",
    "pt": "Codex Local/IDE será usado?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "maybe",
        "Maybe",
        "Talvez"
      ]
    ]
  },
  {
    "id": "codex_cloud",
    "section": "ai",
    "type": "select",
    "en": "Will Codex Cloud be used?",
    "pt": "Codex Cloud será usado?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "maybe",
        "Maybe",
        "Talvez"
      ]
    ]
  },
  {
    "id": "agent_budget",
    "section": "ai",
    "type": "select",
    "en": "Preferred agent topology?",
    "pt": "Topologia de agentes preferida?",
    "options": [
      [
        "main_worker",
        "Main + low-cost Worker",
        "Main + Worker de baixo custo"
      ],
      [
        "main_worker_scout",
        "Main + Worker + Scout",
        "Main + Worker + Scout"
      ],
      [
        "recommend",
        "Let bootstrap research/recommend",
        "Deixar bootstrap pesquisar/recomendar"
      ]
    ]
  },
  {
    "id": "model_constraints",
    "section": "ai",
    "type": "textarea",
    "en": "Known model/plan/usage constraints or preferences?",
    "pt": "Restrições/preferências conhecidas de modelo/plano/uso?"
  },
  {
    "id": "local_memory",
    "section": "ai",
    "type": "select",
    "en": "May implementation tools use local memory as non-authoritative convenience?",
    "pt": "Ferramentas de implementação podem usar memória local como conveniência não autoritativa?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "research",
        "Research/recommend",
        "Pesquisar/recomendar"
      ]
    ]
  },
  {
    "id": "local_large_data",
    "section": "local",
    "type": "multiselect",
    "en": "What large/local-only data might exist?",
    "pt": "Quais dados grandes/somente locais podem existir?",
    "options": [
      [
        "logs",
        "Logs",
        "Logs"
      ],
      [
        "binaries",
        "External binaries",
        "Binários externos"
      ],
      [
        "decompile",
        "Decompiled/extracted output",
        "Saída decompilada/extraída"
      ],
      [
        "screenshots",
        "Screenshots/video",
        "Screenshots/vídeo"
      ],
      [
        "datasets",
        "Datasets",
        "Datasets"
      ],
      [
        "build_artifacts",
        "Build artifacts",
        "Artefatos de build"
      ],
      [
        "none",
        "None expected",
        "Nenhum esperado"
      ],
      [
        "unknown",
        "Unknown",
        "Não sei"
      ]
    ]
  },
  {
    "id": "diagnostic_reduction",
    "section": "local",
    "type": "select",
    "en": "Should large diagnostics be sanitized/compacted into structured data before AI analysis when practical?",
    "pt": "Diagnósticos grandes devem ser sanitizados/compactados em dados estruturados antes da análise por IA quando prático?",
    "options": [
      [
        "yes",
        "Yes",
        "Sim"
      ],
      [
        "no",
        "No",
        "Não"
      ],
      [
        "recommend",
        "Let bootstrap recommend",
        "Deixar bootstrap recomendar"
      ]
    ]
  },
  {
    "id": "must_have_tools",
    "section": "final",
    "type": "textarea",
    "en": "Any tools/editors/services you definitely want to use?",
    "pt": "Alguma ferramenta/editor/serviço que você definitivamente quer usar?"
  },
  {
    "id": "must_avoid_tools",
    "section": "final",
    "type": "textarea",
    "en": "Any tools/editors/services you definitely want to avoid?",
    "pt": "Alguma ferramenta/editor/serviço que você definitivamente quer evitar?"
  },
  {
    "id": "known_risks",
    "section": "final",
    "type": "textarea",
    "en": "Known risks, uncertainties, or previous failed approaches?",
    "pt": "Riscos, incertezas ou abordagens anteriores que falharam?"
  },
  {
    "id": "research_requests",
    "section": "final",
    "type": "textarea",
    "en": "What do you explicitly want the orchestrator to research before proposing architecture?",
    "pt": "O que você quer explicitamente que o orquestrador pesquise antes de propor a arquitetura?"
  },
  {
    "id": "anything_else",
    "section": "final",
    "type": "textarea",
    "en": "Anything else the orchestrator must know?",
    "pt": "Algo mais que o orquestrador precisa saber?"
  }
];
window.BOOTCRATE_SECTIONS = {
  "identity": [
    "Project",
    "Projeto"
  ],
  "owner": [
    "Owner & communication",
    "Owner e comunicação"
  ],
  "platform": [
    "Platforms & distribution",
    "Plataformas e distribuição"
  ],
  "stack": [
    "Technology preferences",
    "Preferências de tecnologia"
  ],
  "external": [
    "External target / modding",
    "Alvo externo / modding"
  ],
  "game": [
    "Game-specific",
    "Específico de jogo"
  ],
  "web": [
    "Web/service-specific",
    "Específico de web/serviço"
  ],
  "security": [
    "Data, security & constraints",
    "Dados, segurança e restrições"
  ],
  "validation": [
    "Validation",
    "Validação"
  ],
  "workflow": [
    "GitHub & workflow",
    "GitHub e fluxo"
  ],
  "ai": [
    "AI workflow",
    "Fluxo de IA"
  ],
  "local": [
    "Local-only workspace",
    "Workspace somente local"
  ],
  "final": [
    "Open questions",
    "Questões abertas"
  ]
};
