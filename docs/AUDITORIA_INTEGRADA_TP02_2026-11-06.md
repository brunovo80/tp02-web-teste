# TP02 / Capar — auditoria técnica integrada antes do próximo APK

**Data:** 6 de novembro de 2026  
**Conclusão:** **NÃO LIBERAR OUTRO APK COMO FUNCIONAL** antes de fechar a descoberta BLE, a autorização do aparelho e o teste de imagem no monitor.  
**Escopo:** arquivo Capar v1.4.4, relatórios Android/Bluetooth do Samsung, manual TP02, versões experimentais 0.1 a 0.4, código reconstruído na branch `capar-clone-protocolo` e registros do GitHub Actions.

## 1. O que foi realmente verificado

| Fonte | Evidência reproduzível | Limite |
| --- | --- | --- |
| APK Capar 1.4.4 (30.594.489 bytes; SHA-256 `a5e6baa4fa3b158f94eb8549112e48f7ee455802aacf7978d7d117b13578f98d`) | Três DEX; `BluetoothHelper`, `ScanActivity`, `CameraActivity`, geração de JPEG, transferência BLE GATT, sequência F4/F0, tratamento de `OPEN_CAMERA` | APK instalado pelo usuário é Capar **1.5.5**; versão atual não foi descompilada nem comparada. Nenhuma garantia de compatibilidade integral |
| Bugreport Bluetooth do Samsung enviado em 05/11 | No fluxo de *Extended Advertising Reports*, há **1.077 registros**, **48 endereços** e **70 anúncios da unidade identificada como SelfieCom**: **35** dados de fabricante e **35** respostas com nome; sempre mesmo endereço naquela captura | Retrata apenas a captura anterior; não informa se o monitor estava transmitindo durante o teste v0.4 |
| Tela da versão 0.4 às 09h47 | Android concedeu permissões, câmera abriu, scan BLE finalizou com **37 dispositivos próximos** e **nenhuma assinatura TP02 recebida** | Não revela estado ligado/desligado, anúncio atual, ocupação por outro app ou tráfego HCI contemporâneo |
| Manual TP02 | Orienta ligar pelo interruptor físico, usar o aplicativo Capar, reconhece `SelfieCom` e informa desligamento automático após **5 min sem conexão com o app**; proteção por baixa tensão | Comportamento de energia pode variar com firmware/bateria; hipótese de desligamento não é diagnóstico confirmado |
| GitHub Actions | Compilação e testes Java de protocolo passaram | Não executam BLE, dispositivo físico, API de vinculação ou imagem real |

**Fonte manual:** https://manuals.plus/keithy/tp02-magnetic-selfie-display-manual  
**Fonte Android `ScanRecord`:** https://developer.android.com/reference/android/bluetooth/le/ScanRecord

## 2. Como o Capar 1.4.4 realmente procura o aparelho

A descompilação estática do DEX recuperou a rotina `BluetoothHelper.startScanDevices`: ela configura `ScanSettings.SCAN_MODE_LOW_LATENCY` (constante 2), inicia `BluetoothLeScanner.startScan` e executa a rotina de resultados `BluetoothHelper$bleScanCallback$1.onScanResult`.

Na callback do Capar, o aplicativo obtém **`BluetoothDevice.getName()`** e compara o nome com `DeviceInfo.getModel_code().trim()` de `AppConfig.getDeviceList()`. Essa lista é carregada por rota de rede `/device/model/list?device_type=selfie_stick`. Ele mantém candidatos descobertos e elimina duplicados por endereço. Também tem tratamento de scan sem resultado (~5 segundos), sugerindo reiniciar Bluetooth; **não é um mecanismo de descoberta mágico por firmware**. Nome de aparelho pode não estar presente em todos os eventos de advertisement.

**Problema do nosso protótipo:**

- 0.1: só reconhecia o nome literal `SelfieCom`.
- 0.2: mostrava **dezenas de aparelhos anônimos para o usuário escolher**, transferindo ao usuário o que o app deveria resolver.
- 0.3: eliminou a lista, mas manteve correspondência por nome ou endereço registrado em uma única sessão.
- 0.4: adicionou correspondência com os **bytes inteiros e exatos** de um anúncio do dia anterior (dados de fabricante e dados de serviço). A verificação unitária **considerava esperado que mudar um byte resultasse em rejeição**. Se o fabricante alterar parte do payload, surgem falsos negativos.

