import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'SourceAssets/tip_samples.json').read_text())
assert not data['error'],data['error']
for idx in range(2):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pts=[Vector((s['tips'][idx][0]/100,-s['tips'][idx][1]/100,s['tips'][idx][2]/100)) for s in data['samples']]
    verts=[];faces=[]
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        ref=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
        n=tangent.cross(ref).normalized();b=tangent.cross(n).normalized()
        for j in range(8):verts.append(p+.008*(math.cos(j*math.tau/8)*n+math.sin(j*math.tau/8)*b))
        if i:
            for j in range(8):faces.append(((i-1)*8+j,(i-1)*8+(j+1)%8,i*8+(j+1)%8,i*8+j))
    mesh=bpy.data.meshes.new('Timestamped trail');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('SM_TipTrail_'+str(idx+1),mesh);bpy.context.collection.objects.link(obj)
    uv=mesh.uv_layers.new(name='Timestamp')
    for loop in mesh.loops:uv.data[loop.index].uv=(data['samples'][loop.vertex_index//8]['t'],0)
    for face in mesh.polygons:face.use_smooth=True
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(ROOT/f'SourceAssets/tip_trail_{idx+1}.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',bake_anim=False,mesh_smooth_type='FACE')
print('TIP_TRAIL_GEOMETRY_COMPLETE')
