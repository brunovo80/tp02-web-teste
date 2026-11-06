import br.com.tp02.interop.*;
import java.security.SecureRandom;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public final class Tp02ProtocolTest {
    private static int count=0;
    private static void ok(boolean pass,String name) {
        count++;if(!pass)throw new AssertionError(name);
    }
    private static void rejects(Runnable action,String name){
        boolean thrown=false;
        try{action.run();}catch(IllegalArgumentException|IllegalStateException e){thrown=true;}
        ok(thrown,name);
    }
    public static void main(String[] args){
        byte[] camera={(byte)0xAA,0x55,1,(byte)0xA0,0,(byte)0xC0,0,0,0,0x3C,0,0};
        ok(Tp02Wire.hex(Tp02Wire.openCameraAck()).equals("AA 55 01 00"),"Capar open camera ACK");
        ok(Tp02Wire.hex(Tp02Wire.mtuReady()).equals("AA 55 F4 00"),"post-MTU F4");
        Tp02Wire.CameraOpen p=Tp02Wire.parseOpenCamera(camera);
        ok(p!=null&&p.width==160&&p.height==192&&p.rotation==0&&p.maxBytes==15360,"camera fields");
        ok(Tp02Wire.parseOpenCamera(Arrays.copyOf(camera,11))==null,"truncated camera");
        ok(Tp02Wire.parseOpenCamera(new byte[]{0,0,0,0})==null,"bad header");
        ok(Tp02Wire.parseOpenCamera(new byte[]{(byte)0xAA,0x55,1,0,0,0,0,0,0,0,0,0})==null,"bad dimensions");
        ok(Tp02Wire.payloadSize(23)==20&&Tp02Wire.payloadSize(517)==514,"ATT MTU chunk");
        rejects(()->Tp02Wire.payloadSize(22),"invalid MTU");
        ok(Tp02Wire.command(new byte[]{(byte)0xAA,0x55,0x0A,0})==10,"+");
        ok(Tp02Wire.command(new byte[]{(byte)0xAA,0x55,0x0B,0})==11,"-");
        ok(Tp02Wire.command(new byte[]{(byte)0xAA,0x55,0x06,0})==6,"flip");
        ok(Tp02Wire.command(new byte[]{(byte)0xAA,0x55,0x02,0})==2,"shutter");
        ok(Tp02Wire.command(new byte[]{(byte)0xAA,0x55,0x03,0})==3,"frame requested");
        byte[] nonce={1,2,3,4,5,6,7,8};
        ok(Tp02Wire.hex(Tp02Wire.licenseRequest(nonce)).equals("AA 55 F0 00 01 02 03 04 05 06 07 08"),"license F0 nonce");
        rejects(()->Tp02Wire.licenseRequest(new byte[7]),"nonce length");
        byte[] plain="DEMO-LICENSE".getBytes(StandardCharsets.UTF_8),reply=Arrays.copyOf(Tp02Wire.control(0xF0),plain.length+4);
        for(int i=0;i<plain.length;i++)reply[4+i]=(byte)(plain[i]^nonce[i%8]);
        ok(Tp02Wire.decodeDeviceLicense(reply,nonce).equals("DEMO-LICENSE"),"license device XOR");
        rejects(()->Tp02Wire.decodeDeviceLicense(reply,new byte[7]),"decrypt wrong nonce");
        ok(Tp02Wire.parseMtuUpdate(new byte[]{(byte)0xAA,0x55,(byte)0xF7,0x2c,1})==300,"F7 little endian");
        ok(Tp02Wire.parseMtuUpdate(new byte[]{(byte)0xAA,0x55,(byte)0xF7})==null,"F7 truncated");
        Tp02Session state=new Tp02Session();
        rejects(()->state.mtuReadyMessage(),"must connect");
        state.onConnected();state.onGattReady();
        ok(Tp02Wire.hex(state.mtuReadyMessage()).equals("AA 55 F4 00"),"state F4");
        ok(state.beginLicenseRequest(new SecureRandom()).length==12,"request license");
        ok(state.state()==Tp02Session.State.LICENSE_PENDING,"license pending");
        rejects(()->state.onOpenCamera(camera),"auth required");
        state.reset();state.onConnected();state.onGattReady();state.onExistingBindingValidated();
        ok(Tp02Wire.hex(state.onOpenCamera(camera)).equals("AA 55 01 00"),"authorized camera ACK");
        ok(state.mayStream(),"stream after authorization");
        state.reset();ok(!state.mayStream(),"disconnect clears state");
        System.out.println("PASS: "+count+" wire protocol and authorization state tests.");
    }
}
