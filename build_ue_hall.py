"""UE editor Python. Creates the dedicated /Game/GuansClub content and level."""
import unreal as u
import json
from pathlib import Path

ROOT = Path(u.Paths.project_dir()).resolve()
REPORT = ROOT / 'build_report.json'
u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
assets = u.AssetToolsHelpers.get_asset_tools()
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
DEST = '/Game/GuansClub'
MAP = DEST + '/FencingHall'
u.EditorAssetLibrary.make_directory(DEST)

def prop(obj, key, value):
    obj.set_editor_property(key, value)

def spawn(cls, name, xyz, rot=(0,0,0)):
    a = actors.spawn_actor_from_class(cls, u.Vector(*xyz), u.Rotator(*rot))
    a.set_actor_label(name)
    return a

assert levels.new_level(MAP), 'Unable to create dedicated hall map'
options = u.FbxImportUI()
prop(options, 'import_mesh', True)
prop(options, 'import_as_skeletal', False)
prop(options, 'automated_import_should_detect_type', False)
prop(options, 'mesh_type_to_import', u.FBXImportType.FBXIT_STATIC_MESH)
prop(options, 'import_materials', True)
prop(options, 'import_textures', False)
mi = options.static_mesh_import_data
for key,val in {'combine_meshes':True,'auto_generate_collision':False,'convert_scene':True,'convert_scene_unit':True,'transform_vertex_to_absolute':True,'generate_lightmap_u_vs':False,'build_nanite':False}.items():
    prop(mi,key,val)
task = u.AssetImportTask()
for key,val in {'filename':str(ROOT/'SourceAssets'/'Hall'/'fencing_hall.fbx'),'destination_path':DEST+'/Meshes','destination_name':'SM_FencingHall','automated':True,'replace_existing':True,'save':True,'options':options}.items():
    prop(task,key,val)
