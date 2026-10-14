# A régua do sênior — Mini-Prontuário · FastAPI

Quarenta competências. Marque [x] só com evidência que existe neste
repositório: ataque (ATQ-xx), invariante (SEC-xx, nunca sozinho) ou
arquivo, com ::trecho quando for um teste ou uma seção. Confira com
`python regua.py`. Trinta com evidência equivalem a 75%.


## A · Modelo mental

- [x] 01 Responde 401, 403 e 404 no caso certo e explica a escolha — ATQ-01.1 · ATQ-01.5 · ATQ-12.1 · tests/test_objeto.py::test_bruno_nao_le_nem_altera_o_atendimento_da_ana_404
- [x] 02 Faz modelagem de ameaças de uma feature em 15 minutos — docs/AMEACAS.md::STRIDE
- [x] 03 Coloca cada verificação na camada certa: borda, rota ou domínio — SEC-25 · SEC-30 · tests/test_pipeline.py::test_portao2_recepcao_nao_le_prescricoes
- [x] 04 Faz rota nova nascer protegida; pública só por declaração — SEC-02 · tests/test_censo.py::test_toda_rota_declara_politica
- [x] 05 Classifica uma falha no OWASP Top 10 e no API Top 10 — docs/ASVS.md · docs/AMEACAS.md::ATQ-01.4

## B · Senhas e credenciais

- [x] 06 Usa argon2id nos parâmetros OWASP e migra hash antigo no login — SEC-05 · tests/test_senhas.py::test_rehash_transparente
- [x] 07 Aplica a política de senha do NIST SP 800-63B-4 — SEC-06 · ATQ-04.1 · ATQ-04.2 · tests/test_senhas.py::test_politica_aceita_frase_longa
- [x] 08 Elimina enumeração de usuários por mensagem, status e tempo — SEC-07 · ATQ-04.3 · ATQ-04.4 · cronometro.py
- [x] 09 Implementa reset com token de uso único, guardado com hash — SEC-08 · tests/test_senhas.py::test_reset_mesma_resposta_e_uso_unico
- [x] 10 Nunca registra segredo em log; sanitiza o que registra — SEC-23 · tests/test_limites.py::test_falha_vira_evento_sem_senha_e_sem_email

## C · Sessão e cookies

- [x] 11 Configura HttpOnly, Secure, SameSite e prefixo __Host- — SEC-10 · ATQ-05.1 · ATQ-05.2 · tests/test_sessoes.py::test_cookie_com_atributos_de_seguranca
- [x] 12 Regenera a sessão no login (fixação de sessão) — ATQ-05.3 · tests/test_sessoes.py::test_login_nao_reaproveita_identificador
- [x] 13 Aplica expiração ociosa e absoluta; logout invalida no servidor — SEC-11 · ATQ-05.4 · tests/test_sessoes.py::test_expira_no_limite_absoluto
- [x] 14 Defende CSRF quando a credencial é um cookie — SEC-12 · ATQ-05.5 · tests/test_sessoes.py::test_csrf_outro_site_recusado_e_proprio_site_passa
- [x] 15 Configura CORS com credenciais sem curinga nem origem refletida — tests/test_pipeline.py::test_cors_so_para_origens_da_lista_nunca_curinga

## D · Tokens

- [x] 16 Verifica JWT com algoritmo fixo, iss, aud e exp — SEC-14 · ATQ-06.4 · tests/test_tokens.py::test_token_de_outra_audiencia
- [x] 17 Sabe o que pode e o que nunca vai no payload — ATQ-06.1 · tests/test_tokens.py::test_so_identificadores_10_minutos
- [x] 18 Faz access curto + refresh com rotação e detecção de reuso — SEC-16 · SEC-17 · ATQ-07.1 · ATQ-07.2 · tests/test_refresh.py::test_reuso_derruba_a_familia
- [x] 19 Decide onde o token mora no navegador e justifica — docs/DECISOES.md::ADR-01
- [x] 20 Planeja revogação e rotação de chaves (kid, JWKS) — SEC-15 · ATQ-06.5 · tests/test_tokens.py::test_chave_anterior_vale_retirada_nao

