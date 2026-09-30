import bpy,math
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
def mat(name,c,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=.3 if metal else .65
    return m
steel=mat('Sabre Steel',(.48,.55,.62),.85)
grip=mat('Sabre Grip',(.022,.028,.035))
def mesh(name,verts,faces,material):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.data.materials.append(material);return o
def cylinder(name,x,depth,radius,material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=depth,location=(x,0,0),rotation=(0,math.pi/2,0))
    o=bpy.context.object;o.name=name;o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o
cylinder('Textured grip',-.0125,.125,.013,grip)
cylinder('Pommel',-.084,.018,.017,steel)
for x in [-.064,-.045,-.026,-.007,.012,.031]:cylinder('Grip seam',x,.003,.014,grip)
# Narrow, straight, tapering sabre blade. Slightly thickened for desktop visibility.
verts=[]
for x,w,t in [(.085,.014,.005),(.88,.007,.0035),(.965,.005,.0035)]:
    verts += [(x,-w/2,-t/2),(x,w/2,-t/2),(x,w/2,t/2),(x,-w/2,t/2)]
faces=[(0,3,2,1),(8,9,10,11)]
for j in [0,4]:
    for k in range(4):faces.append((j+k,j+(k+1)%4,j+4+(k+1)%4,j+4+k))
mesh('Blade',verts,faces,steel)
# Bowl guard, open toward the grip, and a curved knuckle bow.
verts=[];faces=[]
for row in range(9):
    a=.09+(math.pi/2-.09)*row/8
    for j in range(40):
        q=2*math.pi*j/40
        verts.append((.05+.035*math.cos(a),.065*math.sin(a)*math.cos(q),.078*math.sin(a)*math.sin(q)))
for row in range(8):
    for j in range(40):faces.append((row*40+j,row*40+(j+1)%40,(row+1)*40+(j+1)%40,(row+1)*40+j))
o=mesh('Bowl guard',verts,faces,steel)
s=o.modifiers.new('Guard thickness','SOLIDIFY');s.thickness=.0025
for p in o.data.polygons:p.use_smooth=True
curve=bpy.data.curves.new('Knuckle bow','CURVE');curve.dimensions='3D';curve.bevel_depth=.006;curve.bevel_resolution=3
sp=curve.splines.new('BEZIER');sp.bezier_points.add(3)
for b,co in zip(sp.bezier_points,[(.05,0,-.077),(-.015,0,-.10),(-.08,0,-.068),(-.09,0,0)]):b.co=co;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
ob=bpy.data.objects.new('Knuckle bow',curve);bpy.context.collection.objects.link(ob);ob.data.materials.append(steel)
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=o
bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
sabre=bpy.context.object;sabre.name='SM_Sabre';bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'sabre.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',bake_anim=False,mesh_smooth_type='FACE')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sabre.blend'))
# Screen has explicit UVs: readable from the south aisle looking toward +Y in UE.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
screen=mesh('SM_TVScreen',[(3.2,0,-1.8),(-3.2,0,-1.8),(-3.2,0,1.8),(3.2,0,1.8)],[(0,1,2,3)],mat('Screen placeholder',(.01,.01,.01)))
uv=screen.data.uv_layers.new(name='UVMap')
for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=co
screen.select_set(True);bpy.context.view_layer.objects.active=screen
bpy.ops.export_scene.fbx(filepath=str(OUT/'tv_screen.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',bake_anim=False,mesh_smooth_type='FACE')
print('TV_SABRE_GEOMETRY_COMPLETE')
