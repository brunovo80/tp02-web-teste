package br.com.tp02.interop;

import java.security.SecureRandom;
import java.util.Arrays;

/** Never treats possession of an F0 license string as vendor authorization. */
public final class Tp02Session {
    public enum State {DISCONNECTED, CONNECTED, GATT_READY, LICENSE_PENDING,
        WAITING_FOR_AUTHORIZATION, AUTHORIZED, CAMERA_OPEN}
    private State state=State.DISCONNECTED;
    private byte[] nonce;
    private String license;
    public State state(){return state;}
    public void reset(){
        state=State.DISCONNECTED;
        if(nonce!=null)Arrays.fill(nonce,(byte)0);
        nonce=null;license=null;
    }
    public void onConnected(){reset();state=State.CONNECTED;}
    public void onGattReady(){require(State.CONNECTED);state=State.GATT_READY;}
    public byte[] mtuReadyMessage(){require(State.GATT_READY);return Tp02Wire.mtuReady();}
    /** Existing binding requires trustworthy external proof from an authorized provider. */
    public void onExistingBindingValidated(){require(State.GATT_READY);state=State.AUTHORIZED;}
    public byte[] beginLicenseRequest(SecureRandom random){
        require(State.GATT_READY);
        nonce=Tp02Wire.newNonce(random);
        state=State.LICENSE_PENDING;
        return Tp02Wire.licenseRequest(nonce);
    }
    public void acceptLicenseResponse(byte[] reply){
        require(State.LICENSE_PENDING);
        license=Tp02Wire.decodeDeviceLicense(reply,nonce);
        Arrays.fill(nonce,(byte)0);nonce=null;
        state=State.WAITING_FOR_AUTHORIZATION;
    }
    /** Sensitive: do not log or send to any service not explicitly authorized. */
    public String licenseForAuthorizedBinding(){
        require(State.WAITING_FOR_AUTHORIZATION);
        return license;
    }
    public void bindingConfirmedByAuthorizedProvider(boolean success){
        require(State.WAITING_FOR_AUTHORIZATION);
        if(success){license=null;state=State.AUTHORIZED;}
    }
    public byte[] onOpenCamera(byte[] request){
        require(State.AUTHORIZED);
        if(Tp02Wire.parseOpenCamera(request)==null)
            throw new IllegalArgumentException("invalid camera request");
        state=State.CAMERA_OPEN;
        return Tp02Wire.openCameraAck();
    }
    public boolean mayStream(){return state==State.CAMERA_OPEN;}
    private void require(State expected){
        if(state!=expected)throw new IllegalStateException("Expected "+expected+", got "+state);
    }
}
