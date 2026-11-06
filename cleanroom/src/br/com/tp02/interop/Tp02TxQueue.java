package br.com.tp02.interop;

import java.util.Arrays;

/** One BLE packet at a time; next packet only after a write callback. */
public final class Tp02TxQueue {
    private byte[] bytes;
    private int offset,chunkSize,acknowledged;
    private boolean awaitingCallback;
    public boolean begin(byte[] data,int negotiatedMtu){
        if(isBusy()||data==null||data.length==0)return false;
        int packet=Tp02Wire.payloadSize(negotiatedMtu);
        bytes=Arrays.copyOf(data,data.length);
        offset=0;acknowledged=0;chunkSize=packet;awaitingCallback=false;
        return true;
    }
    public byte[] nextPacket(){
        if(bytes==null||awaitingCallback||offset>=bytes.length)return null;
        int end=Math.min(bytes.length,offset+chunkSize);
        byte[] chunk=Arrays.copyOfRange(bytes,offset,end);
        offset=end;awaitingCallback=true;return chunk;
    }
    public void onWriteResult(boolean success){
        if(bytes==null||!awaitingCallback)throw new IllegalStateException("unexpected BLE callback");
        if(!success){reset();return;}
        awaitingCallback=false;acknowledged=offset;
        if(acknowledged==bytes.length){Arrays.fill(bytes,(byte)0);bytes=null;}
    }
    public boolean isBusy(){return bytes!=null;}
    public int acknowledgedBytes(){return acknowledged;}
    public void reset(){
        if(bytes!=null)Arrays.fill(bytes,(byte)0);
        bytes=null;offset=0;chunkSize=0;acknowledged=0;awaitingCallback=false;
    }
}
