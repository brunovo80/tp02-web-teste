# Pesquisa de versões Capar / TP02 — distribuição regional, regressões e testes (06/11/2026)

## Decisão

**Não gerar nem instalar APK experimental adicional sem antes confirmar a origem/canal do Capar instalado.** A hipótese prioritária agora é uma distribuição regional (China continental versus internacional), reforçada por evidência oficial. Não está comprovado que a versão chinesa seja a causa do erro, nem que um downgrade resolverá.

## 1. Descoberta central: o próprio desenvolvedor distingue duas distribuições

**Fonte original:** https://apps.vectorflow.cn/capar?lang=cn

Orientação (tradução de conteúdo visível/indexado): usuários na China continental devem baixar **中国大陆版** (edição para China continental); todos os outros devem baixar **国际版** (edição internacional). A página indica Google Play para a internacional e Xiaomi/Huawei/Oppo/Vivo/应用宝 para a chinesa.

Esta orientação é mais forte que inferir a edição somente pelo número da versão. Não foi possível examinar os URLs finais de download nesta sessão; não presumir que ambas usam certificados, backend ou protocolo diferentes sem verificar.

## 2. Versões Android verificadas em canais diferentes

| Canal | Versão | Data/nota | Fonte |
|---|---|---|---|
| Xiaomi **oficial** (China) | **1.5.2** | atualização 27 set 2026; pacote `cn.vectorflow.capar`, editor 深圳市矢量律动科技有限公司 | https://app.mi.com/details?id=cn.vectorflow.capar |
| Google Play (internacional) | **1.4.9** em índices de setembro/outubro | Changelog genérico "Fix known bugs"; pacote `cn.vectorflow.capar` | https://play.google.com/store/apps/details?id=cn.vectorflow.capar ; https://chrome-stats.com/d/cn.vectorflow.capar |
| APKPure (arquivo, não fonte primária) | 1.3.3, 1.4.3, 1.4.4, 1.4.7, 1.4.9 | datas listadas entre jan-set/2026 | https://apkpure.net/capar/cn.vectorflow.capar |
| iOS App Store **não equiparar versão à Android** | 1.5.5 e 1.5.6 | publicadas no histórico de out/2026, iOS 1.5.0 menciona estabilidade da imagem; não prova Android | https://apps.apple.com/tr/app/capar/id6756035401?platform=ipad |

**Usuário relatou Capar Android 1.5.5 instalado, mas a origem dessa instalação não foi confirmada.** Versão Android 1.5.x é plausível porque Xiaomi distribuiu 1.5.2, mas não foi localizada listagem oficial de APK Android 1.5.5. Não inventar fonte nem link de download.

## 3. Segurança e identidade do APK analisado

O APK antigo que **já temos**: `cn.vectorflow.capar_V 1.4.4.apk`; 30.594.489 bytes, SHA-256 `a5e6baa4fa3b158f94eb8549112e48f7ee455802aacf7978d7d117b13578f98d`.

A extração DEX desta sessão encontrou referências embutidas a:
- `https://capar.vectorflow.cn/docs/privacy.html?lang=cn`
- `https://capar.vectorflow.cn/docs/privacy.html?lang=en`
- `https://capar.vectorflow.cn/docs/tos.html?lang=cn` e `?lang=en`.

Já a ficha Google Play/indexador internacional utiliza política de privacidade `https://capar.oversea.vectorflow.cn/docs/privacy.html?lang=en`. Isso **sugere** diferença regional de configuração, mas links de política no APK não provam o backend de produção nem a edição do binário. Observar essa diferença somente como pista.

O APK fornecido pelo usuário foi usado para análise, sem instalá-lo como downgrade. É diferente do pacote XAPK de 46.8 MB anunciado pelo APKPure (contêiner de múltiplos APKs); comparação dos SHA-256 desses **pacotes diferentes** não permite afirmar adulteração. Verificar certificado de assinatura real, base APK e splits antes de qualquer recomendação de instalação.

**Jamais instruir a ignorar o alerta de "link malicioso" ou desativar Play Protect.** Preferir fontes oficiais (Google Play / fabricante); perguntar ao fabricante por instalador assinado de versão internacional antiga e hash/certificado se necessário. O downgrade Android pode exigir desinstalar e apagar dados/vínculo; preservar instalação atual até ter backup e comparação.

