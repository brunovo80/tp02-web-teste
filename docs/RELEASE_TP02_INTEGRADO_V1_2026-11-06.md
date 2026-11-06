# TP02 Integrado v1.0 — release experimental (06/11/2026)

**APK:** https://github.com/brunovo80/tp02-web-teste/releases/download/tp02-integrado-v1-experimental/TP02-Integrado-v1.apk

**GitHub Actions:** https://github.com/brunovo80/tp02-web-teste/actions/runs/42228588359

**Artefato** `TP02-Integrado-v1.apk`, 35.247 bytes, SHA-256 `68c84dbb80a70e4d3d0d37475ea0a82d523c2a2e2d9c4006db6e0b2404fe7f6b`. Compilação Gradle Java 17 e upload de release concluídos.

## Integrado na mesma compilação

- Descoberta BLE sem escolha de dispositivos desconhecidos: nome `SelfieCom` ou **correlação de anúncios atuais do mesmo endereço** com fabricante 0x0642/modelo registrado e service data 0x3802. Endereço MAC histórico não é requisito.
- Conexão GATT ao dispositivo candidato, conferência dos UUIDs NUS WRITE/NOTIFY, ativação CCCD e negociação MTU.
- Envio de `AA 55 F4 00` após MTU, desafio F0 + nonce e interpretação local da resposta, **sem transmitir licença a serviços externos**.
- Câmera Android Camera2 e visualização real; guarda contra abertura simultânea.
- `OPEN_CAMERA` da própria unidade: ACK `AA 55 01 00` sem fingir que a autorização do fabricante foi confirmada. O pedido de quadro (`03`) inicia captura JPEG com dimensões informadas e envio por chunks MTU–3. Escrita usa callbacks com temporizador de recuperação para `WRITE_TYPE_NO_RESPONSE`.
- Eventos de volume (+/-), troca de câmera e botão físico de captura, com registro de diagnóstico. Opção **COPIAR DIAGNÓSTICO**.
- Dados/imagens locais, sem permissão de Internet. Aplicativo separado `br.com.tp02.integrado`, não substitui Capar.

## Verificações feitas

1. APK é ZIP íntegro: contém três DEX; nenhum arquivo corrompido.
2. GitHub Actions compilação/upload: **sucesso**.
3. Validação local de protocolo/estado: **43 verificações aprovadas**.
4. Validação local de descoberta com anúncios da captura do Samsung, nomes ausentes e bytes variáveis: **16 verificações aprovadas**.

## Limites (não ocultar)

- Nenhum teste real de conexão/espelhamento com o TP02 nesta versão; os testes automatizados não simulam o firmware.
- Uma resposta F0 do dispositivo não equivale a autorização de conta. **A API de vinculação do fabricante não está integrada**, e o aparelho pode recusar o fluxo se essa vinculação for obrigatória.
- A versão Capar inspecionada é 1.4.4; a instalada no Samsung é 1.5.5; o comportamento pode diferir.
- A assinatura do APK é debug do CI, sem chave persistente. Em compilações futuras, o usuário poderá precisar desinstalar o próprio TP02 Integrado para atualizar, até configurar assinatura protegida; o Capar não é afetado.
- O anúncio do monitor pode deixar de aparecer por desligamento automático/bateria/conexão com outro app. Manual TP02 indica desligamento após cerca de cinco minutos sem Capar.

## Um único ensaio de decisão no aparelho

- Fechar Capar e outros apps BLE.
- Ligar fisicamente o TP02 (tela acesa) e, **imediatamente**, abrir o Integrado v1 e tocar **PROCURAR TP02** uma vez; a busca dura até um minuto.
- Copiar diagnóstico pelo botão. Se a tela do aparelho mostrar a câmera, comprovar com foto. Se não, avaliar em qual etapa parou; não selecionar MAC aleatório nem reenviar imagens indiscriminadamente.
- Se nenhum anúncio compatível chegar ao app, confirmar publicidade atual do monitor via nRF Connect uma vez, sem escolher dispositivos desconhecidos. Sem novo build por tentativa/erro.
