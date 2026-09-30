"""Run with Blender 3.6+: blender --background --python build_hall.py"""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
bpy.context.preferences.filepaths.save_version = 0
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1

def material(name, color, metal=0, rough=.5, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = rough
    if emission:
        bs.inputs['Emission'].default_value = (*color, 1)
        bs.inputs['Emission Strength'].default_value = emission
    return m

white = material('Warm plaster', (.78,.80,.78))
dark = material('Graphite steel', (.035,.052,.067), .65)
floor = material('Slate sports floor', (.12,.16,.18), 0, .78)
silver = material('Aluminium piste', (.46,.52,.56), .7, .35)
teal = material('Teal accent', (.015,.30,.32), .2)
endzone = material('Piste end zones', (.17,.25,.30), .6)
wood = material('Oak benches', (.48,.27,.12), 0, .55)
lightmat = material('Light diffuser', (.86,.95,1), 0, .3, 3)
ink = material('White lettering', (.86,.92,.92), 0, .5)
red = material('Red indicator', (.7,.015,.02), 0,.4,2)
green = material('Green indicator', (.03,.7,.23), 0,.4,2)

def box(name, loc, dims, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        o.data.use_auto_smooth = True
        mod = o.modifiers.new('Soft edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return o

def text(name, body, loc, size, mat, rotation=(math.pi/2,0,0), align='CENTER'):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.size = size
    curve.align_x = align
    curve.extrude = .001
    o = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rotation
    o.data.materials.append(mat)
    return o

def area(name, loc, target, power, size, color=(1,1,1)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    data.color = color
    o = bpy.data.objects.new(name, data)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

box('Hall floor', (0,0,-.13), (26,18,.25), floor)
box('North wall', (0,9,2.8), (26,.25,5.6), white)
box('South wall', (0,-9,2.8), (26,.25,5.6), white)
box('East feature wall', (13,0,2.8), (.25,18,5.6), dark)
# Entry opening in the west wall.
for y in [-5.75,5.75]:
    box('Entry wall', (-13,y,2.8), (.25,6.5,5.6), white)
box('Entry lintel', (-13,0,4.6), (.25,5,2), white)
box('Ceiling', (0,0,5.65), (26,18,.15), white)

for y in [-8.82,8.82]:
    box('Wall accent band', (0,y,1.15), (25.8,.05,.13), teal)
    for x in [-10,-6,-2,2,6,10]:
        box('Acoustic panel', (x,y,2.35), (2.8,.10,1.45), dark, .035)
        for offset in [-1,-.5,0,.5,1]:
            box('Acoustic ribs', (x+offset,y- (.07 if y>0 else -.07),2.35), (.025,.035,1.4), teal)

for lane, y in enumerate([-3.1,3.1],1):
    box(f'Piste_{lane}_base', (0,y,.025), (14,1.5,.05), silver, .01)
    for x in [-6,6]:
        box(f'Piste_{lane}_end', (x,y,.052), (2,1.5,.004), endzone)
    for x in [-7,-5,-2,0,2,5,7]:
        box(f'Piste_{lane}_line', (x,y,.056), (.035,1.5,.005), ink)
    for edge in [-.80,.80]:
        box('Piste border', (0,y+edge,.004), (14.3,.035,.006), teal)
    for x in [-7.9,7.9]:
        text(f'Lane_{lane}_floor_number', f'0{lane}', (x,y,.006), .55, ink, (0,0,math.pi/2))
    # Logical anchor: movement/animation origin at the centre of the piste surface.
    anchor = bpy.data.objects.new(f'ReplayOrigin_Piste_{lane:02}', None)
    scene.collection.objects.link(anchor)
    anchor.location = (0,y,.06)
    anchor.empty_display_type = 'ARROWS'
    anchor.empty_display_size = .5
    box('Scoreboard plinth', (9.2,y,.12), (.8,.7,.24), dark, .03)
    box('Scoreboard mast', (9.2,y,.95), (.08,.08,1.5), dark)
    board = box('Scoreboard', (9.2,y,1.75), (.18,1.5,.65), dark, .035)
    # Face the entrance; decorative static score, no match logic.
    text(f'Score_{lane}', '00   00', (9.09,y,1.66), .23, ink, (math.pi/2,0,-math.pi/2))
    box('Red signal', (9.09,y+.60,1.99), (.015,.18,.06), red)
    box('Green signal', (9.09,y-.60,1.99), (.015,.18,.06), green)

for y in [-7,7]:
    for x in [-8,-3,2,7]:
        box('Oak bench seat', (x,y,.47), (3.5,.58,.12), wood, .04)
        for dx in [-1.35,1.35]:
            box('Bench legs', (x+dx,y,.23), (.10,.48,.46), dark, .015)
    for x in [-10.5,10.5]:
        box('Storage cabinet', (x,y,.9), (1,.8,1.8), dark, .025)
        for dx in [-.25,0,.25]:
            box('Cabinet door trim', (x+dx,y+(-.41 if y>0 else .41),.9), (.015,.025,1.65), teal)

for x in [-9,-3,3,9]:
    box('Roof beam', (x,0,5.35), (.16,18,.25), dark)
    for y in [-3.1,3.1]:
        box('Suspended luminaire', (x,y,4.85), (3.5,.22,.12), dark, .02)
        box('Luminaire diffuser', (x,y,4.78), (3.35,.18,.025), lightmat)
        area('Training light', (x,y,4.7), (x,y,0), 450, 3)

text('Club wordmark', "Guan's Fencing Club", (12.84,0,3.75), .75, ink, (math.pi/2,0,-math.pi/2))
text('Club subtitle', 'T R A I N I N G   H A L L', (12.83,0,3.05), .24, ink, (math.pi/2,0,-math.pi/2))
area('Entry soft light', (-11,0,4), (0,0,1), 1000, 6, (.80,.9,1))

scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.18,.22,.28,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_gtao = True
scene.eevee.gtao_distance = 3
scene.eevee.gtao_factor = 1.25
scene.eevee.use_soft_shadows = True
scene.eevee.taa_render_samples = 64
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = .6
scene.render.resolution_x = 1200
scene.render.resolution_y = 780
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

def camera(name, loc, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_end = 150
    o = bpy.data.objects.new(name, data)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o

cameras = [
    camera('Entrance view', (-11.8,-.7,2.5), (2,0,1.2), 22),
    camera('Piste side view', (-8,-7.7,2.9), (1.7,1,1.2), 23),
    camera('Spectator view', (5.5,7.7,1.7), (-2,-1,.9), 24),
]
scene.camera = cameras[0]
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type == 'VIEW_3D':
            a.spaces.active.clip_end = 150
            a.spaces.active.region_3d.view_perspective = 'CAMERA'

manifest = {
    'units': 'metres', 'hall_size': [26,18,5.6],
    'blender_coordinates': 'Z up; piste length along X',
    'replay_origins': [{'name':f'ReplayOrigin_Piste_{i:02}', 'position':[0,y,.06], 'piste_length':14, 'piste_width':1.5} for i,y in enumerate([-3.1,3.1],1)],
    'note': 'Layout prototype. No replay, collision, or player controller implemented. Validate scale and axes after UE import.'
}
(OUT/'scene_manifest.json').write_text(json.dumps(manifest,indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'fencing_hall.blend'))
# Convert a copy of the scene for export so text remains editable in the .blend.
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','FONT'}:
        o.select_set(True)
bpy.context.view_layer.objects.active = next(o for o in scene.objects if o.type == 'MESH')
bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.fbx(filepath=str(OUT/'fencing_hall.fbx'), use_selection=True, object_types={'MESH'}, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Y', axis_up='Z', bake_anim=False)
for i, cam in enumerate(cameras, 1):
    scene.camera = cam
    scene.render.filepath = str(OUT/f'preview_{i:02}.png')
    bpy.ops.render.render(write_still=True)
print('HALL_BUILD_COMPLETE', len(scene.objects), 'objects')
