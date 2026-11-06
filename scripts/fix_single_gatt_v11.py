from pathlib import Path

ble=Path("native-tp02/app/src/main/java/br/com/tp02/prototipo/Tp02Ble.java")
ui=Path("native-tp02/app/src/main/java/br/com/tp02/prototipo/MainActivity.java")
gradle=Path("native-tp02/app/build.gradle")
manifest=Path("native-tp02/app/src/main/AndroidManifest.xml")

def replace(file,old,new):
    s=file.read_text("utf-8")
    count=s.count(old)
    if count!=1:raise RuntimeError(f"Unexpected {file}: matches={count}; string={old[:100]!r}")
    file.write_text(s.replace(old,new),"utf-8")

replace(ble,
    "private boolean scanning = false, ready = false;",
    "private boolean scanning = false, ready = false;\n    private boolean connecting=false, servicesConfigured=false, mtuInitialized=false;")
replace(ble,
    """@Override public void onScanResult(int type, ScanResult result) {
            BluetoothDevice d = result.getDevice();""",
    """@Override public void onScanResult(int type, ScanResult result) {
            // A callback already queued before stopScan must not create a second GATT.
            if(!scanning || connecting || gatt!=null)return;
            BluetoothDevice d = result.getDevice();""")
replace(ble,
    """events.info("Validando serviço de comunicação no monitor...");
                stopScan();connect(d);""",
    """events.info("Validando serviço de comunicação no monitor...");
                connecting=true;
                stopScan();connect(d);""")
replace(ble,
    """catch(Exception e){events.info("Conexão GATT falhou: "+e.getMessage());}""",
    """catch(Exception e){connecting=false;events.info("Conexão GATT falhou: "+e.getMessage());}""")
replace(ble,
    """@Override public void onConnectionStateChange(BluetoothGatt g,int status,int state) {
            if(status==BluetoothGatt.GATT_SUCCESS && state==BluetoothProfile.STATE_CONNECTED) {""",
    """@Override public void onConnectionStateChange(BluetoothGatt g,int status,int state) {
            if(gatt!=null && gatt!=g){
                events.info("Ignorando callback de conexão GATT obsoleta.");
                try{g.close();}catch(Exception ignored){}
                return;
            }
            if(status==BluetoothGatt.GATT_SUCCESS && state==BluetoothProfile.STATE_CONNECTED) {
                connecting=false;""")
replace(ble,
    """ready=false;monitorRequestedCamera=false;sending.set(false);jpegQueue.reset();licenseSession.reset();events.connected(false);""",
    """connecting=false;servicesConfigured=false;mtuInitialized=false;
                ready=false;monitorRequestedCamera=false;sending.set(false);jpegQueue.reset();licenseSession.reset();events.connected(false);""")
replace(ble,
    """@Override public void onServicesDiscovered(BluetoothGatt g,int status) {
            if(status!=BluetoothGatt.GATT_SUCCESS)""",
    """@Override public void onServicesDiscovered(BluetoothGatt g,int status) {
            if(gatt!=null && gatt!=g)return;
            if(servicesConfigured){events.info("Descoberta de serviços duplicada ignorada.");return;}
            if(status!=BluetoothGatt.GATT_SUCCESS)""")
replace(ble,
    """            g.setCharacteristicNotification(rx,true);""",
    """            servicesConfigured=true;
            g.setCharacteristicNotification(rx,true);""")
replace(ble,
    """@Override public void onDescriptorWrite(BluetoothGatt g,BluetoothGattDescriptor d,int status){
            if(status!=BluetoothGatt.GATT_SUCCESS)""",
    """@Override public void onDescriptorWrite(BluetoothGatt g,BluetoothGattDescriptor d,int status){
            if(gatt!=null && gatt!=g)return;
            if(ready){events.info("NOTIFY duplicado ignorado.");return;}
            if(status!=BluetoothGatt.GATT_SUCCESS)""")
replace(ble,
    """@Override public void onMtuChanged(BluetoothGatt g,int size,int status){
            if(status==BluetoothGatt.GATT_SUCCESS) mtu=size;""",
    """@Override public void onMtuChanged(BluetoothGatt g,int size,int status){
            if(gatt!=null && gatt!=g)return;
            if(mtuInitialized){events.info("Segundo evento MTU ignorado.");return;}
            if(status==BluetoothGatt.GATT_SUCCESS){mtuInitialized=true;mtu=size;}""")
replace(ble,
    """stopScan();main.removeCallbacks(feed);sending.set(false);jpegQueue.reset();licenseSession.reset();monitorRequestedCamera=false;ready=false;tx=null;""",
    """stopScan();main.removeCallbacks(feed);sending.set(false);jpegQueue.reset();licenseSession.reset();
        connecting=false;servicesConfigured=false;mtuInitialized=false;monitorRequestedCamera=false;ready=false;tx=null;""")
# Accurate logging: Android accepted WRITE request != monitor ACK.
replace(ble,
    """events.info("OPEN_CAMERA veio do monitor; resposta AA 55 01 00 aceita pelo Android.");""",
    """events.info("OPEN_CAMERA: WRITE AA 55 01 00 aceito pela API Android; monitor ainda não confirmou.");""")
replace(ui,
    """info("TP02 ← resposta de abertura AA 55 01 00.");""",
    """info("TP02 ← WRITE abertura AA 55 01 00; aguardando pedido 03 para enviar JPEG.");""")
replace(gradle,"versionCode 10","versionCode 11")
replace(gradle,"versionName '1.0.0-integrado'","versionName '1.1.0-conexao-unica'")
print("PATCH_OK: single-GATT, one notification setup, one MTU initialization, truthful diagnostics.")
