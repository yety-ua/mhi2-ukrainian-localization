# Parse dumb_persistence_reader output; accept one unambiguous CRC-valid blob.
# No bitwise awk extensions required. Usage: awk -v bytes=389 -f blob.awk file
function xor(a,b, r,p,x,y) {
    r=0; p=1
    while (a || b) {
        x=a%2; y=b%2; if (x!=y) r+=p
        a=int(a/2); b=int(b/2); p*=2
    }
    return r
}
function hex(s, n,i,c) {
    n=0; s=toupper(s)
    for(i=1;i<=length(s);i++) {
        c=index("0123456789ABCDEF",substr(s,i,1))-1
        if(c<0) return -1
        n=n*16+c
    }
    return n
}
function valid(s, crc,i,j,b) {
    if(length(s)!=bytes*2 || s ~ /[^0-9A-F]/) return 0
    crc=65535
    for(i=1;i<=length(s)-4;i+=2) {
        b=hex(substr(s,i,2)); crc=xor(crc,b*256)
        for(j=0;j<8;j++) {
            if(crc>=32768) crc=xor((crc*2)%65536,4129)
            else crc=(crc*2)%65536
        }
    }
    return crc==hex(substr(s,length(s)-3,4))
}
function candidate(s) {
    s=toupper(s)
    if(valid(s) && !seen[s]++) { answer=s; answers++ }
}
{
    line=$0
    gsub(/[^0-9A-Za-z_]/," ",line)
    n=split(line,tokens,/ +/)
    for(k=1;k<=n;k++) {
        t=tokens[k]
        if(t=="") continue
        if(length(t)==bytes*2) candidate(t)
        if(t ~ /^0[xX]/) t=substr(t,3)
        if(length(t)==2 && t !~ /[^0-9a-fA-F]/) {
            run=run t; count++
            if(count==bytes) candidate(run)
        } else { run=""; count=0 }
    }
}
END {
    if(answers!=1) exit 1
    print answer
}
