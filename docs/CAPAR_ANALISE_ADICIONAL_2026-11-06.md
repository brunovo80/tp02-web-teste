# TP02 / Capar 1.4.4 — segunda etapa de engenharia reversa

**Execução:** 6/11/2026. **APK analisado:** `cn.vectorflow.capar_V 1.4.4.apk` (~30 MB, três DEX). **SHA-256:** `a5e6baa4fa3b158f94eb8549112e48f7ee455802aacf7978d7d117b13578f98d`.

## Descobertas verificadas no bytecode

- `CameraActivity.sendOpenCameraResult` usa `BluetoothHelper.sendWrappedData(0x01)`; a função encapsula mensagens como `AA 55 <comando> 00`. Logo, a resposta **correta observada no 1.4.4 é `AA 55 01 00`**. Nosso protótipo respondia erroneamente `AA 55 01 01`.
- `BluetoothHelper.gattCallback.onMtuChanged` envia `AA 55 F4 00` quando a negociação da MTU termina com sucesso.
- `ScanActivity.connectToDevice.onMtuChanged` coloca o aparelho não vinculado no caminho de descoberta da licença; uma coroutine espera **1.000 ms**, chama `sendGetLicense` e aguarda **10.000 ms** antes de verificar `isBound()` e desconectar em caso de timeout. Esse comportamento se refere à versão 1.4.4 e não prova igual temporização na 1.5.5.
- `sendGetLicense` forma um pacote de **12 bytes**: `AA 55 F0 00` seguido de **8 bytes aleatórios** criados com `SecureRandom`.
- `handleReceivedData` reconhece `F0`, extrai os bytes após os primeiros quatro e chama `decryptLicense`.
- `decryptLicense` aplica **XOR com repetição dos oito bytes do nonce** a cada byte recebido e interpreta o resultado como UTF-8. Isso é somente codificação da resposta do dispositivo — não substitui a vinculação ou autorização da conta.
- `ScanActivity.bindDevice` usa **POST `/user/check-device-and-record`** com os campos `device_id` (Android ID), `app_type` (`CAPAR`), `license_key`, `model` e `mac_address`. A chamada depende da infraestrutura e das condições do fabricante. Não foi realizada chamada à API nem tentativa de contornar validação.
- `BluetoothHelper.handleReceivedData` reconhece o controle `F7` e lê um inteiro de 16 bits little-endian após os três primeiros bytes. A abertura da câmera recebe largura, altura, rotação e capacidade de buffer.
- `CameraActivity.handleBluetoothData` usa uma tabela de comandos que inclui pedido de envio de quadro (código `03`); `sendProcessedImage` consome uma fila de JPEGs preparados e não envia uma sequência indiscriminada de quadros.
- O `BluetoothHelper.sendData` fragmenta o fluxo em blocos de **MTU – 3**. `sendNextData` usa `WRITE_TYPE_NO_RESPONSE`; o avanço de blocos depende dos callbacks de escrita da aplicação. Um timer fixo não é substituto comprovado.
- A busca original compara o `BluetoothDevice.getName()` com modelos de `AppConfig.getDeviceList()`. O BLE do app antigo não constitui descoberta confiável de aparelho **sem nome**; o serviço NUS sozinho tampouco prova identidade do TP02.

## Desenvolvimento efetivamente realizado

1. Criados os arquivos Android-independentes `Tp02Wire.java` e `Tp02Session.java` em `cleanroom/` na branch `capar-clone-protocolo`.
2. Corrigido o ACK da câmera e codificados o controle F4, o pedido F0, a decodificação XOR, os parâmetros de abertura, o pacote F7 e a fragmentação MTU–3.
3. Estado de sessão com bloqueio de `OPEN_CAMERA` antes de o provedor autorizado confirmar o vínculo. Dados de licença não são logados.
4. Testes de protocolo e autorização executados localmente (30 verificações num protótipo de referência) e o código versionado validado pelo GitHub Actions.

## Impedimentos e critérios restantes

- **Licença:** falta confirmar um método autorizado para um cliente próprio obter e manter o vínculo com a infraestrutura Capar. Não forjar identidade/assinatura nem ignorar a API.
- **Descoberta:** não foi comprovada a identificação automática do monitor nas condições atuais; não escolher MACs sem nome com base apenas em RSSI.
- **Transmissão real:** a implementação atual é um módulo de protocolo com testes, não um aplicativo completo testado em hardware.
- **Regressão:** preservar Capar instalado e o APK experimental anterior; nunca declarar espelhamento funcional sem imagem demonstrada no monitor.