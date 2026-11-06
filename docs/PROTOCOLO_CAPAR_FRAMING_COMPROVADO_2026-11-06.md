# TP02 / Capar 1.4.4 — causa do bloqueio no início do envio (06/11/2026)

## Inspeção direta do DEX — descoberta central

**Artefato original examinado:** `cn.vectorflow.capar_V 1.4.4.apk` (SHA-256 `a5e6baa4fa3b158f94eb8549112e48f7ee455802aacf7978d7d117b13578f98d`). Três DEX, em particular `classes3.dex`, com inspeção de métodos e opcodes Dalvik.

### Caminho comprovado no bytecode

- `BluetoothHelper.getPacketSize` retorna `mtu - 3`.
- `BluetoothHelper.sendData` calcula **`maxData = getPacketSize() - 1 = mtu - 4`** para cada fragmento; aloca **`maxDataUsado + 1`** e acrescenta um **último byte `01` se restam fragmentos ou `00` no fragmento final**.
- `BluetoothHelper.sendWrappedData` monta `AA 55 <comando> 00` e **envia pelo próprio `sendData`**. Portanto, OPEN_CAMERA ACK como **pacote BLE** é `AA 55 01 00 00`; a string `AA 55 01 00` é só a mensagem lógica, sem o delimitador físico.
- `BluetoothHelper.sendGetLicense` compõe `AA 55 F0 00 + nonce de 8 bytes` e também envia por `sendData`: em um só pacote ATT com 13 bytes, incluindo `00` final.
- `BluetoothHelper.handleReceivedData` trata resposta F0 especialmente; para as outras notificações separa **último byte 01/00**, acumula `fracData` enquanto for 01, remove o marcador final 00 e só então interpreta `AA 55 ...`.
- `CameraActivity.handleBluetoothData` trata comando `03`: se o cache JPEG está vazio, marca `pendingSendImage`; senão, chama `sendProcessedImage`. O cache é abastecido por um timer de prévia, `processPreviewViewFrame` e `processSurfaceTextureFrame`. A transmissão de JPEG é feita por `BluetoothHelper.sendData`, com **mesmo marcador de fragmentação**.
- `CameraActivity.sendOpenCameraResult` utiliza `sendWrappedData(01)`.

### Erro objetivo no nosso TP02 Integrado 1.0

A versão 1.0 enviou **`AA 55 01 00` diretamente à característica GATT**, sem o terminador. O dispositivo pediu `OPEN_CAMERA` e não enviou `REQUEST_FRAME (03)`; permaneceu no QR Code. **A ausência de marcador é uma causa compatível e plausível, mas o firmware físico ainda não confirmou que este era o único bloqueio.**

Também houve conexões GATT duplicadas e tentativa de reativar NOTIFY (retorno local Android `201`), corrigidas no código v1.1. Uma ligação Bluetooth bem-sucedida não é espelhamento.

## Correção implementada na branch `capar-clone-protocolo`

- `cleanroom/src/br/com/tp02/interop/Tp02Framing.java`: serializador e remontador, com limites de tamanho.
- `cleanroom/tests/Tp02FramingTest.java`: **1.328 testes/asserts** de ida e volta executados localmente usando Java, também no CI integrado.
- `scripts/fix_framing_v12.py`: incorpora o enquadramento nas mensagens `F4`, `F0`, `OPEN_CAMERA`, demais controles e nos fragmentos JPEG, além de aplicar desmontagem/recomposição das notificações recebidas.
- `.github/workflows/build-tp02-v12.yml`: começa do projeto canônico e aplica sucessivamente patches v0.3, v0.4, Integrado 1.0, GATT 1.1 e framing 1.2. Só publica APK se compilar e passar nos testes.

### Tramas esperadas

| Mensagem lógica | Transmissão em uma única escrita GATT |
|---|---|
| Abertura confirmada | `AA 55 01 00 00` |
| Controle pós-MTU | `AA 55 F4 00 00` |
| Pedido licença F0 | `AA 55 F0 00 <nonce 8 bytes> 00` |
| JPEG, MTU=498 | Até 494 bytes de JPEG + `01` até o penúltimo pacote; último bloco + `00` |

Com JPEG de 15.360 bytes e MTU 498, são 32 escritas GATT, não 32 blocos crus sem delimitador. O código não afirma recebimento ou exibição no monitor apenas porque o Android aceitou uma escrita.

## Critério de verificação com hardware

O próximo diagnóstico deve observar: 1) uma conexão única + NOTIFY, 2) MTU negociado, 3) abertura recebida do TP02, 4) comando de resposta com **5 bytes**, 5) novo comando `03` do monitor, 6) JPEG enviado com último byte `01/00`, 7) a **imagem real substitui o QR Code**.

Sem o comando `03` mesmo com framing correto, investigar estado de autorização/vinculação, ordem e temporização das escritas, e diferenças 1.4.4 versus Google Play 1.5.5. Não presumir sucesso sem imagem.
