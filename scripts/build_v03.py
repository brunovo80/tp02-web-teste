from pathlib import Path

root=Path("native-tp02")
app=root/"app"
base=app/"src/main/java/br/com/tp02/prototipo"
ble=base/"Tp02Ble.java"
ui=base/"MainActivity.java"
protocol=base/"Tp02Protocol.java"
manifest=app/"src/main/AndroidManifest.xml"
gradle=app/"build.gradle"

def put(p,old,new):
    s=p.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1: raise RuntimeError(f"{p}: expected 1 occurrence, got {n}: {old[:50]!r}")
    p.write_text(s.replace(old,new),encoding="utf-8")

put(protocol,'return new byte[]{(byte)0xAA, 0x55, 0x01, 0x01};',
             'return new byte[]{(byte)0xAA, 0x55, 0x01, 0x00};')
put(protocol,'bytes.length < 13','bytes.length < 12')
put(gradle,"applicationId 'br.com.tp02.prototipo'",
           "applicationId 'br.com.tp02.interopdiagnostico'")
put(gradle,"versionCode 2","versionCode 3")
put(gradle,"versionName '0.2.0-diagnostico'",
           "versionName '0.3.0-validacao'")
put(manifest,'<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" android:maxSdkVersion="30" />',
             '<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />')
put(manifest,'<uses-permission android:name="android.permission.BLUETOOTH_SCAN" android:usesPermissionFlags="neverForLocation" />',
             '<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />')
put(manifest,'android:label="TP02 Imagem Real (Teste)"','android:label="TP02 Conexão 0.3"')

put(ui,'private Button connect, choose, shoot;','private Button connect, shoot;')
s=ui.read_text(encoding="utf-8")
start=s.index('        choose=new Button(this);')
end=s.index('        shoot=new Button(this);',start)
s=s[:start]+'''        TextView auto=label("Identificação automática. O aplicativo NÃO conecta a periféricos desconhecidos.",12);
        root.addView(auto);
'''+s[end:]
ui.write_text(s,encoding="utf-8")
put(ui,'''            return checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED;''',
'''            return checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED;''')
put(ui,'''Manifest.permission.CAMERA,Manifest.permission.BLUETOOTH_SCAN,Manifest.permission.BLUETOOTH_CONNECT},11);''',
'''Manifest.permission.CAMERA,Manifest.permission.BLUETOOTH_SCAN,Manifest.permission.BLUETOOTH_CONNECT,Manifest.permission.ACCESS_FINE_LOCATION},11);''')
put(ui,'''shoot.setEnabled(c);connect.setText(c?"RECONECTAR SELFIECOM":"CONECTAR SELFIECOM");''',
'''shoot.setEnabled(c && ble.authorized());connect.setText(c?"RECONECTAR TP02":"PROCURAR TP02");''')
put(ui,'''status.setText(c?"SelfieCom conectado • esperando o comando de imagem":"Aguardando conexão BLE");''',
'''status.setText(c?"BLE encontrado • verificando licença e vínculo":"Aguardando identificação do TP02");''')
put(ui,'''info("TP02 → " + Tp02Protocol.hex(payload));''',
'''if(cmd!=0xF0)info("TP02 → " + Tp02Protocol.hex(payload));''')
put(ui,'''if(openRequested && cameraReady && ble.ready() && !ackSent){''',
'''if(openRequested && cameraReady && ble.ready() && ble.authorized() && !ackSent){''')
put(ui,'''info("TP02 ← resposta de abertura AA 55 01 01.");''',
'''info("TP02 ← resposta de abertura AA 55 01 00.");''')
put(ui,'''if(!ble.ready() || !cameraReady){info("Ainda sem BLE e câmera prontos.");return;}''',
'''if(!ble.ready() || !ble.authorized() || !cameraReady){info("Câmera ou autorização ainda indisponível. Sem envio ao monitor.");return;}''')
put(ui,'''Aplicativo experimental 0.2.0 / diagnóstico BLE.''',
'''TP02 v0.3 - diagnóstico de Bluetooth e licença; vinculação do fabricante ainda não implementada.''')

# Add the clean-room protocol library to the Android source set.
clean=Path("cleanroom/src/br/com/tp02/interop")
dest=app/"src/main/java/br/com/tp02/interop"
dest.mkdir(parents=True,exist_ok=True)
for filename in ["Tp02Wire.java","Tp02Session.java","Tp02TxQueue.java"]:
    (dest/filename).write_bytes((clean/filename).read_bytes())