prop(task, 'factory', u.FbxFactory())
assets.import_asset_tasks([task])
meshes = [u.load_asset(p) for p in task.imported_object_paths if isinstance(u.load_asset(p),u.StaticMesh)]
assert len(meshes)==1, f'Expected combined hall mesh: {task.imported_object_paths}'
mesh=meshes[0]
prop(mesh.get_editor_property('body_setup'),'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)

# Recreate simple PBR materials, including light-strip emission.
specs={
    'Warm_plaster':((.78,.80,.78),0,.65,0),
    'Graphite_steel':((.035,.052,.067),.65,.5,0),
    'Slate_sports_floor':((.12,.16,.18),0,.78,0),
    'Aluminium_piste':((.46,.52,.56),.7,.35,0),
    'Teal_accent':((.015,.30,.32),.2,.5,0),
    'Piste_end_zones':((.17,.25,.30),.6,.5,0),
    'Oak_benches':((.48,.27,.12),0,.55,0),
    'Light_diffuser':((.86,.95,1),0,.3,8),
    'White_lettering':((.86,.92,.92),0,.5,0),
    'Red_indicator':((.7,.015,.02),0,.4,3),
    'Green_indicator':((.03,.7,.23),0,.4,3)
}
mat_report=[]
for i,slot in enumerate(mesh.static_materials):
    name=str(slot.material_slot_name).replace(' ','_')
    spec=next((v for k,v in specs.items() if k.lower() in name.lower()),None)
    assert spec is not None, f'Unmapped material slot: {name}'
    color,metal,rough,emission=spec
    mat=assets.create_asset('M_'+name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
    if mat is None: mat=u.load_asset(DEST+'/Materials/M_'+name)
    u.MaterialEditingLibrary.delete_all_material_expressions(mat)
    c=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-400,0)
    prop(c,'constant',u.LinearColor(*color,1))
    u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
    for param,value in [(u.MaterialProperty.MP_METALLIC,metal),(u.MaterialProperty.MP_ROUGHNESS,rough)]:
        n=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant)
        prop(n,'r',value)
        u.MaterialEditingLibrary.connect_material_property(n,'',param)
    if emission:
        e=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector)
        prop(e,'constant',u.LinearColor(*(v*emission for v in color),1))
        u.MaterialEditingLibrary.connect_material_property(e,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    u.MaterialEditingLibrary.recompile_material(mat)
    mesh.set_material(i,mat)
    mat_report.append(name)

hall=spawn(u.StaticMeshActor,'Guans Fencing Club',(0,0,0))
comp=hall.static_mesh_component
comp.set_static_mesh(mesh)
comp.set_collision_profile_name('BlockAll')
comp.set_mobility(u.ComponentMobility.STATIC)
origin,extent=hall.get_actor_bounds(False)
assert 1200<extent.x<1400 and 800<extent.y<1000 and 250<extent.z<350, f'Unexpected hall size {extent}'

for x in [-900,-300,300,900]:
    for y in [-310,310]:
        lamp=spawn(u.RectLight,'Ceiling panel', (x,y,473),(-90,0,0))
        lc=lamp.get_component_by_class(u.RectLightComponent)
        lc.set_mobility(u.ComponentMobility.MOVABLE)
        prop(lc,'intensity_units',u.LightUnits.LUMENS)
        lc.set_intensity(7000)
        prop(lc,'attenuation_radius',2000)
        prop(lc,'source_width',335)
        prop(lc,'source_height',18)
for x in [-900,0,900]:
    a=spawn(u.PointLight,'Soft interior fill',(x,0,330))
    lc=a.point_light_component
    lc.set_mobility(u.ComponentMobility.MOVABLE)
    prop(lc,'intensity_units',u.LightUnits.LUMENS)
    lc.set_intensity(1800)
    prop(lc,'attenuation_radius',1600)
    prop(lc,'cast_shadows',False)

pp=spawn(u.PostProcessVolume,'Interior exposure',(0,0,200))
prop(pp,'unbound',True)
settings=pp.get_editor_property('settings')
for k,v in {'override_auto_exposure_min_brightness':True,'override_auto_exposure_max_brightness':True,'auto_exposure_min_brightness':5.0,'auto_exposure_max_brightness':5.0,'override_vignette_intensity':True,'vignette_intensity':.15,'override_motion_blur_amount':True,'motion_blur_amount':0.0}.items(): prop(settings,k,v)
prop(pp,'settings',settings)

start=spawn(u.PlayerStart,'Entrance - player start',(-1080,0,110))
gm=u.load_class(None,'/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode.BP_FirstPersonGameMode_C')
assert gm, 'Template game mode missing'
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
prop(world.get_world_settings(),'default_game_mode',gm)
for index,y in [(1,310),(2,-310)]:
    anchor=spawn(u.TargetPoint,f'ReplayOrigin_Piste_{index:02}',(0,y,6))
    prop(anchor,'tags',[f'ReplayOrigin_Piste_{index:02}'])

# Prevent walking out into empty space while keeping the doorway visibly open.
barrier=spawn(u.StaticMeshActor,'Entry safety boundary',(-1310,0,150))
bc=barrier.static_mesh_component
bc.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube.Cube'))
barrier.set_actor_scale3d(u.Vector(.1,5,3))
bc.set_collision_profile_name('BlockAll')
barrier.set_actor_hidden_in_game(True)

u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(-1120,0,175),u.Rotator(0,0,0))
assert levels.save_current_level()
u.EditorAssetLibrary.save_directory(DEST,only_if_is_dirty=False,recursive=True)
report={'map':MAP,'mesh':mesh.get_path_name(),'extent_cm':[extent.x,extent.y,extent.z],'materials':mat_report,'game_mode':gm.get_path_name(),'actor_count':len(actors.get_all_level_actors()),'status':'built; gameplay validation pending'}
REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('GUANS_HALL_BUILD_COMPLETE '+json.dumps(report))