## 4. Manual e avaliações

- Manual TP02: https://manuals.plus/keithy/tp02-magnetic-selfie-display-manual — QR Code do aparelho é primariamente **link de download do aplicativo**, não QR de autenticação de imagem. Conexão usa BLE `SelfieCom`; desligamento automático após ~5min sem conexão, e controles 0.5x/1x/1.5x, troca de câmera, proporção, espelhamento.
- A loja iOS recebeu relato de `validating error` ao conectar **outro modelo, T30**; é indício de falha no caminho de validação, não prova de que TP02/Android falhem pelo mesmo motivo. https://apps.apple.com/ph/app/capar/id6756035401
- Changelog iOS v1.3.4 registra correção de falha na exibição relacionada à solicitação inicial de permissões; v1.5.0 registra melhora de estabilidade de transmissão no iOS 26. Não extrapolar diretamente para Android 16.
- As buscas em fóruns/Reddit/Google não encontraram demonstração **reprodutível** de que Capar 1.3.3, 1.4.3 ou 1.4.4 exibam câmera no **TP02 + Samsung Android 16**. Nenhuma afirmação de solução garantida.

## 5. Hardware: já sabemos o que funciona

Log TP02 Integrado v1.0 de 06/11 10:55 BRT:
- TP02 identificado por nome/assinatura BLE dinâmica;
- GATT conectou, NOTIFY inicialmente ativo, MTU 498, F4;
- TP02 emitiu comando real `AA 55 01 A0 00 C0 00 00 00 3C 00 00 00` (pedido de 160x192 pixels);
- Android aceitou enfileiramento de ACK `AA 55 01 00` (não é confirmação do firmware);
- Nenhum pedido de quadro 0x03 nem JPEG efetivamente transmitido registrado;
- Segunda conexão/CCCD duplicada e erro 201 na configuração; correção v1.1 compilou, mas **não testada** no hardware e não prova streaming.
- Tela permaneceu QR Code. O QR não é autenticação; é a imagem de inicialização/download do firmware até transição.

Portanto, o hardware comunica-se via Bluetooth. A falha restante é transição de estado/negociação e fluxo de primeiro quadro, possivelmente autorização de backend e/ou regressão do app oficial. **Não focar novamente no filtro BLE**.

## 6. Sequência de trabalho, por evidências e sem perda de dados

1. **Confirmar edição/origem da 1.5.5 instalada** (Google Play, QR/aplicação do fabricante ou outro canal). Não perguntar ao usuário número da versão de novo, pois já forneceu. Confirmar sem desinstalar e capturar informação de instalador/rota de privacidade se disponível.
2. Comparar com a internacional oficial do **Google Play** e com a chinesa **Xiaomi 1.5.2** por assinatura, hashes (APK base e split), serviços de backend e chamadas de vinculação. Não usar download inseguro.
3. Se realmente edição China fora da China, planejar teste da internacional sem destruir a conta/vínculo: preservar dados, checar assinatura e possibilidade de instalação. Emulador é inadequado para BLE real; equipamento Android secundário pode ajudar, se disponível.
4. Se internacional também falhar, adquirir a versão oficial instalada para comparação estática com 1.4.4 e captura HCI do **Capar oficial durante a tentativa**; identificar exatamente quando F0, vínculo, OPEN_CAMERA, ACK e solicitação do primeiro quadro divergirem.
5. Só editar o APK próprio depois de localizar a divergência, com uma sessão GATT por vez e escrita BLE sequenciada; exigir demonstração de JPEG exibido na tela.
6. Contatar suporte do desenvolvedor `google@vectorflow.cn` (publicado no Google Play) sobre canal internacional, versão compatível com Samsung Android 16 e TP02, erro de validação e disponibilização segura de builds anteriores. Não alegar já ter contatado.

## Critério de sucesso

No monitor físico TP02, imagem da câmera em tempo real substituindo QR Code. Build de APK, reconhecimento BLE e MTU não são prova de funcionamento. Não fazer versão nova de tentativa e erro só com outro filtro.
