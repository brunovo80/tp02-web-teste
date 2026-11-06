package br.com.tp02.interop;

import java.util.Arrays;

/**
 * Device identification derived from REAL Samsung HCI snoop advertisements
 * captured 2026-11-05. No random RSSI, anonymous MAC selection or GATT probing.
 *
 * Recorded TP02:
 *  ADV: 02 01 06 10 FF 42 06 02 02 00 EC EF B9 75 E8 D2 00 00 00 00
 *  SCAN_RSP: 0A 09 "SelfieCom" 09 16 02 38 41 42 14 D8 45 7F
 * Manufacturer data and service data come in separate advertisements. Either
 * complete device-specific signature is sufficient, even without a name.
 */
public final class Tp02Advertisement {
    public enum Evidence { DEVICE_SIGNATURE, NAME_ONLY, NONE }
    private static final byte[] MANUFACTURER = {
        0x42,0x06,0x02,0x02,0x00,(byte)0xEC,(byte)0xEF,(byte)0xB9,
        0x75,(byte)0xE8,(byte)0xD2,0x00,0x00,0x00,0x00
    };
    private static final byte[] SERVICE_DATA = {
        0x02,0x38,0x41,0x42,0x14,(byte)0xD8,0x45,0x7F
    };
    private Tp02Advertisement(){}
    public static Evidence classify(byte[] advertisement, String deviceName) {
        if (hasSignature(advertisement)) return Evidence.DEVICE_SIGNATURE;
        if (deviceName!=null && deviceName.trim().equalsIgnoreCase("SelfieCom"))
            return Evidence.NAME_ONLY;
        return Evidence.NONE;
    }
    public static boolean hasSignature(byte[] advertisement) {
        if(advertisement==null)return false;
        int i=0;
        while (i < advertisement.length) {
            int len=advertisement[i++]&0xff;
            if (len==0) break;
            if (i+len>advertisement.length) break;
            int type=advertisement[i]&0xff;
            int start=i+1, end=i+len;
            if (type==0xFF && same(advertisement,start,end,MANUFACTURER))return true;
            if (type==0x16 && same(advertisement,start,end,SERVICE_DATA))return true;
            i+=len;
        }
        return false;
    }
    private static boolean same(byte[] frame,int start,int end,byte[] signature){
        return end-start==signature.length &&
            Arrays.equals(Arrays.copyOfRange(frame,start,end),signature);
    }
}
