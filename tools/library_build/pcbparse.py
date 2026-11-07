"""Footprint Data-stream parser: pads, tracks, arcs, bodies (mm). Reading a whole PcbLib needs olefile."""
import struct, sys, json
MM=0.00000254
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def i32(b,o): return struct.unpack_from('<i',b,o)[0]
def blk(d,o):
    n=u32(d,o); return d[o+4:o+4+n], o+4+n
def props(b):
    s=b.rstrip(b'\x00').decode('latin-1'); r={}
    for p in s.split('|'):
        if '=' in p: k,v=p.split('=',1); r[k.upper()]=v
    return r
def parse_fp(d):
    name_b,o=blk(d,0); name=name_b[1:].decode('latin-1')
    pads=[];bodies=[];prims={};tracks=[];arcs=[]
    while o<len(d):
        t=d[o]; o+=1
        if t==2:
            nb,o=blk(d,o); pname=nb[1:].decode('latin-1')
            _,o=blk(d,o); _,o=blk(d,o); _,o=blk(d,o)
            m,o=blk(d,o); _,o=blk(d,o)
            x=i32(m,13)*MM; y=i32(m,17)*MM; sx=i32(m,21)*MM; sy=i32(m,25)*MM
            hole=i32(m,45)*MM; shape=m[49]; rot=struct.unpack_from('<d',m,52)[0]
            pads.append(dict(n=pname,layer=m[0],x=round(x,4),y=round(y,4),sx=round(sx,4),sy=round(sy,4),hole=round(hole,4),shape=shape,rot=round(rot,2)))
        elif t in (1,3,4,6,11,12):
            b,o=blk(d,o); prims[t]=prims.get(t,0)+1
            if t==4:
                tracks.append(dict(layer=b[0],x1=i32(b,13)*MM,y1=i32(b,17)*MM,x2=i32(b,21)*MM,y2=i32(b,25)*MM,w=i32(b,29)*MM))
            if t==1:
                arcs.append(dict(layer=b[0],x=i32(b,13)*MM,y=i32(b,17)*MM,r=i32(b,21)*MM,w=i32(b,45)*MM))
            if t==12:
                i=b.find(b'V7_LAYER'); 
                bodies.append(props(b[b.find(b'V7_LAYER')-0:] if i>=0 else b[4:]))
        elif t==5:
            b,o=blk(d,o); _,o=blk(d,o); prims[5]=prims.get(5,0)+1
        else:
            raise ValueError('unknown rec %d at %d'%(t,o))
    return name,pads,bodies,prims,tracks,arcs
def load(path):
    import olefile
    ole=olefile.OleFileIO(path); out={}
    for e in ole.listdir():
        if len(e)==2 and e[1]=='Data' and e[0] not in ('Library','FileVersionInfo'):
            try:
                pr=props(ole.openstream((e[0],'Parameters')).read()[4:])
                name,pads,bodies,prims,tracks,arcs=parse_fp(ole.openstream(e).read())
                out[pr.get('PATTERN',name)]=dict(storage=e[0],pads=pads,height=pr.get('HEIGHT'),desc=pr.get('DESCRIPTION'),
                    models=[b.get('MODELID') for b in bodies if b.get('MODELID')],prims=prims,tracks=tracks,arcs=arcs,bodies=bodies)
            except Exception as ex:
                out[e[0]]={'error':str(ex)}
    return out
if __name__=='__main__':
    r=load(sys.argv[1])
    for k,v in r.items():
        print(k, v.get('error') or (v['height'], v['desc'], v['prims'], v['models']))
        for p in v.get('pads',[]): print('   ',p)
