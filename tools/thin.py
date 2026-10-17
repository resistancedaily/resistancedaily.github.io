import json,re,sys
def thin(d,minpx=1.6):
    out=[]
    for ring in re.findall(r'M[^M]*',d):
        closed=ring.rstrip().endswith('Z')
        pts=[tuple(map(float,p.split(','))) for p in re.findall(r'-?[\d.]+,-?[\d.]+',ring)]
        if not pts: continue
        k=[pts[0]]
        for p in pts[1:]:
            if (p[0]-k[-1][0])**2+(p[1]-k[-1][1])**2>=minpx**2: k.append(p)
        if len(k)<3: continue
        out.append('M'+'L'.join(f'{x:.0f},{y:.0f}' for x,y in k)+('Z' if closed else ''))
    return ''.join(out)
d=json.load(open(sys.argv[1]))
for key in d:
    d[key]=re.sub(r'(class="land" d=")([^"]*)"',lambda m:m.group(1)+thin(m.group(2))+'"',d[key])
json.dump(d,open(sys.argv[1],'w'))