## E · Federação e MFA

- [x] 21 Integra login OIDC com Authorization Code + PKCE, state e nonce — SEC-21 · ATQ-08.4 · tests/test_oidc.py::test_fluxo_completo_e_pkce_confere
- [x] 22 Valida um ID token por completo — tests/test_oidc.py::test_id_token_para_outro_cliente
- [x] 23 Implementa TOTP com códigos de recuperação — SEC-19 · SEC-20 · ATQ-08.1 · ATQ-08.3 · tests/test_mfa.py::test_ativa_e_entrega_codigos_de_uso_unico
- [x] 24 Explica passkeys e sabe quando adotá-las — docs/DECISOES.md::ADR-03
- [x] 25 Decide construir ou comprar autenticação com critérios explícitos — docs/DECISOES.md::ADR-02

## F · Autorização

- [x] 26 Escolhe entre ACL, RBAC, ABAC e ReBAC para uma regra real — docs/DECISOES.md::ADR-04 · politicas/casos.json · tests/test_decisao.py::test_rbac_puro_erra_algum_caso
- [x] 27 Verifica permissões, não papéis, no código — SEC-27 · ATQ-11.1 · docs/PERMISSOES.md
- [x] 28 Bloqueia IDOR/BOLA com consulta escopada por dono ou tenant — SEC-30 · ATQ-12.1 · ATQ-12.5 · tests/test_objeto.py::test_lista_ja_vem_escopada
- [x] 29 Bloqueia mass assignment e filtra campos na resposta — SEC-31 · SEC-32 · ATQ-12.3 · ATQ-12.4 · ATQ-12.6 · tests/test_objeto.py::test_campo_fora_da_lista_400_e_nada_muda
- [x] 30 Expressa regra de domínio fora do middleware, com teste — SEC-25 · SEC-26 · tests/test_objeto.py::test_fora_do_plantao_403

## G · Operação

- [x] 31 Limita tentativas por IP e por conta em login, reset e MFA — SEC-22 · tests/test_limites.py::test_cinquenta_falhas_espalhadas_trancam_a_conta
- [x] 32 Registra eventos de segurança auditáveis, sem dado sensível — SEC-23 · tests/test_chaves.py::test_fora_do_escopo_e_403_com_evento_mesmo_dentro_do_papel
- [x] 33 Falha fechado: exceção no caminho de acesso nunca libera — SEC-24 · ATQ-06.6 · tests/test_limites.py::test_excecao_ao_identificar_vira_500_nunca_acesso
- [x] 34 Mantém segredos fora do código e audita dependências — SEC-33 · SEC-34 · varredura.py · scripts/portoes.sh::dependências · tests/test_segredos.py::test_sem_segredos_nao_sobe_e_diz_o_que_falta
- [x] 35 Roda no CI uma suíte de ataques papel × rota — SEC-28 · SEC-36 · .github/workflows/seguranca.yml · scripts/portoes.sh::matriz

## H · IA e máquinas

- [x] 36 Escreve prompt de auth com restrições e critério de pronto verificável — prompts/cap04.md::Done when · prompts/cap15.md::Done when
- [x] 37 Conduz revisão adversarial de código de acesso gerado por IA — SEC-37 · prompts/cap15.md::contexto novo
- [x] 38 Mantém invariantes de segurança no repositório que o agente lê — INVARIANTES.md::SEC-41 · AGENTS.md::MENOR escopo
- [x] 39 Emite chaves de API com prefixo, hash, escopo e expiração — SEC-38 · SEC-40 · ATQ-15.4 · ATQ-15.6 · tests/test_chaves.py::test_vencida_e_401
- [x] 40 Aplica mínimo privilégio a agentes e ferramentas de IA — SEC-39 · ATQ-15.1 · ATQ-15.2 · tests/test_chaves.py::test_mesma_instrucao_injetada_estreita_403_humano_barra_larga_altera