No registro HCI anterior, os 70 anúncios do monitor eram de dois formatos separados: Manufacturer Specific Data de companhia `0x0642` (35 ocorrências) e Scan Response com nome `SelfieCom`/service data UUID `0x3802` (35 ocorrências). A resposta de scan também continha bytes específicos daquela unidade. **Não é correto tratá-los todos como constantes universais do modelo.** O serviço GATT NUS/"Nordic UART" não é, sozinho, identidade exclusiva de TP02.

### Critério corrigido de descoberta (para validar, ainda não entregue como APK)

1. Capturar e correlacionar anúncios **por dispositivo**; processar `ScanRecord` como campos AD (tipo/comprimento), preservando o histórico de evidências ao longo dos resultados.
2. Aceitar como forte candidato nome `SelfieCom` **ou** combinação corroborada de empresa `0x0642` + marcador do modelo e service data `0x3802` no mesmo periférico; **não fixar o MAC ou o restante dos bytes variáveis**.
3. Nunca selecionar por RSSI, nem permitir que o usuário escolha MACs desconhecidos.
4. Depois do candidato, fazer conexão GATT restrita e verificar serviço/characterísticas; **não enviar pacotes de câmera/imagem nem tratar NUS como prova de autorização**.
5. Distinguir no diagnóstico: nenhum anúncio compatível recebido; candidato reconhecido; conexão falhou; GATT incompatível; notificação desativada; licença pendente; vinculação negada.

**Código de engenharia proposto:** `cleanroom/src/br/com/tp02/interop/Tp02DiscoveryV2.java` (branch investigativa, **não integrado ao APK nem validado no hardware**).

## 3. Energia do monitor: hipótese omitida nas quatro versões

O manual descreve desligamento automático depois de 5 minutos sem conexão ao Capar e necessidade de energia suficiente. Assim, 37 periféricos detectados **não** significam que o TP02 estava anunciando. O scan pode estar tecnicamente correto e, mesmo assim, jamais vê-lo.

**Teste físico indispensável, uma única vez e sem instalar outro APK:** iniciar o TP02 pelo interruptor, verificar a tela acesa e, **imediatamente**, fazer scan no nRF Connect (que já foi capaz de identificar o TP02 anteriormente). Se `SelfieCom` aparecer no nRF, mas não no app com a busca iniciada nas mesmas condições, há falha do nosso lado. Se não aparecer no nRF, a próxima investigação deve mirar estado de energia/anúncio, não outra revisão de filtro de aplicativo. Um teste isolado não prova mau funcionamento de hardware; ele separa causas.

## 4. A sequência BLE e a licença — o que temos e o que falta

Fluxo conhecido da versão 1.4.4:

1. Descobrir o candidato -> conectar via BLE GATT e achar serviço `6e400001-b5a3-f393-e0a9-e50e24dcca9d`, escrita `...0002`, notificação `...0003`.
2. Inscrever notificações com CCCD e negociar MTU. Após `onMtuChanged`, `BluetoothHelper` envia `AA 55 F4 00`.
3. Quando o dispositivo não está vinculado, o Capar solicita sua licença com `AA 55 F0 00` + 8 bytes aleatórios; a resposta é decodificada por XOR com o nonce.
4. **A posse da resposta F0 não é autorização**. O Capar usa a rota de rede `/user/check-device-and-record` para validação/vinculação. Precisamos de forma legítima e autorizada de executar esse passo; sem ela, o fluxo independente não está completo.
5. Só depois vem a abertura da câmera. A resposta do Capar a `OPEN_CAMERA` é `AA 55 01 00`, diferente da resposta errada `AA 55 01 01` dos primeiros protótipos.
6. O TP02 pede quadros (comando 03); o Capar gera JPEG enquadrado/rotacionado, coloca em fila e transmite em blocos de tamanho baseado no MTU, acompanhando callbacks BLE de escrita.

**Erros concretos nas implementações feitas:**

