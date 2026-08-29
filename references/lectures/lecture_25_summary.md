# Лекция 25 — выжимка

**Тема:** безопасность: zero trust, идентичность, секреты, supply chain,
STRIDE. Сырьё — старая «Лекция 23. Безопасность в РС и облаках»
(в `archive_2025/`), переработана: добавлены supply chain (SLSA,
sigstore, SBOM) и zero-trust-рамка. Файл —
`curriculum/Лекция_25_Безопасность_zero_trust_секреты_supply_chain.md`.

## Ключевые концепции (введены здесь)

- Периметр (castle-and-moat) умер: «внутри» размазано, атакующий всё
  равно попадает внутрь, внутри никто не проверяет → lateral movement.
  **Zero trust**: доверие по идентичности, не по адресу; три кита —
  проверяй каждого, least privilege, defense in depth.
- Идентичность: людям — OIDC/OAuth2 (+PKCE для мобильных/SPA;
  id_token vs access_token; токены не в localStorage); сервисам — mTLS
  (сертификат = идентичность), выпуск/ротация — сервис-меш (л. 20),
  поверх — авторизация «кто кого зовёт». AuthN ≠ AuthZ.
- Секреты: **base64 ≠ шифрование**, etcd по умолчанию — открытый текст;
  слои: encryption at rest (KMS), жёсткий RBAC на `get secrets`,
  SOPS/sealed secrets для GitOps-репо, динамические секреты с TTL
  (Vault). Не держать токены в env CI без нужды.
- Envelope encryption: данные ← data key ← CMK(KMS); EDK рядом с
  данными; ротация CMK без перешифровки данных; вызовы KMS — в аудит.
- NetworkPolicy: default-deny + явные разрешения пар; слой обороны в
  глубину, не замена идентичности; CNI может тихо не исполнять политики.
- Supply chain: зависимость исполняется с вашими правами; оборона:
  lockfile/`npm ci`/пауза обновлений/без postinstall → изолированная
  сборка + SLSA-провенанс → подпись cosign (sigstore, Rekor) + SBOM +
  admission «только подписанное». SBOM=«что внутри», SLSA=«как собрано»,
  подпись=«не подменили» — три разных вопроса.
- STRIDE-чек-лист (S/T/R/I/D/E) как метод, а не вдохновение.

## Слоты

- **Крючок:** червь Shai-Hulud в npm (15.09.2025): postinstall +
  TruffleHog, кража токенов, самопубликация заражённых пакетов,
  CrowdStrike среди жертв, алерт CISA, «2.0» в ноябре —
  `sources/Веб-находки_Лекция_25.md`.
- **Квиз-извлечение:** по лекции 24 (три сигнала, кардинальность,
  бюджет ошибок, burn rate).
- **PI-1:** два сервиса в приватном кластере; верный B (mTLS +
  авторизация как для внешнего); дистракторы: «сеть приватная» (миф
  периметра), «достаточно NetworkPolicy» (слой одинок), «не покидает
  ДЦ».
- **Живой сеанс:** STRIDE-таблица для обновления прошивки «СмартДома»
  (производитель → облако → Hub → Device): угроза+контроль на каждую
  букву; проверка — сценарий «гость получил доступ».
- **Мост:** чек-лист безопасности PR текущей лабы 8 (секреты в истории,
  npm ci, права токена, пароль Grafana).

## Примеры «СмартДома»

Cloud API ↔ Rule engine (PI), NetworkPolicy allow-api-to-rules,
K8s Secret db-creds (base64-миф), подписанная прошивка, STRIDE «дым →
доступ гостя».

## Студенты знают после

Термины: zero trust, least privilege, defense in depth, lateral
movement, OIDC/PKCE, mTLS, encryption at rest, envelope encryption
(KMS/CMK/EDK), SOPS/sealed secrets, default-deny, supply chain,
lockfile, SBOM, SLSA/провенанс, sigstore/cosign/Rekor, STRIDE,
blameless-аудит. НЕ знают ещё: нагрузочное тестирование и автоскейлинг
(л. 26), FinOps (л. 27), DR (л. 28).

## Презентация

`curriculum/Презентация_25_Безопасность_zero_trust_секреты_supply_chain.pptx`,
23 слайда, палитра «Океан» (`scripts/presentations/build_pres25.js`).
PI — слайды 7–11 (A, D, C → B с бейджем); пауза — слайд 15; маркеры 🖥
в лекции соответствуют колоде.
