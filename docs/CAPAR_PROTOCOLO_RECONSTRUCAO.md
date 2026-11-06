# TP02 / Capar — reconstrução do comportamento (trabalho de engenharia reversa)

Data: 2026-11-06. Branch de investigação: `capar-clone-protocolo`.

## Finalidade e limite

Produzir um aplicativo Android próprio, interoperável com o monitor TP02 legitimamente adquirido, usando comportamento observado no APK Capar 1.4.4 (SHA-256 `a5e6baa4fa3b158f94eb8549112e48f7ee455802aacf7978d7d117b13578f98d`) e nos testes nRF Connect realizados no dispositivo do usuário. **Não publicar nem redistribuir o APK do fornecedor, ativos de marca, credenciais ou código decompilado proprietário**. Não ignorar nem contornar validações de autorização/licença. O aplicativo Capar instalado é a versão 1.5.5; uma análise de 1.4.4 não atesta equivalência entre ambas.

## Evidência verificada no APK 1.4.4

| Recurso | Evidência |
| --- | --- |
| BLE GATT | `BluetoothHelper.startScanDevices`, `connectDevice`, `findCharacteristics`, `gattCallback` |
| Descoberta | `BluetoothHelper$bleScanCallback$1.onScanResult` lê `BluetoothDevice.getName()`, compara com `AppConfig.getDeviceList() -> DeviceInfo.getModel_code().trim()` e evita duplicados pelo endereço. O Capar também depende de um nome reconhecido; não assume automaticamente qualquer periférico sem nome. |
| Serviço BLE identificado anteriormente | `6e400001-b5a3-f393-e0a9-e50e24dcca9d`; escrita `...0002`, notificação `...0003`. É o Nordic UART Service; **não identifica sozinho o TP02**. |
| MTU | `BluetoothHelper$gattCallback$1.onMtuChanged` marca pronto e chama `sendWrappedData(0xF4)`, quando sucesso. |
| Pedido de licença | `BluetoothHelper.sendGetLicense` constrói `AA 55 F0 00` + nonce de 8 bytes. |
| Resposta de licença | `BluetoothHelper.handleReceivedData` reconhece `F0`, usa `decryptLicense` e publica evento de licença para fluxo de vinculação. |
| Vinculação | `ScanActivity$connectToDevice$1.onMtuChanged$lambda$1` marca dispositivo não vinculado; a coroutine de MTU chama `sendGetLicense`. `ScanActivity.onBus` aciona `bindDevice` com licença recebida; `ScanActivity$bindDevice$1.invokeSuspend` usa endpoint `/user/check-device-and-record` e trata sucessos/falhas. |
| Abertura da câmera | `BluetoothHelper.handleReceivedData` interpreta `COMMAND_OPEN_CAMERA` e extrai largura, altura, rotação e buffer; `CameraActivity` responde e começa o envio **depois da fase de vinculação**, quando autorizada. |
| Imagem | `CameraActivity.processPreviewViewFrame`, `sendProcessedImage` e `BluetoothHelper.sendLastImage` constroem JPEG; `sendData` particiona pelo tamanho de pacote derivado do MTU e `sendNextData` usa `WRITE_TYPE_NO_RESPONSE`. |
| Botões, observados no TP02 | Notificações `AA 55 0A 00` (+), `AA 55 0B 00` (-), `AA 55 06 00` (inverter câmera) e `AA 55 02 00` (foto/vídeo). |

## O que ainda **não** está comprovado

1. Modelo de descoberta do TP02 quando não anuncia nome: pode haver alteração de nome/endereçamento, mudança na versão do firmware, política de Bluetooth Android ou estado de vinculação. Não selecionar por RSSI/endereços desconhecidos.
2. Se a API de vinculação do fabricante aceita cliente independente, quais autorizações são necessárias e em que condições a licença do aparelho é válida. Não presumir acesso nem contornar controle de licença.
3. Regras exatas para abrir sessão: ordem/temporização dos comandos, parâmetros e respostas, tipo de confirmação.
4. Formato integral das imagens e mecanismo de pedidos de quadros, incluindo qualidade, orientação, buffers, fragmentação/controle de fluxo.
5. Se o Capar 1.5.5 instalado tem diferenças importantes em relação ao APK 1.4.4 disponível.
6. A falha de câmera 3 (`CameraDevice.StateCallback.ERROR_CAMERA_DISABLED`) e possíveis condições de corrida de câmera devem ser investigadas separadamente do BLE.

## Critérios obrigatórios antes de liberar novo APK

- Identificação inequívoca e automática do TP02 com prova do serviço/assinatura de protocolo e sem pedir ao usuário para selecionar dispositivos aleatórios.
- Conexão BLE e notificações estáveis com reconexão segura.
- Fluxo de licença/autorização **legítima** entendido e funcionando; distinguir falha de rede/licença de erro Bluetooth.
- OPEN_CAMERA recebido/respondido e JPEG real **visível na tela do dispositivo**, comprovado no hardware.
- Câmera e quatro botões físicos funcionais, registro de erros interpretáveis, sem travamentos.
- APK assinado com certificado persistente, CI com verificação dos passos e regressões.
- Testes reais no Samsung Android 16 e monitor TP02; compilar um APK não equivale a demonstrar compatibilidade.

## Regras de execução

- Pausar a geração de APKs de 'tentativa' até a engenharia reversa resolver as lacunas acima.
- Guardar toda conclusão com origem: classe/método do APK ou teste do hardware.
- Implementar um cliente limpo em projeto separado; não substituir o Capar nem desinstalá-lo.
- Não copiar binário/recursos proprietários para repositório público.
- Não depender de nome exato SelfieCom, RSSI alto ou MAC observado como prova de identidade.
- Testar cada etapa em isolamento, sem exigir que usuário pareie aparelhos não identificados.
- A nova versão somente será apresentada como funcional após exibição real comprovada no TP02.