# Use proven F4 and F0 exchanges, without treating device license as server authorization.
put(ble,'import java.util.Arrays;','''import java.util.Arrays;
import java.security.SecureRandom;
import br.com.tp02.interop.Tp02Session;
import br.com.tp02.interop.Tp02Wire;
import br.com.tp02.interop.Tp02TxQueue;''')
put(ble,'''    private final Context context;''','''    private final Tp02Session licenseSession=new Tp02Session();
    private final Tp02TxQueue jpegQueue=new Tp02TxQueue();
    private final Context context;''')
put(ble,'''                events.info("BLE conectado. Descobrindo serviços...");g.discoverServices();''',
'''                licenseSession.onConnected();
                events.info("BLE conectado. Descobrindo serviços...");g.discoverServices();''')
put(ble,'''                ready=false;sending.set(false);events.connected(false);''',
'''                ready=false;sending.set(false);jpegQueue.reset();licenseSession.reset();events.connected(false);''')
put(ble,'''            if(status==BluetoothGatt.GATT_SUCCESS && ready){
                boolean sent=sendOne(new byte[]{(byte)0xAA,0x55,(byte)0xF4,0x00});
                events.info("Comando F4 observado no Capar 1.4.4: enviado="+sent);
            }
            events.info("Esperando comandos; negociação de licença não implementada.");''',
'''            if(status==BluetoothGatt.GATT_SUCCESS && ready){
                try{
                    licenseSession.onGattReady();
                    events.info("Controle MTU F4 enviado="+sendOne(licenseSession.mtuReadyMessage()));
                    main.postDelayed(()->{
                        if(!ready || licenseSession.state()!=Tp02Session.State.GATT_READY)return;
                        try{
                            byte[] f0=licenseSession.beginLicenseRequest(new SecureRandom());
                            events.info("Desafio de identificação F0 enviado="+sendOne(f0));
                        }catch(Exception e){events.info("Erro no desafio F0: "+e.getClass().getSimpleName());}
                    },1000);
                }catch(Exception e){events.info("Falha ao inicializar licença: "+e.getClass().getSimpleName());}
            }
            events.info("Identificação do aparelho não significa autorização do fabricante.");''')
put(ble,'''        @Override public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c,byte[] value){
            events.received(value.clone());
        }''',
'''        private void receive(byte[] value){
            if(value==null)return;
            if(Tp02Wire.command(value)==Tp02Wire.LICENSE_RESPONSE){
                try{
                    licenseSession.acceptDeviceLicenseReply(value);
                    events.info("Resposta F0 válida decodificada; vinculação com fabricante ainda necessária.");
                    events.info("Licença não é exibida nem transmitida a serviços externos.");
                }catch(Exception e){events.info("Resposta F0 inesperada ou inválida.");}
                return;
            }
            events.received(value.clone());
        }
        @Override public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c,byte[] value){
            receive(value);
        }''')
put(ble,'''if(Build.VERSION.SDK_INT<33) events.received(c.getValue().clone());''',
'''if(Build.VERSION.SDK_INT<33) receive(c.getValue());''')
put(ble,'''    public boolean ready(){return ready;}''',
'''    public boolean ready(){return ready;}
    public boolean authorized(){return licenseSession.maySendImage() || licenseSession.state()==Tp02Session.State.AUTHORIZED;}''')
put(ble,'''public void ackOpen(){if(ready) writeSmall(Tp02Protocol.openAck());}''',
'''public void ackOpen(){
        if(!authorized()){events.info("OPEN_CAMERA não confirmado: falta autorização válida.");return;}
        if(ready)writeSmall(Tp02Wire.openCameraAck());
    }''')
put(ble,'''        if(!ready || jpeg==null || jpeg.length==0 || !sending.compareAndSet(false,true))return false;''',
'''        if(!ready || !licenseSession.maySendImage() || jpeg==null || jpeg.length==0 || !sending.compareAndSet(false,true))return false;''')
put(ble,'''        stopScan();main.removeCallbacks(feed);sending.set(false);ready=false;tx=null;''',
'''        stopScan();main.removeCallbacks(feed);sending.set(false);jpegQueue.reset();licenseSession.reset();ready=false;tx=null;''')
# Eliminate the impression that arbitrary MACs can be safely selected by the user.
put(ble,'''events.info("SelfieCom não encontrado. Verifica se o TP02 está ligado.");''',
'''events.info("TP02 não identificado. Sem conexão com dispositivos sem identidade comprovada.");''')
print("v0.3 integration: automatic discovery, clean-room F4/F0, gated camera and permission correction.")
