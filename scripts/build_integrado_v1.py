from pathlib import Path

root=Path("native-tp02")
base=root/"app/src/main/java/br/com/tp02/prototipo"
ble=base/"Tp02Ble.java"
ui=base/"MainActivity.java"
gradle=root/"app/build.gradle"
manifest=root/"app/src/main/AndroidManifest.xml"
clean=Path("cleanroom/src/br/com/tp02/interop/Tp02DiscoveryV2.java")
dest=root/"app/src/main/java/br/com/tp02/interop/Tp02DiscoveryV2.java"

def replace(file, before, after):
    s=file.read_text("utf-8")
    count=s.count(before)
    if count!=1: raise RuntimeError(f"{file}: expected 1 match, found {count} for {before[:85]}")
    file.write_text(s.replace(before,after),"utf-8")

def replace_all(file, before, after):
    s=file.read_text("utf-8")
    if before not in s:raise RuntimeError(f"{file}: no match for {before[:80]}")
    file.write_text(s.replace(before,after),"utf-8")

dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_bytes(clean.read_bytes())

# Keep a stable application id for this integrated line (do not collide with Capar).
replace(gradle,"applicationId 'br.com.tp02.reconhecimentov04'",
        "applicationId 'br.com.tp02.integrado'")
replace(gradle,"versionCode 4","versionCode 10")
replace(gradle,"versionName '0.4.0-reconhecimento'","versionName '1.0.0-integrado'")
replace(manifest,'android:label="TP02 Reconhecimento 0.4"',
        'android:label="TP02 Integrado"')

# Identify using combined *live* scan records. No fixed old MAC, no RSSI choices.
replace(ble,"import br.com.tp02.interop.Tp02Advertisement;",
        "import br.com.tp02.interop.Tp02Advertisement;\nimport br.com.tp02.interop.Tp02DiscoveryV2;")
replace(ble,"private final Tp02TxQueue jpegQueue=new Tp02TxQueue();",
        "private final Tp02TxQueue jpegQueue=new Tp02TxQueue();\n    private final Tp02DiscoveryV2 deviceIdentity=new Tp02DiscoveryV2();\n    private volatile boolean monitorRequestedCamera=false;")
replace(ble,
    '''Tp02Advertisement.Evidence evidence=Tp02Advertisement.classify(observed,n);
            if(evidence!=Tp02Advertisement.Evidence.NONE || addr.equalsIgnoreCase(VERIFIED_MAC)){
                events.info("Identidade TP02: "+evidence+" (anúncio/identidade capturados no Samsung).");''',
    '''Tp02DiscoveryV2.Decision decision=deviceIdentity.observe(addr,observed,n);
            if(decision==Tp02DiscoveryV2.Decision.PROBE_GATT){
                events.info("TP02 candidato identificado pelo nome ou assinatura BLE corroborada.");''')
replace(ble,
    'events.info("Possível TP02 pelo nome/endereço observado: "+addr+". Conectando...");',
    'events.info("Validando serviço de comunicação no monitor...");')
replace(ble,
    '        discovered.clear();foundLabels.clear();',
    '        discovered.clear();foundLabels.clear();deviceIdentity.clear();monitorRequestedCamera=false;')
replace(ble,
    'private static final String VERIFIED_MAC="41:42:14:D8:45:7F";',
    '// Endereço anterior omitido: a identidade deve vir dos anúncios atuais.')
replace(ble,
    '''events.info("Buscando SelfieCom (BLE) por até 20s...");''',
    '''events.info("Buscando o TP02 por nome + dados de modelo BLE, sem seleção manual...");''')
replace(ble,
    '''},20000);''',
    '''},60000);''')
replace(ble,
    'Nenhuma assinatura do TP02 recebida. Dispositivos próximos: ',
    'Sem anúncio compatível do TP02 nesta busca. Outros aparelhos próximos: ')
replace(ble,
    '''events.info("Controle MTU F4 enviado="+sendOne(licenseSession.mtuReadyMessage()));''',
    '''events.info("Controle MTU F4 enviado="+sendOne(licenseSession.mtuReadyMessage()));''')
replace(ble,
    'if(!ready || licenseSession.state()!=Tp02Session.State.GATT_READY)return;',
    'if(!ready || monitorRequestedCamera || licenseSession.state()!=Tp02Session.State.GATT_READY)return;')
replace(ble,
    '''    public boolean authorized(){return licenseSession.mayStream() || licenseSession.state()==Tp02Session.State.AUTHORIZED;}''',
    '''    /** Real camera-open request from the known TP02 is required before sending frames.
     * Account-side binding may still be required by the device firmware. */
    public boolean canStream(){return ready && monitorRequestedCamera;}''')
replace(ble,
    '''public void ackOpen(){
        if(!authorized()){events.info("OPEN_CAMERA não confirmado: falta autorização válida.");return;}
        if(ready)writeSmall(Tp02Wire.openCameraAck());
    }''',
    '''public boolean ackOpen(){
        if(!ready)return false;
        boolean ok=sendOne(Tp02Wire.openCameraAck());
        if(ok){
            monitorRequestedCamera=true;
            events.info("OPEN_CAMERA veio do monitor; resposta AA 55 01 00 aceita pelo Android.");
        }else events.info("Falha ao responder OPEN_CAMERA; tentando novamente.");
        return ok;
    }''')
replace(ble,
    '''if(!ready || !licenseSession.mayStream() || jpeg==null || jpeg.length==0 || !sending.compareAndSet(false,true))return false;''',
    '''if(!canStream() || jpeg==null || jpeg.length==0 || !sending.compareAndSet(false,true))return false;''')
