import br.com.tp02.interop.Tp02Advertisement;
import java.util.Arrays;

/** Recorded ADV and SCAN_RSP from the owner's Samsung HCI snoop capture. */
public final class Tp02AdvertisementTest {
    private static int checked=0;
    static void ok(boolean b,String n){checked++;if(!b)throw new AssertionError(n);}
    static byte[] hex(String s){
        String clean=s.replaceAll("[^0-9a-fA-F]","");
        if(clean.length()%2!=0)throw new IllegalArgumentException();
        byte[] a=new byte[clean.length()/2];
        for(int i=0;i<a.length;i++)a[i]=(byte)Integer.parseInt(clean.substring(i*2,i*2+2),16);
        return a;
    }
    public static void main(String[] args){
        byte[] adv=hex("02 01 06 10 FF 42 06 02 02 00 EC EF B9 75 E8 D2 00 00 00 00");
        byte[] rsp=hex("0A 09 53 65 6C 66 69 65 43 6F 6D 09 16 02 38 41 42 14 D8 45 7F");
        ok(Tp02Advertisement.classify(adv,null)==Tp02Advertisement.Evidence.DEVICE_SIGNATURE,
            "find TP02 with no name on manufacturer advertisement");
        ok(Tp02Advertisement.classify(rsp,null)==Tp02Advertisement.Evidence.DEVICE_SIGNATURE,
            "find TP02 through exact 0x3802 service data without name");
        ok(Tp02Advertisement.classify(rsp,"SelfieCom")==Tp02Advertisement.Evidence.DEVICE_SIGNATURE,
            "specific signal beats just name");
        ok(Tp02Advertisement.classify(null,"SelfieCom")==Tp02Advertisement.Evidence.NAME_ONLY,
            "fallback to original Capar device name");
        ok(Tp02Advertisement.classify(null,"selfiecom ")==Tp02Advertisement.Evidence.NAME_ONLY,
            "case and spaces");
        ok(Tp02Advertisement.classify(null,"Galaxy Fit3")==Tp02Advertisement.Evidence.NONE,
            "other named BLE");
        ok(Tp02Advertisement.classify(null,null)==Tp02Advertisement.Evidence.NONE,
            "unknown anonymous");
        byte[] unrelated=hex("02 01 06 08 FF 4C 00 02 15 01 02 03");
        ok(Tp02Advertisement.classify(unrelated,null)==Tp02Advertisement.Evidence.NONE,
            "Apple manufacturer advertisement not target");
        byte[] wrong=Arrays.copyOf(adv,adv.length);wrong[12]=(byte)0x00;
        ok(Tp02Advertisement.classify(wrong,null)==Tp02Advertisement.Evidence.NONE,
            "similar vendor byte sequence must NOT match");
        wrong=Arrays.copyOf(rsp,rsp.length);wrong[wrong.length-1]=(byte)0x80;
        ok(Tp02Advertisement.classify(wrong,null)==Tp02Advertisement.Evidence.NONE,
            "different service data must NOT match");
        ok(Tp02Advertisement.classify(hex("0A 09 53 65"),null)==Tp02Advertisement.Evidence.NONE,
            "truncated frame must not match");
        ok(Tp02Advertisement.classify(hex("00 10 FF 42 06"),null)==Tp02Advertisement.Evidence.NONE,
            "zero-length terminator");
        System.out.println("PASS: "+checked+" tests based on Samsung HCI advertisements.");
    }
}
