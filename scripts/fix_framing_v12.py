from pathlib import Path
ble=Path("native-tp02/app/src/main/java/br/com/tp02/prototipo/Tp02Ble.java")
ui=Path("native-tp02/app/src/main/java/br/com/tp02/prototipo/MainActivity.java")
gradle=Path("native-tp02/app/build.gradle")
dest=Path("native-tp02/app/src/main/java/br/com/tp02/interop/Tp02Framing.java")
src=Path("cleanroom/src/br/com/tp02/interop/Tp02Framing.java")

def one(path,a,b):
    s=path.read_text("utf-8")
    n=s.count(a)
    if n!=1:raise RuntimeError(f"{path} expected 1 anchor, found {n}: {a[:95]}")
    path.write_text(s.replace(a,b),"utf-8")
def all_hits(path,a,b):
    s=path.read_text("utf-8")
    n=s.count(a)
    if n==0:raise RuntimeError(f"{path}: no anchor {a[:95]}")
    path.write_text(s.replace(a,b),"utf-8")
    return n

dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_bytes(src.read_bytes())
one(ble,"import br.com.tp02.interop.Tp02DiscoveryV2;",
        "import br.com.tp02.interop.Tp02DiscoveryV2;\nimport br.com.tp02.interop.Tp02Framing;")
one(ble,"private final Tp02DiscoveryV2 deviceIdentity=new Tp02DiscoveryV2();",
        "private final Tp02DiscoveryV2 deviceIdentity=new Tp02DiscoveryV2();\n    private final Tp02Framing.Decoder incomingFrames=new Tp02Framing.Decoder(1048576);")

# F4, F0 and OPEN_CAMERA control messages are framed exactly like JPEG bytes.
one(ble,
    'sendOne(licenseSession.mtuReadyMessage())',
    'sendOne(Tp02Framing.encode(licenseSession.mtuReadyMessage(),mtu).get(0))')
one(ble,
    'sendOne(f0)',
    'sendOne(Tp02Framing.encode(f0,mtu).get(0))')
one(ble,
    'sendOne(Tp02Wire.openCameraAck())',
    'sendOne(Tp02Framing.encode(Tp02Wire.openCameraAck(),mtu).get(0))')
one(ble,
    '''sendOne(bytes);
    }
    /** Envio em chunks''',
    '''sendOne(Tp02Framing.encode(bytes,mtu).get(0));
    }
    /** Envio em chunks''')

# Each BLE write is (MTU-4) data bytes followed by an explicit continuation flag.
one(ble,
    'Math.max(20,mtu-3)+" bytes"',
    'Math.max(19,mtu-4)+" dados + 1 marcador por pacote"')
one(ble,
    '''int len=Math.min(Math.max(20,mtu-3),queue.length-offset);
        byte[] packet=Arrays.copyOfRange(queue,offset,offset+len);''',
    '''int len=Math.min(Math.max(19,mtu-4),queue.length-offset);
        byte[] packet=new byte[len+1];
        System.arraycopy(queue,offset,packet,0,len);
        packet[len]=(byte)(offset+len<queue.length?1:0);''')

# The original Capar handles F0 separately, then reassembles all other BLE
# notifications by removing the 0/1 trailing continuation byte.
one(ble,
    '''            events.received(value.clone());
        }
        @Override public void onCharacteristicChanged''',
    '''            byte[] complete=incomingFrames.accept(value);
            if(complete==null)return;
            if(Tp02Wire.command(complete)==Tp02Wire.REQUEST_IMAGE)
                events.info("TP02 confirmou sessão: comando de envio de quadro 03 recebido.");
            events.received(complete);
        }
        @Override public void onCharacteristicChanged''')
# The original implementation reassembles fragments and resets on disconnect.
all_hits(ble,"jpegQueue.reset();licenseSession.reset();",
             "jpegQueue.reset();incomingFrames.reset();licenseSession.reset();")

one(ble,
    '''events.info("OPEN_CAMERA: WRITE AA 55 01 00 aceito pela API Android; monitor ainda não confirmou.");''',
    '''events.info("OPEN_CAMERA: WRITE AA 55 01 00 00 enfileirado; aguardando pedido de quadro 03.");''')
one(ui,
    '''info("TP02 ← WRITE abertura AA 55 01 00; aguardando pedido 03 para enviar JPEG.");''',
    '''info("TP02 ← pacote completo AA 55 01 00 00; aguardando quadro 03.");''')
one(gradle,"versionCode 11","versionCode 12")
one(gradle,"versionName '1.1.0-conexao-unica'","versionName '1.2.0-framing-capar'")
print("TP02 v1.2: CRC-free BLE flag framing (0x01 continuation / 0x00 final), RX reassembly, single GATT preserved")
