from pathlib import Path

root=Path("native-tp02")
ble=root/"app/src/main/java/br/com/tp02/prototipo/Tp02Ble.java"
ui=root/"app/src/main/java/br/com/tp02/prototipo/MainActivity.java"
gradle=root/"app/build.gradle"
manifest=root/"app/src/main/AndroidManifest.xml"
matcher=Path("cleanroom/src/br/com/tp02/interop/Tp02Advertisement.java")
dest=root/"app/src/main/java/br/com/tp02/interop/Tp02Advertisement.java"

def edit(file,old,new):
    text=file.read_text("utf-8")
    count=text.count(old)
    if count!=1:raise RuntimeError(f"{file}: wanted one occurrence, got {count}: {old[:90]!r}")
    file.write_text(text.replace(old,new),"utf-8")

dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_bytes(matcher.read_bytes())
edit(ble,"import br.com.tp02.interop.Tp02TxQueue;",
     "import br.com.tp02.interop.Tp02TxQueue;\nimport br.com.tp02.interop.Tp02Advertisement;")
edit(ble,
     'if((n!=null && n.trim().equalsIgnoreCase("SelfieCom")) || addr.equalsIgnoreCase(VERIFIED_MAC)){',
     '''byte[] observed=result.getScanRecord()==null?null:result.getScanRecord().getBytes();
            Tp02Advertisement.Evidence evidence=Tp02Advertisement.classify(observed,n);
            if(evidence!=Tp02Advertisement.Evidence.NONE || addr.equalsIgnoreCase(VERIFIED_MAC)){
                events.info("Identidade TP02: "+evidence+" (anúncio/identidade capturados no Samsung).");''')
edit(ble,
     'events.info("BLE detectado: "+label+" | "+addr+" | RSSI "+result.getRssi());',
     '// Demais dispositivos são descartados do diagnóstico visível.')
edit(ble,
     'events.info("TP02 não identificado. Sem conexão com dispositivos sem identidade comprovada.");',
     'events.info("Nenhuma assinatura do TP02 recebida. Dispositivos próximos: "+discovered.size()+". Sem tentativa em periféricos desconhecidos.");')
edit(gradle,"applicationId 'br.com.tp02.interopdiagnostico'",
     "applicationId 'br.com.tp02.reconhecimentov04'")
edit(gradle,"versionCode 3","versionCode 4")
edit(gradle,"versionName '0.3.0-validacao'","versionName '0.4.0-reconhecimento'")
edit(manifest,'android:label="TP02 Conexão 0.3"','android:label="TP02 Reconhecimento 0.4"')
edit(ui,'TP02 v0.3 - diagnóstico de Bluetooth e licença; vinculação do fabricante ainda não implementada.',
     'TP02 v0.4 - reconhecimento baseado nos anúncios Bluetooth reais registrados no Samsung.')
print("v0.4: TP02 identified by real manufacturer/service advertisements, no unknown device selection.")
