# TP02 — Teste orientado v0.3 (06/11/2026)

## Objetivo único

Separar os três bloqueios: (1) descoberta do TP02 no Samsung Android 16, (2) conexão GATT/NOTIFY/MTU e (3) leitura de resposta F0 de licença. Este APK **não** é espelhamento funcional e não substitui o Capar.

## Implementação

- Android applicationId `br.com.tp02.interopdiagnostico`; pode coexistir com o Capar e com o TP02 0.2.
- Corrigida a permissão de scan: sem `neverForLocation`, com solicitação explícita de localização precisa para não filtrar resultados BLE. Não usa Internet nem transmite localização.
- Removida a lista manual de MACs. Conexão automática somente com o nome `SelfieCom` ou com o endereço registrado nos testes anteriores `41:42:14:D8:45:7F`. **Isso ainda pode falhar com MAC rotativo/anúncio sem nome; não é identificação universal.**
- Verifica UUIDs GATT, ativa NOTIFY, negocia MTU, envia `AA 55 F4 00` e, após 1 segundo, `AA 55 F0 00` + nonce de 8 bytes.
- Resposta F0 interpretada localmente; conteúdo sensível oculto.
- Corrigido OPEN_CAMERA ACK para `AA 55 01 00`; envio da câmera é **bloqueado** sem prova de autorização legítima com o servidor do fabricante.
- Incorpora arquivos clean-room `Tp02Wire`, `Tp02Session`, `Tp02TxQueue`; script de montagem `scripts/build_v03.py` é determinístico.
- Build GitHub Actions 42214465811 aprovado. Artefato `TP02-Identificacao-Licenca-v03`.

## Teste no aparelho — uma única execução

1. Fechar Capar e nRF Connect, mantendo o TP02 ligado e próximo.
2. Instalar o APK v0.3, abrir, permitir Câmera, Bluetooth/dispositivos próximos **e localização precisa**. Localização é exigida para o scan sem a flag filtrante; o app não tem permissão de Internet.
3. Tocar **PROCURAR TP02 (BLE)** uma vez.
4. Registrar o texto final do log. Se não encontra, não selecionar aparelhos desconhecidos nem repetir tentativas idênticas.

## Resultados possíveis e próximo passo

- `TP02 não identificado`: pesquisar publicidade/anúncios BLE e identidade observável. Não é licença nem câmera.
- `BLE conectado` + `MTU`: descoberta concluída; verificar resposta F0.
- `Resposta F0 válida decodificada`: BLE e licença local provados; autorização de conta/fabricante ainda pendente.
- `Pedido de câmera recebido, mas ainda sem autorização`: autorização legítima é bloqueio. Precisamos de suporte/SDK/protocolo autorizado; não contornar licença.
- Nenhum resultado confirma espelhamento completo. Só confirmar quando imagem real aparecer na telinha.

Não executar testes aleatórios com MACs desconhecidos, nem solicitar credenciais Capar em logs.
