package br.com.tp02.interop;

import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Packet framing independently reconstructed from Capar 1.4.4 DEX.
 * Max (MTU - 4) data bytes, then 01 for more fragments, 00 for last.
 */
public final class Tp02Framing {
    private Tp02Framing() {}
    public static List<byte[]> encode(byte[] message, int mtu) {
        if(message==null||message.length==0)throw new IllegalArgumentException("empty message");
        if(mtu<23||mtu>517)throw new IllegalArgumentException("invalid MTU");
        final int maxData=mtu-4;
        List<byte[]> packets=new ArrayList<>();
        for(int off=0;off<message.length;) {
            int count=Math.min(maxData,message.length-off);
            byte[] packet=Arrays.copyOfRange(message,off,off+count+1);
            off+=count;
            packet[count]=(byte)(off<message.length?1:0);
            packets.add(packet);
        }
        return packets;
    }
    public static final class Decoder {
        private final ByteArrayOutputStream pending=new ByteArrayOutputStream();
        private final int maxMessageBytes;
        public Decoder(int maxBytes) {
            if(maxBytes<256)throw new IllegalArgumentException("low message limit");
            maxMessageBytes=maxBytes;
        }
        public synchronized byte[] accept(byte[] notification) {
            if(notification==null||notification.length<2){pending.reset();return null;}
            int flag=notification[notification.length-1]&255;
            if(flag!=0&&flag!=1){pending.reset();return null;}
            if(notification.length-1>maxMessageBytes-pending.size()){pending.reset();return null;}
            pending.write(notification,0,notification.length-1);
            if(flag==1)return null;
            byte[] ready=pending.toByteArray();
            pending.reset();return ready;
        }
        public synchronized void reset(){pending.reset();}
        public synchronized int pendingBytes(){return pending.size();}
    }
}
