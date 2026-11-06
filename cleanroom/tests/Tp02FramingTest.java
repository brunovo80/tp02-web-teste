import br.com.tp02.interop.Tp02Framing;
import java.util.*;
public final class Tp02FramingTest {
    private static int pass=0;
    private static void ok(boolean c,String name){pass++;if(!c)throw new AssertionError(name);}
    private static byte[] msg(int n){byte[] b=new byte[n];for(int i=0;i<n;i++)b[i]=(byte)(i*17+5);return b;}
    private static void roundTrip(byte[] data,int mtu){
        List<byte[]> packets=Tp02Framing.encode(data,mtu);
        Tp02Framing.Decoder d=new Tp02Framing.Decoder(200000);
        for(int i=0;i<packets.size();i++){
            byte[] p=packets.get(i);
            ok(p.length<=mtu-3,"packet <= ATT payload");
            ok(p[p.length-1]==(i==packets.size()-1?0:1),"trailer flag");
            byte[] ready=d.accept(p);
            ok(i==packets.size()-1?Arrays.equals(ready,data):ready==null,"round trip");
        }
        ok(d.pendingBytes()==0,"decoder clear");
    }
    public static void main(String[] args){
        byte[] ack={(byte)0xAA,0x55,1,0},f4={(byte)0xAA,0x55,(byte)0xF4,0};
        ok(Arrays.equals(Tp02Framing.encode(ack,498).get(0),new byte[]{(byte)0xAA,0x55,1,0,0}),"ACK five bytes");
        ok(Arrays.equals(Tp02Framing.encode(f4,498).get(0),new byte[]{(byte)0xAA,0x55,(byte)0xF4,0,0}),"F4 five bytes");
        ok(Tp02Framing.encode(msg(12),498).get(0).length==13,"F0+nonce 13 bytes");
        ok(Tp02Framing.encode(msg(494),498).get(0).length==495,"MTU498 494 data");
        ok(Tp02Framing.encode(msg(495),498).size()==2,"continuation case");
        ok(Tp02Framing.encode(msg(988),498).size()==2,"exact multiple");
        ok(Tp02Framing.encode(msg(15360),498).size()==32,"15360 image chunks");
        ok(Tp02Framing.encode(msg(19),23).get(0).length==20,"default MTU23");
        roundTrip(ack,23);roundTrip(f4,498);roundTrip(msg(12),498);
        roundTrip(msg(18),23);roundTrip(msg(19),23);roundTrip(msg(20),23);
        roundTrip(msg(494),498);roundTrip(msg(495),498);roundTrip(msg(988),498);
        roundTrip(msg(15360),498);roundTrip(msg(200000),517);
        Tp02Framing.Decoder rx=new Tp02Framing.Decoder(16384);
        ok(rx.accept(new byte[]{1,2,1})==null,"fragment pending");
        ok(rx.pendingBytes()==2,"pending count");
        ok(Arrays.equals(rx.accept(new byte[]{3,4,0}),new byte[]{1,2,3,4}),"reassembly");
        ok(rx.accept(new byte[]{1,2,2})==null,"invalid flag");
        ok(rx.pendingBytes()==0,"reset malformed");
        Tp02Framing.Decoder small=new Tp02Framing.Decoder(256);
        ok(small.accept(Tp02Framing.encode(msg(300),517).get(0))==null,"overflow drop");
        ok(small.pendingBytes()==0,"overflow reset");
        System.out.println("PASS: "+pass+" BLE framing checks.");
    }
}