replace(ble,
    '''ready=false;sending.set(false);jpegQueue.reset();licenseSession.reset();events.connected(false);''',
    '''ready=false;monitorRequestedCamera=false;sending.set(false);jpegQueue.reset();licenseSession.reset();events.connected(false);''')
replace(ble,
    '''sending.set(false);jpegQueue.reset();licenseSession.reset();ready=false;tx=null;''',
    '''sending.set(false);jpegQueue.reset();licenseSession.reset();monitorRequestedCamera=false;ready=false;tx=null;''')
replace(ble,
    '''if(status!=BluetoothGatt.GATT_SUCCESS)events.info("Falha na escrita BLE: "+status);''',
    '''if(status!=BluetoothGatt.GATT_SUCCESS){
                events.info("Falha na escrita BLE: "+status);
                if(sending.get()){queue=null;sending.set(false);main.removeCallbacks(feed);}
            }else if(sending.get()){
                main.removeCallbacks(feed);main.post(feed);
            }''')
replace(ble,
    '''main.postDelayed(feed,20);''',
    '''main.postDelayed(feed,85); // fallback if NO_RESPONSE does not yield a callback''')

# Camera: permit a frame only if the physical TP02 sent OPEN_CAMERA.
replace(ui,
    'shoot.setEnabled(c && ble.authorized());',
    'shoot.setEnabled(c && ble.canStream());')
replace(ui,
    'if(openRequested && cameraReady && ble.ready() && ble.authorized() && !ackSent){',
    'if(openRequested && cameraReady && ble.ready() && !ackSent){')
replace(ui,
    '''ackSent=true;ble.ackOpen();info("TP02 ← resposta de abertura AA 55 01 00.");''',
    '''if(ble.ackOpen()){
                ackSent=true;
                shoot.setEnabled(true);
                info("TP02 ← resposta de abertura AA 55 01 00.");
            }else new android.os.Handler(android.os.Looper.getMainLooper())
                .postDelayed(this::maybeAck,250);''')
replace(ui,
    '''if(!ble.ready() || !ble.authorized() || !cameraReady){info("Câmera ou autorização ainda indisponível. Sem envio ao monitor.");return;}''',
    '''if(!ble.ready() || !ble.canStream() || !cameraReady){
            info("Não houve pedido de câmera confirmado pelo TP02. Quadro não enviado.");return;
        }''')
replace(ui,
    '''TP02 v0.4 - reconhecimento baseado nos anúncios Bluetooth reais registrados no Samsung.''',
    '''TP02 Integrado 1.0 • câmera, descoberta automática, GATT e envio sob solicitação do monitor.''')
replace(ui,
    '''TextView auto=label("Identificação automática. O aplicativo NÃO conecta a periféricos desconhecidos.",12);''',
    '''TextView auto=label("Ligue o TP02 pelo interruptor antes de procurar. A identificação é automática; não é preciso escolher aparelhos.",12);''')

# Prevent the camera from being opened twice during an asynchronous callback.
replace(ui,
    'private boolean frontCamera=false;',
    'private boolean frontCamera=false;\n    private volatile boolean cameraOpening=false;')
replace(ui,
    'if(!hasPermissions() || camera!=null || !preview.isAvailable())return;',
    'if(!hasPermissions() || camera!=null || cameraOpening || !preview.isAvailable())return;')
replace(ui,
    '''manager.openCamera(choice,new CameraDevice.StateCallback() {''',
    '''cameraOpening=true;
            manager.openCamera(choice,new CameraDevice.StateCallback() {''')
replace(ui,
    '''@Override public void onOpened(CameraDevice d){camera=d;openSession();}''',
    '''@Override public void onOpened(CameraDevice d){cameraOpening=false;camera=d;openSession();}''')
replace(ui,
    '''@Override public void onDisconnected(CameraDevice d){d.close();camera=null;cameraReady=false;info("Câmera desconectada.");}''',
    '''@Override public void onDisconnected(CameraDevice d){cameraOpening=false;d.close();camera=null;cameraReady=false;info("Câmera desconectada.");}''')
replace(ui,
    '''d.close();camera=null;cameraReady=false;
                    info(err==CameraDevice.StateCallback.ERROR_CAMERA_DISABLED''',
    '''cameraOpening=false;d.close();camera=null;cameraReady=false;
                    info(err==CameraDevice.StateCallback.ERROR_CAMERA_DISABLED''')
replace(ui,
    '''}catch(Exception e){info("Erro ao abrir câmera: "+e.getMessage());}''',
    '''}catch(Exception e){cameraOpening=false;info("Erro ao abrir câmera: "+e.getMessage());}''')

# Add copyable logs; user no longer needs to transcribe addresses.
replace(ui,
    '''root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);''',
    '''root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        Button copy=new Button(this);
        copy.setText("COPIAR DIAGNÓSTICO");
        copy.setOnClickListener(v->{
            android.content.ClipboardManager cm=(android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
            if(cm!=null){
                cm.setPrimaryClip(android.content.ClipData.newPlainText("TP02 diagnóstico",history.getText().toString()));
                android.widget.Toast.makeText(this,"Diagnóstico copiado",android.widget.Toast.LENGTH_SHORT).show();
            }
        });
        root.addView(copy,new LinearLayout.LayoutParams(-1,dp(50)));
        setContentView(root);''')

print("INTEGRATED_V1_OK discovery+camera+GATT+F4/F0+JPEG+buttons+diagnostic; NO remote auth bypass.")
