package br.com.tp02.interop;

import java.util.HashMap;
import java.util.Map;

/**
 * Evidence accumulator for TP02 BLE advertisements.
 * Based on one captured Samsung HCI session; heuristics must be hardware-validated.
 * It NEVER uses RSSI or an old address to assert identity.
 */
public final class Tp02DiscoveryV2 {
    public enum Decision { IGNORE, CANDIDATE, PROBE_GATT }
    private static final class Evidence {
        boolean name, vendorModel, serviceModel;
    }
    private final Map<String,Evidence> byAddress=new HashMap<>();

    public Decision observe(String address, byte[] rawScanRecord, String androidName) {
        if(address==null || address.isEmpty())return Decision.IGNORE;
        Evidence e=byAddress.computeIfAbsent(address, k->new Evidence());
        if("SelfieCom".equalsIgnoreCase(normalize(androidName)))e.name=true;
        if(rawScanRecord!=null){
            int i=0;
            while(i<rawScanRecord.length) {
                int len=rawScanRecord[i++]&255;
                if(len==0 || i+len>rawScanRecord.length)break;
                int type=rawScanRecord[i]&255;
                int content=i+1;
                int dataSize=len-1;
                if((type==0x09 || type==0x08) && dataSize>0){
                    try {
                        String embedded=new String(rawScanRecord,content,dataSize,"UTF-8");
                        if("SelfieCom".equalsIgnoreCase(normalize(embedded)))e.name=true;
                    }catch(java.io.UnsupportedEncodingException ignored){}
                }
                // 0x0642: manufacturer ID in little-endian; recorded model prefix 02 02 00.
                // Remaining bytes may encode device-specific values: do not freeze them.
                if(type==0xff && dataSize>=5 && value(rawScanRecord,content,0x42,0x06,0x02,0x02,0x00))
                    e.vendorModel=true;
                // 0x3802: 16-bit service-data UUID, observed with a 6-byte device identifier.
                // This is not the Nordic UART GATT service.
                if(type==0x16 && dataSize>=8 && value(rawScanRecord,content,0x02,0x38))
                    e.serviceModel=true;
                i+=len;
            }
        }
        if(e.name || (e.vendorModel && e.serviceModel))return Decision.PROBE_GATT;
        if(e.vendorModel || e.serviceModel)return Decision.CANDIDATE;
        return Decision.IGNORE;
    }
    private static String normalize(String s){return s==null?"":s.trim();}
    private static boolean value(byte[] a,int start,int... prefix){
        if(start+prefix.length>a.length)return false;
        for(int k=0;k<prefix.length;k++)if((a[start+k]&255)!=prefix[k])return false;
        return true;
    }
    public void clear(){byAddress.clear();}
    public int knownAddresses(){return byAddress.size();}
}
