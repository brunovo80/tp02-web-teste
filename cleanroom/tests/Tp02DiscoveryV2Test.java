import br.com.tp02.interop.Tp02DiscoveryV2;
import java.util.Arrays;

public final class Tp02DiscoveryV2Test {
    private static int n=0;
    private static void check(boolean ok,String msg){n++;if(!ok)throw new AssertionError(msg);}
    private static byte[] hex(String h){
        String clean=h.replaceAll("[^0-9a-fA-F]","");
        byte[] b=new byte[clean.length()/2];
        for(int i=0;i<b.length;i++)b[i]=(byte)Integer.parseInt(clean.substring(i*2,i*2+2),16);
        return b;
    }
    public static void main(String[] args){
        // Real byte patterns from Samsung HCI capture; avoid storing user MAC in test.
        byte[] manufacturer=hex("02 01 06 10 FF 42 06 02 02 00 EC EF B9 75 E8 D2 00 00 00 00");
        byte[] response=hex("0A 09 53 65 6C 66 69 65 43 6F 6D 09 16 02 38 41 42 14 D8 45 7F");
        Tp02DiscoveryV2 d=new Tp02DiscoveryV2();
        check(d.observe("X",manufacturer,null)==Tp02DiscoveryV2.Decision.CANDIDATE,"vendor alone not proof");
        check(d.observe("X",response,null)==Tp02DiscoveryV2.Decision.PROBE_GATT,"combine scan response");
        d.clear();
        check(d.observe("X",response,null)==Tp02DiscoveryV2.Decision.PROBE_GATT,"name in scan response");
        d.clear();
        // A service-data report without a name can corroborate the vendor report.
        byte[] service=hex("09 16 02 38 41 42 14 D8 45 7F");
        check(d.observe("X",service,null)==Tp02DiscoveryV2.Decision.CANDIDATE,"service alone insufficient");
        check(d.observe("X",manufacturer,null)==Tp02DiscoveryV2.Decision.PROBE_GATT,"combine two reports");
        d.clear();
        byte[] variation=Arrays.copyOf(manufacturer,manufacturer.length);
        variation[11]=(byte)0x67;variation[12]=(byte)0x02;
        check(d.observe("X",variation,null)==Tp02DiscoveryV2.Decision.CANDIDATE,"dynamic suffix tolerated");
        check(d.observe("X",service,null)==Tp02DiscoveryV2.Decision.PROBE_GATT,"suffix variation retains candidate");
        d.clear();
        check(d.observe("X",manufacturer,null)==Tp02DiscoveryV2.Decision.CANDIDATE,"X vendor");
        check(d.observe("Y",service,null)==Tp02DiscoveryV2.Decision.CANDIDATE,"cannot combine separate peripherals");
        check(d.observe("Z",null,"SelfieCom")==Tp02DiscoveryV2.Decision.PROBE_GATT,"name from Android");
        d.clear();
        check(d.observe("X",null,"Galaxy Fit3")==Tp02DiscoveryV2.Decision.IGNORE,"unrelated name");
        check(d.observe("X",hex("08 FF 4C 00 02 02 00 33 44"),null)==Tp02DiscoveryV2.Decision.IGNORE,"other vendor");
        check(d.observe("X",hex("03 16 02 38"),null)==Tp02DiscoveryV2.Decision.IGNORE,"truncated service");
        check(d.observe("X",hex("10 FF 42 06"),null)==Tp02DiscoveryV2.Decision.IGNORE,"invalid TLV");
        check(d.observe("",manufacturer,null)==Tp02DiscoveryV2.Decision.IGNORE,"empty identity rejected");
        check(d.knownAddresses()==1,"candidate map");
        System.out.println("PASS: "+n+" TP02 dynamic and combined advertisement tests.");
    }
}
