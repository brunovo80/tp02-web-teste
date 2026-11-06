package br.com.tp02.interop;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Locale;

/** Clean-room wire format established by examining Capar 1.4.4 bytecode. */
public final class Tp02Wire {
    public static final String SERVICE="6e400001-b5a3-f393-e0a9-e50e24dcca9d";
    public static final String WRITE="6e400002-b5a3-f393-e0a9-e50e24dcca9d";
    public static final String NOTIFY="6e400003-b5a3-f393-e0a9-e50e24dcca9d";
    public static final int OPEN_CAMERA=1, CAPTURE=2, REQUEST_IMAGE=3, SWITCH_CAMERA=6;
    public static final int VOLUME_PLUS=10, VOLUME_MINUS=11, LICENSE_RESPONSE=0xF0, CONFIG_UPDATE=0xF7;
    private Tp02Wire(){}

    public static boolean hasHeader(byte[] frame) {
        return frame!=null && frame.length>=4 && (frame[0]&255)==0xAA && (frame[1]&255)==0x55;
    }
    public static int command(byte[] frame){return hasHeader(frame)? frame[2]&255 : -1;}
    public static byte[] control(int cmd) {
        if(cmd<0 || cmd>255) throw new IllegalArgumentException("bad command");
        return new byte[]{(byte)0xAA,0x55,(byte)cmd,0};
    }
    /** BluetoothHelper.onMtuChanged uses sendWrappedData(0xF4). */
    public static byte[] mtuReady(){return control(0xF4);}
    /** CameraActivity.sendOpenCameraResult uses sendWrappedData(0x01): last byte is ZERO. */
    public static byte[] openCameraAck(){return control(OPEN_CAMERA);}
    /** F0 challenge. This does not confer authorization to use the device. */
    public static byte[] licenseRequest(byte[] nonce){
        if(nonce==null || nonce.length!=8)throw new IllegalArgumentException("nonce must contain 8 bytes");
        byte[] req=Arrays.copyOf(control(LICENSE_RESPONSE),12);
        System.arraycopy(nonce,0,req,4,8);return req;
    }
    public static byte[] newNonce(SecureRandom random) {
        if(random==null)throw new IllegalArgumentException("SecureRandom required");
        byte[] nonce=new byte[8];random.nextBytes(nonce);return nonce;
    }
    /** Capar.decryptLicense XORs device reply bytes with nonce[i modulo 8].
     * The decoded string still requires legitimate account/device binding. */
    public static String decodeDeviceLicense(byte[] reply,byte[] nonce){
        if(command(reply)!=LICENSE_RESPONSE || reply.length<=4)
            throw new IllegalArgumentException("incomplete F0 response");
        if(nonce==null || nonce.length!=8)throw new IllegalArgumentException("nonce unavailable");
        byte[] decoded=new byte[reply.length-4];
        for(int i=0;i<decoded.length;i++)decoded[i]=(byte)(reply[4+i]^nonce[i%nonce.length]);
        return new String(decoded,StandardCharsets.UTF_8);
    }
    /** Header=3, width/height LE16, rotation byte, buffer size LE32: 12 bytes minimum. */
    public static CameraOpen parseOpenCamera(byte[] data) {
        if(command(data)!=OPEN_CAMERA || data.length<12)return null;
        int w=le16(data,3),h=le16(data,5),rotation=data[7]&255;
        long budget=le32(data,8);
        if(w<=0||h<=0||w>4096||h>4096||budget<256||budget>1024*1024)return null;
        return new CameraOpen(w,h,rotation,(int)budget);
    }
    public static Integer parseMtuUpdate(byte[] data){
        if(command(data)!=CONFIG_UPDATE || data.length<5)return null;
        return le16(data,3);
    }
    public static int payloadSize(int mtu){
        if(mtu<23||mtu>517)throw new IllegalArgumentException("invalid ATT MTU");
        return mtu-3;
    }
    private static int le16(byte[] b,int i){return (b[i]&255)|((b[i+1]&255)<<8);}
    private static long le32(byte[] b,int i){
        return ((long)b[i]&255)|(((long)b[i+1]&255)<<8)|
            (((long)b[i+2]&255)<<16)|(((long)b[i+3]&255)<<24);
    }
    public static String hex(byte[] bytes){
        if(bytes==null)return "null";
        StringBuilder s=new StringBuilder();
        for(byte b:bytes){
            if(s.length()>0)s.append(' ');
            s.append(String.format(Locale.ROOT,"%02X",b&255));
        }
        return s.toString();
    }
    public static final class CameraOpen {
        public final int width,height,rotation,maxBytes;
        public CameraOpen(int w,int h,int r,int m){width=w;height=h;rotation=r;maxBytes=m;}
    }
}