- Protocolo de licença `Tp02Session` foi integrado parcialmente, mas o aplicativo **não contém integração de vinculação autorizada** para avançar ao estado `AUTHORIZED`. O método de liberação do fluxo não é acionado: enviar foto fica deliberadamente bloqueado.
- O código Java testado isoladamente da fila de JPEG não equivale a integração real na versão 0.4. A versão instalada não demonstrou sequer abrir a sessão, muito menos mostrar imagem.
- Teste unitário de parser, compilação e upload de APK **não** equivalem a validar a câmera, autorização, botões ou imagem no monitor.

## 5. Câmera e instalador Android

O Capar utiliza rotinas de câmera/lifecycle e tratamento de falhas específicas; nosso aplicativo experimental usa diretamente `Camera2`. O evento `CameraDevice.StateCallback.ERROR_CAMERA_DISABLED` (erro 3) merece investigação separada, inclusive proteção contra concorrência e ciclos de abrir/fechar a câmera. A captura 09h47 mostra a câmera funcional, mas isso não torna a gestão de câmera robusta.

Compilações `debug` do GitHub foram assinadas com certificados de teste não persistentes e os `applicationId`/nomes foram alterados entre versões, tornando a atualização inconsistente. Uma futura versão entregue ao usuário precisa ter identidade estável, chave de assinatura protegida e testes de atualização. **Não enviar mais artefatos de produção por assinatura aleatória.**

## 6. O que ainda impede um único APK "igual ao Capar"

O APK permite inspecionar boa parte do código e do fluxo, mas **não transfere** contas, vínculos de licença no servidor, backend, assinatura digital do fabricante, firmware nem testes com hardware. Tampouco temos o código da versão Capar 1.5.5 que está atualmente instalada no celular. Um Ctrl+C/Ctrl+V do pacote binário resultaria em cópia do app original, não um aplicativo próprio corrigido; recompilá-lo e re-assiná-lo não reproduz por si só o vínculo do servidor.

A abordagem viável é **reimplementar o comportamento comprovado para interoperabilidade, usando nossa própria identidade/UX**, sem distribuir código/ativos proprietários e sem ignorar mecanismos legítimos de autorização.

## 7. Critérios obrigatórios para voltar a compilar

| Portão | Critério verificável | Estado em 06/11 |
| --- | --- | --- |
| 1 — publicações BLE | Saber se o TP02 está efetivamente anunciando **nas condições atuais** (scan independente logo após ligar) | **Pendente de teste físico** |
| 2 — reconhecimento | Reproduzir eventos de anúncio e scan response, nome ausente e bytes variáveis; sem seleção manual de MAC ou falso positivo | **Modelo novo proposto, não integrado/validado** |
| 3 — conexão | Descobrir serviço e características, CCCD/NOTIFY e MTU no hardware real | **Historicamente comprovado via nRF; não comprovado no app** |
| 4 — autorização | Concluir de forma legítima o vínculo exigido pelo servidor do fabricante, ou obter documentação/SDK autorizada | **Não resolvido** |
| 5 — imagem | OPEN_CAMERA correto; quadro JPEG real solicitado, enviado em ordem e **exibido no TP02** | **Não comprovado** |
| 6 — robustez | Botões, câmera, desconexão, recuperação, atualização por assinatura estável | **Pendente** |
| 7 — regressão | Testes automáticos de pacote/protocolo **e** ensaio no aparelho/Android 16, sem perda de funções existentes | **Parcial** |

## 8. Ação recomendada e decisão

**Congelar lançamentos até sair deste diagnóstico.** Não há justificativa para uma quinta instalação só para reproduzir outro scan. O único ensaio que o código/decompilação não pode substituir é observar o TP02 fisicamente anunciando **agora**, preferencialmente com o scanner independente já instalado. Depois de identificar a camada correta, reconstruir de ponta a ponta a versão independente e fazer teste de aceitação completo, incluindo a autorização legítima. Se o fabricante não permitir vinculação por cliente independente, não afirmar que o espelhamento está disponível.

**Regra de comunicação:** nada de "funcionou" baseado em CI verde, nada de porcentagem de chance sem evidência, nada de indicar que o assistente continuará trabalhando em segundo plano depois da conversa.